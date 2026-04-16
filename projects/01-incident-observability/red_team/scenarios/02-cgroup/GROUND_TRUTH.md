# Ground truth (fill in)

Explain the exact boundary and the kernel mechanism:

## If CPU quota throttling
- Which cgroup controller is used (cgroup v2 `cpu.max` or systemd CPUQuota)
- What signal confirms throttling (`cpu.stat`: nr_throttled, throttled_usec)
- Why throttling causes queueing (requests pile up / runnable wait increases)

## If memory limit
- Which limit is used (`memory.max` / systemd MemoryMax)
- What signal confirms pressure (memory.current, memory.stat, PSI memory)
- What failure mode occurs (reclaim, major faults, OOM kill) and why tail spikes
