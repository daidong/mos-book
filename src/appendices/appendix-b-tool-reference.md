# Appendix B: Tool Reference

This appendix is a compact reference to the measurement and
observability tools used across the labs. It is not a replacement
for man pages, but a quick index of the invocations and flags that
recur most often in systems work. Tools are grouped by layer.

<!-- SOURCE: compiled from
     week2A/HANDOUT_perf_commands.md,
     week2B/use_checklist.md,
     week4/ebpf_quickstart.md,
     week5/HANDOUT_container_ops.md,
     week6-week7 kubectl material,
     various lab instruction documents. -->

---

## B.1 CPU and Scheduling

### `perf stat`

<!-- perf stat -e cycles,instructions,cache-misses,cache-references ./cmd
     Key counters: cycles, instructions, IPC, cache misses,
     branch misses, context-switches, cpu-migrations.
     Use -a for system-wide; -C for pinned cores. -->

### `perf record` / `perf report`

<!-- perf record -g ./cmd; perf report
     perf record -F 99 -a -g -- sleep 30   (system-wide sampling)
     Use --call-graph dwarf for C++ / modern glibc.
     perf script | flamegraph.pl for flamegraphs. -->

### `pidstat`

<!-- pidstat -u -r -d 1   (cpu / memory / io per process, 1s)
     pidstat -t -p <pid>  (per-thread). -->

### `schedstat` / `/proc/schedstat`

<!-- Raw scheduler accounting. Useful when perf and bpf are not
     available. -->

---

## B.2 Kernel-Level Tracing

### `strace`

<!-- strace -c ./cmd            (syscall summary)
     strace -f -e trace=file ./cmd  (follow children, file ops)
     High overhead; do not use on hot paths for latency claims.
     SOURCE: week2B/use_checklist.md -->

### `bpftrace`

<!-- One-liners:
       bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'
       bpftrace -e 'tracepoint:sched:sched_switch { @[comm] = count(); }'
     See week4/ebpf_quickstart.md for the cheat sheet. -->

### `bcc` tools

<!-- /usr/share/bcc/tools:
       runqlat   (run-queue latency histogram)
       runqlen   (run-queue length)
       biosnoop  (block IO per op)
       biolatency (block IO latency histogram)
       offcputime (off-CPU analysis)
     Canonical source for ready-made eBPF programs. -->

---

## B.3 Memory

### `vmstat` / `free`

<!-- vmstat 1 10   (cpu, io, swap, memory per second)
     free -h       (mem / swap snapshot)
     Pair with /proc/meminfo for detail. -->

### `/proc/[pid]/smaps` and `smaps_rollup`

<!-- Per-mapping memory accounting: Rss, Pss, Private_Dirty,
     Shared_Clean. Essential for COW/fork analysis
     (Chapter 4, Chapter 11 BGSAVE). -->

---

## B.4 Block I/O and Filesystems

### `iostat`

<!-- iostat -x 1    (per-device extended stats)
     Columns to watch: %util, r_await, w_await, avgqu-sz. -->

### `filefrag` / `debugfs`

<!-- filefrag -v file        (physical extents)
     debugfs -R "stat <inode>" /dev/sdXN -->

### `fio`

<!-- fio --name=test --rw=randwrite --bs=4k --size=1G \
         --iodepth=32 --numjobs=1 --direct=1 --runtime=60
     Produces latency distributions (including percentiles)
     directly. Prefer fio over dd for any serious measurement. -->

---

## B.5 Containers and Namespaces

### `unshare`, `nsenter`

<!-- unshare -Ufpm --mount-proc /bin/bash    (new user/pid/mount NS)
     nsenter -t <pid> -a                      (join all NS of pid) -->

### Cgroup v2 interface

<!-- /sys/fs/cgroup/<group>/{cpu.max, memory.max, io.max, cgroup.procs}
     echo "100000 1000000" > cpu.max    (10% of one CPU, 1s period)
     echo "268435456" > memory.max      (256 MiB)
     SOURCE: week5 and week6 handouts. -->

---

## B.6 Kubernetes and etcd

### `kubectl`

<!-- kubectl describe pod <p>          (events, conditions)
     kubectl top pod / node            (resource snapshot)
     kubectl get events --sort-by=.lastTimestamp
     kubectl logs <pod> --previous     (post-restart debugging) -->

### `etcdctl`

<!-- ETCDCTL_API=3 etcdctl endpoint status --write-out=table
     etcdctl get "" --prefix --keys-only | head
     etcdctl compaction <rev>
     etcdctl defrag
     etcdctl snapshot save/restore -->

---

## B.7 Networking (Light Reference)

### `ss`, `tcpdump`, `iperf3`

<!-- ss -tnp                (open TCP connections with processes)
     tcpdump -i any 'port 8080' -w pcap
     iperf3 -c host -t 30   (throughput)
     Used sparingly in this book; see course material for detail. -->

---

## B.8 Reading This Appendix

Each tool listed here has exactly one purpose: **to produce a
signal you can cite as evidence.** When a lab or project report
mentions a number, the reader should be able to find the tool
and invocation in this appendix and rerun the measurement.
