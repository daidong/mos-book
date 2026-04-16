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

## 3.1 Why the Mean Lies

<!-- Average hides outliers. In fan-out architectures, the slowest
     component determines end-to-end latency.
     p50 vs p90 vs p99 vs p99.9 — what each tells you. -->

## 3.2 Percentile Statistics

<!-- How to compute percentiles. Sample size requirements.
     Why 100 samples is not enough for p99.
     Histograms vs summary statistics. -->

## 3.3 Common Causes of Tail Latency

<!-- Memory pressure and major page faults.
     CPU runqueue delay (scheduling latency).
     I/O contention and writeback bursts.
     GC pauses, lock contention. -->

## 3.4 The USE Method

<!-- Brendan Gregg's Utilization / Saturation / Errors framework.
     Systematic checklist: for each resource (CPU, memory, disk,
     network), check U, S, and E.
     SOURCE: week2B use_checklist.md -->

## 3.5 Building Evidence Chains

<!-- A diagnosis requires multiple independent signals.
     Example: p99 spike -> check memory pressure (vmstat) ->
     check page faults (perf stat) -> check I/O wait (iostat).
     Two signals that agree = credible. One signal alone = hypothesis. -->

## 3.6 Case Study: Memory Pressure and p99 Spikes

<!-- Walk through a concrete example: memory pressure causes
     major page faults, which inflate p99 latency.
     Show the evidence chain step by step. -->

## Summary

Key takeaways from this chapter:

- Tail latency is the metric that matters in distributed and
  user-facing systems.
- The USE method provides a systematic framework that prevents
  guessing and ensures coverage.
- A credible diagnosis requires at least two independent signals
  pointing to the same root cause, plus one exclusion check ruling
  out an alternative.

## Further Reading

- Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *CACM* 56(2).
- Gregg, B. (2013). *The USE Method.* https://www.brendangregg.com/usemethod.html
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Chapter 2: Methodology.
