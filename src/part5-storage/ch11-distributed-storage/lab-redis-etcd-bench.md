# Lab: Redis and etcd Benchmarks

> **Estimated time:** 5-6 hours
>
> **Prerequisites:** Chapters 8, 10, 11; Docker or a Linux VM with
> Redis, etcd, and optionally MinIO installed
>
> **Tools used:** `redis-benchmark`, `redis-cli`, `etcdctl`,
> `benchmark` (etcd tool), `iostat`, `perf`, `pidstat`

## Objectives

- Measure how Redis's AOF `fsync` policy changes both throughput
  and p99 latency, and connect the result to Chapter 10's
  `fsync` behavior
- Observe Redis `BGSAVE` and confirm copy-on-write memory accounting
  using `/proc/[pid]/smaps` and `pidstat`
- Benchmark etcd write throughput and observe what happens when
  the log grows large and compaction kicks in
- (Optional) Compare small-object write latency on MinIO against
  Redis/etcd to see where object storage sits on the spectrum

## Background

<!-- SOURCE: week10_dist/lab10_instructions.md
     Four-part lab that exercises the layered durability stack
     from Chapter 8 (consensus) -> Chapter 10 (fsync) on real
     production-grade storage systems. -->

## Part A: Redis AOF fsync Benchmark (Required)

<!-- Run redis-benchmark under three AOF configurations:
       appendfsync no  / everysec / always
     Record throughput (ops/s) and p50/p99/p99.9 latency.
     Cross-check with `iostat -x 1` to confirm device-level writes.
     Expected: "always" trades ~10x throughput for stronger durability.
     SOURCE: week10_dist/lab10_instructions.md Part A -->

## Part B: Redis BGSAVE and COW Observation (Required)

<!-- Load ~1 GB of data into Redis. Trigger BGSAVE.
     Observe: fork() latency, child process memory, parent RSS.
     Use /proc/[pid]/smaps Private_Dirty vs Shared_Clean to see
     how COW diverges as the parent writes during the snapshot.
     Connects to fork/COW material from Chapter 4.
     SOURCE: week10_dist/lab10_instructions.md Part B -->

## Part C: etcd Write Throughput + Compaction (Required)

<!-- Run the etcd `benchmark put` tool against a single-node etcd.
     Watch WAL file growth on disk (`ls -l member/wal/`).
     Trigger `etcdctl compaction` and `etcdctl defrag`;
     observe DB size before and after.
     Measure write p99 during an ongoing compaction (interference).
     SOURCE: week10_dist/lab10_instructions.md Part C -->

## Part D: MinIO Comparison (Optional)

<!-- Run MinIO in single-node mode. Use `mc` or `s3cmd` to PUT
     many small objects and measure latency.
     Compare with Redis SET and etcd PUT at the same payload size.
     Discussion: why each system is (or isn't) suitable for that
     workload. -->

## Deliverables

- A three-row table (AOF no / everysec / always) showing throughput
  and p50/p99/p99.9, plus at least one `iostat` snapshot per row.
- A BGSAVE report including fork time, peak child memory, and a
  plot or table of Private_Dirty growth over time.
- etcd results: write p99 during steady state vs during compaction,
  with WAL and DB size evidence before and after.
- (Optional) A comparison table across Redis / etcd / MinIO for
  equivalent payload sizes, with a short discussion of the
  spectrum from Chapter 11.

## Evidence Contract Reminder

Every throughput or latency claim needs two signals (e.g.,
client-side timing + server-side metric or device-level `iostat`)
and one exclusion check (e.g., CPU was not saturated, or network
was not the bottleneck).
