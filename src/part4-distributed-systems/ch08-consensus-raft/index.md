# Chapter 8: Distributed Consensus — Paxos, Raft, and etcd

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why consensus is necessary for replicated state machines
> - Describe Paxos safety guarantees (quorum overlap, proposal ordering)
> - Walk through Raft's leader election, log replication, and commit
>   protocol
> - Trace a write through etcd's Raft implementation (WAL, follower
>   replication, majority ack, commit)
> - Explain the latency cost of strong consistency

## 8.1 The Consensus Problem

<!-- Multiple nodes must agree on a sequence of values despite
     crashes and message loss. Without consensus, distributed
     state diverges. -->

## 8.2 Atomic Commit vs Consensus

<!-- 2PC solves single-transaction agreement (all-or-nothing).
     Consensus solves replicated log agreement (total order).
     Different problems, different protocols. -->

## 8.3 Paxos

<!-- Proposers, acceptors, learners.
     Quorum overlap guarantees safety.
     Proposal numbers enforce ordering.
     Why Paxos is correct but hard to implement. -->

## 8.4 Raft: Consensus Made Teachable

<!-- Terms and randomized election timeouts.
     Leader election: RequestVote, majority wins.
     Log replication: AppendEntries, majority ack = committed.
     Safety: only candidates with up-to-date logs can win. -->

## 8.5 etcd: Raft in Production

<!-- etcd as Kubernetes' brain.
     Write path: leader append -> WAL fsync -> follower replicate
     -> majority ack -> commit -> apply to bbolt.
     Read path: linearizable (leader read) vs serializable.
     Snapshot and compaction. Watch mechanism. -->

## 8.6 The Cost of Strong Consistency

<!-- Every write requires a quorum round-trip.
     fsync on WAL adds local latency.
     Network latency between nodes adds remote latency.
     Why 3-node writes are slower than single-node. -->

## Summary

Key takeaways from this chapter:

- Consensus (Raft/Paxos) provides the foundation for reliable
  distributed coordination — without it, Kubernetes cannot function.
- Strong consistency has a measurable latency cost: quorum
  round-trips plus fsync.
- etcd makes these tradeoffs concrete and observable.

## Further Reading

- Ongaro, D. & Ousterhout, J. (2014). In Search of an Understandable
  Consensus Algorithm (Raft). *USENIX ATC '14.*
- Lamport, L. (2001). Paxos Made Simple.
- etcd documentation: https://etcd.io/docs/
