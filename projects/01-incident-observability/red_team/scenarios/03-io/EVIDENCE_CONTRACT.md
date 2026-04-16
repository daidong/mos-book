# Evidence contract (MS baseline)

## Supporting signal #1 (required)
- `iostat -x`: higher `await`, `aqu-sz`, `%util`
- or `pidstat -d`: higher disk IO and delays

## Supporting signal #2 (required)
- PSI IO (if available via memory/IO pressure) or vmstat (blocked processes)
- application-side logs correlate spikes with write bursts

## Negative control / exclusion (required)
- show CPU pressure is not the primary cause (`/proc/pressure/cpu`, `pidstat -u`)
- show no cgroup throttling if applicable (`cpu.stat`)

## Required before/after
- p50/p95/p99
- one IO mechanism metric must move and correlate with the tail
