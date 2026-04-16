# Chapter 2: Performance Measurement Methodology

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Describe the memory hierarchy (registers, L1/L2/L3, DRAM, disk)
>   and its impact on program performance
> - Explain how CPU caches, TLBs, and branch prediction affect
>   instruction throughput
> - Use `perf stat` to measure IPC, cache-miss rates, and
>   branch-miss rates
> - Design a controlled experiment that isolates a single variable
>   and produces reproducible results

## 2.1 The Memory Hierarchy

<!-- SOURCE: week2A slides — memory_hierarchy.png, cache_line_fetch.png
     Cover: registers, L1/L2/L3 cache, DRAM, disk.
     Latency numbers everyone should know.
     Working set concept. -->

## 2.2 CPU Caches and Cache Lines

<!-- Cache line fetch, spatial locality, temporal locality.
     Why row-major traversal is faster than column-major.
     SOURCE: row_major_memory_layout.png -->

## 2.3 Virtual Memory and the TLB

<!-- Page tables, TLB as a cache for translations.
     TLB misses as a hidden performance cost.
     SOURCE: virtual_memory_translation.png, tlb.png -->

## 2.4 Branch Prediction and Pipelines

<!-- CPU pipelines, branch prediction, misprediction penalty.
     Why sorted data can be faster to process.
     SOURCE: pipeline.png, pipeline-branch.png -->

## 2.5 The First Observability Loop

<!-- time command -> perf stat -> IPC, cache-misses, branch-misses.
     How to read perf stat output.
     Distinguishing CPU-bound vs memory-latency-bound. -->

## 2.6 Designing Controlled Experiments

<!-- One variable at a time. Baseline vs treatment.
     Warm-up runs. Multiple trials. Reporting variance.
     VM considerations: hardware counters may require fallback
     to Valgrind (cachegrind/callgrind). -->

## Summary

Key takeaways from this chapter:

- Performance is shaped by the memory hierarchy — cache misses and TLB
  misses dominate in memory-intensive workloads.
- `perf stat` is the foundational tool for connecting observed
  performance to hardware mechanisms.
- A controlled experiment requires: a clear hypothesis, a single
  variable, a stable baseline, and multiple trials.

## Further Reading

- Gregg, B. (2020). *Systems Performance*, 2nd ed. Chapter 6: CPUs.
- Drepper, U. (2007). *What Every Programmer Should Know About Memory.*
- Arpaci-Dusseau & Arpaci-Dusseau (2018). *OSTEP*, Chapters 18-23
  (Virtual Memory).
