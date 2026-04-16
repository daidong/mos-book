# Chapter 7: Kubernetes as a Resource Manager

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Distinguish between Kubernetes requests (used for scheduling) and
>   limits (used for enforcement via cgroups)
> - Explain the three QoS classes (Guaranteed, Burstable, BestEffort)
>   and their eviction priority
> - Diagnose CPU throttling using CFS bandwidth control and
>   `nr_throttled` counters
> - Explain memory OOM behavior and kubelet eviction signals

## 7.1 From Cgroups to Kubernetes

<!-- K8s pods are cgroups with declarative specs.
     requests and limits in a pod spec become cgroup settings.
     The scheduler uses requests; the kubelet enforces limits. -->

## 7.2 Requests, Limits, and QoS Classes

<!-- Guaranteed: requests == limits for all containers.
     Burstable: at least one request set, but limits differ.
     BestEffort: no requests or limits.
     Eviction order: BestEffort first. -->

## 7.3 CPU Throttling

<!-- CFS bandwidth control: cpu.max = quota period.
     When a pod exhausts its quota, it is throttled.
     nr_throttled in cpu.stat.
     Effect on latency: requests queue during throttle window. -->

## 7.4 Memory Limits and OOM

<!-- memory.max in cgroup v2.
     When exceeded: kernel reclaims pages or kills processes.
     OOMKilled in pod status.
     Difference between cgroup OOM and node-level eviction. -->

## 7.5 Kubelet Eviction

<!-- Node-level signals: memory.available, nodefs.available.
     Soft vs hard eviction thresholds.
     Pod eviction order based on QoS class and usage. -->

## 7.6 Scheduler Pipeline

<!-- Filter: which nodes can run this pod?
     Score: which node is best?
     Bind: assign pod to node, write to etcd.
     Taints and tolerations. -->

## Summary

Key takeaways from this chapter:

- Kubernetes translates declarative pod specs into cgroup enforcement
  on each node.
- CPU throttling and memory OOM are cgroup mechanisms — understanding
  Chapter 6 makes Kubernetes behavior predictable.
- QoS classes determine eviction priority; Guaranteed pods survive
  longest under memory pressure.

## Further Reading

- Kubernetes documentation: Managing Resources for Containers.
- Kubernetes documentation: Configure Quality of Service for Pods.
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Chapter 11:
  Cloud Computing.
