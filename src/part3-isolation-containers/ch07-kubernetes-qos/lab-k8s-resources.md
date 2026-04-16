# Lab: K8s CPU Throttling and OOM

> **Estimated time:** 3-4 hours
>
> **Prerequisites:** Chapter 7 concepts, kind installed in VM
>
> **Tools used:** kind, kubectl, crictl, cgroup v2 filesystem

## Objectives

- Deploy pods with different QoS classes on a local kind cluster
- Reproduce and observe CPU throttling via CFS bandwidth control
- Reproduce and observe memory OOM behavior
- Correlate pod-level symptoms with cgroup-level evidence

## Background

<!-- SOURCE: week6/week6_final_slides.md, week7 K8s manifests
     Students use kind (Kubernetes-in-Docker) to create a local
     cluster and observe resource control mechanisms. -->

## Part A: QoS Class Comparison (Required)

<!-- Deploy three pods: Guaranteed, Burstable, BestEffort.
     Inspect their cgroup settings via crictl or
     /sys/fs/cgroup on the kind node.
     Verify that requests/limits map to cpu.max and memory.max. -->

## Part B: CPU Throttling (Required)

<!-- Deploy a CPU-intensive pod with low CPU limits.
     Observe throttling: kubectl top, cpu.stat nr_throttled.
     Measure request latency before and after throttling. -->

## Part C: Memory OOM (Required)

<!-- Deploy a memory-hungry pod with tight memory limits.
     Observe: OOMKilled status, pod restarts.
     Check dmesg/journalctl for OOM messages. -->

## Part D: Eviction Under Pressure (Optional)

<!-- Simulate node memory pressure.
     Observe kubelet eviction order based on QoS class.
     Verify BestEffort pods are evicted first. -->

## Deliverables

- Table mapping pod specs to cgroup settings for each QoS class
- Evidence of CPU throttling: nr_throttled counts, latency impact
- Evidence of OOM: pod status, kernel messages, restart count
- Written explanation connecting K8s symptoms to cgroup mechanisms
