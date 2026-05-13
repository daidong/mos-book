# Project 02 Rubric — Mini-K8s Multi-hop Service, QoS / Cgroups, End-to-End Tail Latency

The goal is not "get Kubernetes running" — it is **a mechanism-level
explanation of end-to-end tail latency plus a validated mitigation.**

This rubric is one tier. The same standard applies to every team.

---

## 1. Required deliverables (a missing item caps the grade)

- **Multi-hop topology:** at least two internal hops (the load generator
  does not count).
- **Metrics:** p50 / p95 / p99 end-to-end latency, plus throughput and
  error rate (recorded at minimum).
- **K8s / cgroup experiments:** must include both
  *requests/limits → cgroup behavior* and *QoS class* effects.
- **Two mitigations:**
  1. **Resource / OS / K8s-level** (requests/limits, QoS, isolation,
     priority).
  2. **Application-level** (timeout, backoff, batching, caching,
     admission control).
- **Environment record:** `uname -r`, VM configuration (vCPU / RAM),
  kind or k3s version.

Every interference experiment and every mitigation must satisfy the
**evidence contract**:

1. **Two independent supporting signals**, drawn from different
   observation layers. At least one application/user-space signal
   (end-to-end latency, hop latency, error rate, throughput) and at
   least one OS / resource-control / K8s control-plane signal
   (cgroup stats, PSI, `pidstat`, `iostat`, `kubectl events`).
   Two screenshots of `top` do not count.
2. **One negative control** ruling out a plausible alternative (e.g.,
   stable `iostat` → not IO; no throttling in `cpu.stat` → not the CPU
   quota).
3. **Before/after percentiles plus a mechanism-level metric that
   moved.** Report p50 / p95 / p99 (or at minimum p50 / p99) and one
   mechanism metric (`throttled_usec`, PSI, `iostat await`, OOM /
   eviction events) consistent with the explanation.

`perf` PMU counters may not work in VMs; do not depend on hardware
cache events.

---

## 2. Scoring rubric (100 points)

### A. System setup and reproducibility (25)
- (10) One command (or three steps max) deploys the cluster, the
  service, and produces a baseline result.
- (8) Explicit resource budget: VM configuration, node count, image
  size kept laptop-friendly.
- (7) Reproduction and cleanup scripts that prevent residual state from
  contaminating later runs.

### B. Measurement methodology and metric definitions (20)
- (8) Controlled load generation: warmup, repetition count, fixed
  concurrency or arrival rate.
- (7) Correct latency statistics: percentile window, sample count,
  histogram or log-based computation.
- (5) Noise discussion: VM jitter, GC or JIT, cache warming.

### C. Mechanism explanation and evidence chain (35)
At least two interference experiments, each worth ~17.5 points:
- (6) Attribute end-to-end p99 degradation to a specific hop or
  resource (critical-path identification).
- (6) Reach the mechanism (quota throttling → runqueue delay;
  reclaim → faults; writeback → IO wait; netem → retransmits or
  queue growth).
- (5) Two independent signals from different layers.
- (0.5) One explicit negative control.

> If an experiment is missing the negative control or the mechanism
> metric, that experiment caps at "located the resource but did not
> close the mechanism loop".

### D. Mitigation and validation (20)
- (10) Resource / OS / K8s-level mitigation: before/after percentiles,
  before/after mechanism metric, and an explanation.
- (10) Application-level mitigation: same standard (e.g., timeout +
  backoff preventing retry storms, admission control bounding queue
  depth).

**Bonuses (max +10)**
- +5: A parameter sweep (`limit` or `requests` vs p99 curve) rather
  than a single before/after comparison.
- +5: A simple queueing-model explanation of the critical path
  (Little's Law intuition) that matches the observed data.

---

## 3. Where the difficulty actually lives

1. **End-to-end vs hop-level attribution.** p99 is a system-level
   phenomenon; proving *which hop is dragging the tail* is harder than
   making the tail bad.
2. **Bridging K8s abstractions to kernel mechanisms.** Showing how
   `requests` / `limits` / QoS land as cgroup throttling, OOM, or
   eviction is the project's intellectual core.
3. **Methodology under noise.** Rigorous experiments on a kind / k3s
   cluster running inside a VM are noticeably harder than "running a
   demo".

---

## 4. Submission checklist

- `deploy/`: manifests (or Helm / Kustomize).
- `run.sh`: one-command baseline + interference + mitigation.
- `collect/`: at minimum, cgroup, PSI, and K8s event collection.
- `results/`: raw logs and parsed plots / tables (end-to-end p99 plus
  at least one hop-level piece of evidence).
- Final report and presentation slides.
