# Appendix C: Environment Setup Guide

This appendix describes how to build a lab environment that
supports every lab in this book. The canonical target is a
Linux VM (Ubuntu 22.04 or 24.04 LTS) with root access, either
on a laptop via VirtualBox / UTM / VMware, or in the cloud.

<!-- SOURCE: week0/env_setup.md, week0/README_VirtualBox_Setup.md,
     week1/HANDOUT_quick_start.md
     Do NOT import anything from outdated/ or archive/ directories. -->

## C.1 Why a Linux VM

Most labs rely on kernel features (eBPF tracepoints, cgroups v2,
user namespaces, the ext4 journal) that are not directly
accessible from macOS or Windows hosts. A VM provides an
isolated, reproducible, disposable environment where experiments
that require `sudo` and kernel tunables cannot damage your host.

## C.2 VM Specifications

<!-- Recommended:
       CPUs: 4 vCPUs (2 minimum)
       RAM: 8 GB (4 GB minimum)
       Disk: 40 GB
       Network: NAT + host-only adapter
     Graduate labs (K8s, etcd, Redis at scale) benefit from the
     recommended spec; the minimum spec is enough for Chapters 1-6.
     SOURCE: week0/README_VirtualBox_Setup.md -->

## C.3 Host-Specific Setup

### VirtualBox (x86_64 Linux or Windows host)

<!-- Download Ubuntu 22.04 LTS ISO.
     Create VM, enable VT-x / nested paging.
     Install Guest Additions for shared folders and clipboard.
     Reference: week0/README_VirtualBox_Setup.md -->

### UTM / Parallels (Apple Silicon)

<!-- Use the arm64 Ubuntu ISO. Most tooling works identically;
     one exception: some eBPF programs and perf events are
     gated on arm64 and may need newer kernels. Chapter 5
     labs flag these cases where they occur. -->

### Cloud (if a VM is not practical)

<!-- An e2-standard-2 / t3.medium VM is sufficient for most labs.
     Be aware that shared tenancy introduces noise — tail-latency
     labs (Chapters 3, 5, 7) should be run on dedicated or
     bare-metal instances for trustworthy results. -->

## C.4 Base Package Installation

<!-- On a fresh Ubuntu 22.04 VM:
       sudo apt update
       sudo apt install -y build-essential git vim tmux \
         linux-tools-common linux-tools-$(uname -r) \
         bpfcc-tools bpftrace \
         strace ltrace \
         iotop sysstat \
         fio \
         e2fsprogs \
         python3-pip python3-venv \
         docker.io \
         jq curl
     SOURCE: week0/env_setup.md -->

## C.5 Tool Installation by Chapter

| Chapter | Additional tools |
|---|---|
| 1 — Environment | Base packages above. |
| 2 — Measurement | `perf`, `fio`, `flamegraph.pl` (from Brendan Gregg's repo). |
| 3 — Tail latency | `wrk`, `hey`, `histogram` helpers. |
| 4 — Threads | GCC ≥ 11, `pthread`, `valgrind`. |
| 5 — Scheduler | `bpftrace`, `bcc-tools` (runqlat, runqlen, offcputime). |
| 6 — Containers | `util-linux` (unshare), `crun` or a clone of `minictl`. |
| 7 — K8s QoS | `kind`, `kubectl`, `stress-ng`. |
| 8 — Consensus | `etcd` ≥ 3.5, `etcdctl`. |
| 9 — K8s scheduling | `kind`, `kubectl` (reuse Ch 7). |
| 10 — Filesystems | `filefrag`, `debugfs`, `fio`, `blktrace`. |
| 11 — Distributed storage | `redis-server`, `redis-cli`, `etcd`, optional `minio`. |
| 12 — Agent runtimes | Python 3.11+, `libseccomp-dev`, optional `firejail`. |
| 13 — Methodology | No additional system tools; focus is on reporting. |

## C.6 Sanity Check

Before starting Chapter 2, confirm the baseline works:

1. `perf stat ls` returns counters (perf is installed and permitted).
2. `bpftrace -l 'tracepoint:sched:*'` lists events (BPF works).
3. `docker run hello-world` succeeds (container runtime works).
4. `kind create cluster` succeeds and `kubectl get nodes` shows it.

## C.7 Troubleshooting Pointers

<!-- - perf "permission denied": set kernel.perf_event_paranoid.
     - bpftrace "not found": install linux-headers-$(uname -r).
     - kind "failed to create cluster": check that cgroup v2 is on,
       /etc/docker/daemon.json "exec-opts": ["native.cgroupdriver=systemd"].
     - VirtualBox slow: disable KVM paravirtualization if nested
       virtualization is off on the host.
     Detailed walk-throughs live in the lab-specific READMEs. -->

## C.8 Reproducibility Hooks

Every report you produce should record: Ubuntu version
(`lsb_release -a`), kernel version (`uname -r`), CPU model
(`lscpu`), key tool versions (`perf --version`, `bpftrace --version`,
`docker --version`, `kubectl version --short`). See Chapter 13.
