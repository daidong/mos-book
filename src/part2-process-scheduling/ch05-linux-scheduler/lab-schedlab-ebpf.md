# Lab: SchedLab — eBPF Scheduler Tracing

> **Estimated time:** 4-5 hours
>
> **Prerequisites:** Chapter 5 concepts (CFS, eBPF, tracepoints)
>
> **Tools used:** eBPF (libbpf), perf, make, gcc

## Objectives

- Build and run an eBPF-based scheduler observation tool
- Measure scheduling latency distributions under idle and loaded
  conditions
- Analyze CFS fairness by comparing vruntime across competing tasks
- Quantify the observer effect of eBPF tracing

## Background

<!-- SOURCE: week4/schedlab/
     SchedLab attaches eBPF programs to sched_wakeup and
     sched_switch tracepoints. It records per-event timestamps
     and computes wake-to-run latency. -->

## Part A: Build and Baseline (Required)

<!-- Compile SchedLab. Run on idle system.
     Collect scheduling latency histogram.
     Report p50, p90, p99. -->

## Part B: Loaded System (Required)

<!-- Launch CPU-intensive background tasks.
     Re-measure scheduling latency.
     Compare distributions: idle vs loaded. -->

## Part C: Fairness Analysis (Required)

<!-- Run two tasks with different nice values.
     Observe their vruntime progression.
     Verify CFS allocates CPU time proportionally to weight. -->

## Part D: Observer Overhead (Optional)

<!-- Measure a workload with and without eBPF tracing.
     Quantify the overhead in microseconds per event
     and as a percentage of total runtime. -->

## Deliverables

- Latency distributions (histogram or percentile table) for idle
  and loaded conditions
- Fairness analysis showing vruntime progression for two tasks
- Brief discussion of observer effect (qualitative is sufficient
  for Part C; quantitative for Part D)
