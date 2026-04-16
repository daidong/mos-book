# Lab: fsync Latency Measurement

> **Estimated time:** 4-6 hours
>
> **Prerequisites:** Chapter 10 concepts, a Linux VM with ext4 and
> root access (for dropping caches and installing tools)
>
> **Tools used:** `dd`, `filefrag`, `debugfs`, `/proc/meminfo`, `iostat`,
> `fio`, `write_latency.c` (provided in `code/ch10-fsync-bench/`)

## Objectives

- Inspect how a file is physically laid out on disk using `filefrag`
  and `debugfs`
- Observe the page cache in action: hit vs miss, dirty pages, writeback
- Measure write latency distributions with and without `fsync`
- Quantify the interference caused by a concurrent writer

## Background

<!-- SOURCE: week9_fs/lab9_instructions.md
     Four-part lab progressing from passive inspection to active
     measurement. Emphasizes the evidence contract from Chapter 3:
     every claim needs 2 signals + 1 exclusion. -->

## Part A: File Layout Inspection (Required)

<!-- Create files of various sizes, use filefrag -v to see extents,
     use debugfs -R "stat <inode>" to read inode metadata.
     Question: how does ext4 allocate blocks for a 1 GB file?
     Compare with a file written in many small appends. -->

## Part B: Page Cache Observation (Required)

<!-- Read a file twice: cold vs warm.
     Watch /proc/meminfo Cached and Dirty.
     Use `echo 3 > /proc/sys/vm/drop_caches` to reset.
     Measure the difference using time and iostat.
     SOURCE: week9_fs/lab9_instructions.md Part B -->

## Part C: Write Latency Measurement (Required)

<!-- Compile and run write_latency.c (from code/ch10-fsync-bench/).
     Measure per-write latency under four modes:
       1. buffered write, no fsync
       2. buffered write + fsync per write
       3. buffered write + fdatasync per write
       4. O_DIRECT write
     Produce a p50/p99/p99.9 table and a CDF plot. -->

## Part D: Interference Experiments (Optional, Advanced)

<!-- Run a background `dd` writer while measuring fsync latency
     on a foreground process. Quantify the tail-latency impact.
     Repeat under different I/O schedulers (mq-deadline, bfq, none).
     Connects to the tail-latency methodology from Chapter 3. -->

## Deliverables

- A layout report with filefrag and debugfs output for at least two
  files, with a short explanation of the allocator's behavior.
- A page cache demonstration: before/after `drop_caches`, with
  `/proc/meminfo` snapshots and timing evidence.
- A latency table and CDF comparing the four write modes from Part C.
- (Optional) Interference plots showing p99 fsync latency as a
  function of background writer throughput.

## Evidence Contract Reminder

For every performance claim in your report, provide two independent
signals (e.g., application-level timing + `iostat` device stats) and
one exclusion check (e.g., confirming the page cache was cold or
that `fsync` actually reached the device).
