# Chapter 6: Container Foundations — Namespaces and Cgroups

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Name the seven Linux namespace types and explain what each isolates
> - Describe how `task_struct` fields implement container identity
> - Use cgroup v2 controllers to enforce CPU, memory, and I/O limits
> - Explain how rootless containers work via user namespace UID mapping
> - Describe the role of OverlayFS in filesystem isolation

## 6.1 What Is a Container?

<!-- A container is not a VM. It is a process (or group of processes)
     with restricted visibility and resource limits, implemented by
     two kernel mechanisms: namespaces and cgroups. -->

## 6.2 Linux Namespaces

<!-- Seven types: UTS, PID, Mount, Network, User, IPC, Cgroup.
     Each namespace isolates a different aspect of the system view.
     Created with clone() or unshare() syscalls.
     SOURCE: week5 slides -->

## 6.3 The task_struct and Container Identity

<!-- How the kernel knows which namespace a process belongs to.
     nsproxy pointer in task_struct.
     /proc/<pid>/ns/ interface. -->

## 6.4 Cgroups v2

<!-- Unified hierarchy. Controllers: cpu, memory, io, pids.
     Interface: /sys/fs/cgroup/ tree.
     Key files: cpu.max, memory.max, memory.current, io.max.
     How the kernel enforces limits. -->

## 6.5 Filesystem Isolation

<!-- Mount namespaces: private mount trees.
     chroot vs pivot_root.
     OverlayFS: layered filesystem for container images.
     Why layers matter for image distribution. -->

## 6.6 Rootless Containers

<!-- User namespaces: map container UID 0 to unprivileged host UID.
     Why this matters: containers without host root.
     Limitations and remaining attack surfaces. -->

## Summary

Key takeaways from this chapter:

- Containers are built from two kernel mechanisms: namespaces (what
  you can see) and cgroups (what you can use).
- Cgroup v2 provides a unified interface for resource control that
  is directly observable via the filesystem.
- Understanding these building blocks is essential for diagnosing
  container behavior in production.

## Further Reading

- Kerrisk, M. (2013-2016). Namespaces in Operation (LWN series).
- Linux kernel documentation: cgroup-v2.txt.
- Walsh, D. (2019). *Container Security.* O'Reilly Media.
