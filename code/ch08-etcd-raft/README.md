# code/ch08-etcd-raft

The Chapter 8 lab (*Observing Raft in etcd*) runs stock etcd and
etcdctl from upstream Docker images — no custom source code is
needed.

## Layout

```
code/ch08-etcd-raft/
├── README.md
└── scripts/
    ├── cluster-up.sh     # start a 3-node etcd cluster in Docker
    └── cluster-down.sh   # tear down all lab containers
```

## Quick start

```bash
export ETCD_IMAGE=quay.io/coreos/etcd:v3.5.17
docker pull $ETCD_IMAGE

bash scripts/cluster-up.sh     # creates etcd1, etcd2, etcd3
# ... run lab exercises ...
bash scripts/cluster-down.sh   # cleanup
```

See `src/part4-distributed-systems/ch08-consensus-raft/lab-etcd-raft.md`
for the full lab procedure.
