# Lab: Quicksort Performance Analysis

> **Estimated time:** 3–4 hours
>
> **Prerequisites:** Chapter 2 concepts; working Ubuntu VM with
> `gcc`, `perf`, and `valgrind`
>
> **Tools used:** `perf stat`, Valgrind (`cachegrind`, `callgrind`,
> `massif`), `gcc`, `make`, `/usr/bin/time`

## Objectives

- Measure how input pattern (random, sorted, reverse, nearly-sorted)
  affects quicksort performance
- Use `perf stat` (or Valgrind as a fallback) to observe IPC, cache
  miss rates, and branch miss rates
- Find the input size at which quicksort transitions from CPU-bound
  to memory-bound
- Practice the measurement discipline from the chapter: hypothesis,
  one variable, baseline, rate not count

## Background

Quicksort is familiar, and its cost structure is rich enough to
exercise every mechanism in Chapter 2. Its running time depends on
pivot selection (which turns worst-case inputs into O(n²) behavior),
on cache locality (the partition step streams the array), and on
branch prediction (the comparison inside the partition is the tight
inner branch). Different input patterns stress different mechanisms,
so the same code can be fast or slow for reasons that look nothing
alike in the counter output.

Source code and starter datasets live in `code/ch02-quicksort/`.

> **VM note:** Hardware PMU events (`cycles`, `cache-misses`,
> `branch-misses`) are frequently unavailable in VirtualBox and
> VMware guests. If `perf stat` prints `<not supported>` or zero for
> these events, use the Valgrind fallback described below. Keep the
> `perf` commands in your write-up either way.

## Prerequisites

Verify your tools:

```bash
gcc --version
perf --version       # may need sudo
valgrind --version
```

If anything is missing:

```bash
sudo apt update
sudo apt install -y build-essential linux-tools-common \
  linux-tools-$(uname -r) valgrind
```

## Part A: Quicksort Warm-up (Required)

**Goal:** Get familiar with the profiling tools and collect baseline
numbers for four input patterns.

### A.1 Build

```bash
cd code/ch02-quicksort
make clean
make
```

### A.2 Generate Datasets

The starter `Makefile` supports `make datasets N=...`. You can also
generate them by hand:

```bash
shuf -i 1-100000 -n 100000 > datasets/random_100000.txt
seq 1 100000 > datasets/sorted_100000.txt
seq 100000 -1 1 > datasets/reverse_100000.txt
seq 1 100000 | awk -v N=100000 'BEGIN{srand()} \
  {if (rand() < 0.1) print int(rand()*N)+1; else print}' \
  > datasets/nearly_sorted_100000.txt
```

### A.3 Time Each Input Three Times

```bash
for DS in random sorted reverse nearly_sorted; do
    for i in 1 2 3; do
        /usr/bin/time -f "%e" ./qs datasets/${DS}_100000.txt
    done
done
```

### A.4 Collect Hardware Counters (or Valgrind Equivalents)

Preferred, if `perf` supports the events:

```bash
sudo perf stat -e cycles,instructions,cache-references,\
cache-misses,branches,branch-misses -r 3 \
  ./qs datasets/random_100000.txt
```

Fallback when counters are unavailable:

```bash
valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
  --cachegrind-out-file=outputs/cg_random.out \
  ./qs datasets/random_100000.txt
```

Read `D refs`, `D1 misses`, `LLd misses`, `Branches`, `Mispredicts`
from the cachegrind output. Convert to rates.

### A.5 Fill the Table

| Dataset | Run 1 (s) | Run 2 (s) | Run 3 (s) | Mean | Cache miss rate | Branch miss rate |
|---|---|---|---|---|---|---|
| random_100000 |   |   |   |   |   |   |
| sorted_100000 |   |   |   |   |   |   |
| reverse_100000 |   |   |   |   |   |   |
| nearly_sorted_100000 |   |   |   |   |   |   |

### A.6 Two- or Three-sentence Explanation

Answer:

1. Which input is slowest? By roughly how much?
2. Does the branch miss rate explain the slowdown?
3. Does the cache miss rate explain it?

The expected story: the sorted input triggers worst-case pivot
behavior in textbook quicksort, so the algorithm itself degrades
toward O(n²). The cycle and instruction counts climb steeply; the
cache miss rate often stays comparable to random. That is a case
where the mechanism is algorithmic, not hardware — and you should be
able to say so in one sentence.

### A.7 Part A Checklist

- [ ] Built the quicksort program
- [ ] Generated all four dataset patterns
- [ ] Timed each input three times
- [ ] Collected `perf stat` or cachegrind data
- [ ] Wrote a short explanation of the slowest case

## Part B: Finding the CPU→Memory Transition (Required)

**Goal:** Identify the input size at which quicksort moves from
CPU-bound to memory-bound, and explain the mechanism.

### B.1 Write Your Hypothesis First

Before running anything, record:

1. Your L3 cache size:

   ```bash
   lscpu | grep "L3 cache"
   cat /sys/devices/system/cpu/cpu0/cache/index3/size  # alternate
   ```

2. At 4 bytes per integer, how many integers fit in L3?
3. At what `N` do you expect cache miss rate to climb?
4. At what `N` do you expect IPC to drop?

Write this down *before* seeing the data. Part of the grade is that
you committed to a hypothesis.

### B.2 Experiment

```bash
for N in 1000 5000 10000 20000 50000 100000 200000 500000 1000000; do
    shuf -i 1-$N -n $N > datasets/random_$N.txt
done

for N in 1000 5000 10000 20000 50000 100000 200000 500000 1000000; do
    echo "=== N = $N ==="
    sudo perf stat -e cycles,instructions,cache-references,\
cache-misses -r 3 ./qs datasets/random_$N.txt
done
```

VM fallback (cachegrind):

```bash
for N in 1000 5000 10000 20000 50000 100000 200000 500000 1000000; do
    echo "=== N = $N ==="
    valgrind --tool=cachegrind --cache-sim=yes --branch-sim=no \
      --cachegrind-out-file=outputs/cg_${N}.out \
      ./qs datasets/random_$N.txt 2>&1 | \
      egrep "D\s+refs|D1\s+misses|LLd\s+misses"
    /usr/bin/time -f "%e" ./qs datasets/random_$N.txt
done
```

### B.3 Collect the Data

| N | Wall time (s) | Cycles | Instructions | IPC | Cache refs | Cache misses | Miss rate |
|---|---|---|---|---|---|---|---|
| 1,000 |   |   |   |   |   |   |   |
| 5,000 |   |   |   |   |   |   |   |
| 10,000 |   |   |   |   |   |   |   |
| 20,000 |   |   |   |   |   |   |   |
| 50,000 |   |   |   |   |   |   |   |
| 100,000 |   |   |   |   |   |   |   |
| 200,000 |   |   |   |   |   |   |   |
| 500,000 |   |   |   |   |   |   |   |
| 1,000,000 |   |   |   |   |   |   |   |

### B.4 Plot

Plot two curves on a log-x axis: wall time vs `N`, and cache miss
rate vs `N`. Mark the `N` at which miss rate climbs sharply. Mark the
`N` at which IPC drops below 1.

### B.5 Write-up (1–2 pages)

Your report should answer:

1. **Hypothesis.** What did you predict, and why? Include your L3
   size and the math.
2. **Design.** Which `N` values did you pick, and why? How many
   repeats, and how did you handle variance?
3. **Results.** The table above, plus at least one plot. Include the
   environment (CPU, kernel, VM config).
4. **Interpretation.** Was your hypothesis correct? If the transition
   happened at a different `N` than predicted, why? (L2 vs L3? Extra
   overhead from the recursion stack? Partitioning overhead?)
5. **Surprise.** One sentence on anything you did not expect.

### B.6 Part B Checklist

- [ ] Wrote hypothesis before running experiments
- [ ] Generated datasets across a wide range of `N`
- [ ] Collected metrics with three repeats per `N`
- [ ] Computed IPC and miss rate
- [ ] Plotted the results
- [ ] Identified the transition and explained the mechanism

## Part C: Your Own Workload (Optional)

Choose one:

### Option 1: Profile a Standard Tool

Pick `sort`, `grep`, `wc`, or `gzip`. Profile it on a large file:

```bash
yes "the quick brown fox jumps over the lazy dog" | head -1000000 \
  > testfile.txt
sudo perf stat sort testfile.txt > /dev/null
sudo perf stat grep "fox" testfile.txt > /dev/null
sudo perf stat wc testfile.txt
```

Answer: is it CPU-bound or memory/IO-bound? What is the IPC? Which
counter best explains its cost?

### Option 2: Cache-Friendly vs Cache-Unfriendly

Write the row-major and column-major sums from Section 2.2, measure
both at several matrix sizes, and find the `N` at which the gap
becomes significant. Explain the mechanism (cache line size vs row
stride).

### Option 3: Profile Your Own Code

Pick one function in a project you care about. Isolate it into a
benchmark, run `perf stat` and `perf record`, identify the
bottleneck, and connect it to a mechanism from Chapter 2.

### Part C Write-up (1 page)

State what you profiled, which metrics you collected, what you found,
and which Chapter 2 mechanism explains the result.

## Submission

Submit a single PDF or Markdown report containing:

1. **Part A Results** (~1 page) — data table and short explanation
2. **Part B Analysis** (1–2 pages) — hypothesis, design, results,
   interpretation, surprise
3. **Part C Extension** (1 page, if completed) — workload, metrics,
   findings, mechanism

Use `templates/lab-report-template.md` as a starting point.

## Grading Rubric

| Criterion | Points |
|---|---|
| **Part A (30)** | |
| Data collected correctly, multiple runs | 15 |
| Correct explanation of worst-case input | 15 |
| **Part B (60)** | |
| Clear hypothesis stated before experiments | 10 |
| Sound experiment design | 15 |
| Data collected and presented clearly | 15 |
| Interpretation connects numbers to a mechanism | 20 |
| **Part C (10 bonus)** | |
| Meaningful analysis of a new workload | 10 |

**Total: 90 points (+ 10 bonus).**

## Common Pitfalls

1. **Single run, single number.** Variance is large; three runs
   minimum.
2. **Miss *count* vs miss *rate*.** A bigger dataset has more
   accesses and therefore more misses. Report the rate.
3. **Cold cache on first run.** Throw out the first run or warm up
   with a dry run.
4. **Counters read as `<not supported>`.** Do not try to interpret
   zeros. Switch to cachegrind and note the change in your write-up.
5. **No mechanism in the explanation.** "Cache misses slowed it down"
   is not a mechanism — *why* did misses appear (working set > cache?
   bad stride? pointer chasing?) is the mechanism.

## Troubleshooting

- **`perf` refuses to run.** Use `sudo`, or set
  `sudo sysctl kernel.perf_event_paranoid=-1` for this session only
  on your own VM.
- **Valgrind writes "Permission denied".** An earlier `sudo` run left
  root-owned output files. Use `--cachegrind-out-file=outputs/cg_%p.out`
  to send output somewhere you own.
- **Noisy results.** Close other applications; pin the governor:
  `sudo cpupower frequency-set --governor performance`.

## Reference: perf Commands

```bash
sudo perf stat ./program
sudo perf stat -e cycles,instructions,cache-misses,branch-misses ./program
sudo perf stat -r 5 ./program
sudo perf record -g ./program && sudo perf report
perf list      # all available events
```
