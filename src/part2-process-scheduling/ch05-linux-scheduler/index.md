# Chapter 5: Linux Scheduler Internals and Observability

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain how CFS / EEVDF works: weights, virtual runtime,
>   eligibility, and task selection
> - Describe the critical path from wakeup to running and identify
>   the tracepoints that observe it
> - Write small eBPF programs (bpftrace one-liners and a libbpf tool)
>   that measure scheduling latency
> - Reason about the observer effect and when eBPF overhead matters

Two facts from Chapter 4 set up this one. First, scheduling latency
— the wait between `sched_wakeup` and `sched_switch` — is the
dominant tail-latency source on any system that is not 100 %
loaded. Second, that wait is determined by which task the kernel
picks next, which is the scheduler's job.

So the question this chapter answers is: *given a wakeup, how does
the kernel decide who runs, and how do I see that decision from
user space without recompiling the kernel?* The answer is two
things. The first is **CFS** (and its EEVDF successor) — the
policy that picks the most under-served runnable task in O(log n).
The second is **eBPF** — the verifier-checked, in-kernel
observability mechanism that lets you measure the picking decision
at production scale without patches. By the end of the chapter, you
should be able to look at any p99 latency problem and know which
tracepoints to attach in the next thirty seconds.

## 5.1 How does CFS share a CPU fairly?

The scheduling problem CFS solves is small to state and large to
implement. Given `n` runnable tasks with weights `w₁, w₂, …, wₙ`
sharing one CPU, allocate to task `i` a share of CPU time equal to
`wᵢ / Σw`. Equal weights means equal time. Doubled weight means
double the share. The scheduler must pick the next task in O(log n)
on every preemption, fair across short windows as well as long
ones, and tolerant of tasks coming and going.

Ingo Molnar's CFS, merged into Linux 2.6.23 in October 2007
(Molnar, 2007), is the kernel's answer. It replaced the O(1)
multilevel-feedback scheduler that had served Linux since 2.6.0 in
2003. In one sentence:

> CFS gives each runnable task CPU time proportional to its weight,
> and keeps tasks from falling too far behind.

The trick that makes this O(log n) is **virtual runtime** — a
single scalar per task that summarizes "how much credit you have
been denied so far." The next-to-run is whichever runnable task is
most under-served, found by following the leftmost pointer of a
red-black tree. We will derive the bookkeeping in three steps.

### Step 1: vruntime as weighted real time

Each `task_struct` carries a `vruntime` field — a scalar counter
measured in nanoseconds. When a task runs for `runtime` nanoseconds
of real time, its `vruntime` advances by

```text
Δvruntime = runtime × (weight_0 / weight_task)
```

where `weight_0` is the weight at `nice = 0`. The intuition is
straightforward: a high-weight task accumulates `vruntime` slowly
(it "earns credit" cheaply) and a low-weight task accumulates
`vruntime` quickly (it earns the same credit in fewer real
nanoseconds). Two equal-weight tasks see their `vruntime` advance at
the same wall-clock rate.

### Step 2: pick the smallest vruntime

The scheduling rule is then trivially simple: at each decision
point, **run the runnable task with the smallest `vruntime`**.
Smaller `vruntime` means "most under-served relative to weight,"
and running that task is how CFS catches it up.

This rule has the right asymptotic behavior. Two equal-weight
tasks alternate, each accumulating `vruntime` at the same rate. A
weight-1024 task and a weight-110 task share a CPU 9.3 : 1, because
the weight-110 task's `vruntime` rises 9.3× faster, so it must run
9.3× less often to keep its `vruntime` competitive.

### Step 3: red-black tree for O(log n)

Linux stores runnable tasks in a per-CPU **red-black tree** ordered
by `vruntime`. "Smallest `vruntime`" is the leftmost node — an
O(log n) lookup that is fast enough for the scheduling hot path
even on a runqueue with hundreds of tasks. Insertion (on wakeup)
and removal (on sleep) are also O(log n). Cormen et al. (2022) is
the standard reference for the data structure; `kernel/sched/fair.c`
is where Linux uses it.

![CFS data structures: the per-CPU rq contains a cfs_rq with a red-black tree of sched_entity nodes ordered by vruntime; the leftmost node is the next to run](figures/cfs_structs_rq_cfsrq_se.svg)
*Figure 5.1: CFS data structures. Each CPU's `rq` contains a `cfs_rq` with a red-black tree of scheduling entities ordered by `vruntime`. The leftmost node — the most under-served task — is the next to run.*

### Nice, weight, and CPU share

The `nice` values you can set correspond to a lookup table of
weights. A small slice of it:

| nice | weight (approx) | share vs nice=0 |
|---|---|---|
| −20 | 88 761 | ~86× |
| 0 | 1 024 | 1× |
| +19 | 15 | ~1/68× |

If three tasks with weights `w_A`, `w_B`, `w_C` share one CPU,
CFS allocates each a share proportional to `w_i / Σ w`. Lab 3
(Chapter 4) used `nice -n 19` to starve a background hog; the
numbers above are why it worked.

### Target latency and minimum granularity

CFS picks a **target latency** — a period over which every runnable
task should get at least one chance to run — and divides it among
runnable tasks by weight. Tunables:

- `sched_latency_ns` (default ~6 ms on desktops)
- `sched_min_granularity_ns` (lower bound per slice, default ~0.75 ms)
- `sched_wakeup_granularity_ns` (preemption threshold on wakeup)

Each task's time slice is `sched_latency × weight / Σ weights`,
clamped below by `min_granularity` to avoid pathological tiny slices
when the runqueue is long. These knobs are exposed under
`/sys/kernel/debug/sched/` on kernels with `CONFIG_SCHED_DEBUG`.

### From CFS to EEVDF (Linux 6.6+)

In October 2023, Linux 6.6 replaced CFS's pick logic with an
**EEVDF**-style scheduler (Earliest Eligible Virtual Deadline
First). The patch series was led by Peter Zijlstra; the algorithm
comes from a 1995 paper by Stoica and Abdel-Wahab at Old Dominion
University (Stoica & Abdel-Wahab, 1995), originally proposed for
proportional-share resource allocation in real-time systems.

EEVDF is a small generalization of classical CFS. Two new ideas
are layered on top of `vruntime`:

- **Eligibility.** A task is *eligible* to run once it has not been
  "paid" more service than it was owed. A task that was just running
  and consumed its slice becomes ineligible for a brief period; a
  task that just woke is eligible immediately. This prevents
  starvation of long-sleepers without the ad-hoc "`vruntime` floor"
  hacks that classical CFS accumulated over fifteen years.
- **Virtual deadline.** Each eligible task carries a deadline
  computed from its weight and the current virtual time. The
  scheduler picks the eligible task with the **earliest deadline**.

`vruntime` still represents "service received"; EEVDF just adds the
deadline as a more principled way to pick among eligible tasks. The
practical consequences for this book:

![Intuition for vruntime, eligible tasks, and deadlines: Task A has high vruntime (well-served), Task B just woke with low vruntime and earliest deadline, so the scheduler picks B](figures/vruntime_eligible_deadline_intuition.png)
*Figure 5.2: EEVDF intuition. Three tasks with different vruntime values. Task B just woke with the lowest vruntime and the earliest virtual deadline, so the scheduler picks it next. The eligible set excludes tasks that have been over-served relative to their weight.*

- Existing scheduler tracepoints (`sched_wakeup`, `sched_switch`,
  `sched_migrate_task`) continue to work — they observe events, not
  internal function names.
- The "run the most under-served eligible task" intuition from CFS
  still explains most of what you see in the lab.

## 5.2 The critical path from wakeup to run

Knowing how CFS picks the next task is half the story. The other
half is *when* the picking happens — because between the
`sched_wakeup` event and the corresponding `sched_switch`, the
kernel may run several other things first. That delay is the
scheduling latency Chapter 4 named.

When a task becomes runnable, four things happen:

1. **Wakeup.** The task transitions from `Blocked` to `Runnable` —
   an I/O completed, a timer fired, a lock was released. The kernel
   generates `sched:sched_wakeup` (or `sched_wakeup_new` for newly
   forked tasks).
2. **Enqueue.** The task is placed in a per-CPU runqueue. The choice
   of which CPU depends on the wakeup's source CPU, affinity mask,
   cache topology, and idle-balance hints; the kernel tries to wake
   a task on a CPU that is already warm for it.
3. **Pick.** On the target CPU, the scheduler picks the next task to
   run. EEVDF/CFS walks a small chain of scheduling classes —
   Deadline (`SCHED_DEADLINE`), Realtime (`SCHED_FIFO`/`SCHED_RR`),
   Fair (normal tasks), Idle — and the first class with a runnable
   task wins. Almost everything in userspace is Fair.

![Scheduling class chain: pick_next_task walks Deadline → Realtime → Fair → Idle, selecting the first class with a runnable task](figures/sched_class_chain_pick_next_task.svg)
*Figure 5.3: The scheduling class chain. `pick_next_task` walks the classes in strict priority order. Deadline and Realtime always preempt Fair; almost all user-space work lives in the Fair class.*
4. **Switch.** A context switch delivers CPU to the chosen task,
   generating `sched:sched_switch`.

Why does step 4 lag step 1? In roughly decreasing order of impact:

- The CPU is busy and the current task has not reached a preemption
  point. This is the most common case on a saturated runqueue.
- The runqueue is long: multiple tasks are ahead in the EEVDF tree.
- The wakeup landed on the "wrong" CPU and a migration is needed.
  Linux's wake-affine logic (`select_task_rq_fair` in
  `kernel/sched/fair.c`) tries to wake a task on a CPU that is
  already cache-warm for it, but on a busy multi-socket box the
  hint can be wrong.
- A higher-priority class (RT, Deadline) is running and Fair does
  not get a chance.
- Interrupt work, kernel threads (`ksoftirqd`, `kworker`), or RCU
  callbacks are occupying the CPU briefly.

The first-order predictor of scheduling latency is *how many
runnable tasks share the CPU, weighted by their weights*. That is
exactly the number eBPF can estimate from the tracepoints in the
next section.

### sched_ext: eBPF-based scheduling classes (Linux 6.12+)

Starting with Linux 6.12 in November 2024, the kernel supports
**sched_ext** — a framework for writing entire scheduling policies
as eBPF programs (Heo et al., 2024). Instead of observing the
scheduler from outside, sched_ext lets you *replace* the Fair
class's pick logic with a BPF program that the verifier checks at
load time. The merge was contentious; the public mailing-list
discussion is a useful primary source on what the Linux community
considers an acceptable scheduler-extension surface.

Three reasons sched_ext matters for this book:

- It validates Chapter 4's separation of policy and mechanism
  (Lampson, 1983). sched_ext keeps the kernel's context-switch
  and runqueue mechanism intact; only the pick-next-task policy is
  pluggable.
- Production users — Meta has published its `scx_layered` policy
  for partitioning latency-sensitive front-ends and batch jobs on
  the same kernel — are already deploying sched_ext for
  workload-specific scheduling. Google and Oracle have publicly
  contributed policies of their own.
- The tracepoints this chapter teaches (`sched_wakeup`,
  `sched_switch`) still work under sched_ext, because they
  observe events, not policy internals. Nothing in the lab
  changes.

We will not write a sched_ext scheduler in this book, but
understanding CFS/EEVDF is the prerequisite for understanding what
sched_ext replaces and why.

## 5.3 Tracing the scheduler with eBPF

Knowing the policy and the critical path is not enough; you also
have to *see* the policy decide and the path execute. The standard
Linux answer is **eBPF**: extended Berkeley Packet Filter — a
verifier-checked, in-kernel virtual machine that runs small
programs in response to kernel events.

The lineage matters for understanding what eBPF can and cannot do.
BPF began as McCanne and Jacobson's (1993) packet-filter language
for `tcpdump`. Two decades later, Alexei Starovoitov rebuilt it as
a general-purpose in-kernel programming environment, merged into
Linux 3.18 (2014) and aggressively expanded since (Fleming, 2017;
Gregg, 2019). The verifier statically proves that an eBPF program
terminates, does not dereference unsafe memory, and does not loop
unboundedly — which is what makes attaching code to the scheduler's
hot path safe enough for production.

Two kinds of attachment points matter for this chapter:

- **Tracepoints** are *stable* instrumentation sites deliberately
  placed in the kernel source. Their field layouts are part of the
  kernel's observable API and are tested across kernel versions.
  Scheduler tracepoints — `sched_wakeup`, `sched_switch`,
  `sched_migrate_task`, and others — have been stable since
  approximately Linux 2.6.32 (2009) and are the right first
  choice.
- **kprobes** attach to arbitrary kernel function entries. They are
  more flexible and more fragile: a function inline or a rename in
  a new kernel can silently break your probe. Use tracepoints
  when you can, kprobes only when you have to.

You can list scheduler tracepoints and their fields with `bpftrace`:

```bash
$ sudo bpftrace -l 'tracepoint:sched:*'
tracepoint:sched:sched_wakeup
tracepoint:sched:sched_wakeup_new
tracepoint:sched:sched_switch
tracepoint:sched:sched_migrate_task
...

$ sudo bpftrace -lv tracepoint:sched:sched_switch
tracepoint:sched:sched_switch
    char prev_comm[16]
    pid_t prev_pid
    int prev_prio
    long prev_state
    char next_comm[16]
    pid_t next_pid
    int next_prio
```

The fields tell you what `args->...` can read inside a bpftrace
handler.

### bpftrace in one page

bpftrace is "awk for the kernel": pick an event, write a handler,
aggregate in-kernel. Four idioms are enough for most scheduler
investigations.

**Filters.** Only run the handler under a condition.

```bpftrace
tracepoint:sched:sched_switch / comm == "bash" / { @c = count(); }
```

**State.** Store per-PID or per-TID information in a BPF map.

```bpftrace
tracepoint:sched:sched_wakeup { @ts[args->pid] = nsecs; }
```

**Aggregation.** `count()`, `sum()`, `avg()`, `hist()` build the
result in kernel memory without streaming every event to userspace.

```bpftrace
@lat_us = hist($d_us);
```

**Cleanup.** `delete(@map[key])` removes one entry; `clear(@map)`
empties the whole map.

![eBPF tracing measurement pattern: Event 1 (sched_wakeup) stores a timestamp in a BPF map; Event 2 (sched_switch) looks up the timestamp, computes the delta, and stores the result in an in-kernel histogram; user space reads aggregates](figures/ebpf_latency_recipe.png)
*Figure 5.4: The "two events + one state" eBPF recipe. `sched_wakeup` records a timestamp; `sched_switch` computes the delta and pushes it to an in-kernel histogram. User space reads the aggregated result — no per-event streaming required.*

Together those idioms express the canonical scheduler-latency
script, which is small enough to memorize:

```bpftrace
tracepoint:sched:sched_wakeup {
    @ts[args->pid] = nsecs;
}

tracepoint:sched:sched_switch / @ts[args->next_pid] / {
    $d_us = (nsecs - @ts[args->next_pid]) / 1000;
    @lat_us = hist($d_us);
    delete(@ts[args->next_pid]);
}
```

Two events, one piece of state: record the wakeup timestamp, look it
up when the task actually runs, push the delta to a histogram. This
is the recipe. Every measurement in this chapter's lab is a variation
on it.

### More useful one-liners

**Who is switching out the most?**

```bpftrace
tracepoint:sched:sched_switch { @sw[args->prev_comm] = count(); }
interval:s:5 { print(@sw, 20); clear(@sw); }
```

High switch-out counts reveal short CPU bursts — typically
I/O-bound work or lock contention. Note that this does *not* mean
"uses the most CPU"; for that you need runtime accounting.

**Latency broken down by program.**

```bpftrace
tracepoint:sched:sched_wakeup { @ts[args->pid] = nsecs; }
tracepoint:sched:sched_switch / @ts[args->next_pid] / {
    $d_us = (nsecs - @ts[args->next_pid]) / 1000;
    @lat_by_comm[args->next_comm] = hist($d_us);
    delete(@ts[args->next_pid]);
}
```

Produces one histogram per `comm`, so you can see which program is
living in the tail.

### A production debugging example

The recipe above is not a classroom exercise; it is the standard
first step in production scheduler debugging. A concrete use: an
inference-serving team sees p99 latency spike from 12 ms to 80 ms
on a 64-core host at ~40 % average CPU. They attach a one-liner:

```bash
sudo bpftrace -e '
  tracepoint:sched:sched_wakeup /comm == "infer-worker"/ {
      @ts[args->pid] = nsecs;
  }
  tracepoint:sched:sched_switch /comm == "infer-worker" && @ts[args->next_pid]/ {
      @lat_us = hist((nsecs - @ts[args->next_pid]) / 1000);
      delete(@ts[args->next_pid]);
  }
  interval:s:10 { exit(); }
'
```

The histogram shows a bimodal distribution: most wakeups land in
1–5 µs, but ~2 % land in 2–8 ms. Cross-referencing with
`sched:sched_migrate_task`, those slow wakeups correlate with
cross-NUMA migrations triggered by a log-shipping cgroup that
periodically saturates one socket. Pinning the inference workers to
NUMA node 0 via `numactl --cpunodebind=0` eliminates the tail.

### When bpftrace is not enough

bpftrace is perfect for exploration — a one-liner gets you a
histogram in seconds. For longer investigations you usually want:

- a stable output format (CSV for later analysis)
- precise field selection
- the ability to build up state across many probes

That is where a **libbpf**-based program comes in: C code with BPF
sections, a user-space loader, a ring buffer for events. The
`schedlab` tool in the lab is exactly this — a minimal libbpf
program that attaches to the scheduler tracepoints and writes
per-event CSV. Its `.bpf.c` file is less than a hundred lines, and
its two attachment points are the same `sched_wakeup` /
`sched_switch` pair you just saw in bpftrace.

### From observation to enforcement: cpuset isolation at scale

The NUMA-pinning vignette above shows what one team did on one
host. The platform-level version of the same problem is what
hyperscalers do across millions of cores: they observe the
scheduler with the same tracepoints, then *enforce* placement
through `cpuset` cgroups so that observation becomes guarantee.
Three documented patterns are worth naming because each one is the
production interpretation of a Chapter 4–7 mechanism:

- **AWS Nitro / Firecracker hypervisor pinning.** Each Nitro
  hypervisor reserves dedicated CPUs for the platform (network,
  storage, telemetry) and exposes only the remaining cores to the
  guest VM. The reservation uses `cpuset` cgroups to fence the
  platform threads off the guest cores (Agache et al., 2020).
  Without it, every guest's p99 would carry the variance of every
  host-side packet interrupt and EBS I/O completion. The published
  sub-millisecond IO jitter on a c7i instance is unreachable
  without this isolation.

- **Google Borg / Kubernetes static CPU manager.** Borg's
  scheduler reserves whole physical cores for *latency-sensitive*
  jobs and leaves *batch* jobs to share the remainder via CFS
  (Verma et al., 2015). Kubernetes copied the design as the
  kubelet's `--cpu-manager-policy=static`: a Pod with
  `Guaranteed` QoS and integer CPU requests gets pinned to
  specific cores via `cpuset.cpus`, while every other Pod runs on
  the shared pool. This is the production interpretation of
  Chapter 7's QoS classes — they are not just a billing tier; they
  are a cgroup membership decision that changes which CFS
  runqueue your workload competes on.

- **NUMA-aware pinning for ML inference.** Meta's Llama serving
  fleet pins inference workers per NUMA node so that the model
  weights, the KV cache, and the worker thread all live on one
  socket. Cross-socket access on a modern Xeon costs ~2–3× the
  memory latency of local access; for bandwidth-bound decode
  loops, that ratio is the difference between meeting and missing
  TTFT SLO. The kernel-side support is straightforward
  (`numactl`, `cpuset.mems`); the discipline is in keeping the
  binding correct as the worker pool resizes.

Three platforms, one mechanism: `cpuset` cgroups plus NUMA binding
turn a shared multi-tenant box into something that behaves like a
private one for the tenants that need it. The lab's eBPF tracing is
the same observation tool the platform teams use to validate that
the binding actually has the intended effect. "We set
`cpuset.cpus = 0-3`" and "`sched_migrate_task` no longer fires
across the boundary" are two independent signals that together
close the evidence loop à la Chapter 3 §3.6.

## 5.4 Measuring scheduling latency end to end

Putting the recipe and tools together, the measurement procedure is
four lines long:

1. Attach to `sched_wakeup`; store `nsecs` keyed by `pid` in a BPF
   map.
2. Attach to `sched_switch`; when the `next_pid` has a stored
   wakeup time, compute `nsecs - wakeup_time` and emit it (via
   histogram or ring buffer).
3. Delete the map entry so the wakeup is only counted once.
4. In user space, aggregate percentiles from the stream of
   latencies.

`schedlab --mode latency --duration 20 --output latency.csv` does
exactly this and produces one row per observed scheduling event.

Cross-check with the probe from Chapter 4's lab: the p99 reported by
`schedlab` should agree with `wakeup_lat`'s percentile to within
measurement noise. If they disagree sharply, either the eBPF tool is
misattributing events (common if the task's wakeups coalesce
faster than `sched_switch` fires) or the probe is not the only
runnable task on the CPU.

### Fairness: comparing tasks directly

The same tracepoints give you a fairness view. `sched_switch` tells
you which task got each scheduling slot. Tracking runtime per task
(time it spent as the `prev` task in each switch) and wait time
(time between a wakeup and the matching switch-in) lets you compute

```text
CPU share ≈ run_time / (run_time + wait_time)
```

for each task. In a CFS world, CPU shares should be proportional to
weights. If you launch two `stress-ng --cpu 1` workers with `nice=0`
and `nice=10`, their shares should come out roughly `1 : (1024/110) ≈
9.3 : 1`. The lab walks through this experiment.

## 5.5 What does the observation cost?

Every tracing tool costs something. The same property that makes
eBPF safe enough to attach to the scheduler hot path — a
verifier-checked program that runs on every event — also means the
program runs on every event, and every event has a price.
Heisenberg's principle for systems work: you cannot measure the
scheduler without slightly perturbing it. The discipline is making
the perturbation small enough that it does not move the number you
care about.

Three sources of overhead in eBPF tracing:

- **Running on a hot path.** `sched_switch` fires every context
  switch — potentially millions per second on a busy machine.
- **Map operations.** Storing and loading per-PID state uses hash
  maps; a full miss is a few hundred nanoseconds.
- **Emitting events.** Streaming every event to userspace via perf
  ring buffer is strictly more work than aggregating in-kernel.

Two practical rules keep the observer effect small:

1. **Aggregate in-kernel whenever possible.** `hist()`, `count()`,
   and `sum()` are free compared to a ring-buffer event per switch.
2. **Keep per-event logic minimal.** No printing from the hot path.
   No userspace callouts. No expensive map lookups.

In this lab, with in-kernel histograms and no streaming, you should
see less than ~1 µs per event of added cost and less than a few
percent total CPU overhead even on a busy system. The optional Part D
measures this directly.

> **Warning:** Streaming scheduler events without any filter on a
> busy host can easily consume 5–20 % of a CPU and distort the very
> p99 you are trying to measure. Always start with filters (`pid`,
> `comm`, cgroup) or aggregations.

### VM reality check

In a VM, hardware PMU events are often unavailable or wrong — but
**tracepoints are not PMU events**. They are stable kernel
instrumentation that works in VirtualBox, VMware, KVM, or on bare
metal. That is why the lab uses eBPF tracepoints as its primary
measurement tool: cache-miss numbers may be zero in your VM, but the
scheduler tracepoints will be real.

## Summary

Key takeaways from this chapter:

- CFS (and its EEVDF successor since Linux 6.6) runs the most
  under-served eligible runnable task. Weight determines how fast
  `vruntime` accumulates; the red-black tree keeps "smallest
  `vruntime`" selectable in O(log n).
- The critical path from wakeup to run has four steps (wakeup,
  enqueue, pick, switch), each observable through a stable
  tracepoint.
- eBPF plus two tracepoints (`sched_wakeup` and `sched_switch`) is
  enough to measure scheduling latency precisely. The pattern —
  "two events plus one piece of state" — is small enough to write
  as a bpftrace one-liner and extend into a libbpf tool for
  production.
- The observer effect is real but manageable: aggregate in-kernel,
  keep per-event work minimal, filter early. Tracepoints work in
  VMs where hardware PMU events do not.

## Further Reading

### CFS, EEVDF, and sched_ext

- Molnar, I. (2007). *CFS Scheduler Design.*
  <https://www.kernel.org/doc/Documentation/scheduler/sched-design-CFS.rst>
- Stoica, I., & Abdel-Wahab, H. (1995). *Earliest Eligible Virtual
  Deadline First: A Flexible and Accurate Mechanism for Proportional
  Share Resource Allocation.* Old Dominion University Tech. Rep.
  TR-95-22.
- Zijlstra, P. (2023). "sched/eevdf: An EEVDF-based replacement for
  the fair scheduler." Linux kernel patch series; merged in v6.6.
- Heo, T., Vernet, D., et al. (2024). "sched_ext: Extensible
  scheduling class for the Linux kernel." Linux Plumbers Conference.
- Wong, C. S., et al. (2008). "Towards Achieving Fairness in the
  Linux Scheduler." *ACM SIGOPS OSR*. (Pre-CFS critique that
  motivated the rewrite.)
- Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C.
  (2022). *Introduction to Algorithms*, 4th ed. MIT Press.
  Chapter 13 (red-black trees).

### eBPF

- McCanne, S., & Jacobson, V. (1993). "The BSD Packet Filter: A New
  Architecture for User-Level Packet Capture." *USENIX Winter*.
- Fleming, M. (2017). "A thorough introduction to eBPF." LWN.net.
  <https://lwn.net/Articles/740157/>
- Gregg, B. (2019). *BPF Performance Tools.* Addison-Wesley.
  Chapters 1–3, Chapter 6 (CPUs), Chapter 8 (File Systems).
- Calavera, D., & Fontana, L. (2019). *Linux Observability with
  BPF.* O'Reilly.
- Nakryiko, A. "BPF Portability and CO-RE."
  <https://nakryiko.com/posts/bpf-portability-and-co-re/>

### Datacenter and platform context

- Verma, A., Pedrosa, L., Korupolu, M., et al. (2015). "Large-scale
  cluster management at Google with Borg." *EuroSys*.
  <https://doi.org/10.1145/2741948.2741964>
- Agache, A., Brooker, M., et al. (2020). "Firecracker: Lightweight
  virtualization for serverless applications." *NSDI*.
- Tang, C., Yu, K., Veeraraghavan, K., et al. (2020). "Twine:
  A Unified Cluster Management System for Shared Infrastructure."
  *OSDI*. (Meta's Borg-equivalent; describes per-NUMA pinning at
  fleet scale.)

### Kernel sources and docs

- Linux kernel: `kernel/sched/fair.c`, `kernel/sched/core.c`,
  `kernel/sched/ext.c`.
- bpftrace reference:
  <https://github.com/iovisor/bpftrace/blob/master/docs/reference_guide.md>
- libbpf documentation: <https://libbpf.readthedocs.io/>
