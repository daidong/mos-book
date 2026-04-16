# Scenario 01 — Scheduling / Concurrency (template)

## Symptom spec
- User-visible symptom: p99 latency spikes, but average stays mostly OK.
- Optional secondary symptom: increased timeout/error rate.

## Reproduction
1) Start workload + loadgen (baseline)
2) Start collectors (Blue team scripts)
3) Inject scheduler interference (examples):
   - pin a CPU hog to the same CPU as the service
   - create lock convoy (intentionally contended mutex)
   - reduce CPU share of the service (nice/cgroup weight)

## Expected story (high level)
- runnable-queue pressure / lock contention → scheduling latency increases
- tail latency amplifies because the worst wakeups hit long queueing delays

## Files to provide (Red team)
- `INJECT.sh`, `CLEANUP.sh`
- `GROUND_TRUTH.md`
- `EVIDENCE_CONTRACT.md`
