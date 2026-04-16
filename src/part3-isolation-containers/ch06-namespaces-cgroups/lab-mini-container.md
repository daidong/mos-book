# Lab: Build a Mini Container Runtime

> **Estimated time:** 5-6 hours
>
> **Prerequisites:** Chapter 6 concepts (namespaces, cgroups, chroot)
>
> **Tools used:** gcc, clone(), unshare(), mount, cgroup v2 filesystem

## Objectives

- Implement a minimal container runtime (`minictl`) from scratch in C
- Progressively add isolation layers: chroot, namespaces, cgroups
- Test rootless container execution
- Measure the overhead of isolation mechanisms

## Background

<!-- SOURCE: week5/minictl/
     Students build a container runtime in three stages,
     each adding a layer of isolation. The goal is to
     understand that containers are just processes with
     kernel-enforced restrictions. -->

## Part A: chroot Sandbox (Required)

<!-- Create a minimal root filesystem.
     Use chroot() to restrict filesystem visibility.
     Run /bin/sh inside the sandbox.
     Observe: can the process see host files? -->

## Part B: Namespace Isolation (Required)

<!-- Use clone() with namespace flags:
     CLONE_NEWUTS, CLONE_NEWPID, CLONE_NEWNS, CLONE_NEWUSER.
     Verify isolation: hostname, PID 1, mount visibility.
     Set up UID mapping for user namespace. -->

## Part C: Cgroup Resource Limits (Required)

<!-- Create a cgroup v2 subtree.
     Set memory.max and cpu.max.
     Run cpu_hog and mem_hog inside the container.
     Verify enforcement: throttling, OOM behavior. -->

## Deliverables

- Working `minictl` binary that creates an isolated process with
  namespace + cgroup restrictions
- Test output showing: hostname isolation, PID isolation, memory
  limit enforcement, CPU throttling
- Brief report describing what each layer adds and the overhead
  of each (wall-clock time to create container vs bare process)
