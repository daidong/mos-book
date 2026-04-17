# Chapter 13: Systems Research Methodology and Reproducibility

> **Learning objectives**
>
> After completing this chapter, you will be able to:
>
> - Design a systems experiment that isolates the variable you
>   actually care about from the ones you do not
> - Apply the evidence contract introduced in Chapter 3 — two
>   independent signals plus one exclusion check — to any
>   performance or correctness claim in your own work
> - Produce a reproducibility artifact (code, data, configuration,
>   and script) that lets a peer reproduce your result from
>   scratch
> - Review a peer's artifact the way a program committee would:
>   does the code run, does it reproduce the claim, are the
>   claims actually supported by the evidence?

Twelve chapters of mechanisms. This one is about the habits that
outlast any specific mechanism. Every technology in this book —
cgroups, Raft, eBPF, agent runtimes — will someday be superseded
by something else. The discipline of matching a claim to
evidence, and the discipline of writing results so a stranger
can reproduce them, will not. This chapter names those
disciplines explicitly and gives you the tools to apply them to
your own projects.

## 13.1 What Makes a Systems Experiment

A systems experiment is a *controlled comparison*. The only
claims it can legitimately support are of the form "under
condition A versus condition B, this metric changed by that
much, because of this mechanism". Three variables:

- **Independent variable.** The thing you change. It has to be
  *one* thing. Memory limit, scheduler, fsync policy, input
  size, anything.
- **Dependent variable.** The thing you measure. Throughput, p99
  latency, context-switch count, error rate.
- **Controlled variables.** Everything else. Hardware, kernel
  version, compiler, workload pattern, ambient temperature,
  time of day, the moon.

An experiment fails when a controlled variable was not actually
controlled. You changed the workload pattern between runs; you
upgraded the kernel halfway through; Turbo Boost kicked in
during the afternoon. The result becomes uninterpretable.

A practical checklist, adapted from Chapter 2 and refined by
every lab since:

1. **State the hypothesis before running.** "Raising
   `memory.max` from 512 Mi to 1 Gi will reduce p99 from ~80 ms
   to ~5 ms, because `pgmajfault` will return to baseline."
2. **Pick a baseline.** What are you comparing against? "Before
   the change." "With the default scheduler." "Single-node."
3. **Design the treatment.** Change exactly one thing.
4. **Control noise.** Same machine, same kernel, pin CPU
   governor, warm up, repeat at least three times, report the
   variance.
5. **Plan the analysis in advance.** Which metrics? Which
   percentiles? Which plots? If you decide after the data is in,
   the temptation to cherry-pick is strong.
6. **Write down what would falsify the hypothesis.** A good
   experiment can be wrong. If yours cannot, it is not an
   experiment; it is a confirmation.

## 13.2 The Evidence Contract

Chapter 3 introduced the evidence contract. It applies from
Chapter 3 to here; here is the version to carry forward.

> Every performance or correctness claim needs **two independent
> supporting signals** plus **one exclusion check** that rules
> out a plausible alternative.

Examples of what it looks like in practice, distilled from the
labs:

- Claim: "The p99 spike came from major faults."
  - Signal 1: `pgmajfault` climbed 10× during the spike window.
  - Signal 2: `/usr/bin/time -v` reported matching major faults
    per process.
  - Exclusion: `iostat %util` was flat — rules out disk
    saturation from some other workload.

- Claim: "The scheduler starved our probe under load."
  - Signal 1: Probe p99 inflated from 200 µs to 30 ms under
    contention.
  - Signal 2: `perf stat -e context-switches` tripled.
  - Exclusion: `cpu.stat:nr_throttled` on the probe's cgroup
    was zero — rules out CFS bandwidth throttling.

- Claim: "Raft's quorum survived the leader failure."
  - Signal 1: `etcdctl endpoint status` showed a new leader
    within 2 seconds of the kill.
  - Signal 2: A sustained-write client saw ≤ 1 s of failures
    and resumed.
  - Exclusion: No writes were committed to the dead leader —
    confirmed by inspecting the WAL on the restarted node.

What "independent" means here is a live question. Two readings
from the same counter are not independent; an application-level
timer and a kernel counter *are* independent. The rule of thumb:
if the two signals could be explained by the same measurement
bug, they are not independent.

### Why the exclusion matters

Without an exclusion, a claim with two supporting signals is
still vulnerable to a confounder. "p99 rose and disk was busy" is
consistent with several stories: maybe disk caused the p99, or
maybe something else caused both. The exclusion — "CPU was not
saturated", "the change was not a config reload", "the
background scrub was not running" — actively argues against a
plausible rival hypothesis. The signal count is a measure of
support; the exclusion is a measure of rigor.

## 13.3 Reproducibility Standards

A reproducible artifact lets a stranger, starting with only a
working laptop, reproduce your result. "Reproducible" is not
"I can run it on my machine"; it is "someone who has never met
me can run it and get the same answer".

At minimum, your artifact provides:

- **Exact versions.** OS, kernel, compilers, runtimes,
  libraries, tools. Pin everything. If you used a container,
  commit the image digest, not just the tag.
- **Environment script.** `setup.sh`, `Dockerfile`, or an
  Ansible playbook that produces the environment from a clean
  base. No manual steps. No "also install X if needed".
- **Raw data.** Every CSV, trace, and log your figures derive
  from. A plot without raw data is a claim without evidence.
- **Analysis scripts.** The code that turns raw data into every
  number and figure. `python3 analyze.py data/ > results.csv`,
  `gnuplot plot.gp > figure3.png`. No hand-edits.
- **README.** For each claim in the paper/report, state: "To
  reproduce Figure N, run `command X`. Expected runtime: Y.
  Expected output: Z."

### ACM artifact badging

The ACM artifact review process uses four badges:

- **Available.** The artifact is publicly downloadable.
- **Functional.** It compiles, runs, and produces something.
- **Reusable.** It is documented, extensible, and reasonable to
  modify.
- **Reproduced.** An independent reviewer re-ran it and got the
  same result.

Aim for Reusable at minimum. Reproduced is the benchmark.

### Containers, VMs, and the reproducibility ladder

Ordered from least to most reproducible:

1. "Run these commands on your Ubuntu machine."
2. A `Dockerfile` and a container.
3. A `docker-compose.yml` or Kubernetes manifest that brings up
   the whole stack.
4. A full VM image or cloud-provider snapshot.
5. A deterministic replay trace (for measurements that depend on
   timing, record the entire run and replay it later).

Higher rungs cost more upfront and pay off when the artifact
outlives the author. A grad student's Dockerfile from five years
ago still runs. A grad student's machine from five years ago
does not.

## 13.4 Common Pitfalls

Ten failures this book has taught you to recognize, in rough
order of how often they appear in student (and production) work:

1. **Cold vs warm caches.** The first run of any experiment is
   slower because caches are empty. Either warm up or throw out
   the first run.
2. **Measurement overhead changes what you measure.** eBPF on
   every context switch distorts the scheduler. Aggregate
   in-kernel, filter early.
3. **Turbo frequency and thermal throttling.** A desktop CPU
   can boost to 5 GHz for a few seconds and drop to 3 GHz when
   hot. Pin the governor, disable Turbo if you can.
4. **CPU affinity, NUMA, IRQ steering.** Migrations destroy
   cache locality. `taskset -c 0` is cheap insurance.
5. **Noisy neighbors.** Other processes, other VMs, other
   tenants. Close browsers, run on a dedicated node, or
   explicitly quantify the noise.
6. **Background kernel work.** `kworker`, writeback, RCU, TLB
   shootdowns. Check `top` before starting; investigate any
   process you did not expect.
7. **p50 hides the tail.** A system can have perfect p50 and
   catastrophic p99. Always report percentiles; never report
   only the mean.
8. **Small sample sizes.** 100 samples gives you one p99 data
   point. Ten thousand is the minimum.
9. **Cherry-picked runs.** "The runs I liked". Pre-register the
   analysis; publish all runs; report outliers separately.
10. **Overclaiming.** A 5 % speedup across five runs with 3 %
    variance is not a 5 % speedup. State the variance and let
    the reader judge.

Read Heiser's *Systems Benchmarking Crimes* once a year. It is
a short, honest list.

## 13.5 Peer Review as a Systems Skill

Reviewing other people's work makes you better at your own.
A simple review procedure:

1. **Read the abstract.** Write down, in your own words, what
   claims it makes. Be specific: "X is N× faster than Y under
   workload Z."
2. **For each claim, find the evidence.** Is there a figure?
   Cite it. Are the axes labeled? Is the sample size stated?
3. **Apply the evidence contract.** Are there two independent
   signals? Is there an exclusion?
4. **Try to reproduce the headline number.** If the artifact is
   public, run it. If it is not, note that fact in the review.
5. **Identify one missing piece.** What would strengthen the
   claim most? "Compare against the default scheduler", "report
   variance across five runs", "add an `iostat` cross-check".

For this book's final project, students reproduce each other's
experiments. The reproduction-report template is in
`templates/reproduction-report-template.md`. The act of
reproducing someone else's work is often more instructive than
doing your own — you discover every implicit assumption the
author forgot to write down.

## 13.6 From Student to Practitioner

The mechanisms in this book will change. Schedulers will get
new policies; consensus protocols will evolve; agent runtimes
will look completely different in five years. The habits should
not:

- **Every claim gets a number.** "Slow" and "fast" are
  negotiations; numbers are evidence.
- **Every number gets a mechanism.** A number without a
  mechanism is a fact without an explanation. Facts without
  explanations do not transfer to new systems.
- **Every result gets a reproducibility artifact.** Including
  for yourself three months later.
- **Every review applies the evidence contract.** Including to
  your own drafts.

The combination of those habits is what the professional
community calls *engineering judgment*. It is not something one
course teaches in twelve weeks — but twelve weeks is enough to
install the habit, and the habit compounds for the rest of a
career.

The book ends where it began: understand, measure, explain.
Every chapter has been an exercise in all three. The labs put
numbers on the mechanisms. The final project puts *your*
numbers on a mechanism you chose. Do enough of that, and you
will find that every apparently novel system you meet decomposes
into pieces you already know how to measure.

## Summary

Key takeaways from this chapter and the book:

- A systems experiment isolates one variable, uses a clear
  baseline, runs multiple trials, and reports variance.
- The evidence contract — two independent signals plus one
  exclusion check — is the through-line from Chapter 3 to here.
  It is the habit that transfers most durably to practice.
- Reproducibility is a gift to your future self and to the
  community; the artifact almost always costs less to build up
  front than to reconstruct later.
- Peer review is the mirror image of doing your own work. Apply
  the evidence contract to other people's claims *and* your
  own; the habit compounds.
- Systems come and go — fsync, Raft, cgroups, agents. Disciplined
  measurement and honest reporting do not.

## Further Reading

- Heiser, G. *Systems Benchmarking Crimes.*
  <https://www.cse.unsw.edu.au/~gernot/benchmarking-crimes.html>
- ACM Artifact Review and Badging.
  <https://www.acm.org/publications/policies/artifact-review-and-badging-current>
- Collberg, C. & Proebsting, T. A. (2016). *Repeatability in
  computer systems research.* CACM 59(3).
- Jain, R. (1991). *The Art of Computer Systems Performance
  Analysis.* Wiley. (Dated but still the best single reference.)
- Claerbout, J. (1992). *Electronic documents give reproducible
  research a new meaning.* (One of the earliest calls for
  reproducibility in computational science.)
- Donoho, D. L. (2010). *An invitation to reproducible
  computational research.* Biostatistics 11(3).
