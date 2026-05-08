# Lab: Build a Mini Container Runtime

> **Estimated time:** 5–6 hours
>
> **Prerequisites:** Chapter 6 concepts (namespaces, cgroups,
> `chroot`, `pivot_root`); Linux kernel 5.10+ with cgroup v2
>
> **Tools used:** `gcc`, `clone()`, `unshare()`, `mount`,
> cgroup v2 filesystem, Alpine minirootfs

## Objectives

- Implement a minimal container runtime (`minictl`) in three
  progressive stages
- Add isolation layers one at a time (chroot → namespaces →
  cgroups) and observe what each buys you
- Test rootless execution via user-namespace UID mapping
- Measure the startup overhead of each isolation layer

## Background

`minictl` is a teaching runtime: a few hundred lines of C that
demonstrates exactly what Docker does, minus the distribution,
registry, and networking plumbing. Source and tests live in
`code/ch06-minictl/`. You implement three commands:

| Command | What it adds | Chapter §
|---|---|---|
| `minictl chroot <rootfs> <cmd>` | filesystem isolation only | 6.4 |
| `minictl run <rootfs> <cmd>` | namespaces (UTS, PID, MNT, USER) | 6.2, 6.5 |
| `minictl run --mem-limit --cpu-limit …` | cgroup v2 resource caps | 6.3 |

> **Important:** Do **not** open a persistent root shell
> (`sudo -i`, `sudo bash`, etc.) during this lab. Use `sudo` on
> individual commands only. Environment variables (`$ROOTFS`,
> `$MINICTL`) and file ownership break in a sustained root session,
> and Part B (user namespaces) is designed to run *without* `sudo`.

## Prerequisites

### System requirements

- Ubuntu 22.04+ VM (or other Linux with kernel 5.10+)
- cgroup v2 unified hierarchy mounted
- Not inside Docker (the kernel restricts nested namespace creation)

Verify:

```bash
uname -r                                          # 5.10+ expected
mount | grep cgroup2                              # unified hierarchy
cat /sys/fs/cgroup/cgroup.controllers             # cpu memory io pids
cat /proc/1/cgroup | grep -v docker | grep -v containerd
```

On Ubuntu 24.04, AppArmor may restrict unprivileged user namespaces.
If Part B fails with "Operation not permitted" on `clone()`:

```bash
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
```

### Prepare a rootfs

Alpine's minirootfs is small and reliable:

```bash
mkdir -p rootfs
ARCH=$(uname -m)
wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/${ARCH}/alpine-minirootfs-3.18.0-${ARCH}.tar.gz
tar -xzf alpine-minirootfs-3.18.0-${ARCH}.tar.gz -C rootfs
ls rootfs/bin/sh                                  # should exist
```

The rootfs architecture must match your kernel — `uname -m` gives
you the right value. A mismatched rootfs will produce
`Exec format error` and burn an hour of your time.

### Build and env vars

```bash
cd code/ch06-minictl
make clean && make

cd ..
export ROOTFS=$(pwd)/rootfs
export MINICTL=$(pwd)/code/ch06-minictl/minictl

$MINICTL --help
```

## Part A: `chroot` Sandbox (Required)

**Goal:** Implement `minictl chroot <rootfs> <cmd>`, run `/bin/sh`
inside it, and demonstrate what `chroot` *does not* isolate.

### A.1 Predict Before You Build

Before writing any code, answer in your report:

1. After `chroot`, will the process see the host's `/etc/hostname`
   or the rootfs's? Why?
2. Will `ps aux` inside the chroot show only container processes
   or all host processes? Explain in terms of which namespace
   `chroot` does and does not create.
3. Name one specific attack that lets a process escape a chroot.

This prediction is graded. Write it before implementing.

### A.2 Implement

File: `src/chroot_cmd.c`. The `fork`/`waitpid` scaffold is already
in place. Inside the child branch, fill in the four lines:

```c
if (child == 0) {
    if (chdir(rootfs) < 0)    { perror("chdir to rootfs"); exit(1); }
    if (chroot(rootfs) < 0)   { perror("chroot");          exit(1); }
    if (chdir("/") < 0)       { perror("chdir to /");      exit(1); }
    execvp(cmd_args[0], cmd_args);
    perror("execvp");
    exit(1);
}
```

Rebuild: `make clean && make`.

### A.3 Test

```bash
sudo $MINICTL chroot $ROOTFS /bin/sh -c 'pwd; ls /; hostname'
# Expected output:
#   /
#   bin dev etc home lib ...
#   <your host hostname>   ← chroot does NOT isolate hostname
```

Then document what `chroot` alone leaves exposed. Suggested
experiments:

```bash
sudo $MINICTL chroot $ROOTFS /bin/hostname
sudo $MINICTL chroot $ROOTFS /bin/ps aux | head    # if ps is in rootfs
sudo cp /etc/resolv.conf $ROOTFS/etc/resolv.conf
sudo $MINICTL chroot $ROOTFS /bin/cat /etc/resolv.conf
```

### Part A Checklist

- [ ] Prediction written before implementation
- [ ] `minictl chroot` runs `/bin/sh` inside the rootfs
- [ ] Demonstrated that hostname / PID table / network are not
      isolated by `chroot`
- [ ] Prediction compared to observation — did the result match?

## Part B: Namespace Isolation (Required)

**Goal:** Implement `minictl run <rootfs> <cmd>` that creates UTS,
PID, mount, and user namespaces via `clone()` and uses `pivot_root`
for filesystem isolation.

### B.1 Predict Before You Build

Before writing any code:

1. If you create a PID namespace but do *not* mount a new `/proc`,
   what will `ps aux` inside the container show? Why?
2. If you skip the `MS_PRIVATE` flag on the root mount, what might
   `pivot_root` do to the host's mount table?
3. Will the container process be able to `kill -9` a host process?
   Which namespace prevents this?

### B.2 Implement `setup_user_namespace()`

File: `src/run_cmd.c`. Two writes:

```c
snprintf(path, sizeof(path), "/proc/%d/uid_map", child_pid);
snprintf(content, sizeof(content), "0 %d 1", getuid());
fd = open(path, O_WRONLY);
if (fd < 0) { perror("open uid_map"); return -1; }
write(fd, content, strlen(content));
close(fd);

snprintf(path, sizeof(path), "/proc/%d/gid_map", child_pid);
snprintf(content, sizeof(content), "0 %d 1", getgid());
fd = open(path, O_WRONLY);
if (fd < 0) { perror("open gid_map"); return -1; }
write(fd, content, strlen(content));
close(fd);
```

### B.3 Implement `setup_mounts()` with `pivot_root`

Replace the placeholder body:

```c
static int setup_mounts(const char *rootfs) {
    mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL);
    mount(rootfs, rootfs, NULL, MS_BIND | MS_REC, NULL);

    char old_root[PATH_MAX];
    snprintf(old_root, sizeof(old_root), "%s/old_root", rootfs);
    mkdir(old_root, 0755);

    if (pivot_root(rootfs, old_root) < 0) {
        // Fallback for environments where pivot_root fails (some VMs):
        chdir(rootfs);
        chroot(".");
        chdir("/");
    } else {
        chdir("/");
        umount2("/old_root", MNT_DETACH);
        rmdir("/old_root");
    }

    mount("proc", "/proc", "proc", 0, NULL);
    return 0;
}
```

Rebuild.

### B.4 Test

```bash
sudo $MINICTL run --hostname=testcontainer $ROOTFS /bin/hostname
# Expected: testcontainer

sudo $MINICTL run $ROOTFS /bin/sh -c 'echo $$'
# Expected: 1    ← PID 1 inside the PID namespace

sudo $MINICTL run $ROOTFS /bin/sh -c 'id'
# Expected: uid=0(root) gid=0(root) ...   ← mapped via user namespace
```

### Part B Checklist

- [ ] Prediction written before implementation
- [ ] Hostname isolated (own UTS namespace)
- [ ] Process is PID 1 inside container (own PID namespace)
- [ ] `id` shows `uid=0` inside a rootless run
- [ ] `/proc` reflects the container's PID namespace
- [ ] Predictions compared to observations

## Part C: Cgroup Resource Limits (Required)

**Goal:** Add `--mem-limit=BYTES` and `--cpu-limit=PCT` that apply
cgroup v2 memory and CPU caps to the container.

### C.1 Predict Before You Build

1. If you set `memory.max` to 64 MiB but the program allocates
   only 32 MiB, will you see any signal in `memory.events`?
2. If you set `cpu.max` to `"10000 100000"` (10 % CPU), will
   `top` show 10 % or something lower? Why might it differ?
3. What happens if the cgroup directory is not cleaned up after
   the container exits?

### C.2 Implement cgroup writes

File: `src/cgroup.c`. Uncomment `cgroup_set_memory`'s write block,
and fill in the `open`/`write`/`close` bodies of
`cgroup_set_cpu()` and `cgroup_add_process()` (the `path` and
`content` strings are constructed for you).

File: `src/run_cmd.c`. In `cmd_run()`, uncomment the four calls
`cgroup_create`, `cgroup_set_memory`, `cgroup_set_cpu`, and
`cgroup_add_process`, plus the matching `cgroup_cleanup(child)` on
the exit path.

### C.3 Compile test hogs

```bash
cd code/ch06-minictl/tests
gcc -O2 -static -o cpu_hog cpu_hog.c
gcc -O2 -static -o mem_hog mem_hog.c
sudo mkdir -p $ROOTFS/usr/local/bin
sudo cp cpu_hog mem_hog $ROOTFS/usr/local/bin/
cd ../../..
```

Static linking matters because Alpine uses musl, not glibc. A
dynamically linked hog from your Ubuntu host will fail with "No
such file or directory" inside the Alpine rootfs because the glibc
loader is absent.

### C.4 Test

```bash
# Memory: should be OOM-killed around 64 MiB
sudo $MINICTL run --mem-limit=64M $ROOTFS /usr/local/bin/mem_hog

# CPU: cpu_hog should run at ~10 % of one core
sudo $MINICTL run --cpu-limit=10 $ROOTFS /usr/local/bin/cpu_hog &
top             # confirm ~10 % CPU for cpu_hog
kill %1
```

### Part C Checklist

- [ ] Memory cap triggers OOM kill at the expected limit
- [ ] CPU cap produces the expected percentage in `top`
- [ ] cgroup files (`/sys/fs/cgroup/minictl-<pid>/cgroup.procs`,
      `memory.max`, `cpu.max`) verified by `ls` / `cat`

## Part D: Measure the Overhead (Required)

**Goal:** Quantify the startup cost of each isolation layer.

```bash
# Baseline — no sandbox
time for i in $(seq 500); do sudo /bin/true; done

# chroot only
time for i in $(seq 500); do sudo $MINICTL chroot $ROOTFS /bin/true; done

# namespaces
time for i in $(seq 500); do sudo $MINICTL run $ROOTFS /bin/true; done

# namespaces + cgroup
time for i in $(seq 500); do sudo $MINICTL run --mem-limit=64M --cpu-limit=50 $ROOTFS /bin/true; done
```

Record mean startup time per invocation (elapsed / 500) for each
configuration:

| Configuration | Mean startup (ms) | Δ vs baseline |
|---|---|---|
| Baseline `/bin/true` |   | — |
| + chroot |   |   |
| + clone() with 4 namespaces |   |   |
| + cgroup create/attach/cleanup |   |   |

Expected: chroot adds little; namespaces add a few hundred µs to
low ms; cgroup setup adds another ms or two. Exact numbers depend
on the host.

## Deliverables

Submit:

1. **Source code** — Parts A–C applied; `make` builds without
   warnings.
2. **`report.md`** — the narrative. Must include:
   - One paragraph per part summarizing what you added and what
     you observed.
   - Test outputs or screenshots showing: hostname isolation, PID 1
     inside container, rootless `id` output, memory OOM, CPU cap in
     `top`.
   - The Part D overhead table with interpretation.
   - A short "what surprised you?" reflection.
   - **Ruled-out alternative.** Pick one of your overhead numbers
     from Part D and name a plausible *competing* explanation for
     it. For example: "the namespaces row could be slow because of
     `clone` itself, not the namespace flags." Then cite one
     measurement that excludes the alternative — for example, a
     `time strace -c` showing where the per-invocation seconds
     actually go. One paragraph; the form of the argument is more
     important than the choice of alternative.

## AI Use and Evidence Trail

This lab is graded on **prediction → evidence → mechanism**, not
on polish. AI tools are allowed within
[Appendix D](../../appendices/appendix-d-ai-policy.md) (Regime 1):
they may help debug, recall flags, or polish prose; they may
**not** generate the prediction, fabricate raw data, or substitute
for your own mechanism-level explanation. Substantial use must be
disclosed in the Evidence Trail — honest disclosure is not
penalized; non-disclosure of substantial use is.

Append the following section to your report (full template and
examples in Appendix D §"The Evidence Trail"):

```markdown
## Evidence Trail

### Environment and Reproduction
- Commands used: see the Procedure sections above
- Raw output files: list paths in your submission

### AI Tool Use
- **Tool(s) used:** [tool name and version, or "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you re-checked against
  your own data]
- **What I changed or rejected:** [if a suggestion was wrong or
  inapplicable]

### Failures and Iterations
- [At least one thing that did not work on the first attempt and
  what you learned from it.]
```

## Grading Rubric

| Criterion | Points |
|---|---|
| Predictions (Parts A–C) written before implementation | 15 |
| Part A (chroot) works and demonstrates non-isolation | 12 |
| Part B (namespaces) works; PID 1, hostname, rootless verified | 28 |
| Part C (cgroups) works; memory and CPU caps enforced | 18 |
| Part D overhead measurement, with interpretation | 10 |
| Prediction vs observation comparison; surprises explained | 8 |
| Ruled-out alternative for one Part D row | 9 |

**Total: 100 points.**

The AI-resistant components are the predictions and the ruled-out
alternative. An LLM cannot predict per-invocation overhead on your
specific VM, and it cannot exclude an alternative explanation
without your `strace -c` or `perf stat` output to point to.

## Troubleshooting

- **`Operation not permitted` on `clone()`.** You are inside
  Docker, or AppArmor restricts unprivileged user namespaces. See
  Prerequisites.
- **`Permission denied` on cgroup writes.** cgroup v2 operations
  often need root; use `sudo` for individual commands. Do not
  enter a root shell.
- **`pivot_root: Invalid argument`.** The old and new roots are on
  the same mount. The `mount(rootfs, rootfs, NULL, MS_BIND, NULL)`
  line fixes this; make sure it is present.
- **Memory limit not enforced.** Check that the cgroup exists
  (`ls /sys/fs/cgroup/minictl-*`) and that the child PID appears in
  `cgroup.procs`.
- **`Exec format error`.** Your rootfs architecture does not match
  `uname -m`. Re-download the matching Alpine tarball.

## Reference: Useful Manpages

- `man 2 clone` — the foundation of everything here
- `man 7 namespaces` — the seven namespace types
- `man 7 cgroups` — cgroup concepts
- `man 2 pivot_root` — filesystem root swap
- `man 5 proc` — the `/proc/<pid>/ns/`, `uid_map`, `gid_map`,
  `setgroups` files

## Appendix: The Mental Model, Restated

- Part A showed that `chroot` restricts *what files the process can
  see*, and nothing else.
- Part B showed that namespaces restrict *what kernel resources the
  process can see* — processes, hostnames, mounts, UIDs.
- Part C showed that cgroups restrict *how much the process can
  use* — memory, CPU.
- Part D showed that isolating a process costs a few milliseconds;
  far cheaper than a VM, at the cost of sharing a kernel.

That is the entire container story. Everything else — Docker,
Kubernetes, OCI runtimes — is orchestration on top of these four
observations.
