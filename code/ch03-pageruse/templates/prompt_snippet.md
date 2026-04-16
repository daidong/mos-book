# Prompt template notes (PagerUSE)

You can tune the LLM behavior by editing `src/core.js` (system prompt) and by adding scenario-specific fields.

Recommended additions per scenario:

- `groundTruth.primary`: cpu/memory/disk/network/mixed
- `groundTruth.mechanism`: one sentence (the answer you want students to reach)
- `commandLibrary`: **deterministic outputs** for key commands so the LLM stays consistent

<!--
IMAGE PLACEHOLDER idea (for the UI):
- Add a small "latency histogram" card with p50/p95/p99 and a long tail.
- Add an "events timeline" card: deploy, config change, batch job start.
-->
