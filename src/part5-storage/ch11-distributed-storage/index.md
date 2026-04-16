# Chapter 11: Distributed Storage — From KV Store to Object Store

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Place storage systems on a spectrum from in-memory caches to
>   durable object stores, and explain the tradeoffs at each point
> - State the CAP theorem and reason about when each of the three
>   properties is actually being sacrificed in production
> - Describe etcd's on-disk format: the WAL, bbolt, and how Raft
>   (Chapter 8) lands on ext4 (Chapter 10)
> - Compare Redis's RDB snapshots and AOF logging as durability
>   mechanisms, and reason about their recovery characteristics
> - Explain object-storage design: immutable objects, flat keyspaces,
>   and erasure coding for space-efficient durability

## 11.1 The Storage Spectrum

<!-- Cache (Redis, memcached) -> KV store (etcd, FoundationDB) ->
     OLTP DB (Postgres) -> OLAP / warehouse -> object store (S3).
     Axes: latency, durability, consistency, cost per GB.
     SOURCE: week10_dist/week10_slides.md opening sections -->

## 11.2 CAP in Practice

<!-- Partitions happen; "choose C or A" is really "choose what
     breaks during a partition."
     Examples: etcd (CP) vs DynamoDB (AP).
     Consistency levels: linearizable, sequential, eventual.
     SOURCE: week10_dist/week10_slides.md CAP section -->

## 11.3 etcd: WAL + bbolt

<!-- Write path: client -> Raft log (WAL on disk) -> commit ->
     apply to bbolt (B+tree KV).
     Compaction: snapshots + log truncation.
     Why etcd fsync latency dominates K8s control-plane latency.
     Connects to Chapter 8 (Raft) and Chapter 10 (fsync).
     SOURCE: week10_dist/week10_slides.md etcd section -->

## 11.4 Redis Durability: RDB and AOF

<!-- RDB: periodic snapshot via fork+COW (Chapter 4/6 connection).
     AOF: append-only log of commands, configurable fsync policy
     (always / everysec / no).
     Recovery: AOF replay vs RDB load.
     SOURCE: week10_dist/week10_slides.md Redis section -->

## 11.5 Object Storage: S3 and MinIO

<!-- Immutable objects, flat keys, HTTP API.
     Multipart upload. Eventual vs strong consistency (S3 post-2020).
     Why object stores are the substrate of modern data lakes.
     SOURCE: week10_dist/week10_slides.md object storage section -->

## 11.6 Erasure Coding

<!-- Replication wastes space (3x for 2 failures tolerated).
     Reed-Solomon (k, m): k data + m parity shards.
     Rebuild cost, repair traffic, placement policies.
     Why cold storage tiers use (10, 4) or wider codes.
     SOURCE: week10_dist/week10_slides.md EC section -->

## 11.7 Connecting the Stack

<!-- A single K8s write:
       kubectl -> API server -> etcd (Raft log -> WAL ->
       ext4 journal -> SSD FTL).
     Every layer from Chapter 8 down to Chapter 10 participates.
     This chapter is where the stack becomes visible end to end. -->

## Summary

Key takeaways from this chapter:

- Distributed storage is a set of tradeoffs (latency, durability,
  consistency, cost); no single system dominates the spectrum.
- etcd and Redis are instructive because they expose their
  durability mechanisms — you can see the WAL, AOF, and snapshots.
- Erasure coding makes durability affordable at petabyte scale,
  and is the reason cloud object storage is economically viable.

## Further Reading

- Ongaro, D. and Ousterhout, J. (2014). In search of an
  understandable consensus algorithm. *USENIX ATC '14.* (Raft.)
- DeCandia, G. et al. (2007). Dynamo: Amazon's highly available
  key-value store. *SOSP '07.*
- Calder, B. et al. (2011). Windows Azure Storage. *SOSP '11.*
- Rashmi, K. V. et al. (2014). A "hitchhiker's" guide to fast
  and efficient data reconstruction in erasure-coded data centers.
  *SIGCOMM '14.*
