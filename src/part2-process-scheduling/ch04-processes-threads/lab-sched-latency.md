# Lab: Scheduling Latency Under CPU Contention

> **Estimated time:** 3–4 hours
>
> **Prerequisites:** Chapter 4 concepts (processes, threads,
> preemption, scheduling latency)
>
> **Tools used:** `perf stat`, `taskset`, `nice`, `/proc/schedstat`,
> Python 3 (for percentile scripts)

## Objectives

- Measure baseline wakeup latency on an idle CPU
- Observe how CPU contention inflates p99 scheduling latency
- Collect at least one supporting OS signal (context switches or
  `/proc/<pid>/sched`)
- Apply a mitigation (nice, affinity, or cgroup) and verify the tail
  improves

## Background

**Theme:** tail latency is often scheduling latency.

The experiment uses two small programs that ship with the book in
`code/ch04-sched-latency/`:

- `wakeup_lat` — a latency probe. Each iteration sleeps until an
  absolute timestamp 1 ms after the previous wakeup, measures how
  *late* it actually woke up, and prints `iter=K latency_us=L`. This
  is a direct user-visible measure of scheduling latency.
- `cpu_hog` — a controllable load generator. Starts `N` CPU-bound
  threads and pins them to a configurable CPU.

Baseline run: the probe runs alone, latency is small and stable.
Contended run: pin hogs to the same CPU as the probe, latency tail
inflates. Mitigation: reduce the queue pressure and show the tail
recover.

## Prerequisites

```bash
sudo apt update
sudo apt install -y build-essential python3
# Optional — gives you perf stat, if your VM permits:
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
```

Build:

```bash
cd code/ch04-sched-latency
make
```

## Part A: Baseline Measurement (Required)

**Goal:** Establish what the latency distribution looks like on a
quiet CPU.

Pin the probe to CPU 0 and collect at least 20 000 samples:

```bash
./wakeup_lat --iters 20000 --period-us 1000 --cpu 0 > baseline.log
python3 scripts/latency_to_csv.py baseline.log baseline.csv
python3 scripts/percentiles.py baseline.csv
```

Record:

| Percentile | Latency (µs) |
|---|---|
| p50 |   |
| p90 |   |
| p99 |   |
| p99.9 |   |

The baseline should be tight — p99 typically under a few hundred
microseconds on bare metal, though VMs are noisier.

### Part A Checklist

- [ ] 20 000 samples collected on a pinned CPU
- [ ] Percentiles computed
- [ ] Hardware and environment noted in report (CPU model, kernel
      version, VM config, whether the host was under load)

## Part B: Add CPU Contention (Required)

**Goal:** Show how CPU contention inflates p99.

In a second terminal, pin hogs to the same CPU as the probe:

```bash
./cpu_hog --threads 4 --cpu 0
```

Rerun the probe (CPU 0 again) and collect new samples:

```bash
./wakeup_lat --iters 20000 --period-us 1000 --cpu 0 > contended.log
python3 scripts/latency_to_csv.py contended.log contended.csv
python3 scripts/percentiles.py contended.csv
```

Compare:

| Percentile | Baseline (µs) | Contended (µs) | Ratio |
|---|---|---|---|
| p50 |   |   |   |
| p90 |   |   |   |
| p99 |   |   |   |

You should see p99 grow dramatically — often one or two orders of
magnitude — while p50 may remain modest. This is tail inflation, and
it is exactly what Chapter 4 Section 4.6 predicted.

### Part B Checklist

- [ ] Contention generated on the same CPU as the probe
- [ ] New percentiles collected
- [ ] p99 visibly worse than baseline

## Part C: Supporting Evidence (Required)

**Goal:** Bind the inflated percentile to a specific OS signal. One
signal is enough if chosen well; two is better.

### Option 1: `perf stat`

```bash
sudo perf stat -e context-switches,cpu-migrations \
  ./wakeup_lat --iters 20000 --period-us 1000 --cpu 0 > /dev/null
```

Compare the context-switch count between baseline and contended
runs. Under contention, the probe is preempted more often — each
preemption is potentially a queue wait.

### Option 2: `/proc/<pid>/sched`

While the probe runs:

```bash
PID=$(pgrep -n wakeup_lat)
cat /proc/$PID/sched | sed -n '1,80p'
```

Look for `nr_involuntary_switches` (and its wake-to-run latency
fields if your kernel reports them). Under contention, the involuntary
count rises quickly — each one is a time the scheduler pushed the
probe off-CPU in favor of a hog.

### Option 3: `/proc/schedstat`

A system-wide view. Less precise than `perf stat` but always
available, even in restricted VMs.

In your report, include the counter values for both baseline and
contended runs and explain what each supports. "`context-switches`
tripled under contention" is not enough; the full thought is
"`context-switches` tripled because the probe was preempted each time
a hog's quantum ran out, which is exactly the runqueue wait that
shows up as p99 inflation".

### Part C Checklist

- [ ] At least one supporting signal collected
- [ ] Values compared between baseline and contended runs
- [ ] Written explanation tying the signal to the mechanism

## Part D: Apply a Mitigation (Required)

**Goal:** Show that a targeted mitigation restores the tail.

Pick **one** and verify:

### Mitigation 1: `nice` the hogs

Stop the hogs and restart them at lowest priority:

```bash
nice -n 19 ./cpu_hog --threads 4 --cpu 0
```

Rerun the probe (CPU 0) and collect `mitigated.csv`. Niced hogs
should lose most contests against the probe.

### Mitigation 2: Affinity isolation

Move the probe to a different CPU while the hogs stay on CPU 0:

```bash
./wakeup_lat --iters 20000 --period-us 1000 --cpu 1 > isolated.log
```

The probe now runs on an uncontended CPU; p99 should drop back
toward baseline.

### Mitigation 3: cgroup CPU control (optional, advanced)

If your VM supports cgroup v2, put the hogs in a cgroup with
`cpu.weight = 1` (the minimum) or `cpu.max = "10000 100000"` (10 %
CPU) and watch p99 on the probe.

### Compare

| Percentile | Baseline | Contended | Mitigated | Ratio mitigated/baseline |
|---|---|---|---|---|
| p50 |   |   |   |   |
| p90 |   |   |   |   |
| p99 |   |   |   |   |

State the result: which mitigation worked, by how much, and why it
worked in terms of the mechanism (runqueue sharing, priority weight,
or CPU isolation).

### Part D Checklist

- [ ] One mitigation applied
- [ ] Mitigated percentiles compared to baseline and contended
- [ ] Mechanism of the mitigation explained

## Deliverables

Submit:

1. **`report.md`** — the narrative. For each part: what you did, the
   numbers, and the mechanism explanation. Include a table showing
   p50/p90/p99 across baseline / contended / mitigated.
2. **`baseline.csv`**, **`contended.csv`**, **`mitigated.csv`** —
   raw percentile data.
3. **Commands used** — copy/paste the exact command lines so a
   grader can reproduce the experiment.
4. **Mechanism paragraph** — one or two paragraphs stating:
   contention → shared runqueue → wakeup-to-run delay → p99
   inflation; mitigation interrupts which step of that chain.

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

## Grading Rubric

| Criterion | Points |
|---|---|
| Correct baseline + contended percentiles, with enough samples (≥10 000) | 30 |
| Supporting OS signal collected and interpreted | 25 |
| One mitigation applied; before/after comparison clear | 25 |
| Mechanism explanation ties numbers to runqueue delay | 20 |

**Total: 100 points.**

## Common Pitfalls

- **Too few samples.** Fewer than 10 000 samples and p99 is one
  outlier. 20 000 is the minimum in this lab.
- **Not pinning.** If the probe and hog end up on different CPUs,
  you will not see contention. Use `--cpu 0` on both — and verify
  with `taskset -p <pid>` if in doubt.
- **VM host noise.** Results on a laptop can swing widely. Close
  other applications; run on AC power; repeat to see variance.
- **Reporting averages.** "Mean latency doubled" is a weak claim.
  "p99 went from 200 µs to 30 ms" is the claim that matters.

## Troubleshooting

- **`perf stat` prints `<not supported>`.** Your VM does not expose
  the PMU. Use `/proc/<pid>/sched` or `/proc/schedstat` instead.
- **Probe already has high p99 on baseline.** The host is busy.
  Close browser tabs, disable Spotlight or its equivalent, retry.
- **Python scripts disagree on percentiles.** Make sure every CSV
  has exactly one sample per line and the iteration count is
  correct.

## Reference: Useful Commands

```bash
taskset -c 0 ./wakeup_lat ...       # pin to CPU 0
taskset -p <pid>                    # show current affinity
nice -n 19 ./cpu_hog ...            # lowest priority
renice 10 -p <pid>                  # change priority of running pid
cat /proc/<pid>/sched                # per-task scheduler stats
cat /proc/schedstat                  # system-wide scheduler stats
sudo perf stat -e context-switches,cpu-migrations ./prog
```
