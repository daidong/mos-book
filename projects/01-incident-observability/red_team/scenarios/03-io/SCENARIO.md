# Scenario 03 — Storage / writeback tail latency (template)

Goal: make p99 bad due to IO path effects (fsync/writeback/await), ideally with a misleading primary symptom.

Examples:
- background fsync writer → writeback bursts → latency spikes
- IO saturation → queueing in block layer → higher await

Deliverables:
- `INJECT.sh` / `CLEANUP.sh`
- `GROUND_TRUTH.md`
- `EVIDENCE_CONTRACT.md` (2 signals + 1 negative control)
