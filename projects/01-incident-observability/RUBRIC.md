# Project 01 Rubric — Red/Blue Oncall Game

This rubric answers three things:

1. What "complete" looks like for this project.
2. How to grade it (concrete deduction and bonus points).
3. Where the real difficulty lives, so effort lands in the right place.

The rubric is one tier. The same standard applies whether the team is
two students or a single graduate student; team size only changes the
expected breadth of the scenario pack, not the standard for each
scenario.

---

## 1. Required deliverables (a missing item caps the project's grade)

Red and Blue teams both must satisfy:

- **Reproducibility.** A clean VM runs the scenario (or diagnosis
  workflow) end-to-end with one command or no more than three steps,
  and produces an artifact bundle: raw logs, parsed metrics, plots.
- **Metric definitions.** At least one user-facing metric
  (p99 latency / error rate / a saturation metric), with the
  collection method documented.
- **Evidence chain.** "I think it's X" is not acceptable. Every
  finding follows the chain *symptom → suspect resource → mechanism*.
- **Environment record.** `uname -r`, host type (bare metal / VM / cloud
  instance), resource budget (vCPU, RAM).

Every scenario (Red-authored, Blue-solved) must include the **evidence
contract**:

- **Two independent supporting signals**, drawn from different
  observation layers (e.g., application latency histogram *plus* cgroup
  `cpu.stat` or PSI).
- **One negative control** that rules out a plausible alternative
  explanation.

Every mitigation must include:

- **Before/after p50/p95/p99** (or at minimum p50/p99).
- **A mechanism-level metric that moved** in the expected direction
  (`cpu.stat:throttled_usec`, PSI, `iostat` `await`,
  `memory.current` / `oom_kill`, etc.).

---

## 2. Scoring rubric (100 points)

### Red team (100)

#### A. Scenario package quality (30)
- (10) **Reproducible.** Each injection script runs deterministically.
- (10) **Cleanable.** Cleanup scripts return the system to baseline so
  a second run is not corrupted by the first.
- (10) **Documented.** Scenario description, trigger, expected
  symptoms, and how to collect evidence are written out.

#### B. Diagnosability design (40)
- (15) **Evidence contract.** Each scenario provides two independent
  supporting signals plus one explicit negative control.
- (10) **No magic.** The scenario does not depend on `perf` PMU cache
  counters (often unavailable in VMs) or on hidden outputs only the
  author knows about.
- (10) **Difficulty ladder.**
  - Scenario 1: single factor, obvious signals.
  - Scenario 2: two factors interacting.
  - Scenario 3: misleading primary symptom — the root cause is somewhere
    other than where the alert points.
- (5) **Mechanism coverage.** The three scenarios collectively cover
  scheduling / concurrency, cgroup boundaries, and IO / writeback.

#### C. Ground truth and mechanism explanation (20)
- (12) Ground truth is **mechanism-level** (reclaim, writeback,
  throttling, runqueue delay, lock convoy) — not "CPU is high" or
  "memory is full".
- (8) The writeup explains *why p99 degrades before the mean does*
  (queueing, microbursts, retries amplifying).

#### D. Scoring interface and anti-guessing (10)
- (6) A grading interface that the Blue team can actually run against
  (checklist, scoring script, or written rubric card).
- (4) Rules that prevent pure guessing: Blue must submit evidence
  artifacts; disruptive actions taken without evidence lose points.

**Red team bonuses (max +10).**
- +5: Two distinct injection paths to the same root cause (improves
  robustness against accidental Blue-team workarounds).
- +5: A "common wrong diagnosis paths" writeup with how to avoid them
  (pedagogical value).

### Blue team (100)

#### A. Diagnosis workbench / workflow (25)
- (10) One command (or a short, clear runbook) starts collection.
- (10) Signal coverage: at least one VM-friendly source from each of
  process-level (`pidstat` / `vmstat` / `iostat` / `ss`), PSI, and
  cgroup v2.
- (5) Result organization: plots, tables, or a timeline (notebook or
  scripted, either is fine).

#### B. Evidence chain per scenario (55)
Averaged across the three scenarios (~18 per scenario):
- (7) Symptom → suspect resource layer (CPU / memory / IO / network /
  lock / queue).
- (7) Resource → mechanism (CPU quota throttling → runqueue delay;
  memory limit → reclaim or major faults; etc.).
- (4) Two independent signals + one negative control.

#### C. Mitigation and validation (15)
- (7) At least one mitigation per scenario, system-level or
  application-level.
- (8) Validation includes:
  - Before/after p50 / p95 / p99 (or at minimum p50 / p99),
  - Before/after of a mechanism-level metric
    (`throttled_usec`, PSI, `iostat await`, `memory.current` /
    `oom_kill`),
  - A sentence connecting "the mechanism metric moved like this →
    therefore the tail moved like that".

#### D. Report and retrospective (5)
- (3) A clear timeline: what was observed, what was tried, why, and
  what changed.
- (2) Explicit limitations: VM measurement noise, signals that were
  unavailable, sources of bias.

**Blue team bonuses (max +10).**
- +5: A reusable diagnosis template (USE / RED method, decision tree,
  triage flowchart).
- +5: Quantified cost of "wrong actions" (e.g., how much downtime an
  evidence-free restart added).

---

## 3. Where the difficulty actually lives

Three things are harder than they look. Spend effort here.

1. **Designing a scenario that is *diagnosable*** — not just one that
   makes the system slow. Many injections produce slowdowns whose
   evidence chain is too noisy to be solved reliably.
2. **Mechanism-level ground truth.** Pinning the symptom to a specific
   OS mechanism (throttling, reclaim, writeback, runqueue delay, lock
   convoy) is the hard part — naming the resource that ran out is not.
3. **Reproducibility under VM noise.** VMs are noisy, `perf` PMU
   counters are often unavailable. Robust evidence chains use PSI,
   cgroup, and `/proc` rather than depending on hardware events.

---

## 4. Submission checklist

- `run.sh` (or `make run`): one-command end-to-end execution.
- `REPRODUCE.md`: clean-VM reproduction steps and dependencies.
- Red: scenario pack with `INJECT.sh`, `CLEANUP.sh`, `SCENARIO.md`,
  `GROUND_TRUTH.md`, `EVIDENCE_CONTRACT.md` per scenario.
- Blue: diagnosis workbench (collect, analyze, report generator).
- `results/`: raw logs, parsed plots and tables, timeline.
- Final report and presentation slides.
