# code/ch10-fsync-bench

Benchmark harness for the Chapter 10 fsync-latency lab.

See `src/part5-storage/ch10-filesystems/lab-fsync-latency.md`.

## Contents

- `write_latency.c` — per-write latency recorder (four modes).
- `Makefile` — builds `write_latency`.
- `scripts/percentiles.py` — summarizes stdout into p50/p99/p99.9.

## Quick start

```
make
./write_latency /tmp/wl.dat 1 10000 | scripts/percentiles.py
```

Modes: `0`=buffered, `1`=fsync-per-write, `2`=fdatasync-per-write,
`3`=O_DIRECT. Expect to see `1` an order of magnitude slower than
`0` on a typical SSD, with `1` and `2` converging as file
metadata stabilizes.
