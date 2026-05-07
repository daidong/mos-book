# Lab: PagerUSE Oncall Simulation — Memory-Pressure Tail Latency

> **Estimated time:** 4–5 hours
>
> **Prerequisites:** Chapter 3 concepts; Node.js 18+; Part I Ubuntu
> environment
>
> **Tools used:** `top`, `free`, `vmstat`, `cat /proc/vmstat`, `dmesg`,
> `journalctl`, `ss`, `ps`, the RED method, and the USE method

## Objectives

- Diagnose a memory-pressure-driven tail-latency incident using RED and USE
  rather than ad hoc guessing
- Build evidence chains with two supporting signals and one exclusion check
- Distinguish memory pressure from competing explanations such as CPU
  saturation or network symptoms
- Explain why major faults can inflate p99 while leaving p50 mostly unchanged
- Synthesize the Part I pattern: mechanism → observation → evidence →
  exclusion → verification
- Produce a report that remains meaningful even if AI helps with formatting,
  because the grading depends on your own command sequence and evidence

## Background

PagerUSE is a small web application that simulates an oncall dashboard and a
restricted observation terminal. You are given an alert, a short context
panel, and a constrained set of Linux-style observation commands. The goal is
not to be shell-clever. The goal is to reason about OS mechanisms under
partial observability.

The required path is intentionally centered on memory pressure. Part A is the
main case: working-set growth, reclaim, major faults, and a p99 spike. Part B
adds a small scheduling preview so you practice separating coexisting causes.
Part C is optional and previews storage/retry debugging for later chapters.

The simulator includes three scenarios:

| Difficulty | Scenario | Main lesson | Investigation trap |
|---|---|---|---|
| Easy | `easy_memory_major_faults` | memory pressure as the dominant mechanism | high memory use is not enough; you need the fault path |
| Medium | `medium_multi_cause` | memory pressure plus a scheduling preview | one true signal does not explain the whole tail |
| Hard | `hard_misleading_network` | optional preview of storage/retry symptoms | timeout symptoms can hide storage or retry amplification |

Source lives in `code/ch03-pageruse/`.

## Setup

```bash
cd code/ch03-pageruse
npm install
LLM_MODE=mock npm start
```

Open <http://localhost:3000>.

Mock mode is the recommended grading path because it is deterministic.

## Terminal Rules

The terminal is intentionally restricted.

- It does **not** execute on your real machine.
- It allows only a small observation-oriented command set.
- Pipes, redirects, quotes, command substitution, and chaining are disabled.
- The point is evidence and interpretation, not shell tricks.

Type `help` inside a scenario to see the allowed commands for that scenario.

## Part A: Easy Scenario — One Dominant Cause (Required)

**Scenario:** `easy_memory_major_faults`

### A.1 Incident Card Before Investigation

Before you run any command, fill in the first section of
`use_checklist.md`.

Record:

1. the alert symptom and baseline;
2. the failed SLI and the implied SLO risk;
3. two plausible hypotheses from different resources;
4. the first three commands you plan to run and why.

This is the lab's equivalent of a pre-run hypothesis. You may use AI to
clarify what a command does, but the initial hypotheses and command plan must
come from you before exploration.

### A.2 Run a RED Pass

Start from the service view:

- **Rate:** did request volume change?
- **Errors:** did error or timeout rate change?
- **Duration:** which latency percentile violated the SLO?

The UI gives only partial RED evidence. Record what you can infer and what
is missing. Then move to USE.

### A.3 Run a USE Pass

Use the checklist in `code/ch03-pageruse/use_checklist.md` to frame the
resource surface:

- CPU: utilization, runqueue, throttling?
- Memory: usage, reclaim, major faults, OOM?
- Disk: queueing, latency, errors?
- Network: backlog, retransmits, resets?

Do not jump straight to the explanation. Collect evidence.

### A.4 Build the Evidence Chain

Your report must contain:

1. **Signal 1** supporting the primary hypothesis;
2. **Signal 2** that is independent of Signal 1;
3. **Exclusion** ruling out one plausible competing hypothesis.

A strong memory-pressure chain often includes:

- `free -m` or cgroup memory usage;
- `pgmajfault` from `/proc/vmstat`;
- an exclusion against CPU saturation or network backlog.

### A.5 Write the Diagnosis

In `report.md`, write one short section with these headings:

- Symptom
- Initial hypotheses
- RED summary
- USE summary
- Signal 1
- Signal 2
- Exclusion
- Mechanism
- Mitigation
- Verification plan

The **Mechanism** paragraph is the most important part. Explain why the slow
path inflates p99 but does not necessarily move p50 much.

### A.6 Part A Checklist

- [ ] Incident card completed before investigation
- [ ] RED pass recorded, including missing information
- [ ] USE pass recorded across CPU, memory, disk, and network
- [ ] Two supporting signals collected
- [ ] One exclusion check collected
- [ ] Mechanism explained causally
- [ ] Mitigation and verification plan included

## Part B: Medium Scenario — Memory Plus a Scheduling Preview (Required)

**Scenario:** `medium_multi_cause`

This scenario is harder because memory pressure is not the only real signal.
You are not expected to know Linux scheduler internals yet; Chapters 4 and 5
will teach that. Here, the goal is simpler: notice when the memory-fault story
is incomplete and identify the competing queueing signal.

Before running commands, predict:

1. which two resources are most likely involved;
2. whether memory pressure or CPU queueing will dominate p99;
3. what signal would change your mind.

Then investigate. Your job is to:

1. identify the memory-pressure mechanism with evidence;
2. identify the competing CPU-queueing signal without overclaiming scheduler
   internals;
3. explain whether one dominates or whether they compose;
4. justify which mitigation you would try first.

A strong write-up usually includes a mapping table like this:

| Observation | Supports mechanism | Does not prove |
|---|---|---|
| `pgmajfault` elevated | paging / memory pressure | that CPU is irrelevant |
| `vmstat r` elevated | CPU runqueue delay | that memory is irrelevant |
| disk queue near baseline | excludes storage as primary root cause | that storage has zero cost |

### Part B Checklist

- [ ] Prediction written before command exploration
- [ ] Both mechanisms named explicitly
- [ ] Each mechanism has at least one direct supporting signal
- [ ] Interaction between mechanisms explained
- [ ] One plausible rival explanation excluded
- [ ] Mitigation order justified

## Part C: Preview Scenario — Misleading Network Symptom (Optional)

**Scenario:** `hard_misleading_network`

This optional scenario previews later storage and distributed-systems
chapters. The apparent story is network trouble. Your task is to show whether
that story survives contact with the evidence.

A strong Part C submission will include:

1. one signal that makes the network theory weaker;
2. the actual mechanism chain;
3. an explanation of how retries or queueing amplify the symptom;
4. a mitigation that avoids making the hidden bottleneck worse.

## Part D: Part I Synthesis (Required)

This short section closes Part I. Use evidence from the memory-pressure case
and concepts from Chapters 1–3 to complete the table below.

| Question | Your answer from this lab |
|---|---|
| What was the mechanism? |  |
| Which layer exposed the first symptom: application, runtime, kernel, or hardware? |  |
| Which command or dashboard observation measured the user-facing symptom? |  |
| Which command measured the mechanism-facing signal? |  |
| Which alternative did you rule out? |  |
| What would you verify after mitigation? |  |

Then write one paragraph answering this question:

> How did Chapters 1, 2, and 3 change the way you would debug a production
> performance incident compared with simply asking an AI tool for likely root
> causes?

A generic answer will not receive credit. Refer to at least two concrete
commands or observations from your transcript.

## Deliverables

Submit a directory containing:

| File | Required? | Purpose |
|---|---|---|
| `report.md` | Yes | scenario write-ups with RED/USE summaries and evidence chains |
| `use_checklist.md` | Yes | your filled checklist and incident card |
| `transcript.txt` | Yes | commands issued, key output lines, annotations |
| screenshots | Optional | only if they clarify the workflow |

Use `code/ch03-pageruse/use_checklist.md` as your starting template.

Your `transcript.txt` should preserve the order of investigation. That order
matters: a random pile of commands is weaker evidence of systematic thinking
than a coherent narrowing process.

A good transcript looks like this:

```text
# scenario: easy_memory_major_faults
$ free -m
Mem: 2048 1648 66 112
# -> memory availability is low, but this alone is only utilization evidence

$ grep -E pgmajfault /proc/vmstat
pgmajfault 129834
# -> major-fault counter supports a paging slow path

$ vmstat 1 5
r b swpd free ...
# -> runqueue does not support CPU saturation as the primary cause
```

## AI Use and Evidence Trail

This lab is graded on **prediction → evidence → mechanism**, not on polish.
AI tools are allowed within
[Appendix D](../../appendices/appendix-d-ai-policy.md) (Regime 1): they may
help debug, recall flags, or polish prose; they may **not** generate the
prediction, fabricate raw data, or substitute for your own mechanism-level
explanation. Substantial use must be disclosed in the Evidence Trail. Honest
disclosure is not penalized; non-disclosure of substantial use is.

Append the following section to your report (full template and examples in
Appendix D §"The Evidence Trail"):

```markdown
## Evidence Trail

### Environment and Reproduction
- Commands used: see `transcript.txt`
- Scenario IDs: list the scenarios you completed
- Raw output files: list paths in your submission

### AI Tool Use
- **Tool(s) used:** [tool name and version, or "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you re-checked against
  your own transcript]
- **What I changed or rejected:** [if a suggestion was wrong or
  inapplicable]

### Failures and Iterations
- [At least one thing that did not work on the first attempt and
  what you learned from it.]
```

## Grading Rubric (100 pts)

| Area | Points | Criterion |
|---|---:|---|
| Incident framing | 15 | hypotheses and first commands recorded before exploration |
| Methodology | 20 | RED and USE applied systematically rather than randomly |
| Evidence quality | 25 | two supporting signals plus one exclusion, with cited lines |
| Mechanism depth | 25 | explanation is causal and tied to the memory-pressure slow path |
| Part I synthesis | 10 | connects mechanism, observation, exclusion, and verification across Chapters 1–3 |
| Mitigation and verification | 5 | proposed response matches the mechanism |

## Common Pitfalls

- Treating one suggestive counter as a complete diagnosis
- Confusing high utilization with saturation
- Treating timeout symptoms as proof that the network is the root cause
- Copying entire command dumps instead of citing the lines that matter
- Naming two mechanisms but never explaining how they interact
- Writing a plausible story without ruling out a competitor
- Letting AI produce a generic incident narrative that is not grounded in
  your transcript
