# Project 04 Rubric — Full-stack Profiling of SWE-agent (Agent Runtime as a System)

The "system" here is not the Linux kernel by itself. It is the
combination of *agent + tool calls + subprocesses + IO + (optionally)
remote model calls*.

This rubric is one tier. The same standard applies to every submission.

---

## 1. Required deliverables (a missing item caps the grade)

- **Task pack (10–20 tasks).** Each task includes input repo / issue,
  a success criterion, and a timeout budget.
- **Machine-readable log (JSONL).** Each tool call records start /
  end timestamps, command and argument summary, and exit code.
- **Resource experiments (cgroup v2).** Both CPU quota and memory limit.
- **External-cost transparency.** If a remote LLM API is used, the
  report names the model, the parameters, the cost cap, and the actual
  spend estimate.
- **Environment record:** `uname -r`, VM configuration, SWE-agent
  version, dependency versions.

Every resource experiment must satisfy the **evidence contract**:

1. **Two independent supporting signals** drawn from different
   observation layers. At least one agent / application-level signal
   (time breakdown, success rate, failure-mode distribution) and at
   least one OS / resource-control signal (cgroup, PSI, `pidstat`,
   `iostat`).
2. **One negative control** ruling out a plausible alternative
   (`iostat` stable → not IO; no OOM and PSI memory low → not a memory
   limit issue dressed up as something else).
3. **Before/after + a mechanism-level metric.** At least one primary
   outcome (success rate, total runtime, cost) moves measurably, and a
   mechanism metric (`throttled_usec`, PSI, `memory.current`, OOM
   events) moves consistently with the explanation.

---

## 2. Scoring rubric (100 points)

### A. Benchmark pack quality (20)
- (8) Clear task definitions: input repo or issue, success criterion,
  timeout.
- (7) Reproducibility: under the same agent version and environment,
  the *type* of outcome (success / failure mode) is stable.
- (5) Coverage: tasks are not all the same kind.

### B. Profiling, logging, and analysis pipeline (30)
- (10) Reasonable log schema: replayable, statable (tool, LLM, tests,
  git, etc.).
- (10) Credible time decomposition that distinguishes waiting from
  local execution.
- (10) Automated analysis producing at least three metric categories:
  total runtime, success rate, and either tool-call share or
  failure-mode distribution.

### C. Resource-constraint experiments and mechanism explanation (30)

**CPU quota (15)**
- Outcome metric changes (total runtime, success rate, shifts in
  tool-call share).
- Two independent cross-layer signals (e.g., `cpu.stat` throttling +
  `pidstat -w` / PSI CPU / agent-loop evidence).
- One explicit negative control (e.g., `iostat` stable → not IO).
- Mechanism explanation: how throttling affects the agent loop, test
  execution, and builds.

**Memory limit (15)**
- OOM / reclaim / jitter signals (`memory.current`, `memory.stat`,
  PSI memory).
- Two independent signals + one negative control.
- Mechanism explanation: memory peaks during dependency install,
  compilation, or test execution, and the resulting failure mode.

### D. Strategy / mitigation and validation (20)
- (10) Implement at least one strategy or mitigation: timeouts,
  tool allowlist, dependency caching, retry caps.
- (10) Controlled-comparison validation showing the effect on at
  least one primary metric (success rate, total runtime, cost).

Every mitigation must show before/after on a primary metric plus a
mechanism-level metric moving consistently.

**Bonuses (max +10)**
- +5: A failure-mode taxonomy written like a small paper —
  defined precisely, auto-classifiable, illustrated with examples.
- +5: Quantified side effects of a strategy (e.g., "fewer loops but
  lower success rate") and a proposed refinement.

---

## 3. Where the difficulty actually lives

1. **Turning agent behavior into a measurable system.** Without a
   logging schema and an analysis pipeline, every later conclusion
   sits on sand.
2. **Controlling external variables.** Remote models, network, and
   dependency installs inject noise. Holding variables and running
   controls is the project's craft.
3. **Mechanism explanation, not empirical hand-waving.** "Resource
   limits cause specific failure modes (OOM, timeout, loop)" must be
   demonstrated through OS / cgroup / PSI signals.

---

## 4. Submission checklist

- `tasks/`: task definitions and input repositories.
- `runner/`: run scripts (single-task and batch).
- `collect/`: OS / cgroup / PSI collection.
- `analyze/`: JSONL → plots / tables / summary.
- `results/`: raw logs and aggregated outputs.
- Final report and presentation slides.
