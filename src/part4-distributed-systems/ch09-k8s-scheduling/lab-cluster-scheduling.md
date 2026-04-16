# Lab: Cluster Scheduling Simulation and Observation

> **Estimated time:** 4-5 hours
>
> **Prerequisites:** Chapter 9 concepts, kind and kubectl installed
>
> **Tools used:** Python, kind, kubectl, etcdctl

## Objectives

- Implement FIFO and Backfill scheduling algorithms in a Python
  simulator and compare their performance
- Observe real Kubernetes scheduler behavior in a kind cluster
- Trigger and diagnose Pending pod states
- Connect scheduler decisions to etcd state from Chapter 8

## Background

<!-- SOURCE: week8/lab8_scheduling_instructions.md
     Two-part lab: Part A uses a simulator to understand scheduling
     algorithms. Parts C-D use a real kind cluster to observe
     Kubernetes scheduling. -->

## Part A: Scheduling Simulator (Required)

<!-- Implement FIFO and Backfill schedulers in Python.
     Given a workload (job arrival times, resource needs, durations),
     compute: makespan, average completion time, average wait time,
     utilization. Compare the two algorithms. -->

## Part B: Workload Analysis (Required)

<!-- Vary workload characteristics (job sizes, arrival rates).
     Identify when Backfill significantly outperforms FIFO.
     Explain in terms of head-of-line blocking. -->

## Part C: Real K8s Scheduling Observation (Required)

<!-- Create a kind cluster with limited node resources.
     Deploy pods that exceed node capacity -> observe Pending.
     Use kubectl describe to see FailedScheduling events.
     Use node affinity to observe scoring behavior. -->

## Part D: etcd Connection (Optional)

<!-- Use etcdctl to inspect the pod binding in etcd.
     Show that scheduler decisions are persisted via Raft.
     Verify consistency between kubectl get and etcd state. -->

## Deliverables

- Simulator output: comparison table (makespan, wait time, utilization)
  for FIFO vs Backfill across at least two workloads
- Real cluster observations: FailedScheduling events, node affinity
  scoring, Pending -> Running transitions
- Written analysis connecting simulator insights to real K8s behavior
