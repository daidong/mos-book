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

Interpretation rules of thumb (Chapter 2 §2.8–2.9):

- **IPC = instructions / cycles**; ~2–4 is healthy, below 1 is
  usually memory-stall-bound.
- **cache miss rate = cache-misses / cache-references**; look
  at the rate, not the count.
- **`<not supported>` in a VM** means the PMU event is
  unavailable; switch to Valgrind (Chapter 2 §2.9, *Valgrind
  fallback for VMs*).

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

### `bpftool`

The official kernel tool for inspecting loaded BPF programs and
maps. Used in Chapter 5's lab to confirm a libbpf tool actually
attached:

```bash
sudo bpftool prog                  # list loaded BPF programs
sudo bpftool prog show id <id>     # details for one program
sudo bpftool map                   # list BPF maps
sudo bpftool map dump id <id>      # dump map contents
sudo bpftool perf show             # perf-event attachments
```

`bpftool` ships with `linux-tools-$(uname -r)` on Ubuntu. It is
the right answer to "is my eBPF program actually running?" — if
it is not in `bpftool prog`, your `bpftrace` or libbpf loader
failed silently.

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

### `seccomp-tools` and `libseccomp`

Used in Chapter 12 to install syscall filters around tool
execution.

```bash
sudo apt install -y libseccomp-dev seccomp
# Inspect a binary's installed seccomp filter at runtime:
sudo cat /proc/<pid>/status | grep -E "Seccomp|Speculation"
# Dump a binary's static filter (if present):
seccomp-tools dump ./hardened_binary
```

Writing a filter from Python:

```python
import seccomp
f = seccomp.SyscallFilter(defaction=seccomp.KILL)
for name in ["read", "write", "openat", "close",
             "fstat", "exit_group", "mmap", "munmap"]:
    f.add_rule(seccomp.ALLOW, name)
f.load()                              # filter is now active
```

Key rule: install the filter **after** any heavyweight runtime
(Python, JVM) has finished its own startup syscalls, or hand off
to a minimal helper binary via `execve`. See Chapter 12 §12.7
for the per-tool filter design.

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

### `kind`

"Kubernetes-in-Docker" — the lab cluster used in Chapters 7, 9,
and 11. Gives you a real control plane and kubelet inside
Docker containers without provisioning a VM cluster.

```bash
# Install the binary (or `go install sigs.k8s.io/kind@latest`):
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/

# Create a cluster (single-node by default):
kind create cluster --name lab
# Multi-node from a config file:
kind create cluster --name lab --config kind-cluster.yaml

# Common ops:
kind get clusters
kind get nodes --name lab          # docker container names of nodes
kind delete cluster --name lab

# The Pod's cgroup lives on the node container, not the host:
NODE=$(kind get nodes --name lab | grep worker | head -1)
docker exec -it $NODE bash         # shell on the kind node
```

A frequent pitfall: looking for cgroup files or `dmesg` lines on
the *host*. They live on the kind node container; `docker exec`
is the entry point.

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

### etcd `benchmark`

Not installed by default; build from source (Chapter 8 lab):

```bash
git clone --depth 1 --branch v3.5.17 https://github.com/etcd-io/etcd
cd etcd && go install ./tools/benchmark
export PATH=$PATH:$(go env GOPATH)/bin

# Single-key write throughput
benchmark --endpoints=$EP --conns=1 --clients=1 \
  put --total=10000 --key-size=16 --val-size=256

# Linearizable vs serializable read latency
benchmark --endpoints=$EP range /foo --consistency=l --total=1000
benchmark --endpoints=$EP range /foo --consistency=s --total=1000
```

---

## B.7 Storage Benchmarks (Redis, MinIO)

### `redis-cli` and `redis-benchmark`

Two tools that ship together. `redis-cli` is for inspection;
`redis-benchmark` is for throughput and latency measurement.

```bash
# Inspection
redis-cli -p 6379 PING
redis-cli -p 6379 INFO memory | grep used_memory_human
redis-cli -p 6379 CONFIG GET appendfsync
redis-cli -p 6379 DEBUG POPULATE 1000000 prefix 100   # synthetic data
redis-cli -p 6379 BGSAVE                              # trigger RDB snapshot

# Benchmarking
redis-benchmark -h 127.0.0.1 -p 6379 -t set -n 200000 -c 50 -P 1
# -t   workload (set, get, lpush, ...)
# -n   total operations
# -c   parallel clients
# -P   pipeline depth (--csv adds CSV output)
```

The `-P` knob is essential when measuring fsync-bound modes
(Chapter 11 §11.4): pipelining amortizes one fsync over many
operations. Run `-P 1` and `-P 16` to see the gap.

### `mc` (MinIO client)

S3-compatible CLI used in Chapter 11 lab Part D:

```bash
# Install
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Configure an alias for an endpoint
mc alias set local http://127.0.0.1:9000 admin password

# Bucket and object ops
mc mb local/lab                        # create bucket
mc cp ./file.dat local/lab/            # PUT
mc ls local/lab/                       # list
mc cat local/lab/file.dat              # GET
mc rm local/lab/file.dat               # DELETE
```

`mc` works against any S3-compatible endpoint, not just MinIO
(AWS, Cloudflare R2, Backblaze B2). For benchmarking, use
`mc admin trace` or `s3-benchmark` rather than wrapping `mc cp`
in a shell loop — the loop's process-startup cost dominates.

---

## B.8 Networking (Light Reference)

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

## B.9 Agent and trace observability

Used in Chapter 12 Lab F. None of these need to be installed by
hand; the lab implements a minimal tracer in 30 lines of Python.
In production you would use one of:

```bash
# OTel auto-instrumentation for Python LLM apps
pip install opentelemetry-distro \
            opentelemetry-instrumentation-openai
opentelemetry-bootstrap -a install

# OpenLLMetry / OpenInference / Phoenix / Langfuse:
# pip-installable libraries that emit gen_ai.* spans automatically.
```

The relevant attribute names are the OTel *generative AI*
semantic conventions. Use them verbatim:

| Span name | When |
|---|---|
| `agent.task` (or `invoke_agent`) | one full agent task (root) |
| `gen_ai.client.request` | one LLM call |
| `tool.call` (or `execute_tool`) | one tool invocation |

Key attributes:

- `gen_ai.system` ("openai", "anthropic", ...)
- `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
  `gen_ai.usage.output_tokens`, `gen_ai.response.finish_reasons`
- `tool.name`, `tool.args_hash`, `tool.status`

If your code emits compliant spans, any OTel-aware backend
(Jaeger, Tempo, Honeycomb, Datadog, Phoenix, Langfuse) renders
the waterfall the same way.

---

## B.10 Reading This Appendix

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
point of the Chapter 3 evidence contract: every measurement
should carry the tool that produced it, the exact invocation,
and the raw output, so a peer can audit the chain without
asking you to re-run anything.
