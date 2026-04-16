# Lab: Scheduling Latency Under CPU Contention

> **Estimated time:** 3-4 hours
>
> **Prerequisites:** Chapter 4 concepts (processes, scheduling, preemption)
>
> **Tools used:** perf stat, taskset, nice, cgroups (optional)

## Objectives

- Measure baseline wakeup latency on an idle system
- Observe how CPU contention inflates p99 scheduling latency
- Collect supporting OS signals (context switches, /proc/schedstat)
- Apply a mitigation (nice, CPU affinity, or cgroup CPU control) and
  verify its effect

## Background

<!-- SOURCE: week3/lab3_instructions.md, lab3_sched_latency/
     Uses wakeup_lat probe to measure wake-to-run delay.
     cpu_hog generates contention on the same CPU core.
     Students compare baseline vs contended distributions. -->

## Part A: Baseline Measurement (Required)

<!-- Run wakeup_lat alone on a quiet system.
     Collect N >= 10000 samples.
     Report p50, p90, p99. -->

## Part B: Add CPU Contention (Required)

<!-- Pin cpu_hog to same CPU as wakeup_lat using taskset.
     Re-measure. Observe p99 inflation.
     Explain why: runqueue delay from competing task. -->

## Part C: Supporting Evidence (Required)

<!-- Collect context-switch count (perf stat -e context-switches)
     or read /proc/<pid>/sched for nr_involuntary_switches.
     Show that the mechanism (scheduling delay) matches the
     symptom (p99 inflation). -->

## Part D: Mitigation (Required)

<!-- Apply one of:
     - nice: lower priority of cpu_hog
     - taskset: move probe to a different CPU
     - cgroup cpu.max: throttle cpu_hog
     Re-measure and show improvement. -->

## Deliverables

- Table: p50, p90, p99 for baseline, contended, and mitigated
- Supporting evidence (context-switch counts or schedstat)
- Written explanation connecting the measurements to the scheduling
  mechanism
