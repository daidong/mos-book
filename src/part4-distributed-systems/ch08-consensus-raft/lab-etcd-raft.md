# Lab: Observing Raft in etcd

> **Estimated time:** 4-5 hours
>
> **Prerequisites:** Chapter 8 concepts (Raft, etcd architecture)
>
> **Tools used:** etcd, etcdctl, curl, bash

## Objectives

- Build and operate a 3-node etcd cluster
- Observe leader election, term progression, and log indices
- Measure the latency cost of consensus (single-node vs 3-node)
- Simulate failures (leader crash, network partition) and observe
  recovery

## Background

<!-- SOURCE: week7/lab7_raft_instructions.md
     Students run a local 3-node etcd cluster and use etcdctl
     to inspect cluster state, trigger elections, and measure
     write/read latency. -->

## Part A: Cluster Setup and State Inspection (Required)

<!-- Start 3-node cluster. Use etcdctl endpoint status to inspect
     term, leader, raft index. Put/get a key and observe index
     progression. -->

## Part B: Leader Failure and Re-election (Required)

<!-- Kill the leader node. Observe: new election, term increment,
     new leader selected. Measure time to re-election.
     Note: randomized timeout prevents split votes. -->

## Part C: Consensus Latency (Required)

<!-- Benchmark write latency: 1-node vs 3-node.
     Benchmark read latency: linearizable vs serializable.
     Explain the difference in terms of quorum round-trips. -->

## Part D: Writes During Leader Failure (Required)

<!-- Run sustained writes. Kill leader mid-stream.
     Observe: writes fail during election, resume after.
     Count lost writes. -->

## Part E: Network Partition (Optional)

<!-- Simulate partition: isolate one node.
     Show that the 2-node majority continues serving.
     Show that the isolated node cannot commit writes.
     Heal partition, observe catch-up. -->

## Part F: Follower Lag and Catch-up (Optional)

<!-- Stop a follower. Write many keys. Restart follower.
     Observe snapshot transfer or incremental catch-up. -->

## Deliverables

- Cluster state table (term, leader, raft index) before and after
  each experiment
- Latency comparison: single-node vs 3-node writes
- Re-election timeline with measurements
- Written explanation of each observation in terms of Raft protocol
