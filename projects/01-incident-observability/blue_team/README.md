# Project 01 — Blue Team Scaffold

This folder is **optional scaffolding** for building a diagnosis
workbench that can solve unknown incidents.

The standard for a complete diagnosis:

- Each scenario solved with **two independent signals + one negative
  control**.
- Each mitigation includes **before/after p50 / p95 / p99** and **a
  mechanism-level metric** that moved in the expected direction.

## Recommended workflow

1) **Reproduce**
- Run the workload baseline
- Trigger scenario injection

2) **Collect signals (VM-friendly first)**
- PSI: `/proc/pressure/*`
- `/proc/vmstat`, `/proc/schedstat` (if available)
- cgroup v2 stats: `cpu.stat`, `memory.current`, `memory.stat`, `io.stat`
- `pidstat`, `vmstat`, `iostat`, `ss`, `top -H`

3) **Build an evidence chain**
- symptom → suspect resource (CPU/mem/IO/network/locks/queues)
- resource → mechanism (throttling/reclaim/writeback/runqueue delay/lock convoy)
- **negative control**: at least one explicit exclusion ("not network", "not IO", "not GC", etc.) with evidence

## Scaffolded scripts

- `collect/collect_basic.sh`: collect PSI + vmstat/iostat/pidstat snapshots
- `analyze/latency_percentiles.py`: compute p50/p95/p99 from a CSV column and generate a histogram

These are templates; you should adapt them to your workload and logging format.
