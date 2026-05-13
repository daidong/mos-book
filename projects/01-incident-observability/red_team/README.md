# Project 01 — Red Team Scaffold

This folder is **optional scaffolding**: it gives you templates and starter scripts for building reproducible incident scenarios.

You are expected to create **3 scenarios** and exchange them with a
Blue team.

## Required scenario coverage (3 buckets)

Your 3 scenarios must collectively cover:

1) **Scheduling / concurrency** (book Chapters 4–5)
   - examples: runqueue delay, noisy neighbor on the same CPU, lock
     convoying, timer wakeup delays
2) **cgroup v2 resource boundary** (book Chapters 6–7)
   - examples: CPU quota throttling (`cpu.max`), memory limit
     (`memory.max`) → reclaim or OOM
3) **Storage / writeback tail latency** (book Chapter 10)
   - examples: background `fsync` writer, writeback bursts, IO
     saturation

## Scenario structure (recommended)

Each scenario folder should include:

- `SCENARIO.md`: symptom spec + how to reproduce
- `GROUND_TRUTH.md`: mechanism-level explanation (what actually happens)
- `EVIDENCE_CONTRACT.md`: 
  - **2 independent supporting signals** (VM-friendly)
  - **1 negative control / exclusion** (what you checked to rule out an alternative)
- `INJECT.sh`: start the fault/interference
- `CLEANUP.sh`: return system to baseline

## Templates

See:
- `scenarios/01-scheduler/`
- `scenarios/02-cgroup/`
- `scenarios/03-io/`

Copy them and adapt to your chosen workload.
