# Chapter 5: Linux Scheduler Internals and Observability

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain how CFS (Completely Fair Scheduler) works: vruntime,
>   red-black tree, time slices, and task selection
> - Describe the difference between tracepoints and kprobes for
>   kernel observability
> - Use eBPF to attach to scheduler tracepoints and measure
>   scheduling latency distributions
> - Analyze the observer effect and measurement overhead

## 5.1 CFS: The Completely Fair Scheduler

<!-- vruntime as the key abstraction.
     Red-black tree: leftmost node has smallest vruntime.
     Time slice proportional to weight (nice value).
     How fairness emerges from vruntime accounting. -->

## 5.2 Scheduler Data Structures

<!-- struct sched_entity, struct rq, struct cfs_rq.
     Per-CPU runqueues. Load balancing across CPUs (brief). -->

## 5.3 Tracing the Scheduler with eBPF

<!-- What is eBPF: safe, in-kernel programs attached to events.
     Tracepoints vs kprobes: stability vs flexibility.
     Key scheduler tracepoints: sched_wakeup, sched_switch,
     sched_migrate_task. -->

## 5.4 Measuring Scheduling Latency

<!-- Attach to sched_wakeup (record timestamp) and sched_switch
     (compute delta). This gives precise wake-to-run latency.
     Distribution analysis: histogram, percentiles. -->

## 5.5 Observer Effect and Measurement Overhead

<!-- Every measurement perturbs the system.
     eBPF overhead: typically < 1 microsecond per event.
     How to quantify overhead: measure with and without tracing.
     When overhead matters and when it doesn't. -->

## Summary

Key takeaways from this chapter:

- CFS achieves fairness through virtual runtime accounting — the task
  with the smallest vruntime always runs next.
- eBPF provides a safe, low-overhead way to observe kernel scheduling
  behavior in production systems.
- Understanding observer effect is essential for credible measurement.

## Further Reading

- Molnar, I. (2007). CFS Scheduler Design.
  https://www.kernel.org/doc/Documentation/scheduler/sched-design-CFS.rst
- Gregg, B. (2019). *BPF Performance Tools.* Addison-Wesley.
  Chapters 1-3, Chapter 6: CPUs.
