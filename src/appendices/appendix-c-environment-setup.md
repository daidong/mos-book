# Appendix C: Environment Setup Guide

This appendix describes how to build a lab environment that
supports every lab in this book. The canonical target is a
Linux VM (Ubuntu 22.04 or 24.04 LTS) with root access, either
on a laptop via VirtualBox / UTM / VMware, or in the cloud.

## C.1 Why a Linux VM

Most labs rely on kernel features — eBPF tracepoints, cgroups
v2, user namespaces, the ext4 journal — that are not directly
accessible from macOS or Windows hosts. A VM provides:

- **An isolated environment.** Experiments that require `sudo`
  and kernel tunables cannot damage the host.
- **Reproducibility.** Snapshot before a risky change; roll
  back if it breaks. Share the VM image with a peer.
- **Disposability.** A corrupted VM is reinstalled in thirty
  minutes; a corrupted host is a weekend.

Specifically *not* supported (stated once in Chapter 1 and
again here):

- **WSL2.** Kernel feature surface is narrower than real Linux;
  eBPF and `perf` frequently fail.
- **Docker as your OS.** BPF capabilities restricted; no direct
  `/proc` / `/sys` access; kernel isolation is not the point of
  Docker.
- **macOS or Windows host tools.** No `/proc`, no `perf`, no
  cgroups. Xcode and Visual Studio are beautiful, but they do
  not help here.

## C.2 VM Specifications

Minimum (enough for Chapters 1–6):

- 2 vCPUs
- 4 GB RAM
- 25 GB disk
- NAT networking

Recommended (for Chapters 7–12, especially Kubernetes, etcd,
Redis benchmarks, and agent sandbox):

- 4 vCPUs
- 8 GB RAM
- 40 GB disk
- NAT + (optionally) host-only adapter for easier host-to-VM
  port access

Kernel requirement:

- **Minimum** Linux kernel **5.10** (for cgroup v2, modern eBPF
  and BTF).
- **Recommended** kernel **5.15+** — the default on Ubuntu
  22.04 LTS. Ubuntu 20.04 typically runs 5.4 and misses features
  used in later labs.

Verify with `uname -r` before starting.

## C.3 Host-Specific Setup

### VirtualBox (x86_64 Linux or Windows host)

1. Download VirtualBox from <https://www.virtualbox.org/>.
2. Download the Ubuntu 22.04 LTS (or 24.04 LTS) amd64 desktop
   ISO from <https://ubuntu.com/download/desktop>.
3. Create a new VM with the specs above. Enable VT-x / AMD-V
   and Nested Paging in the VM settings.
4. Attach the ISO and install. Accept the default options;
   remember the username and password.
5. After first boot, install Guest Additions for clipboard and
   shared folders:
   ```bash
   sudo apt install -y virtualbox-guest-utils virtualbox-guest-x11
   ```
6. To see realistic CPU cache sizes in `getconf -a | grep CACHE`,
   on the host run:
   ```bash
   VBoxManage modifyvm "Ubuntu-OS-Course" --cpu-profile host
   ```

### UTM / Parallels (Apple Silicon)

VirtualBox's Apple Silicon support is limited at the time of
writing. UTM (free) or Parallels (paid) are the usual choice:

1. Download the Ubuntu 22.04/24.04 **arm64 server** ISO from
   <https://ubuntu.com/download/server/arm>.
2. Create the VM with the recommended specs.
3. Most tooling works identically to x86_64. Exceptions:
   - Some eBPF programs and `perf` events are gated on arm64
     and may need newer kernels. Chapter 5 flags the cases
     where this matters.
   - Hardware PMU events (cache/branch counters) are often not
     exposed through the hypervisor; fall back to Valgrind
     (Chapter 2 §2.5) as the labs recommend.

### Cloud VM

If a local VM is impractical, an `e2-standard-2` (GCP) or
`t3.medium` (AWS) VM is sufficient for Chapters 1–11. Important
caveats for tail-latency labs (Chapters 3, 5, 7):

- Shared tenancy introduces neighbor noise.
- Cloud VMs virtualize the clock and often some counters.
- Power management on cloud hosts is opaque; `cpupower
  frequency-set --governor performance` may be a no-op.

For trustworthy p99 numbers, use a dedicated or bare-metal
instance, or run on your own hardware.

## C.4 Base Package Installation

On a fresh Ubuntu 22.04 VM, install everything you will need
across the book:

```bash
sudo apt update
sudo apt install -y \
    build-essential git vim tmux jq curl wget \
    linux-tools-common linux-tools-$(uname -r) \
    strace ltrace valgrind \
    bpftrace bpfcc-tools \
    iotop sysstat fio e2fsprogs \
    python3-pip python3-venv python3-dev \
    docker.io \
    stress-ng
```

Add your user to the `docker` group so you do not need `sudo`
for Docker:

```bash
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
```

## C.5 Tool Installation by Chapter

| Chapter | Additional tools | Install command |
|---|---|---|
| 1 — Environment | Base packages | (see §C.4) |
| 2 — Measurement | `perf`, `fio`, Valgrind | In base packages |
| 3 — Tail latency | `wrk2` or equivalent | Build from source |
| 4 — Threads | GCC ≥ 11, pthreads | In base packages |
| 5 — Scheduler | `bpftrace`, `bcc-tools`, libbpf headers | `sudo apt install libbpf-dev clang llvm` |
| 6 — Containers | `util-linux` (unshare) | In base packages |
| 7 — K8s QoS | `kind`, `kubectl` | See §C.6 |
| 8 — Consensus | etcd container image | `docker pull quay.io/coreos/etcd:v3.5.17` |
| 9 — K8s scheduling | `kind`, `kubectl` (reuse) | Already installed |
| 10 — Filesystems | `filefrag`, `debugfs`, `fio`, `blktrace` | `sudo apt install e2fsprogs blktrace` |
| 11 — Distributed storage | Redis, etcd, optional MinIO | `sudo apt install redis-tools` |
| 12 — Agent runtimes | Python 3.11+, libseccomp | `sudo apt install libseccomp-dev` |
| 13 — Methodology | No additional tools | — |

## C.6 Kubernetes Tooling (Chapters 7, 9, 11)

### Install `kubectl`

```bash
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/
kubectl version --client
```

(On arm64, replace `amd64` with `arm64`.)

### Install `kind`

```bash
# Go source (requires Go 1.21+):
go install sigs.k8s.io/kind@latest

# Or pre-built binary:
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind version
```

### Quick smoke test

```bash
kind create cluster --name smoke
kubectl get nodes
kubectl run test --image=busybox --restart=Never -- sleep 30
kubectl get pods
kind delete cluster --name smoke
```

## C.7 Sanity Check

Before starting Chapter 2, confirm the baseline works. All of
these should succeed:

```bash
uname -r                                  # kernel ≥ 5.10
gcc --version                             # compiler works
sudo perf stat ls                         # perf installed and permitted
sudo bpftrace -l 'tracepoint:sched:*' | head # BPF works
docker run hello-world                    # container runtime works
ls /sys/kernel/btf/vmlinux                # BTF for libbpf CO-RE
kind create cluster && kubectl get nodes  # K8s stack up
kind delete cluster
```

If any fail, see §C.9 before starting the labs.

## C.8 Reproducibility Hooks

Every report you produce should record, as the first block of
the report:

- Ubuntu version: `lsb_release -a`
- Kernel version: `uname -r`
- CPU model: `lscpu`
- Tool versions: `perf --version`, `bpftrace --version`,
  `docker --version`, `kubectl version --client`, `etcd
  --version` (if applicable)
- VM configuration: vCPUs, RAM, disk, host OS
- Whether you pinned CPU governor: `cpupower frequency-info`

Collect them with a one-liner and paste the output verbatim:

```bash
(lsb_release -a; uname -r; lscpu | head -20; \
 perf --version; bpftrace --version 2>&1 | head; \
 docker --version; kubectl version --client --short 2>/dev/null) 2>&1 \
 | tee env.txt
```

Include `env.txt` with every lab submission.

## C.9 Troubleshooting Pointers

- **`perf: command not found`.** `sudo apt install
  linux-tools-common linux-tools-$(uname -r)`. If the
  kernel-matched package is missing, install
  `linux-tools-generic`.
- **`perf: permission denied`.** Use `sudo`, or relax policy
  on your own VM only:
  ```bash
  sudo sysctl kernel.perf_event_paranoid=1
  ```
- **`bpftrace` not available.** `sudo apt install bpftrace
  libbpf-dev linux-headers-$(uname -r)`. Verify BTF: `ls
  /sys/kernel/btf/vmlinux`.
- **`kind` fails to create a cluster.** Docker must be using
  the systemd cgroup driver on Ubuntu 22.04+:
  ```json
  // /etc/docker/daemon.json
  { "exec-opts": ["native.cgroupdriver=systemd"] }
  ```
  Restart Docker: `sudo systemctl restart docker`.
- **VirtualBox VM is slow.** Ensure VT-x and Nested Paging are
  enabled. Allocate more RAM. Disable KVM paravirtualization
  if nested virt is off on the host.
- **Ubuntu 24.04 rejects `unshare --user` in the minictl lab
  (Chapter 6).** AppArmor is restricting unprivileged user
  namespaces:
  ```bash
  sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
  ```
- **fsync latency reads as 0.01 ms.** You are on tmpfs. Check
  `df -T /tmp` and use an ext4 path on a real disk.

## C.10 When In Doubt

Every lab-specific README in this book's `code/` directory
includes a "Troubleshooting" section for that chapter. Start
there, then fall back to this appendix, then to the tool's man
page. The course forum and office hours are the last resort —
environment bugs get harder to fix under deadline pressure, so
ask early.
