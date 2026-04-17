# Appendix A: Capstone Projects

This appendix summarizes four multi-week capstone projects. They
integrate material from multiple chapters and are the intended
vehicle for the second half of a semester built around this book.

Each project is deliverable as a short paper plus a
reproducibility artifact (see Chapter 13). Full project briefs
and grading rubrics live in the `projects/` directory of the
book repository.

All four projects share a common shape:

1. **Frame a concrete system case study.** A specific service
   exhibiting a specific behavior — an LLM inference server
   with unstable p99, a microservice chain with fan-out tail
   inflation, a container runtime with cold-start latency.
2. **Build an evidence-driven investigation.** Apply the
   Chapter 3 contract: two independent signals plus one
   exclusion for every claim.
3. **Propose and validate an intervention.** Change one thing,
   measure before/after, explain the mechanism.
4. **Ship a reproducibility artifact.** Scripts, raw data,
   figure-regeneration code, environment pinning (Chapter 13).

Pick the project that matches your background. All four touch
on Chapters 2–3 (measurement, tail latency); the other chapters
each project emphasizes are listed below.

---

## A.1 Project 1: Red/Blue Oncall Game

Two-team adversarial project. Teams alternate roles.

- **Red team** injects faults into a small service stack
  (sample: a Redis + nginx + stress-ng setup inside a `kind`
  cluster). Fault categories: CPU contention, `fsync` stalls,
  memory pressure causing OOM kills, packet loss, throttling
  via `cpu.max`, bursty background I/O.
- **Blue team** is on call. They use the observability stack
  from Chapters 3 (USE method), 5 (eBPF), 7 (cgroup stats),
  and 10 (`iostat`, `filefrag`). For each incident they
  produce a postmortem: symptom timeline, hypothesis chain,
  evidence, mechanism, mitigation.

Teams rotate midway through the project. Final deliverable:
a unified report with one postmortem per incident and a
reflective section on what each team learned from being on the
other side of the alert.

**Chapters exercised:** 3 (tail latency, USE), 5 (scheduler
internals), 6–7 (containers, K8s QoS), 10 (fsync, page cache).

**Skills built:** incident response under time pressure,
observability toolchains, systematic debugging, producing
postmortems that are readable by engineers who were not in the
room.

**Difficulty:** Medium. Good fit for 2–3 student teams.

---

## A.2 Project 2: Multi-hop K8s Tail Latency

Deploy a 3–4 hop service chain on a local `kind` cluster —
frontend → API → cache → database. Generate traffic with a
load generator (`wrk2` or Locust at constant arrival rate,
Chapter 3 §3.2) and record end-to-end p99 at multiple request
rates.

Decompose the tail by hop using distributed tracing (OpenTelemetry
exporters are cheap to wire in) plus kernel-level eBPF probes at
critical points (scheduler wakeups, disk I/O, TCP establishment).
Identify which hop owns the tail at each load level, and why.

Propose and validate at least one intervention: pod affinity so
the cache and its consumer co-locate, a PriorityClass that
protects the latency-sensitive tier, a `net.core.somaxconn`
bump, or a QoS class change from Burstable to Guaranteed.
Measure before and after with the same evidence contract.

**Chapters exercised:** 3 (tail latency, USE method), 5 (eBPF
tracepoints), 7 (QoS and CFS bandwidth control), 9 (scheduling
constraints and affinity).

**Skills built:** end-to-end performance analysis in a
realistic microservice stack, distributed tracing, evidence-
driven tuning, writing a performance paper that is honest about
where the latency actually comes from.

**Difficulty:** Medium–high. Individual or pair project.

---

## A.3 Project 3: LLM Inference Server Profiling

Stand up a local LLM inference server — vLLM, llama.cpp, TGI,
or similar — on whatever accelerator you have (including CPU).
Characterize its performance:

- **Time-to-first-token (TTFT)** under varying prompt lengths.
- **Inter-token latency (ITL)** during decoding.
- **Steady-state throughput** in tokens per second at varying
  concurrencies.
- **Resource utilization:** GPU utilization if you have one,
  otherwise CPU %, memory usage, page faults.
- **Batching behavior.** Does the server batch requests? What
  does the batch-size distribution look like? How does it
  respond to bursty arrivals?

Your experiments should quantify how batch size, context
length, and concurrency interact to produce the shape of p99
TTFT. At least one intervention: tune a batching parameter,
pin the worker, change the KV-cache page size, or run with a
different precision (fp16 vs int8). Explain the mechanism
behind the change you observe.

**Chapters exercised:** 2 (measurement methodology), 3 (tail
latency, percentiles), 4 (concurrency and queuing), 10–11
(storage if model weights stream from disk).

**Skills built:** GPU/CPU profiling, reasoning about queuing
delays in a stateful server, distinguishing
compute-bound from memory-bound from I/O-bound regimes, writing
performance claims about an AI system that survive scrutiny.

**Difficulty:** Medium–high. Prior exposure to GPU tooling
helps but is not required.

---

## A.4 Project 4: SWE-agent Runtime Profiling

Instrument an open-source software-engineering agent — SWE-agent,
OpenHands, or similar — running against a small benchmark (a
subset of SWE-bench-lite is the canonical choice). Produce a
per-tool-call latency breakdown:

- Model think time (the time spent waiting for the LLM response).
- Tool execution time (the child process, the HTTP request,
  etc.).
- Sandbox setup cost (container creation, namespace setup — see
  Chapter 12).
- I/O wait time inside the tool.

Build the breakdown from structured audit logs (Chapter 12 §12.5)
plus OS-level instrumentation (eBPF or `strace`). Identify the
dominant cost per task: model inference? sandbox setup? file
I/O? Is it consistent across tasks or task-dependent?

Propose one concrete optimization — a pre-forked sandbox pool,
a smaller tool allowlist, caching reads of unchanged files, a
faster model served locally — implement it, and evaluate. Your
evaluation must honestly report cases where the optimization
does not help, or makes a different bucket of latency worse.

**Chapters exercised:** 2–3 (measurement, tail latency), 4
(fork and process lifecycle), 6 (container sandboxing), 12
(agent runtime safety and performance).

**Skills built:** instrumenting complex systems you did not
write, reasoning about end-to-end latency budgets in an agent,
connecting measurement to improvement without overclaiming.

**Difficulty:** High. Individual project for graduate students
with prior systems experience.

---

## Deliverables Common to All Projects

Every project submits:

1. **A short paper** (6–10 pages) in the template at
   `templates/final-report-template.md`. Must include:
   problem, hypothesis, methodology, results, mechanism,
   limitations, future work.
2. **A reproducibility artifact** meeting the standards of
   Chapter 13: environment script, pinned versions, raw data,
   analysis scripts, per-figure reproduction instructions.
3. **A 12–15 minute final presentation.**
4. **A peer-reproduction report** — another team attempts to
   reproduce your headline result and submits a report using
   `templates/reproduction-report-template.md`.

The peer reproduction step is where artifacts get graded most
honestly. "Works on my machine" quickly becomes "works on
someone else's machine or it doesn't."
