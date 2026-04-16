# Lab: Quicksort Performance Analysis

> **Estimated time:** 3-4 hours
>
> **Prerequisites:** Chapter 2 concepts, working Ubuntu VM with perf
>
> **Tools used:** perf stat, valgrind (cachegrind), gcc, make

## Objectives

- Measure how input pattern (random, sorted, reverse, nearly-sorted)
  affects quicksort performance
- Use `perf stat` to observe IPC, cache-miss rates, and branch-miss
  rates across different inputs
- Connect observed performance differences to memory hierarchy and
  branch prediction mechanisms
- Practice designing and reporting a multi-variable experiment

## Background

<!-- SOURCE: week2A/lab1_instructions.md
     Quicksort's performance depends on pivot selection and input
     pattern. Different patterns stress different hardware mechanisms:
     cache behavior, branch prediction, memory access patterns. -->

## Part A: Baseline Measurements (Required)

<!-- Run quicksort binary with different input patterns and sizes.
     Record wall-clock time with `time`.
     Plot time vs N for each pattern. -->

## Part B: Hardware Counter Analysis (Required)

<!-- Use perf stat (or valgrind --tool=cachegrind in VM) to measure
     cache-misses and branch-misses for each input pattern.
     Build a table: pattern x metric.
     Explain why patterns differ. -->

## Part C: Deep Dive (Optional)

<!-- Investigate a specific anomaly from Part B.
     Example: why does nearly-sorted have different cache behavior
     than random? Use cachegrind to get per-function breakdowns. -->

## Deliverables

- Timing plot: wall-clock time vs input size for all four patterns
- Hardware counter table: IPC, cache-miss rate, branch-miss rate per
  pattern (at a fixed large N)
- Written explanation (1-2 paragraphs per pattern) connecting the
  numbers to the mechanism
