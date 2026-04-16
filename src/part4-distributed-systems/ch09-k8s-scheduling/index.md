# Chapter 9: Kubernetes Scheduling and the Control Plane

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Describe the Kubernetes control plane architecture (API server,
>   etcd, controller manager, scheduler, kubelet)
> - Explain the scheduler pipeline: Filter, Score, Bind
> - Use taints, tolerations, and node affinity to influence placement
> - Compare packing vs spreading strategies and their tradeoffs
> - Connect scheduler decisions to etcd persistence (Chapter 8)

## 9.1 Why Kubernetes Is an Operating System

<!-- K8s extends the OS abstraction to a cluster.
     Pods are the unit of scheduling (like processes).
     The scheduler replaces the CPU scheduler but operates
     across nodes with richer constraints. -->

## 9.2 Control Plane Architecture

<!-- API server: the front door (REST + watch).
     etcd: durable state (Raft consensus from Chapter 8).
     Controller manager: reconciliation loops.
     Scheduler: placement decisions.
     Kubelet: node-level enforcement.
     SOURCE: week8 Kubernetes-architecture-diagram.png -->

## 9.3 The Scheduler Pipeline

<!-- 1. Filter: eliminate nodes that cannot run the pod
        (insufficient resources, taints, affinity violations).
     2. Score: rank remaining nodes by preference
        (spread, balance, affinity weights).
     3. Bind: assign pod to chosen node, write to etcd. -->

## 9.4 Scheduling Constraints

<!-- Taints and tolerations: keep pods off certain nodes.
     Node affinity: prefer or require specific node labels.
     Inter-pod affinity/anti-affinity: co-locate or separate pods.
     Topology spread constraints: distribute across zones. -->

## 9.5 Packing vs Spreading

<!-- Packing: maximize utilization, minimize cost.
     Spreading: maximize availability, minimize blast radius.
     Head-of-line blocking: when large pods block small ones.
     Backfilling: scheduling smaller pods while waiting. -->

## 9.6 From Scheduler to etcd and Back

<!-- When a pod is bound, the binding is written to etcd
     (via Raft from Chapter 8). The kubelet watches for new
     bindings and starts the pod. This closes the loop:
     consensus -> scheduling -> enforcement. -->

## Summary

Key takeaways from this chapter:

- Kubernetes is a distributed operating system that extends process
  scheduling to cluster-level pod placement.
- The scheduler pipeline (Filter -> Score -> Bind) mirrors classical
  scheduling but adds multi-resource and multi-node dimensions.
- Every scheduling decision is persisted through etcd/Raft, making
  the control plane consistent and recoverable.

## Further Reading

- Kubernetes documentation: Scheduling Framework.
- Verma, A. et al. (2015). Large-scale cluster management at Google
  with Borg. *EuroSys '15.*
- Burns, B. et al. (2016). Borg, Omega, and Kubernetes. *CACM* 59(5).
