# Appendix A: Capstone Projects

This appendix summarizes four multi-week capstone projects. They
integrate material from multiple chapters and are the intended
vehicle for the second half of a semester built around this book.

Each project is deliverable as a short paper plus a reproducibility
artifact (see Chapter 13). Full project briefs and grading rubrics
live in the `projects/` directory of the book repository.

<!-- SOURCE: OS-CISC663/projects/README.md and each project's
     project_instruction.md + RUBRIC.md. Only use the v2
     integrative formulation (PROJECTS_v2_integrative.md), not
     the older PROJECTS_v1_lablike.md version. -->

---

## A.1 Project 1: Red/Blue Oncall Game

<!-- SOURCE: projects/01-incident-observability-redblue/
     Two-team adversarial project.
     Red team: inject faults (CPU contention, fsync stalls, OOM,
       packet loss) into a small service stack.
     Blue team: detect, diagnose, and remediate using the
       observability stack from Chapters 3, 5, 7, 10.
     Rotates roles midway through the project.
     Deliverable: a postmortem per incident + a unified report. -->

**Chapters exercised:** 3 (tail latency), 5 (scheduler), 6-7
(containers, K8s QoS), 10 (fsync).

**Skills built:** incident response, observability toolchains,
systematic debugging under time pressure.

---

## A.2 Project 2: Multi-hop K8s Tail Latency

<!-- SOURCE: projects/02-multihop-k8s-tail-latency/
     Deploy a 3-4 hop service chain in K8s.
     Measure end-to-end p99 under varying request rates.
     Decompose tail latency by hop using distributed tracing and
     kernel-level eBPF probes.
     Propose and validate at least one intervention
       (e.g., pod affinity, priority class, sysctl tune). -->

**Chapters exercised:** 3 (tail latency), 5 (scheduler), 7 (QoS),
9 (scheduling constraints).

**Skills built:** end-to-end performance analysis in a realistic
microservice stack, evidence-driven tuning.

---

## A.3 Project 3: LLM Inference Server Profiling

<!-- SOURCE: projects/03-llm-inference-profiling/
     Stand up a local LLM inference server (vLLM, llama.cpp, or
     similar).
     Characterize: time-to-first-token, steady-state throughput,
     GPU/CPU utilization, memory pressure, batching behavior.
     Study the effect of batch size, context length, and
     concurrency on p99 first-token latency. -->

**Chapters exercised:** 2 (measurement), 3 (tail latency),
4 (threads/concurrency), 10-11 (storage if models stream from disk).

**Skills built:** GPU/CPU profiling, interpreting queuing delays,
reasoning about accelerator scheduling.

---

## A.4 Project 4: SWE-agent Runtime Profiling

<!-- SOURCE: projects/04-swe-agent-profiling/
     Instrument an open-source SWE-agent (e.g., SWE-agent, OpenHands)
     running against a small benchmark.
     Produce a per-tool-call latency breakdown (think time, tool
     execution time, I/O wait).
     Identify the bottleneck: model inference? sandbox setup?
     file I/O? Propose a concrete optimization and evaluate it. -->

**Chapters exercised:** 2-3 (measurement, tail latency),
6 (containers for sandboxing), 12 (agent runtimes).

**Skills built:** instrumenting complex systems you did not write,
reasoning about agent latency budgets, connecting measurement to
improvement.

---

## Deliverables Common to All Projects

- A short paper (6-10 pages) in the template provided in
  `templates/final-report-template.md`.
- A reproducibility artifact that satisfies the standards of
  Chapter 13 (scripts, versions, raw data, figure regeneration).
- A 15-minute final presentation.
- A peer-reproduction report in which a different team attempts
  to reproduce the headline result (see
  `templates/reproduction-report-template.md`).
