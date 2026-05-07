# Lab: Quicksort Performance Analysis

> **Estimated time:** 4–5 hours
>
> **Prerequisites:** Chapter 2 concepts; Ubuntu environment from Lab 0
>
> **Tools used:** `/usr/bin/time -v`, `perf stat`, `/proc`, optional cgroup
> files, Valgrind (`cachegrind`, `callgrind`, optional `massif`), `gcc`,
> `make`

## Objectives

- Compare quicksort behavior across multiple input patterns and input sizes
- Use counters to distinguish "the program did more work" from "the same
  work ran less efficiently"
- Estimate where the working set crosses cache and translation boundaries,
  then test the estimate against measurements
- Use OS-visible signals such as maximum resident set size, minor faults,
  major faults, and cgroup or `/proc` memory counters when available
- Produce a report that includes original raw artifacts, one explicit
  alternative explanation, and a mechanism-level conclusion

## Background

Quicksort is familiar enough that you can focus on measurement rather than on
learning a new application. It is also rich enough to expose several failure
modes at once: algorithmic imbalance, cache effects, branch behavior,
recursion overhead, and changing working-set size. The point of the lab is
not to memorize a stock story. The point is to argue from evidence.

In Chapter 2, the classical OS question was: does the resident memory cover
the working set? In this lab, the smaller version of that question is: does
the hot data fit in the relevant cache and translation structures, and if it
does not, which signal moves first?

Starter code lives in `code/ch02-quicksort/`.

> **VM note:** In many student VMs, performance-monitoring unit (PMU) events
> such as `cache-misses` and `branch-misses` are unavailable. If `perf stat`
> reports `<not supported>` or zeros for those events, switch to Valgrind and
> say so explicitly in your report.

## Prerequisites

```bash
cd code/ch02-quicksort
make clean
make
make datasets N=100000
```

Verify your toolchain:

```bash
perf --version
valgrind --version
/usr/bin/time --version
```

## Part A: Input Pattern Study (Required)

### A.1 Prediction Before Measurement

Before you run anything, add a **Prediction** section to your report and
answer:

1. Rank `random`, `sorted`, `reverse`, and `nearly_sorted` from fastest to
   slowest.
2. Which mechanism do you think will dominate the slowest case: more total
   work, worse cache locality, worse branch prediction, or something else?
3. Name one alternative explanation you will try to rule out.

You may inspect the source code before predicting, but you may not use any
measurements yet.

### A.2 Build and Run the Four Inputs

```bash
make clean
make
make datasets N=100000

for DS in random sorted reverse nearly_sorted; do
  echo "=== ${DS} ==="
  for i in 1 2 3; do
    /usr/bin/time -f "%e" ./qs datasets/${DS}_100000.txt
  done
done
```

### A.3 Collect Counter Evidence

Preferred path with `perf`:

```bash
for DS in random sorted reverse nearly_sorted; do
  echo "=== ${DS} ==="
  sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
branches,branch-misses -r 3 ./qs datasets/${DS}_100000.txt
done
```

Fallback with Valgrind:

```bash
mkdir -p outputs
for DS in random sorted reverse nearly_sorted; do
  valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
    --cachegrind-out-file=outputs/${DS}.cg.out \
    ./qs datasets/${DS}_100000.txt
done
```

### A.4 Record the Results

| Dataset | Run 1 (s) | Run 2 (s) | Run 3 (s) | Mean (s) | IPC or note | Cache miss rate | Branch miss rate |
|---|---:|---:|---:|---:|---|---:|---:|
| random |  |  |  |  |  |  |  |
| sorted |  |  |  |  |  |  |  |
| reverse |  |  |  |  |  |  |  |
| nearly_sorted |  |  |  |  |  |  |  |

If you used Valgrind, write `Valgrind` instead of IPC and explain the tool
limitation in one sentence.

### A.5 Explain the Slowest Case

Write one short subsection that answers all three questions:

1. Which input was slowest, and by what ratio relative to `random`?
2. Which measurements support your explanation?
3. Which alternative explanation did you rule out, and how?

Do **not** say only "cache misses were high" or "it is O(n^2)." Tie the
claim to the specific evidence you collected.

### A.6 Part A Checklist

- [ ] Prediction written before measurement
- [ ] Four inputs timed three times each
- [ ] Counter evidence collected with `perf` or Valgrind
- [ ] Slowest case explained using at least two signals
- [ ] One alternative explanation explicitly ruled out

## Part B: Predict the Working-Set Boundary (Required)

### B.1 Write the Hypothesis First

Before generating the data, record:

1. your L1, L2, and L3 cache sizes;
2. your base page size;
3. a rough estimate of how many 4-byte integers fit in L2 and L3;
4. the input size `N` at which you expect the cache-miss rate to rise;
5. the input size `N` at which you expect IPC to drop or runtime to bend
   upward;
6. whether you expect minor or major page faults to matter, and why;
7. one reason the observed transition might differ from your estimate.

Helpful commands:

```bash
lscpu | grep -E 'L1d|L2|L3|NUMA'
getconf PAGESIZE
getconf -a | grep CACHE
cat /sys/devices/system/cpu/cpu0/cache/index*/size
```

The estimate does not need to be exact. It must be mechanistic. For example:
"The input array is `4N` bytes, but quicksort also uses recursion and file
I/O buffers. I expect the random input to show a cache-miss-rate increase
somewhere after the array no longer fits in L3, but I do not expect major
faults because the data should remain resident in RAM."

### B.2 Run the Size Sweep

```bash
mkdir -p outputs
for N in 1000 5000 10000 20000 50000 100000 200000 500000 1000000; do
  make datasets N=$N
  echo "=== N = $N ===" | tee outputs/random_${N}.header.txt
  /usr/bin/time -v -o outputs/random_${N}.time.txt \
    ./qs datasets/random_${N}.txt
  sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
page-faults,major-faults -r 3 -o outputs/random_${N}.perf.txt \
    ./qs datasets/random_${N}.txt
done
```

If your machine exposes TLB events, add them after checking the names:

```bash
perf list | grep -i 'dtlb\|itlb'
sudo perf stat -e dTLB-loads,dTLB-load-misses ./qs datasets/random_100000.txt
```

Fallback with Valgrind:

```bash
mkdir -p outputs
for N in 1000 5000 10000 20000 50000 100000 200000 500000 1000000; do
  echo "=== N = $N ==="
  /usr/bin/time -v -o outputs/random_${N}.time.txt \
    ./qs datasets/random_${N}.txt
  valgrind --tool=cachegrind --cache-sim=yes --branch-sim=no \
    --cachegrind-out-file=outputs/random_${N}.cg.out \
    ./qs datasets/random_${N}.txt
done
```

### B.3 Record the Sweep

| N | Wall time (s) | Cycles | Instructions | IPC | Cache misses | Miss rate | Minor faults | Major faults | Max RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 |  |  |  |  |  |  |  |  |  |
| 5,000 |  |  |  |  |  |  |  |  |  |
| 10,000 |  |  |  |  |  |  |  |  |  |
| 20,000 |  |  |  |  |  |  |  |  |  |
| 50,000 |  |  |  |  |  |  |  |  |  |
| 100,000 |  |  |  |  |  |  |  |  |  |
| 200,000 |  |  |  |  |  |  |  |  |  |
| 500,000 |  |  |  |  |  |  |  |  |  |
| 1,000,000 |  |  |  |  |  |  |  |  |  |

If you used Valgrind, replace IPC and hardware-counter fields with the
closest Cachegrind-derived instruction, data-reference, cache-miss, and
branch-miss metrics. Keep the `/usr/bin/time -v` fields.

### B.4 Plot and Interpret

Create at least one plot with `N` on a log-x axis. At minimum, plot wall
runtime and either cache-miss rate or the closest Valgrind-derived miss
metric. If your data include minor faults, major faults, or TLB misses, plot
one of those signals or explain why it stayed flat.

Your write-up must answer:

1. Did the observed transition match your prediction?
2. If not, what is the best mechanism-level explanation?
3. Did the evidence point to cache capacity, translation overhead,
   algorithmic work, page faults, or measurement noise?
4. Which alternative explanation did you consider and reject?

### B.5 Part B Checklist

- [ ] Working-set hypothesis recorded before the sweep
- [ ] Cache/page-size information included
- [ ] Size sweep collected across several orders of magnitude
- [ ] Raw `perf` or Valgrind output plus `/usr/bin/time -v` output saved
- [ ] At least one plot included
- [ ] Transition interpreted with mechanism and evidence
- [ ] Alternative explanation discussed explicitly

## Part C: Extend the Memory-Management Story (Optional)

Choose **one** extension. The extension is optional, but if you attempt it,
you must write a prediction before collecting data and include raw artifacts.

### Option 1: Standard Utility

Profile `sort`, `grep`, `wc`, or `gzip` on a large file. Decide whether the
workload is primarily compute-, memory-, or I/O-limited, and defend the
classification with counters.

### Option 2: Cache-Friendly vs Cache-Unfriendly Access

Write a small program that traverses an array sequentially and then with a
large stride. Measure the difference and explain it with locality.

### Option 3: OS Memory-Management Probe

Run one safe experiment that exposes an OS memory-management signal. Examples:

- compare a small and large input with `/usr/bin/time -v` and explain the
  change in maximum resident set size and minor faults;
- run inside a disposable VM or cgroup with a modest memory limit and record
  `memory.events` and `memory.pressure`;
- use `valgrind --tool=massif` to show heap growth and connect it to the
  working-set estimate.

Do **not** create a swap storm or memory-pressure experiment on a shared host.
If you use a cgroup or VM limit, document how you created it and how you
removed it.

### Option 4: Your Own Code

Pick a program you wrote for another course or project. State one hypothesis
about its bottleneck, test it, and explain the result.

## Submission

Submit a single PDF or Markdown report plus the raw artifacts you used to
support it.

Required files:

| File | Required? | Purpose |
|---|---|---|
| `report.md` or `report.pdf` | Yes | prediction, results, plots, interpretation |
| raw `perf` or Valgrind outputs | Yes | evidence behind every hardware-counter claim |
| raw `/usr/bin/time -v` outputs | Yes | OS-visible evidence: RSS, faults, context switches |
| plot script or notebook | Yes | reproducibility |
| `code/ch02-quicksort` changes, if any | Optional | only if you modified the starter |

Your report must include:

1. the Part A prediction;
2. the Part B working-set hypothesis;
3. cache and page-size information for your machine;
4. at least two tables and one plot;
5. one explicit alternative explanation ruled out in Part A and one in Part B;
6. enough environment detail for another student to reproduce the run.

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
| Prediction quality | 15 | hypotheses are specific and stated before measurement |
| Experimental design | 20 | baselines, repeats, and tool choices are appropriate |
| Evidence quality | 25 | raw outputs, tables, plots, and OS-visible signals support the claims |
| Mechanism depth | 30 | explanation distinguishes work increase, efficiency loss, and memory-management effects |
| Alternative ruled out | 10 | report explicitly rejects at least one plausible competing story |

## Common Pitfalls

- Treating miss **counts** as if they were miss **rates**
- Reporting one run and calling it representative
- Ignoring tool limitations in a VM
- Treating minor page faults as disk I/O
- Claiming a mechanism without citing a signal that actually measures it
- Writing the conclusion first and using the data only as decoration
