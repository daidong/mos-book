# code/ch08-etcd-raft

The Chapter 8 lab (*Observing Raft in etcd*) is instruction-driven
and uses stock `etcd` and `etcdctl` from upstream releases rather
than custom code. No source files ship with the book.

See the lab writeup at
`src/part4-distributed-systems/ch08-consensus-raft/lab-etcd-raft.md`
for the full procedure. In summary, you will:

1. Install `etcd` ≥ 3.5 and `etcdctl` (see Appendix C).
2. Start a single-node and then a 3-node etcd cluster.
3. Use `etcdctl endpoint status`, `endpoint health`, and `member list`
   to observe the Raft role (leader / follower) of each node.
4. Inject a leader failure and watch re-election in the logs.
5. Measure write latency under steady state and during an election.

All data and log outputs from the lab should be placed in a
subdirectory under the student's working copy, not committed back
into this repository.
