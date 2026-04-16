# Evidence contract (MS baseline)

## Supporting signal #1 (required)
- cgroup v2 stats:
  - CPU: `cpu.stat` (throttled_usec / nr_throttled)
  - Memory: `memory.current`, `memory.stat`, `cgroup.events` (oom_kill)

## Supporting signal #2 (required)
- PSI: `/proc/pressure/cpu` or `/proc/pressure/memory`
- `pidstat` (context switches, %CPU) or `vmstat` (faults)

## Negative control / exclusion (required)
- show IO is stable if the mechanism is CPU/memory
- or show CPU is stable if the mechanism is IO

## Required before/after
- p50/p95/p99 and throughput/error rate
- the cgroup metric must move in the expected direction
