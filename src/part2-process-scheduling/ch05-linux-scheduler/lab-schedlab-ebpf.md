# Lab: SchedLab — eBPF Scheduler Tracing

> **Estimated time:** 4–5 hours
>
> **Prerequisites:** Chapter 5 concepts (CFS/EEVDF, tracepoints,
> eBPF); Linux kernel 5.15+ with BTF enabled
>
> **Tools used:** libbpf, clang, bpftool, bpftrace, `stress-ng`,
> Python 3 (percentile script)

## Objectives

- Build and run an eBPF-based scheduler observation tool
- Measure scheduling latency distributions under idle and loaded
  systems
- Compare CFS fairness by running tasks with different nice values
- Quantify the observer effect of eBPF tracing (optional)

## Background

SchedLab is a small libbpf-based tool that attaches to
`sched:sched_wakeup` and `sched:sched_switch` and emits per-event
scheduling data. Source lives in `code/ch05-schedlab/`. The BPF
program is less than 100 lines; the user-space loader a few hundred.
Three modes:

- `--mode stream` — print all scheduler events (noisy; for sanity
  checks).
- `--mode latency` — measure wakeup-to-run latency and write CSV.
- `--mode fairness` — accumulate per-task run time and wait time.

## Prerequisites

```bash
sudo apt update
sudo apt install -y clang llvm libbpf-dev bpftool bpftrace \
  linux-headers-$(uname -r) stress-ng

# BTF must exist (CO-RE depends on it):
ls /sys/kernel/btf/vmlinux

# Kernel version (for your report):
uname -r
```

Verify bpftrace runs at all:

```bash
sudo bpftrace -e 'BEGIN { printf("eBPF works!\n"); exit(); }'
```

If this fails, fix permissions or missing packages before continuing.
Everything below depends on it.

### Build SchedLab

```bash
cd code/ch05-schedlab
./scripts/gen_vmlinux.sh     # one-time; generates vmlinux.h
make clean && make

# Sanity: stream a few seconds of scheduler events.
sudo ./schedlab --mode stream --duration 5
```

You should see a burst of switch and wakeup events scroll past. If
you do not, either BTF is unavailable or tracepoints are somehow
disabled; re-run the verification block above.

### Fallback: bpftrace-only path

If the libbpf toolchain does not build (missing headers, old clang,
BTF issues), you can complete Parts A–C using **bpftrace one-liners
only**. The lab handout marks each section with the bpftrace
alternative. You must note in your report that you used the
fallback, and your mechanism explanations are graded identically.

The core measurement is:

```bpftrace
sudo bpftrace -e '
  tracepoint:sched:sched_wakeup { @ts[args->pid] = nsecs; }
  tracepoint:sched:sched_switch / @ts[args->next_pid] / {
      $d_us = (nsecs - @ts[args->next_pid]) / 1000;
      @lat_us = hist($d_us);
      delete(@ts[args->next_pid]);
  }
  interval:s:20 { exit(); }
'
```

This gives you a histogram directly. For CSV output, pipe through
`bpftrace -f json` and post-process with the scripts in
`code/ch05-schedlab/scripts/`.

## Part A: Build and Baseline (Required)

**Goal:** Establish the scheduling-latency distribution on an idle
system.

Collect 20 seconds of latency data while the system is otherwise
quiet:

```bash
sudo ./schedlab --mode latency --duration 20 --output latency_idle.csv
python3 scripts/percentiles.py latency_idle.csv
```

Record:

| Percentile | Latency (µs) |
|---|---|
| p50 |   |
| p90 |   |
| p99 |   |
| p99.9 |   |

Also record the number of samples. For a busy desktop you will see
tens of thousands of events in 20 seconds; for a very quiet VM, the
counts may be low enough to worry about statistical significance.
If you have fewer than ~5 000 samples, extend the duration.

### Part A Checklist

- [ ] SchedLab built successfully
- [ ] Ran `--mode stream` and saw plausible events
- [ ] Collected 20 s of idle-system latency
- [ ] Percentiles computed, environment documented (kernel,
      VM/bare metal, host load)

## Part B: Loaded System (Required)

**Goal:** Observe how CPU load inflates the scheduling-latency tail.

In one terminal, start a CPU-bound workload:

```bash
stress-ng --cpu 4 --timeout 30s &
```

In another, collect latency data for the same duration:

```bash
sudo ./schedlab --mode latency --duration 20 \
  --output latency_loaded.csv
python3 scripts/percentiles.py latency_loaded.csv
```

**bpftrace fallback:** run the histogram one-liner from the
Prerequisites section while `stress-ng` is running. Compare the
histogram shape to your idle run.

Compare:

| Percentile | Idle (µs) | Loaded (µs) | Ratio |
|---|---|---|---|
| p50 |   |   |   |
| p90 |   |   |   |
| p99 |   |   |   |
| p99.9 |   |   |   |

The tail should inflate noticeably. On a 4-core VM with
`--cpu 4`, the runqueue is saturated and p99 typically grows an
order of magnitude.

### Interpret the result

Two paragraphs in your report:

1. **Mechanism.** Which step of the wakeup-to-run path (Chapter 5
   §5.2) is taking longer under load? In a 4-CPU system with 4 extra
   CPU-bound tasks, the most likely answer is "enqueue picks a busy
   CPU; the task waits for the current hog's quantum".
2. **Evidence.** What in the distribution supports that answer?
   A growing median (all wakeups pay a bit of queue wait) points to
   systemic runqueue pressure; a sharp tail with unchanged median
   points to rare events (migrations, cross-CPU wakeups, or brief
   interrupts).

### Part B Checklist

- [ ] Data collected under CPU load
- [ ] Side-by-side comparison with idle
- [ ] Mechanism paragraph tied to the wakeup-to-run path

## Part C: Fairness Analysis (Required)

**Goal:** Verify that CFS/EEVDF allocates CPU time proportional to
weight.

Launch two CPU hogs with different nice values. A good minimal test:

```bash
nice -n 0  stress-ng --cpu 1 --timeout 30s &
nice -n 10 stress-ng --cpu 1 --timeout 30s &
```

Collect fairness data:

```bash
sudo ./schedlab --mode fairness --duration 20 \
  --output fairness.csv
python3 scripts/fairness.py fairness.csv
```

**bpftrace fallback:** use the per-comm runtime tracker:

```bpftrace
sudo bpftrace -e '
  tracepoint:sched:sched_switch {
      @runtime[args->prev_comm] = sum(
          (nsecs - @on[args->prev_pid]) / 1000000);
      @on[args->next_pid] = nsecs;
  }
  interval:s:20 { exit(); }
'
```

Compare the `@runtime` values for `stress-ng` processes with
different nice values.

`fairness.csv` contains per-task `run_time_ns` and `wait_time_ns`.
Compute the CPU share for each task:

```text
share = run_time / (run_time + wait_time)
```

Expected: the `nice=0` task gets roughly `1024 / (1024 + 110) ≈ 90 %`
of the CPU, the `nice=10` task about 10 %. Real numbers will wander a
few percent either way because of bookkeeping, interrupts, and other
runnable tasks on the system.

### Your report should answer

1. Did CFS allocate time proportional to weight? Cite the expected
   ratio from Section 5.1's weight table.
2. If there is a discrepancy, what is plausibly causing it?
   (Interrupts? Migrations across CPUs? Background processes?)
3. If you repeat with `nice=0` vs `nice=19`, does the ratio still
   match the weight table?

### Part C Checklist

- [ ] Two tasks with different nice values
- [ ] Shares computed from `schedlab --mode fairness`
- [ ] Comparison to the theoretical weight ratio
- [ ] At least one experiment with a second nice value

## Part D: Observer Overhead (Optional)

**Goal:** Quantify the cost of eBPF tracing itself.

Pick a workload with a known cost — e.g. `./wakeup_lat` from Chapter
4's lab or `stress-ng --cpu 1 --timeout 20s`. Run it three times:

1. Without tracing.
2. With `schedlab --mode latency` running in the background.
3. With `schedlab --mode stream` running in the background (the
   expensive mode; ring-buffer per event, no aggregation).

Record wall time and, if possible, total context-switch count from
`perf stat -e context-switches`. Compute the overhead:

```text
overhead (%) = (runtime_with_tracing - runtime_baseline) / runtime_baseline
```

Expected: `--mode latency` costs a few percent at most. `--mode
stream` can cost substantially more — sometimes double-digit percent
— on a busy system.

### Part D write-up

One paragraph:

- What workload did you use?
- What was the overhead for each tracing mode?
- Which source of overhead (hot path, map ops, event emission) is
  most likely responsible?

## Deliverables

Submit:

1. **`report.md`** — the narrative. For Parts A–C each: what you
   ran, the numbers, the mechanism explanation. Part D if
   attempted.
2. **`latency_idle.csv`**, **`latency_loaded.csv`**,
   **`fairness.csv`** — raw data.
3. **Environment block** — kernel version, CPU model, VM / bare
   metal, host load conditions, and the exact `schedlab`
   command lines.
4. **Distribution plot** (Parts A + B) — histogram or CDF of
   idle vs loaded; percentile lines overlaid.

## Grading Rubric

| Criterion | Points |
|---|---|
| SchedLab builds and runs; baseline percentiles collected | 25 |
| Loaded-system percentiles; distribution compared | 20 |
| Fairness analysis with nice-value ratio and interpretation | 25 |
| Mechanism explanation ties numbers to wakeup→run path | 20 |
| Plot included and properly labeled | 10 |
| **Optional** observer-overhead analysis | +10 bonus |

**Total: 100 (+ 10 bonus).**

## Common Pitfalls

- **Map entry loss.** A task that wakes twice before running has its
  first wakeup timestamp overwritten. Short runs and filtered probes
  avoid this; long unfiltered runs will lose some events.
- **PID reuse.** Over long traces the kernel reuses PIDs. For
  rigorous work, key on `(pid, start_time)` rather than `pid`
  alone.
- **`--mode stream` overload.** Ring-buffered events at scheduler
  rates can produce megabytes per second and distort the very
  latency you are measuring. Use it for debugging, not for data
  collection.
- **VM host noise.** The same concern as Chapter 4's lab — close
  other applications and repeat to see variance. Scheduler
  tracepoints work in VMs, but the host can still preempt your
  guest underneath.

## Troubleshooting

- **`BTF not found` / build failure.** Your kernel lacks BTF.
  `cat /boot/config-$(uname -r) | grep BTF` should show
  `CONFIG_DEBUG_INFO_BTF=y`. If not, switch to a kernel that has it
  (Ubuntu 22.04's default does).
- **`Operation not permitted`.** eBPF requires root. Use `sudo`.
- **Empty event stream.** Sanity check with
  `sudo bpftrace -l 'tracepoint:sched:*'`. If tracepoints are
  missing, something has disabled ftrace.
- **Wildly different numbers between runs.** Expected — scheduler
  latency is noisy. Report medians across repeated runs if single
  runs are unstable.

## Reference: Useful Commands

```bash
sudo bpftrace -l 'tracepoint:sched:*'              # list probes
sudo bpftrace -lv tracepoint:sched:sched_switch    # field layout
sudo bpftool prog                                   # loaded BPF programs
sudo bpftool map                                    # BPF maps
sudo ./schedlab --help                              # tool usage
```

## Appendix: The Recipe, Distilled

```bpftrace
tracepoint:sched:sched_wakeup {
    @ts[args->pid] = nsecs;
}
tracepoint:sched:sched_switch / @ts[args->next_pid] / {
    $d_us = (nsecs - @ts[args->next_pid]) / 1000;
    @lat_us = hist($d_us);
    delete(@ts[args->next_pid]);
}
```

Run that, generate some load, and you have reproduced the core
measurement of this lab in two stanzas. SchedLab is the same idea
with stable CSV output and a user-space percentile script.
