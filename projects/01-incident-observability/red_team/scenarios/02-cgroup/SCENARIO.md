# Scenario 02 — cgroup v2 resource boundary (template)

Goal: demonstrate an incident where a resource **limit** changes behavior (not just "CPU got busy").

Pick one primary mechanism:
- CPU quota throttling (`cpu.max`) → latency amplification
- memory limit (`memory.max`) → reclaim/major faults/OOM kill

Deliverables:
- `INJECT.sh` / `CLEANUP.sh`
- `GROUND_TRUTH.md` (mechanism)
- `EVIDENCE_CONTRACT.md` (2 signals + 1 negative control)
