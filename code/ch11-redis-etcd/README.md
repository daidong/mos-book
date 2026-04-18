# code/ch11-redis-etcd

The Chapter 11 lab (*Redis and etcd Benchmarks*) exercises stock
tools: `redis-benchmark`, `redis-cli`, `etcdctl`, the etcd
`benchmark` tool, and — optionally — `mc` for MinIO. Helper
scripts automate instance setup.

## Layout

```
code/ch11-redis-etcd/
├── README.md
└── scripts/
    ├── redis-lab-up.sh     # launch three Redis instances (no/everysec/always)
    └── redis-lab-down.sh   # tear down Redis containers
```

## Quick start

```bash
bash scripts/redis-lab-up.sh ~/lab11/redis   # ports 6379/6380/6381
# ... run lab exercises ...
bash scripts/redis-lab-down.sh               # cleanup
```

See `src/part5-storage/ch11-distributed-storage/lab-redis-etcd-bench.md`
for the full lab procedure.
