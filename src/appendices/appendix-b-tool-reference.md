# Appendix B: Tool Reference

This appendix is a compact reference to the measurement and
observability tools used across the labs. It is not a
replacement for man pages, but a quick index of the invocations
and flags that recur most often in systems work. Tools are
grouped by layer.

Each tool listed here has exactly one purpose: **produce a
signal you can cite as evidence.** When a lab or project report
mentions a number, the reader should be able to find the tool
and invocation in this appendix and rerun the measurement.

---

## B.1 CPU and Scheduling

### `perf stat`

Run a command and report hardware counters:

```bash
sudo perf stat ./program
sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
branches,branch-misses,page-faults,major-faults -r 5 ./program
```

Useful flags:

- `-e ...` select events; see `perf list` for the full set.
- `-r N` run `N` repeats and report mean + variance.
- `-a` system-wide (all CPUs).
- `-C 0,1` restrict to specific CPUs.
- `-p <pid>` attach to a running process.
- `--` separate `perf` flags from program args.

Interpretation rules of thumb (Chapter 2 §2.5):

- **IPC = instructions / cycles**; ~2–4 is healthy, below 1 is
  usually memory-stall-bound.
- **cache miss rate = cache-misses / cache-references**; look
  at the rate, not the count.
- **`<not supported>` in a VM** means the PMU event is
  unavailable; switch to Valgrind (Chapter 2 §2.5).

### `perf record` / `perf report`

Sampled profile of where CPU time is spent:

```bash
sudo perf record -g ./program            # per-process, with stacks
sudo perf record -F 99 -a -g -- sleep 30 # system-wide at 99 Hz, 30 s
sudo perf report                         # interactive browser
sudo perf report --stdio | head -50      # plain text

# Flamegraph pipeline
sudo perf record -F 99 -a -g -- sleep 30
sudo perf script > out.perf
./FlameGraph/stackcollapse-perf.pl out.perf | ./FlameGraph/flamegraph.pl > fg.svg
```

`--call-graph dwarf` helps with C++ and modern glibc where frame
pointers are missing.

### `pidstat`

Per-process CPU / memory / I/O, updated every second:

```bash
pidstat 1                  # CPU per process
pidstat -u -r -d 1         # CPU, memory, disk I/O
pidstat -t -p <pid>        # per-thread for one PID
```

### `/proc/schedstat` and `/proc/<pid>/sched`

Raw scheduler accounting. Useful when `perf` and eBPF are not
available (common in VMs):

```bash
cat /proc/schedstat
cat /proc/<pid>/sched | head -30
```

Key fields: `nr_switches`, `nr_voluntary_switches`,
`nr_involuntary_switches`, `sum_exec_runtime`.

### `taskset`, `nice`, `renice`

Pin a process or change its priority:

```bash
taskset -c 0 ./program           # pin to CPU 0
taskset -p <pid>                 # show current affinity
nice -n 19 ./batch_job           # lowest priority
renice 10 -p <pid>               # change priority of running PID
```

---

## B.2 Kernel-Level Tracing

### `strace`

Syscall tracer. High overhead; fine for correctness analysis,
bad for latency claims on hot paths.

```bash
strace -c ./program                  # syscall summary
strace -f -e trace=file ./program    # follow children, file ops
strace -T -e fsync ./program         # per-syscall timing
strace -p <pid>                      # attach to a running process
```

### `bpftrace`

"awk for the kernel": pick a probe, write a handler, aggregate
in-kernel.

```bash
bpftrace -l 'tracepoint:sched:*'
bpftrace -lv tracepoint:sched:sched_switch

# syscalls-by-program histogram
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_openat {
  printf("%s %s\n", comm, str(args->filename));
}'

# scheduling latency (Chapter 5 §5.3 recipe)
sudo bpftrace -e '
tracepoint:sched:sched_wakeup { @ts[args->pid] = nsecs; }
tracepoint:sched:sched_switch / @ts[args->next_pid] / {
  $d = (nsecs - @ts[args->next_pid]) / 1000;
  @lat_us = hist($d);
  delete(@ts[args->next_pid]);
}'
```

Idioms: `/filter/`, `@map[key] = count()`, `hist()`,
`delete(@map[key])`, `clear(@map)`, `interval:s:5` for periodic
printing. See Chapter 5 §5.3 for the full cheat sheet.

### `bcc` tools

Ready-made eBPF programs in `/usr/share/bcc/tools/`:

```bash
sudo runqlat-bpfcc            # runqueue latency histogram
sudo runqlen-bpfcc            # runqueue length
sudo biolatency-bpfcc -D      # block-I/O latency by device
sudo biosnoop-bpfcc           # per-op block I/O trace
sudo offcputime-bpfcc -K 30   # off-CPU stack profile, 30 s
sudo ext4slower-bpfcc 1       # ext4 ops slower than 1 ms
sudo tcpretrans-bpfcc         # TCP retransmits
```

A partial alternative if `bcc` is not installed: many of the
same tools live in `bpftrace-tools` or can be written as
bpftrace one-liners.

### `ftrace` / `trace-cmd`

Lower-level kernel tracing:

```bash
sudo trace-cmd record -e sched_switch -p <pid>
sudo trace-cmd report
```

---

## B.3 Memory

### `vmstat`

Memory + CPU + I/O sampled per interval:

```bash
vmstat 1 10     # 10 samples, 1 s each
```

Columns: `r` (runqueue length), `b` (blocked), `si`/`so`
(swap in/out), `bi`/`bo` (block in/out), `cs` (context switches).

### `free`

Memory snapshot:

```bash
free -h         # human-readable
```

`buff/cache` includes the page cache. `available` estimates how
much memory can be claimed without swapping.

### `/proc/meminfo`

Most fields you care about:

```bash
grep -E "MemFree|MemAvailable|Cached|Dirty|Writeback|Swap" /proc/meminfo
```

`Dirty` is "data at risk" — written but not yet on stable
storage.

### `/proc/[pid]/smaps` and `smaps_rollup`

Per-mapping memory accounting. Essential for fork+COW analysis
(Chapter 4, Chapter 11 `BGSAVE`):

```bash
cat /proc/<pid>/smaps_rollup
cat /proc/<pid>/smaps | awk '
  /^Private_Dirty/ { pd += $2 }
  /^Shared_Clean/  { sc += $2 }
  END { print "Private_Dirty:", pd, "kB;  Shared_Clean:", sc, "kB" }
'
```

---

## B.4 Block I/O and Filesystems

### `iostat`

Per-device extended statistics, sampled per interval:

```bash
iostat -x 1
```

Columns to watch: `r/s` (reads per second), `w/s`, `rkB/s`,
`wkB/s`, `await` (average latency in ms — the signal for p99
issues), `%util` (saturation signal).

### `filefrag`

Show a file's physical layout:

```bash
filefrag -v largefile.dat
```

One extent = contiguous; many small extents = fragmented.

### `debugfs`

Inspect ext4 internals (read-only on a mounted filesystem):

```bash
sudo debugfs -R "stat <${inode_number}>" /dev/sdXN
sudo debugfs -R "ls -l /path" /dev/sdXN
```

### `fio`

The right tool for serious I/O benchmarking (use this, not
`dd`):

```bash
fio --name=test --rw=randwrite --bs=4k --size=1G \
    --iodepth=32 --numjobs=1 --direct=1 --runtime=60 \
    --time_based --group_reporting
```

`--direct=1` bypasses the page cache. Output includes latency
percentiles and IOPS.

---

## B.5 Containers and Namespaces

### `unshare` and `nsenter`

```bash
sudo unshare -Ufpmn --mount-proc /bin/bash    # new user/pid/mount/net NS
unshare --user --map-root-user /bin/bash       # rootless, no sudo
sudo nsenter -t <pid> -a                        # join all namespaces of <pid>
sudo nsenter -t <pid> -n -- ss -tnp             # run ss in <pid>'s netns
```

### `/proc/<pid>/ns/`

Inspect which namespaces a process is in:

```bash
ls -la /proc/$$/ns/
# symlinks to inodes: processes in the same namespace share an inode
```

### cgroup v2

Everything under `/sys/fs/cgroup`:

```bash
# create a cgroup and add a process
sudo mkdir /sys/fs/cgroup/mylab
echo $$ | sudo tee /sys/fs/cgroup/mylab/cgroup.procs

# limits
echo "50000 100000"              | sudo tee /sys/fs/cgroup/mylab/cpu.max
echo $((256*1024*1024))          | sudo tee /sys/fs/cgroup/mylab/memory.max
echo 16                          | sudo tee /sys/fs/cgroup/mylab/pids.max

# stats
cat /sys/fs/cgroup/mylab/cpu.stat        # includes nr_throttled
cat /sys/fs/cgroup/mylab/memory.current
cat /sys/fs/cgroup/mylab/memory.events
```

### `crictl`

When working inside a Kubernetes node (especially `kind`):

```bash
sudo crictl ps                    # list containers
sudo crictl inspect <id>          # full container state
sudo crictl logs <id>             # logs
```

---

## B.6 Kubernetes and etcd

### `kubectl`

Everyday operations:

```bash
kubectl get pods -o wide
kubectl describe pod <name>
kubectl logs <pod>                   # current
kubectl logs <pod> --previous        # previous container instance
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --field-selector reason=FailedScheduling
kubectl top pod
kubectl top node
kubectl describe node <name>         # capacity and Allocated resources
```

QoS and resource inspection:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass
```

Debugging a scheduling failure:

```bash
kubectl describe pod <name> | grep -A 10 Events
```

### `etcdctl`

Use inside a container to avoid host etcd version mismatches:

```bash
ETCDCTL_API=3 etcdctl --endpoints=... endpoint status -w table
ETCDCTL_API=3 etcdctl --endpoints=... endpoint health
ETCDCTL_API=3 etcdctl --endpoints=... member list -w table

# data operations
etcdctl put /mykey "value"
etcdctl get /mykey
etcdctl get "" --prefix --keys-only | head
etcdctl watch /prefix --prefix

# maintenance
etcdctl compaction <rev>
etcdctl defrag
etcdctl snapshot save backup.db
etcdctl snapshot restore backup.db --data-dir /var/lib/etcd
```

---

## B.7 Networking (Light Reference)

### `ss`

Socket statistics, faster and more informative than `netstat`:

```bash
ss -tnp                 # open TCP connections, with processes
ss -s                   # summary
ss -tln                 # listening sockets
```

### `tcpdump`

Packet capture:

```bash
sudo tcpdump -i any 'port 8080' -w out.pcap
```

Filter expressions follow pcap-filter syntax.

### `iperf3`

Throughput testing:

```bash
# server
iperf3 -s

# client
iperf3 -c <server> -t 30 -P 4
```

### `ip`

Modern replacement for `ifconfig`:

```bash
ip addr                 # interfaces
ip route                # routing table
ip -s link show eth0    # per-interface counters
```

---

## B.8 Reading This Appendix

Think of this appendix as the bridge between the body of the
book and the man pages. The book tells you *why* a tool matters
and *which question* it answers; this appendix tells you *how*
to invoke it. The man pages are the authoritative reference for
details.

For every number you report in a lab or project, you should be
able to cite:

1. The tool that produced it (an entry in this appendix).
2. The exact invocation (`perf stat -r 5 -e ...`).
3. The raw output it came from (saved alongside your report).

That three-part citation is what makes a claim reviewable by
someone who was not in the room — which is, in the end, the
point of Chapter 13.
