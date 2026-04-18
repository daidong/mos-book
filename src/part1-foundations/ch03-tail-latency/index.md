# Chapter 3: Tail Latency and Systematic Debugging

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why p99 latency matters more than average latency for most
>   production services
> - Read percentile summaries and reason about what they hide
> - Apply the USE method (Utilization, Saturation, Errors) as a disciplined
>   incident workflow
> - Build an evidence chain with supporting signals and an explicit exclusion
>   check

Chapter 2 focused on a single program. This chapter shifts to services and
incidents. The question is no longer merely "why is this binary slower?" It
is "why are a small fraction of requests suddenly much slower, and how do I
prove the cause?"

## 3.1 Why p99 Matters More Than the Mean

Suppose a service reports these numbers:

| Metric | Value |
|---|---:|
| mean | 6 ms |
| p50 | 3 ms |
| p90 | 8 ms |
| p99 | 150 ms |
| p99.9 | 800 ms |

The mean sounds fine. The tail does not. One request in a hundred takes 150
ms. If a page fan-outs to 100 backend calls, the chance that at least one of
those calls lands in the p99 is:

```text
1 - 0.99^100 ≈ 0.63
```

![Diagram showing one page request faning out to one hundred backend calls, where a small fraction of slow calls still makes many page loads experience the tail](figures/tail-amplification.svg)
*Figure 3.1: Tail amplification is a fan-out effect. A dependency can be slow only rarely and still dominate the user-facing experience once each page load depends on many such calls.*

So a page composed of many individually "good" services can still feel slow
most of the time. This is why production teams care about p99 and p99.9.
They capture user-visible risk that the mean hides.

A quick histogram makes the same point more concretely:

| Latency bucket | Requests out of 10,000 |
|---|---:|
| 0–5 ms | 8,700 |
| 5–10 ms | 1,100 |
| 10–50 ms | 120 |
| 50–200 ms | 70 |
| 200+ ms | 10 |

Most requests are fine. A small slow tail dominates the operational story.
That is the normal shape of production latency bugs.

![Latency distribution histogram with percentile markers showing p50 at 5ms, average at 15ms, p95 at 50ms, p99 at 200ms, and p99.9 at 500ms](figures/latency_distribution_percentiles.png)
*Figure 3.2: A typical long-tail latency distribution. The median looks healthy. The mean is already misleading. The p99 and p99.9 reveal the true user-facing risk.*

> **Key insight:** Tail latency is not "average slowness." It is usually a
> mostly healthy fast path plus a rare slow path with a large fixed cost.

## 3.2 Percentiles, Histograms, and Coordinated Omission

A percentile is a position in the sorted sample set. That sounds simple, but
it has consequences.

First, sample count matters. The p99 of 100 requests is just the single worst
request. The p99 of 10,000 requests is the worst 100 requests, which is much
more stable. As a rule of thumb for this course, do not quote a p99 from only
a few hundred samples unless you are explicit about the uncertainty.

Second, a percentile summary is not the whole distribution. A histogram or
CDF tells you whether the tail is narrow, heavy, bimodal, or drifting over
time. Those shapes often distinguish different mechanisms.

Third, many naive load generators under-report the tail because of
**coordinated omission**. The bug looks like this:

```python
while True:
    start = now()
    send_request()
    record(now() - start)
```

If one request stalls for a long time, the benchmark stops sending during the
stall. The worst period is under-sampled, so the published p99 looks better
than reality.

Practical fixes:

- send at a constant arrival rate;
- use tools such as `wrk2` or HdrHistogram-backed clients;
- record the waiting-to-send time, not just the server-side service time.

In industry, this mistake is common in RPC benchmarks, microservice load
reviews, and autoscaling evaluations. Tail numbers are only useful if the
measurement method can see the tail.

## 3.3 p99 Usually Comes from a Slow Path and a Queue

Most services have a fast path and several rare slow paths. The fast path is
computation on warm data with no blocking. The slow path waits somewhere.
That "somewhere" is usually a queue in or near the OS.

| Slow path | What waits? | First observations |
|---|---|---|
| CPU runqueue delay | runnable thread waits for core time | `vmstat r`, load average, scheduler traces |
| major page fault | thread waits for a page to be supplied | `major-faults`, `/proc/vmstat`, cgroup memory counters |
| blocking storage I/O | thread waits for device completion | `iostat`, application logs, `%wa` |
| lock contention | thread waits on another thread | `perf lock`, futex traces, app lock stats |
| retry amplification | later requests wait on earlier delays | logs, timeout counters, dependency graph |

![Request lifecycle showing time spent executing and waiting in OS queues: CPU runqueue, disk I/O queue, socket buffers, and lock wait queues](figures/os_queues_tail_latency.png)
*Figure 3.3: A request's total latency is execution time plus queue wait time. Most of the slow path is usually waiting, not processing. Each OS queue — CPU runqueue, disk I/O queue, socket buffer, lock wait queue — is a potential source of tail latency.*

The production contexts change, but the queueing logic does not. A Kubernetes
pod with CPU quota still waits on a runqueue. A database replica still waits
on storage I/O. An inference server still suffers when the working set spills
and faults. An API gateway still amplifies the tail when retries overlap.

That is why the right debugging question is often: **what rare event can add
this much waiting time to only a small fraction of requests?**

## 3.4 The USE Method as an Incident Workflow

Brendan Gregg's **USE method** is a coverage algorithm. For every resource,
check three things.

- **Utilization:** how busy is it?
- **Saturation:** is there a queue or backlog?
- **Errors:** are operations failing?

For a Linux service, the first-pass checklist often looks like this:

| Resource | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | `top`, `mpstat` | `vmstat r`, load average | throttling, involuntary context switches |
| Memory | RSS, `free -m`, cgroup usage | reclaim, swap, major faults | OOM events |
| Disk | `%util`, throughput | `await`, queue depth | device or fs errors |
| Network | bandwidth, socket counts | backlog, retransmits | resets, drops |

The strength of USE is that it prevents tunnel vision. Engineers often jump
straight to their favorite theory: "must be CPU," "must be the database,"
"must be the network." USE forces you to cover the resource surface before
narrowing.

A useful discipline in modern systems is to write down two plausible
hypotheses before diving deeper. For example:

1. memory pressure is causing major faults;
2. CPU saturation is causing runqueue delay.

Then collect evidence for one and an exclusion check for the other.

## 3.5 Evidence Chains Beat Hunches

One signal is a hypothesis. Two supporting signals plus one exclusion check is
a diagnosis you can defend.

A good evidence chain has this form:

1. **Symptom:** p99 rose from 5 ms to 180 ms at 01:47.
2. **Hypothesis:** memory pressure is forcing major faults.
3. **Signal 1:** memory usage is near the cgroup limit.
4. **Signal 2:** `pgmajfault` or per-process major faults increased sharply.
5. **Exclusion:** CPU runqueue and disk queue depth stayed near baseline.
6. **Mechanism:** faulting requests block on page supply, inflating only the
   tail.
7. **Fix:** raise limit, reduce working set, or protect hot data.
8. **Verification:** tail recovers and the mechanism-aligned signal returns
   toward baseline.

The exclusion step is where many weak write-ups fail. Without it, you do not
have a diagnosis; you have a plausible story.

A short operational example:

| Claim | Supporting signal | Independent supporting signal | Excluded alternative |
|---|---|---|---|
| memory pressure drives the tail | `memory.current` near `memory.max` | `pgmajfault` spike | CPU saturation |
| CPU runqueue drives the tail | high `vmstat r` | scheduler delay trace | storage queueing |
| network is **not** the root cause | stable retransmits | stable socket backlog | misleading timeout symptoms |

![Workflow diagram from symptom to hypotheses, two supporting signals, exclusion check, diagnosis, mitigation, and verification](figures/evidence-chain.svg)
*Figure 3.4: The target structure for an incident write-up is symptom → hypotheses → two supporting signals → one exclusion check → diagnosis → mitigation and verification. The exclusion step is what turns a plausible story into a defensible one.*

## 3.6 Worked Incident: Memory Pressure and p99 Spikes

Imagine this alert:

```text
Service: order-service
Alert:   p99 latency > 500 ms (baseline: 20 ms)
Start:   01:47
Impact:  ~1% of requests
```

That "~1%" is already a clue. The fast path still works. A rare slow path is
firing.

### Step 1: USE pass

A quick sweep shows memory is the suspicious resource.

```bash
$ free -m
              total   used   free   available
Mem:           1024    960     10          45
```

High utilization alone is not enough, so keep going.

### Step 2: Check the fault path

```bash
$ grep -E 'pgfault|pgmajfault' /proc/vmstat
pgfault    81219310
pgmajfault    34127
```

If baseline `pgmajfault` was roughly 3,000 for the same interval, this is a
strong signal that the slow path involves storage-backed page supply rather
than ordinary compute.

### Step 3: Exclude the obvious rival

```bash
$ vmstat 1 5
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0 346112  67584  18432 319488    8   12   210   120  610  980 18  3 78  1  0
```

Runqueue length is not elevated enough to make CPU saturation the primary
story. That does not prove CPU is irrelevant, but it weakens it as the root
cause.

### Step 4: State the mechanism

The causal chain is:

1. the service runs close to its memory limit;
2. the kernel reclaims pages to stay within the limit;
3. some later requests touch reclaimed pages;
4. those requests incur major faults and wait off-CPU for page supply;
5. only the unlucky requests that hit reclaimed data enter the tail.

That explains the observed shape: p50 remains acceptable while p99 spikes.

### Step 5: Mitigate and verify

A production-minded response is not just "raise the limit." It is:

- apply the least risky mitigation first, such as modestly raising
  `memory.max`;
- watch both the user-facing metric and the mechanism-aligned signal;
- confirm that p99 and `pgmajfault` move together in the expected direction.

An example before/after table makes the verification logic explicit:

| Metric | Before | After |
|---|---:|---:|
| p50 latency | 3 ms | 3 ms |
| p99 latency | 540 ms | 18 ms |
| `pgmajfault` / min | 1,200 | 25 |
| `memory.current / memory.max` | 95% | 72% |

The exact numbers will differ in real incidents. The structure should not.

## Summary

Key takeaways from this chapter:

- Tail latency is usually a rare slow path with a large waiting cost, not a
  uniform slowdown of all requests.
- Percentiles require enough samples and a measurement method that does not
  hide the worst periods through coordinated omission.
- The USE method is valuable because it enforces coverage across CPU,
  memory, storage, and network before you narrow.
- Strong incident analysis requires two supporting signals and one explicit
  exclusion check. Without the exclusion, the write-up is still vulnerable.
- The best fixes are verified with both a user-facing metric and a
  mechanism-facing metric.

## Further Reading

- Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *CACM* 56(2).
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Chapter 2.
- Gregg, B. *The USE Method.*
  <https://www.brendangregg.com/usemethod.html>
- Tene, G. *How NOT to Measure Latency.*
  <https://www.youtube.com/watch?v=lJ8ydIuPFeU>
- HdrHistogram: <https://github.com/HdrHistogram/HdrHistogram>
