# Chapter 3: Tail Latency and Systematic Debugging

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why tail latency (p99) matters more than average latency
>   in production systems
> - Compute and interpret percentile distributions from raw latency
>   data
> - Apply the USE method (Utilization, Saturation, Errors) to
>   systematically diagnose performance problems
> - Build an evidence chain with multiple independent signals to
>   support a diagnosis

Chapter 2 gave you the tools to measure a single process. This
chapter asks a different question: when the thing being measured is a
*service*, and the symptom is "p99 latency spiked", where do you
look? The answer has two layers. The first layer is statistical — why
the mean is a misleading number for a distribution with a long tail.
The second layer is mechanical — why p99 is almost always an OS
"slow path" (fault, queue, I/O wait, lock contention) that fires on a
small fraction of requests. Together they give you a debugging
discipline: the USE method, which turns "something is slow" into a
finite checklist.

## 3.1 Why the Mean Lies

A service reports "typical latency around 5 ms". Is it fast? It
depends on what you mean by typical:

| Percentile | Latency |
|---|---|
| p50 (median) | 3 ms |
| p90 | 8 ms |
| p99 | 150 ms |
| p99.9 | 800 ms |

The median looks fine. The tail does not. One request in a hundred
waits 150 ms — 50× the median. A page that makes a hundred backend
calls to render hits that tail on almost two-thirds of page loads:

```text
P(at least one call hits the p99) = 1 - 0.99^100 ≈ 0.63
```

In a fan-out system, the slowest component's tail becomes the user's
typical experience. This is **tail amplification**, and it is the
reason production systems live and die on p99, not on mean.

> **Key insight:** Averages hide the tail. A well-behaved service and
> a deeply broken one can have the same mean latency. If you only
> watch averages, you will not notice the broken one until customers
> complain.

### What percentiles actually mean

A percentile is a position in the sorted list of samples. Given
sorted latencies, p50 is the halfway value, p99 is the value that 99 %
of samples fall below:

```text
sorted latencies: [1, 2, 2, 3, 5, 8, 10, 15, 50, 500] ms
                   p10 p20 p30 p40 p50 p60 p70 p80 p90 p100
```

Two consequences:

- **Sample size matters.** The p99 of 100 samples is just the worst
  one — one noisy outlier and the whole metric moves. With 10 000
  samples, p99 is the top 100, which you can analyze statistically.
  The rule of thumb in this course: collect at least 10 000 requests
  before quoting a p99 number.
- **Histograms beat summaries.** A single p99 value summarizes the
  tail, but plotting the full distribution (or a CDF) shows whether
  the tail is a shelf, a ramp, or a bimodal mix. Tools like
  HdrHistogram store the distribution compactly for exactly this
  reason.

## 3.2 Percentile Statistics and Coordinated Omission

There is a common benchmarking bug that makes p99 numbers look
better than reality. The pattern is:

```python
while True:
    start = time.now()
    response = send_request()   # what if this takes 1 second?
    latency = time.now() - start
    record(latency)
```

If one request stalls, the benchmark stops sending during the stall.
The slow periods get under-sampled, which drags p99 down toward the
fast-path values. Gil Tene called this **coordinated omission**, and
his observation that "most published latency numbers are wrong" still
holds.

Three practical fixes:

1. **Constant arrival rate.** Decide to send a request every *X*
   milliseconds regardless of what the previous request did. A request
   that is "late to send" becomes a latency sample, not a missing
   measurement.
2. **Purpose-built tools.** `wrk2`, Gatling, and anything backed by
   HdrHistogram avoid coordinated omission by design.
3. **Measure from the client.** Include queue time — the time a
   request spent waiting to be sent — so you do not silently exclude
   the worst cases.

The lab in this chapter is small enough that coordinated omission is
not a problem (a single-threaded loop drives the workload and records
every iteration), but in any real benchmarking project this is the
first question to ask.

## 3.3 p99 Is Usually an OS "Slow Path"

Why does tail latency exist at all? A useful mental model:

- **Most requests** follow a **fast path** — data in cache, no
  contention, no fault, no queue. Latency is bounded by computation.
- **A few requests** trigger a **slow path** — a rare event with a
  large fixed cost. Latency is bounded by whatever the slow path has
  to wait for.

Slow paths are almost always OS-mediated. Four of them dominate
production outages:

- **CPU runqueue delay.** The thread is ready to run but the CPU is
  busy with something else. Measured by `sched_wakeup` →
  `sched_switch` latency; eBPF surfaces this directly (Chapter 5).
- **Blocking I/O.** A disk read, a network read, a fsync. The thread
  goes off-CPU and joins a queue. Measured by `iostat` (queue depth,
  `await`) and `/usr/bin/time -v` (voluntary context switches).
- **Page faults.** A minor fault is cheap; a major fault requires
  disk I/O and can cost milliseconds. Measured by `pgmajfault` in
  `/proc/vmstat` and `perf stat -e major-faults`.
- **Lock contention.** Mutex, futex, or spinlock wait. The thread is
  off-CPU waiting for another thread to release the resource.
  Measured by `perf lock`, bpftrace, or application-level lock
  counters.

The common thread: **tail latency is mostly time spent *waiting*, not
time spent *executing*.** Every one of these waits is a queue
somewhere in the OS — run queue, I/O queue, socket buffer, mutex
wait queue. If you find the queue, you find the slow path.

> **Note:** When the symptom is "only ~1 % of requests are slow", the
> 1 % is a big clue. It says some event that fires rarely is
> responsible. Start by listing the rare events your workload can
> trigger: major faults, GC pauses, compaction, failovers. Rule them
> out one at a time.

## 3.4 The USE Method

Brendan Gregg's **USE method** is not a tool. It is a coverage
algorithm: for every resource, check three things.

- **Utilization.** How busy is the resource? (% time busy, occupied
  capacity.)
- **Saturation.** Is there a queue? Is work backing up?
- **Errors.** Are operations failing?

The checklist is finite. For a typical Linux system:

| Resource | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | `top`, `mpstat` | `vmstat r`, `loadavg` | high involuntary context switches |
| Memory | `free -m`, RSS | reclaim, swap activity | OOM, major faults |
| Disk | `iostat -x` | `await`, queue depth | `dmesg` I/O errors |
| Network | `sar -n DEV` | `ss -s` | `netstat -s` |

USE is valuable precisely because it is boring. It forces you to
consider every resource, not just the one you already suspect.
"CPU is at 40 %, so it is not a CPU problem" is a common wrong answer
— the utilization is fine, but the *saturation* (runqueue length,
involuntary context switches) might not be. USE checks both.

### USE for memory, in detail

Memory is the workhorse of tail latency outages, so it is worth
expanding:

- **Utilization.** Process RSS, `free -m`, or in a container
  `memory.current` from cgroup v2. High by itself is not an error —
  Linux will happily use all your RAM for the page cache.
- **Saturation.** Reclaim activity (`pgscan_*` counters), swap in/out,
  direct reclaim stalls. This is where memory pressure first
  becomes visible.
- **Errors.** OOM-kill events in `dmesg`, and — the most important
  one for tail latency — **major page faults** (`pgmajfault`). A major
  fault is a rare, expensive event that looks exactly like a p99 slow
  path should look.

The case study in the next section walks through the full chain.

## 3.5 Building Evidence Chains

A single signal is a hypothesis. Two independent signals that agree
is a credible diagnosis. One signal plus an exclusion check that
rules out an alternative is better still. The rule of thumb in this
book: **two supporting signals + one exclusion check.**

Why "independent"? Because correlated signals do not prove anything
beyond what one of them already showed. `top` and `vmstat r` both
read CPU utilization — they are the same signal twice. `pgmajfault`
from `/proc/vmstat` and major faults from `/usr/bin/time -v` cover
the same mechanism from two different vantage points — one is a
system-wide counter, the other is per-process, and each could
disagree with the other for instructive reasons.

An evidence chain looks like this:

1. **Symptom.** p99 latency rose from 2 ms to 150 ms at 01:47.
2. **Hypothesis.** Memory pressure → major faults → tail spike.
3. **Signal 1.** `memory.current` sits at 95 % of `memory.max`.
4. **Signal 2.** `pgmajfault` increased 20× over baseline.
5. **Exclusion.** CPU utilization and `iostat` queue depth unchanged
   (rules out CPU saturation and disk contention as the primary
   mechanism).
6. **Diagnosis.** Memory pressure is forcing reclaim, and re-accessed
   pages cause major faults, which block requests long enough to
   appear as p99 outliers.
7. **Fix.** Raise `memory.max` to 1 Gi.
8. **Verification.** After the fix, `pgmajfault` returns to baseline
   and p99 drops from 150 ms to 5 ms.

A report without step 5 is a story. A report with step 5 is a
diagnosis.

## 3.6 Case Study: Memory Pressure and p99 Spikes

The alert arrives at 2 AM:

```text
Service: order-service
Alert:   p99 latency > 500 ms (threshold: 100 ms)
Started: 01:47
Affected: ~1 % of requests
```

The 1 % figure is already informative — something rare is happening.

**Step 0. Do not panic.** Before touching anything, ask three
questions: is this affecting users (errors, timeouts)? Is it getting
worse? Did anything change (deploy, config, traffic)? In this
scenario: errors normal, no deploys, traffic steady.

**Step 1. Frame the resources with USE.** A quick pass across CPU,
memory, disk, network. The memory column lights up:

```bash
$ free -m
                total        used        free      available
Mem:            1024         960          10             45
```

Memory usage is 95 % of the limit. That is utilization. Is there
saturation or are there errors?

**Step 2. Form hypotheses.** High memory could mean a leak (usage
trending up), a traffic spike (more concurrent requests), a noisy
neighbor (shared host pressure), or a too-tight limit (app needs
more headroom). Pick the two most plausible, investigate both,
exclude one before committing.

**Step 3. Check the fault counter.** This is the decisive signal for
memory-driven tail latency:

```bash
$ cat /proc/vmstat | egrep "pgmajfault|pgfault"
pgfault       81219310
pgmajfault       34127
```

Compared to baseline (`pgmajfault ≈ 3 000`), major faults are up
about 10×. Now we have a mechanism candidate.

**Step 4. Construct the chain.**

1. Memory utilization is near the limit.
2. The kernel reclaims pages to stay under `memory.max`.
3. Later accesses to those pages trigger **major faults**.
4. A major fault goes off-CPU for disk I/O; the scheduler runs
   something else; the request's clock keeps ticking.
5. The resulting wait inflates the tail, but only for requests that
   happen to touch a reclaimed page — hence "1 %".

This is why p50 looks fine: most requests never trigger the slow
path. The fast path is still the fast path.

**Step 5. Verify with an exclusion.** `iostat -x 1 5` shows disk
queue depth and `%util` unchanged outside brief bursts coincident
with the faults — the disk is not the primary bottleneck; it is
downstream of the memory pressure. Ruling out "disk saturation" as
the root cause strengthens the memory-pressure hypothesis.

**Step 6. Fix and verify.**

```bash
kubectl set resources deployment/order-service --limits=memory=1Gi
```

Watch for:

- `memory.current / memory.max` drops below 80 %.
- `pgmajfault` rate returns to baseline.
- p99 recovers to around 5 ms within a few minutes.

No before/after measurement = no confidence in the fix.

**Step 7. Prevent recurrence.** Short term: alert on
`memory.current / memory.max` and on `pgmajfault` rate. Long term:
right-size limits in staging with a realistic workload; reduce the
working set by improving locality or caching.

The case study matches the structure you will use in every oncall
write-up in this book: symptom → hypothesis → evidence → mechanism →
fix → verification. The lab turns this template into a simulated
oncall shift.

## Summary

Key takeaways from this chapter:

- The mean is a misleading number for a distribution with a long
  tail. Percentiles, especially p99, are what production systems
  live or die on. Tail amplification means a page with a hundred
  backend calls hits the p99 on ~63 % of loads.
- p99 latency is almost always an OS slow path: runqueue delay,
  blocking I/O, page faults, or lock contention. Find the queue,
  find the slow path.
- The USE method (Utilization, Saturation, Errors) is a coverage
  algorithm that forces you to consider every resource, not just
  the one you already suspect.
- A credible diagnosis needs at least two independent supporting
  signals plus one exclusion check. Two correlated signals is still
  one signal.
- Always verify a fix with before/after measurements. A fix you did
  not measure is a hope, not a fix.

## Further Reading

- Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *CACM* 56(2).
- Gregg, B. (2013). *The USE Method.*
  <https://www.brendangregg.com/usemethod.html>
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Chapter 2:
  Methodology.
- Tene, G. *How NOT to Measure Latency*.
  <https://www.youtube.com/watch?v=lJ8ydIuPFeU>
- HdrHistogram: <https://github.com/HdrHistogram/HdrHistogram>
- Linux kernel, `man 5 proc` — the `/proc/vmstat` counters.
- Linux cgroup v2 memory controller:
  <https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html>
