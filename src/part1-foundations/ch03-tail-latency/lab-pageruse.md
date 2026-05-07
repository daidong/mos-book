# Lab: PagerUSE Oncall Simulation

> **Estimated time:** 3–4 hours
>
> **Prerequisites:** Chapter 3 concepts; Node.js 18+; Part I Ubuntu
> environment
>
> **Tools used:** `top`, `free`, `vmstat`, `cat /proc/vmstat`,
> `dmesg`, `ss`, `ps`, simulated `/usr/bin/time -v`, and the USE method

## Objectives

- Diagnose tail-latency incidents using the USE method rather than ad hoc
  guessing
- Build evidence chains with two supporting signals and one exclusion check
- Distinguish a root cause from a misleading symptom
- Produce a report that remains meaningful even if AI helps you draft it,
  because the grading depends on your own command sequence and evidence

## Background

PagerUSE is a small web application that simulates an oncall dashboard and a
restricted observation terminal. You are given an alert, a short context
panel, and a constrained set of Linux-style observation commands. The goal is
not to be shell-clever. The goal is to reason about OS mechanisms under
partial observability.

The simulator includes three scenarios:

| Difficulty | Scenario | Main lesson |
|---|---|---|
| Easy | `easy_memory_major_faults` | one dominant mechanism |
| Medium | `medium_multi_cause` | two co-occurring mechanisms |
| Hard | `hard_misleading_network` | misleading symptom, real root cause elsewhere |

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
2. two plausible hypotheses from different resources;
3. the first three commands you plan to run and why.

This is the lab's equivalent of a pre-run hypothesis.

### A.2 Run a USE Pass

Use the checklist in `code/ch03-pageruse/use_checklist.md` to frame the
resource surface:

- CPU: utilization, runqueue, throttling?
- Memory: usage, reclaim, major faults, OOM?
- Disk: queueing, latency, errors?
- Network: backlog, retransmits, resets?

Do not jump straight to the explanation. Collect evidence.

### A.3 Build the Evidence Chain

Your report must contain:

1. **Signal 1** supporting the primary hypothesis;
2. **Signal 2** that is independent of Signal 1;
3. **Exclusion** ruling out one plausible competing hypothesis.

A strong memory-pressure chain often includes:

- `free -m` or cgroup memory usage;
- `pgmajfault` from `/proc/vmstat`;
- an exclusion against CPU or disk saturation.

### A.4 Write the Diagnosis

In `report.md`, write one short section with these headings:

- Symptom
- Hypothesis
- Signal 1
- Signal 2
- Exclusion
- Mechanism
- Mitigation
- Verification plan

The **Mechanism** paragraph is the most important part. Explain why the slow
path inflates p99 but does not necessarily move p50 much.

### A.5 Part A Checklist

- [ ] Incident card completed before investigation
- [ ] Two supporting signals collected
- [ ] One exclusion check collected
- [ ] Mechanism explained causally
- [ ] Mitigation and verification plan included

## Part B: Medium Scenario — Two Contributing Causes (Required)

**Scenario:** `medium_multi_cause`

This scenario is harder because more than one mechanism is real.

Your job is to:

1. identify both mechanisms with separate evidence;
2. explain whether one dominates or whether they compose;
3. justify which mitigation you would try first.

A strong write-up usually includes a mapping table like this:

| Observation | Supports mechanism |
|---|---|
| `pgmajfault` elevated | paging / memory pressure |
| `vmstat r` elevated | CPU runqueue delay |
| disk queue near baseline | excludes storage as primary root cause |

### Part B Checklist

- [ ] Both mechanisms named explicitly
- [ ] Each mechanism has at least one direct supporting signal
- [ ] One plausible rival explanation excluded
- [ ] Mitigation order justified

## Part C: Hard Scenario — Misleading Symptom (Optional)

**Scenario:** `hard_misleading_network`

The apparent story is network trouble. Your task is to show whether that
story survives contact with the evidence.

A strong Part C submission will include:

1. one signal that makes the network theory weaker;
2. the actual mechanism chain;
3. an explanation of how retries or queueing amplify the symptom.

## Deliverables

Submit a directory containing:

| File | Required? | Purpose |
|---|---|---|
| `report.md` | Yes | scenario write-ups with evidence chains |
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
Mem: 1024 960 10 45
# -> memory availability is nearly exhausted

$ grep -E pgmajfault /proc/vmstat
pgmajfault 129834
# -> major-fault counter is far above baseline

$ vmstat 1 5
r b swpd free ...
# -> runqueue does not support CPU saturation as the primary cause
```

## AI Use and Evidence Trail

This lab is graded on **prediction → evidence → mechanism**, not
on polish. AI tools are allowed within
[Appendix D](../../appendices/appendix-d-ai-policy.md) (Regime 1):
they may help debug, recall flags, or polish prose; they may
**not** generate the prediction, fabricate raw data, or substitute
for your own mechanism-level explanation. Substantial use must be
disclosed in the Evidence Trail — honest disclosure is not
penalized; non-disclosure of substantial use is.

Append the following section to your report (full template and
examples in Appendix D §"The Evidence Trail"):

```markdown
## Evidence Trail

### Environment and Reproduction
- Commands used: see the Procedure sections above
- Raw output files: list paths in your submission

### AI Tool Use
- **Tool(s) used:** [tool name and version, or "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you re-checked against
  your own data]
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
| Methodology | 20 | USE applied systematically rather than randomly |
| Evidence quality | 30 | two supporting signals plus one exclusion, with cited lines |
| Mechanism depth | 25 | explanation is causal and tied to an OS slow path |
| Mitigation and verification | 10 | proposed response matches the mechanism |

## Common Pitfalls

- Treating one suggestive counter as a complete diagnosis
- Confusing high utilization with saturation
- Copying entire command dumps instead of citing the lines that matter
- Naming two mechanisms but never explaining how they interact
- Writing a plausible story without ruling out a competitor
