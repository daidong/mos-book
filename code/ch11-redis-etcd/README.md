# code/ch11-redis-etcd

The Chapter 11 lab (*Redis and etcd Benchmarks*) is driven by
stock tools: `redis-benchmark`, `redis-cli`, `etcdctl`, the `etcd`
`benchmark` tool, and — optionally — `mc` for MinIO. No custom
lab source is shipped.

See `src/part5-storage/ch11-distributed-storage/lab-redis-etcd-bench.md`
for the full procedure and deliverables.

## Suggested Layout for Your Runs

```
runs/
├── redis-aof-no/
├── redis-aof-everysec/
├── redis-aof-always/
├── redis-bgsave/
└── etcd-compaction/
```

Keep the `redis.conf` and `etcd` flags you used with each run,
and store the raw `redis-benchmark` / `etcdctl benchmark` stdout
in the run directory. This is a reproducibility requirement
(Chapter 13): every number in the report must be traceable to
a captured invocation.
