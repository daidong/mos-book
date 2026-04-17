# Chapter 6: Container Foundations — Namespaces and Cgroups

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Name the seven Linux namespace types and explain what each
>   isolates
> - Describe how `task_struct` fields implement container identity
> - Use cgroup v2 controllers to enforce CPU, memory, and I/O limits
> - Explain how rootless containers work via user namespace UID
>   mapping
> - Describe the role of `pivot_root` and OverlayFS in filesystem
>   isolation

Chapter 5 ended at the boundary of a single machine. This chapter
stays inside the same machine but shrinks the unit of isolation:
from "all processes share everything" to "each container sees a
private system view". The surprise, if you have not seen it before,
is that a container is *not* a new kind of object. It is an
ordinary Linux process that has been given two things: a restricted
view (namespaces) and a resource budget (cgroups). The container
runtime is just a small program that composes them.

## 6.1 What Is a Container?

A container is not a VM. A VM emulates hardware and runs its own
kernel; a container shares the host kernel. The boundary of a
container is not a hypervisor — it is a collection of kernel
mechanisms applied to the processes inside.

Two mechanisms do almost all of the work:

- **Namespaces** control **what the process can see**. Each namespace
  type (PID, network, mount, user, …) gives the process a private
  view of a kernel resource.
- **Cgroups** control **what the process can use**. Each controller
  (CPU, memory, I/O, pids) caps or accounts for a specific resource.

Everything else — images, registries, image layers, Kubernetes —
builds on top of those two primitives. Liz Rice's "Containers from
Scratch" talk makes the point with a hundred lines of Go; the lab at
the end of this chapter makes the point with a few hundred lines of
C. When you can build a container runtime from `clone()` and
cgroup writes, you stop thinking of containers as magic.

> **Key insight:** Containers do not add new OS abstractions; they
> partition existing ones. PID namespaces partition the process
> table. Mount namespaces partition the mount tree. cgroup memory
> partitions physical RAM. Once you see the pattern, every "new"
> container feature becomes "oh, a new namespace" or "oh, a new
> cgroup controller".

## 6.2 Linux Namespaces

Linux currently has **seven namespace types** (eight if you count
the `time` namespace, which is newer and rarely relevant to this
book). Each gets its own section of `man 7 namespaces`; for this
book, the one-line summaries are enough:

| Namespace | What it isolates |
|---|---|
| **UTS** | Hostname and domain name |
| **PID** | Process IDs — each namespace has its own PID 1 |
| **Mount (MNT)** | Mount table — `/proc/mounts` is per-namespace |
| **Network (NET)** | Network interfaces, routing tables, sockets, ports |
| **User (USER)** | UIDs and GIDs — plus the kernel-visible "am I root?" |
| **IPC** | System V IPC, POSIX message queues |
| **Cgroup** | The root of the cgroup tree a process sees |

A container typically enters all of these at once. A "container" as
the user understands it is the set of processes sharing those seven
namespaces plus a cgroup.

### Creating namespaces: `clone` and `unshare`

Two syscalls do the work. `clone()` creates a new process (like
`fork`) with additional flags that put the new process into new
namespaces:

```c
#define _GNU_SOURCE
#include <sched.h>

int flags = CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS
          | CLONE_NEWUSER;
pid_t child = clone(child_fn, stack_top, flags | SIGCHLD, arg);
```

`unshare()` is `clone`'s cousin: it detaches the *calling* process
from its current namespace(s) and puts it into new ones. Useful at
the command line:

```bash
# Create a new PID namespace in a new process (needs root by default)
sudo unshare --pid --fork --mount-proc /bin/bash

# Create a new user namespace — unprivileged!
unshare --user --map-root-user /bin/bash
# Inside: `id` reports uid=0, but you are not really root on the host.
```

The last example is the heart of rootless containers, which
Section 6.6 covers.

### Inspecting namespaces: `/proc/<pid>/ns/`

Every process has a small directory of symlinks that identify which
namespace it currently inhabits:

```bash
$ ls -la /proc/$$/ns/
total 0
lrwxrwxrwx 1 dong dong 0 cgroup -> 'cgroup:[4026531835]'
lrwxrwxrwx 1 dong dong 0 ipc    -> 'ipc:[4026531839]'
lrwxrwxrwx 1 dong dong 0 mnt    -> 'mnt:[4026531840]'
lrwxrwxrwx 1 dong dong 0 net    -> 'net:[4026531969]'
lrwxrwxrwx 1 dong dong 0 pid    -> 'pid:[4026531836]'
lrwxrwxrwx 1 dong dong 0 user   -> 'user:[4026531837]'
lrwxrwxrwx 1 dong dong 0 uts    -> 'uts:[4026531838]'
```

Two processes are in the same namespace iff their symlinks point at
the same inode number. This is how `nsenter` works: open one of
these files, call `setns()` to join, and you are inside the
container — no Docker necessary.

## 6.3 The `task_struct` and Container Identity

The kernel does not have a `container` data structure. What it has
is a `task_struct` (the process control block from Chapter 4) with a
pointer called `nsproxy`:

```c
struct task_struct {
    ...
    struct nsproxy *nsproxy;   // the namespaces this task is in
    struct cred    *cred;      // credentials — UID/GID, capabilities
    struct css_set *cgroups;   // cgroup memberships
    ...
};
```

`nsproxy` points at a struct that references each of the namespace
types. When you create a new namespace via `clone`, the kernel
copies the parent's `nsproxy`, replaces the relevant entries with
new namespace objects, and attaches the result to the child.
Different tasks sharing `nsproxy` see the same namespaces; different
tasks with different `nsproxy`s do not. That is the entire
mechanism.

Container identity, then, is not a separate concept. A "container"
is the set of tasks sharing an `nsproxy` (and, typically, a
`css_set`). You can confirm this by noting that Kubernetes, Docker,
and Podman all use exactly the same kernel facilities — they differ
only in how they arrange the runtime, not in what the kernel sees.

## 6.4 Cgroups v2

Where namespaces answer "what can this process see?", **cgroups**
answer "how much can this process use?". A cgroup is a node in a
tree; controllers attached to the tree enforce resource limits and
collect accounting data for every process in the subtree rooted at
that node.

Cgroup v1 had separate hierarchies per controller and was a mess to
reason about. **Cgroup v2** unifies everything into one hierarchy
under `/sys/fs/cgroup`, which is the only version this book uses.
All modern kernels and container runtimes support it.

### The filesystem interface

```bash
$ mount | grep cgroup2
cgroup2 on /sys/fs/cgroup type cgroup2 ...

$ cat /sys/fs/cgroup/cgroup.controllers
cpu io memory pids cpuset hugetlb rdma

$ cat /proc/$$/cgroup
0::/user.slice/user-1000.slice/session-5.scope
```

To make a cgroup, create a directory; to destroy it, `rmdir`. To add
a process, write its PID to `cgroup.procs`. Everything else is
reading and writing files.

### The five files you will touch most

Assume a cgroup at `/sys/fs/cgroup/mylab`:

- **`cgroup.procs`** — list of PIDs in this cgroup. Write a PID to
  add it.
- **`cpu.max`** — `"<quota_us> <period_us>"`. `"50000 100000"` means
  50 ms of CPU per 100 ms — half a CPU. `"max <period>"` means
  unlimited.
- **`memory.max`** — maximum memory usage in bytes. Writing `max`
  removes the limit.
- **`memory.current`** — current usage. Read-only.
- **`memory.events`** — counters: `oom`, `oom_kill`,
  `max`-breaches, `low`-pressure events. Read-only.

A complete example of a 512 MiB memory cap:

```bash
sudo mkdir /sys/fs/cgroup/mylab
echo $((512 * 1024 * 1024)) | sudo tee /sys/fs/cgroup/mylab/memory.max
echo $$ | sudo tee /sys/fs/cgroup/mylab/cgroup.procs
# Your shell (and everything it launches) is now capped at 512 MiB.
```

You will recognize this pattern from Lab 2 in Chapter 3, which used
cgroup memory limits to reproduce a p99 spike.

### How the kernel enforces limits

The mechanism differs per controller:

- **CPU.** The `cpu` controller uses **CFS bandwidth control**. The
  cgroup has a quota and a period; when the quota for the current
  period is exhausted, tasks in the cgroup are **throttled** (moved
  off-runqueue) until the next period. You will see this as spiky
  tail latency in Chapter 7.
- **Memory.** The `memory` controller accounts every page charged
  to tasks in the cgroup. Exceeding `memory.max` triggers reclaim
  first (writing dirty pages, freeing clean cache) and the OOM
  killer if reclaim cannot find enough. `memory.events` increments
  `oom_kill` when a task is killed.
- **I/O.** The `io` controller rate-limits block device I/O via
  `io.max` (bandwidth caps) or `io.weight` (proportional share).
- **PIDs.** The `pids` controller caps the number of processes in
  the cgroup — useful against fork bombs in multi-tenant settings.

All of this is kernel code. The runtime is just a userspace program
that arranges the right writes.

## 6.5 Filesystem Isolation

Mount namespaces give a process a private mount tree, but that is
not enough to make a container. The container also needs:

1. A **rootfs** — a directory that looks like a miniature Linux
   root filesystem (`/bin`, `/lib`, `/etc`, …).
2. A way to make the rootfs the container's root directory.
3. A `/proc` mount that reflects the PID namespace, not the host's.

### `chroot` vs `pivot_root`

`chroot(new_root)` changes the current process's notion of `/` to
`new_root`. It is simple and ancient. It is also escapable — a
process with capabilities can fairly easily break out of a chroot
— and does not detach the old root.

`pivot_root(new_root, put_old)` swaps the current root with
`new_root` and moves the old root to `put_old` (a directory under
the new root). After `pivot_root`, you can `umount` and `rmdir` the
old root, leaving the container's only visible filesystem as the
new one. `pivot_root` is what production runtimes use.

The minimal sequence, adapted from the lab:

```c
// 1. Make mounts private so the container does not disturb the host.
mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL);

// 2. Bind-mount the rootfs onto itself (pivot_root requires this).
mount(rootfs, rootfs, NULL, MS_BIND | MS_REC, NULL);

// 3. Make a place to stash the old root.
mkdir(rootfs "/old_root", 0755);

// 4. Perform the swap.
pivot_root(rootfs, rootfs "/old_root");
chdir("/");
umount2("/old_root", MNT_DETACH);
rmdir("/old_root");

// 5. Mount a fresh /proc (needed for PID namespace correctness).
mount("proc", "/proc", "proc", 0, NULL);
```

### OverlayFS and image layers

A container image is typically a stack of read-only layers plus a
thin writable layer on top. **OverlayFS** is the Linux kernel
filesystem that composes these: a *lowerdir* (read-only, possibly
many stacked), an *upperdir* (writable), and a *merged* view that
reads from the upper layer when present and falls back to the
lowers. Writes copy the modified file into the upper layer
(copy-on-write) — which is why starting a container feels instant:
you are reusing the same lower layers Docker cached yesterday.

For this book, the important observation is that OverlayFS is a
regular Linux filesystem. You can `mount -t overlay` it yourself
without Docker. Image distribution (registries, content-addressable
layers) is a userspace convention built on top.

## 6.6 Rootless Containers

A container whose processes think they are root but are not actually
root on the host is called **rootless**. It is a dramatic security
improvement: if the container escapes any of its namespaces, the
damage is bounded by the *host* UID the namespace maps to, not by
host root.

The mechanism is **user namespaces with UID mapping**. Inside the
new namespace, UID 0 is mapped to (say) host UID 1000. From the
container's perspective:

```bash
$ unshare --user --map-root-user /bin/bash
# id
uid=0(root) gid=0(root) groups=0(root),65534(nobody)
```

From the host's perspective, that `bash` is still running as UID
1000. The kernel enforces operations based on the *host* UID, so
"root" inside the namespace cannot, for example, read
`/etc/shadow` on the host.

The mapping is written to `/proc/<pid>/uid_map` and
`/proc/<pid>/gid_map`:

```c
// inside the parent after clone()
snprintf(path, sizeof(path), "/proc/%d/uid_map", child_pid);
snprintf(content, sizeof(content), "0 %d 1", getuid());
int fd = open(path, O_WRONLY);
write(fd, content, strlen(content));
close(fd);
```

`"0 1000 1"` means "inside the namespace, UID 0 maps to host UID
1000; exactly one UID is mapped". Writing `gid_map` works the same
way, with one quirk: on modern kernels you must also write
`"deny"` to `/proc/<pid>/setgroups` before `gid_map` for an
unprivileged caller.

### What rootless does not buy you

User namespaces do not remove the shared-kernel threat. A kernel bug
that bypasses the namespace check — and several such bugs have been
CVE'd over the years — gives an attacker whatever privilege the
kernel allows. Rootless containers also add attack surface (more
kernel code exposed to unprivileged callers), and every few years a
new class of "user namespace escape" appears.

The net verdict from the security community is still "yes, use
rootless when you can". But it is not a substitute for a hypervisor
for high-assurance isolation. When you really need hardware-level
separation, use a VM (or a lightweight VM like gVisor or
Kata Containers).

## Summary

Key takeaways from this chapter:

- A container is an ordinary process with restricted visibility
  (namespaces) and a resource budget (cgroups). Nothing more.
- Seven namespaces partition distinct kernel resources: UTS, PID,
  Mount, Network, User, IPC, Cgroup. `clone()` and `unshare()`
  create them; `/proc/<pid>/ns/` inspects them.
- Cgroup v2 is a unified filesystem hierarchy at `/sys/fs/cgroup`.
  Controllers enforce CPU (via CFS bandwidth control), memory (via
  OOM), I/O (via `io.max`), and PID limits. Adding a process is
  `echo $PID > /cgroup/path/cgroup.procs`.
- Filesystem isolation uses mount namespaces plus `pivot_root`. A
  typical rootfs is an OverlayFS stack of read-only image layers
  with a writable upper layer.
- Rootless containers map container UID 0 to an unprivileged host
  UID via user namespaces. They reduce risk but do not eliminate
  the shared-kernel threat.

## Further Reading

- Kerrisk, M. (2013–2016). *Namespaces in Operation.* LWN.net series.
  Start at <https://lwn.net/Articles/531114/>.
- Linux kernel documentation: `Documentation/admin-guide/cgroup-v2.rst`.
- Walsh, D. (2019). *Container Security.* O'Reilly Media.
- Rice, L. *Containers from Scratch.* YouTube and her book
  *Container Security* (O'Reilly).
- `man 7 namespaces`, `man 7 cgroups`, `man 2 clone`, `man 2
  unshare`, `man 2 pivot_root`.
- Julia Evans. *What even is a container?*
  <https://jvns.ca/blog/2016/10/10/what-even-is-a-container/>
