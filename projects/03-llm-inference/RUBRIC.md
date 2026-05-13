# Project 03 Rubric — LLM Inference Server Profiling (CPU-first)

This project treats LLM inference as a server workload. The core output
is the chain *metrics → observation → OS mechanism → mitigation
validation*.

This rubric is one tier. The same standard applies to every submission.

---

## 1. Required deliverables (a missing item caps the grade)

- **Workload definition:** what counts as a "request" (CLI or HTTP),
  fixed prompt and generation length (or explicit handling of
  randomness).
- **Metrics:** at minimum, **TTFT**, **tokens per second**, and
  **p95 / p99 request latency**.
- **Resource experiments**, both required:
  1. **cgroup v2 CPU quota.**
  2. **cgroup v2 memory limit.**
- **Variable sweep:** at least three dimensions (context length,
  output length, concurrency, thread count, model size / quantization,
  cold vs warm start).
- **At least two mitigations**, ideally one system-level and one
  application-level.
- **Evidence sources:** VM-friendly signals only (PSI, cgroup, `/proc`,
  `pidstat`, `vmstat`). `perf` hardware PMU cache counters may be
  unavailable; do not depend on them.
- **Environment record:** `uname -r`, VM configuration, model
  version / quantization, thread count.

Every resource experiment and every mitigation must satisfy the
**evidence contract**:

1. **Two independent supporting signals**, drawn from different
   observation layers. At least one application/user-space signal
   (TTFT, p99, tokens/s) and at least one OS / resource-control signal
   (cgroup, PSI, `pidstat`, `vmstat`, `iostat`).
2. **One negative control** ruling out a plausible alternative
   (`iostat` stable → not IO; no throttling in `cpu.stat` → not the
   CPU quota; PSI memory low → not reclaim).
3. **Before/after percentiles plus a mechanism-level metric that
   moved** (`throttled_usec`, PSI, major faults).

---

## 2. Scoring rubric (100 points)

### A. Reproducibility and baseline stability (25)
- (10) A one-command run produces baseline results (metrics + logs).
- (8) Repetition: N ≥ 5 (or the chosen N is justified) with variance,
  box plots, or confidence intervals reported.
- (7) Environment record: model version, quantization, thread count,
  and VM configuration are written down.

### B. Measurement methodology and metric definitions (20)
- (8) TTFT and tokens/s definitions are explicit (timestamp source,
  computation method).
- (7) Client concurrency and server queue / thread-pool behavior are
  documented.
- (5) Noise sources are discussed (cache warming, first-load effects,
  CPU frequency scaling, VM jitter).

### C. Resource experiments and mechanism explanation (35)

**CPU quota (18)**
- Metric changes (TTFT, p99, tokens/s).
- Two independent cross-layer signals (e.g., application metric +
  `cpu.stat` `throttled` or PSI CPU or `pidstat`).
- One explicit negative control (e.g., `iostat` stable → not IO).
- A mechanism explanation: how throttling translates into queueing,
  runnable-wait, and a longer critical phase.

**Memory limit (17)**
- Metric changes.
- Two independent cross-layer signals (e.g., application metric +
  `memory.current` / `memory.stat` + PSI memory or major faults).
- One explicit negative control (e.g., no throttling in `cpu.stat` →
  not the CPU quota).
- A mechanism explanation: reclaim, major faults, possible OOM.

### D. Mitigation and validation (20)
- (10) System-level mitigation: pinning / affinity, thread tuning,
  warmup, avoiding swap, cgroup adjustment.
- (10) Application-level mitigation: concurrency control, admission
  control, prompt constraints, caching or batching where feasible.

Every mitigation must show before/after percentiles plus a
mechanism-level metric moving consistently with the explanation.

**Bonuses (max +10)**
- +5: A cold-start breakdown into model-file load, page-faulting in,
  JIT (if applicable), with time shares.
- +5: A simple model explaining the tokens-per-second ceiling
  (CPU utilization, thread scaling, context-switch overhead) that
  matches the data.

---

## 3. Where the difficulty actually lives

1. **Metric definitions and reproducibility.** LLM inference has many
   non-deterministic factors (caching, threading, queueing). Making
   the experiments *comparable* is the first challenge.
2. **From resource limit to mechanism evidence.** "Quota is smaller,
   therefore slower" is not an explanation. The mechanism must be
   demonstrated through cgroup, PSI, and `/proc` signals.
3. **Explaining the tail.** p99 typically comes from queueing and
   jitter (throttling, reclaim, IO). Attributing the tail to a
   specific critical phase is the project's signature analysis.

---

## 4. Submission checklist

- `server/`: how to run the inference service or CLI.
- `bench/`: load generator with controllable concurrency / rate.
- `collect/`: PSI, cgroup, `pidstat`, `vmstat` collection.
- `experiments/`: variable-sweep configurations.
- `results/`: raw logs and parsed plots / tables.
- Final report and presentation slides.
