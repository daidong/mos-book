# Evidence contract

## Supporting signal #1 (required)
Example options:
- increased `pidstat -w` context switches for victim PID
- higher `/proc/schedstat` runnable delays (if available)
- eBPF tracepoint: wakeup→run latency distribution (book Chapter 5)

## Supporting signal #2 (required)
Example options:
- PSI CPU pressure: `/proc/pressure/cpu`
- runqueue length / load average correlation with p99
- cgroup `cpu.stat` (if you run victims in cgroups)

## Negative control / exclusion (required)
Example options:
- show `iostat` is stable → not IO
- show `ss` / network retransmits stable → not network
- show RSS/faults stable → not memory reclaim

## Expected before/after
- before/after p50/p95/p99
- before/after *one mechanism metric* that moved in the expected direction
