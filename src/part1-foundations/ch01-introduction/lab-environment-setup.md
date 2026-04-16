# Lab: Environment Setup

> **Estimated time:** 2-3 hours
>
> **Prerequisites:** VirtualBox installed, Ubuntu 22.04 or 24.04 ISO
>
> **Tools used:** VirtualBox, apt, perf, strace, gcc

## Objectives

- Set up an Ubuntu VM suitable for all labs in this book
- Install and verify core observability tools (perf, strace, bpftrace)
- Run a first `perf stat` measurement and interpret the output
- Establish habits for reproducible experiments

## Background

All labs in this book run inside an Ubuntu VM on VirtualBox. This
ensures a consistent, reproducible environment regardless of your host
OS. We avoid WSL and Docker because they restrict access to kernel
tracing interfaces that later labs require.

<!-- SOURCE: week0/env_setup.md, week1/lab0_instructions.md -->

## Part A: VM Installation and Tool Setup (Required)

<!-- Step-by-step: VirtualBox VM creation, Ubuntu install,
     tool installation (build-essential, linux-tools, strace, bpftrace),
     env_check.sh verification -->

## Part B: First Measurement with perf stat (Required)

<!-- Run perf stat on a simple program.
     Record: instructions, cycles, IPC, cache-misses.
     Interpret what the numbers mean. -->

## Part C: Context Switch Observation (Optional)

<!-- Use perf stat to measure context switches.
     Run a CPU-bound program, observe voluntary vs involuntary
     context switches. -->

## Deliverables

- Screenshot or text output of `env_check.sh` passing
- Output of your first `perf stat` run with a brief interpretation
  (2-3 sentences explaining what the counters tell you)
