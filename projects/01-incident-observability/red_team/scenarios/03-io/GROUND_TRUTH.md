# Ground truth (fill in)

Explain the IO mechanism, e.g.:
- why fsync/writeback causes tail spikes (queueing, flush, journal)
- what the critical path is for the service (sync writes? metadata? page cache?)
- why p99 amplifies (bursty writeback, contention with reads)
