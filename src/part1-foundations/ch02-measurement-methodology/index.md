# Chapter 2: Performance Measurement Methodology

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Describe the memory hierarchy (registers, L1/L2/L3, DRAM, disk)
>   and its impact on program performance
> - Explain how CPU caches, TLBs, and branch prediction affect
>   instruction throughput
> - Use `perf stat` to measure IPC, cache-miss rates, and
>   branch-miss rates
> - Design a controlled experiment that isolates a single variable
>   and produces reproducible results

Performance work starts with a discipline: a number is evidence, and a
mechanism is an explanation. A report that says "the program got 2×
faster" without naming what mechanism changed is not a result — it is
an anecdote. This chapter builds the mechanical vocabulary
(hierarchy, caches, TLB, branches) and the measurement vocabulary
(`time`, `perf stat`, Valgrind) that the rest of the book relies on.

## 2.1 The Memory Hierarchy

A modern CPU can retire billions of instructions per second. DRAM,
measured in cycles, is two orders of magnitude slower than the core
that wants to read it. If every memory access went all the way to
DRAM, the CPU would idle for 99 % of its clock. The memory hierarchy
exists to hide that gap.

The hierarchy trades size against speed. Small, fast levels sit close
to the core; large, slow levels sit further away. Typical
order-of-magnitude numbers on a modern server-class CPU look like
this:

| Level | Latency | Typical size | Analogy |
|---|---|---|---|
| Registers | 0 cycles | ~1 KB | Your hands |
| L1 cache (SRAM) | 4 cycles | 32–64 KB per core | Grab book from desk |
| L2 cache | 12 cycles | 256 KB–1 MB per core | Walk to bookshelf |
| L3 cache | 40 cycles | 2–32 MB shared | Walk to next room |
| DRAM | ~200 cycles | 8–128 GB | Drive to library |
| SSD | 50,000+ cycles | 256 GB–4 TB | Order online |
| HDD | 10,000,000+ cycles | 1–20 TB | International shipping |

The exact numbers vary by CPU and workload; the structure does not.
An L1 miss that is served from DRAM is roughly 50× slower than an L1
hit. If that happens inside a tight inner loop, the algorithm may
still be O(N), but the constant factor hides a 50× multiplier.

You can read your own machine's cache sizes directly:

```bash
$ getconf -a | grep CACHE
LEVEL1_DCACHE_SIZE                 32768
LEVEL1_ICACHE_SIZE                 32768
LEVEL2_CACHE_SIZE                  262144
LEVEL3_CACHE_SIZE                  8388608
$ cat /sys/devices/system/cpu/cpu0/cache/index*/size
```

Apple Silicon hosts (M-series) expose their own cache topology through
`sysctl`. Inside a VirtualBox VM on an Intel host, you may need
`VBoxManage modifyvm "<name>" --cpu-profile host` to see realistic
values.

> **Key insight:** The question "does your working set fit in cache?"
> is the first thing to ask about any memory-intensive program.
> Most surprising slowdowns come from crossing a cache boundary, not
> from an algorithmic change.

## 2.2 CPU Caches and Cache Lines

A cache is small, fast memory that holds recent data. Four properties
describe a cache: **capacity** (how much it holds), **line size** (the
unit of transfer, usually 64 bytes), **associativity** (how flexible
placement is), and **replacement policy** (typically LRU-approximate).

The line size matters more than most programmers realize. The CPU
never reads a single byte from memory; it reads a full 64-byte line
at a time. If you touch byte 10, the cache now holds bytes 0–63 — so
the next 53 byte accesses in that block are effectively free. Sixty-
four bytes is a deliberate balance between spatial locality (fetch
nearby data together) and bandwidth (do not fetch data you will not
use). It holds 16 32-bit integers or 8 doubles.

Programs get cache benefit through **locality**:

- **Temporal locality.** Access X, then access X again soon. A counter
  updated in a loop lives in a register or L1 forever.
- **Spatial locality.** Access X, then access nearby addresses. A
  sequential walk through an array touches each cache line once.

Consider a small but revealing example: summing a 2D array. In C,
arrays are stored row-major, so `arr[i][0]` and `arr[i][1]` are
adjacent in memory.

```c
// Row-major: sequential access, excellent locality
for (int i = 0; i < N; i++)
    for (int j = 0; j < N; j++)
        sum += arr[i][j];

// Column-major: strided access, each read likely misses
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++)
        sum += arr[i][j];
```

The two loops do the same arithmetic. On a 1000 × 1000 int array the
second version can be 10–50× slower. `perf stat -e
cache-references,cache-misses` shows the cause directly:

```text
# row-major
    31,162,964      cache-references
        64,245      cache-misses       # 0.2% miss rate

# column-major
    31,162,964      cache-references
     1,001,764      cache-misses       # 3.2% miss rate
```

Same algorithm, same data, fifteen times as many misses.

### Arithmetic of a miss rate

A 10 % L1 miss rate sounds harmless until you price the misses:

```text
effective latency = 0.9 * 4 cycles + 0.1 * 200 cycles
                  = 3.6 + 20
                  = 23.6 cycles per access
```

That is 6× slower than a pure L1 hit. If the program spends most of
its time chasing data, this is where the slowdown hides.

> **Note:** Cache and branch events are *hardware PMU* counters.
> Many VMs (VirtualBox, VMware Fusion, Apple Silicon guests) expose
> these as `<not supported>` or zero. When that happens, do not
> invent interpretations — switch to Valgrind (`cachegrind`) for
> simulated but *stable* and *explainable* evidence. Section 2.5
> covers the fallback workflow.

## 2.3 Virtual Memory and the TLB

Every modern OS gives each process a **virtual address space** that is
independent of physical RAM. Virtual memory buys three things:
**isolation** (process A cannot touch process B), **simplicity**
(every process thinks it starts at address 0), and **overcommit**
(the kernel can hand out more virtual memory than it has physical
frames for, and fault pages in on demand).

The unit of bookkeeping is a **page**, typically 4 KB on x86. A
per-process **page table** maps virtual pages to physical frames, with
permission and presence bits. Every load and store translates a
virtual address to a physical one by looking up the page table.

That lookup would be slow if done for every access — a page-table
walk takes 10–100 cycles on modern hardware. The **TLB (translation
lookaside buffer)** is a small, fast cache of recent translations:

| Translation path | Latency |
|---|---|
| TLB hit | ~1 cycle |
| TLB miss, page table walk | 10–100+ cycles |
| Minor page fault (page in RAM, not mapped) | ~1,000 cycles |
| Major page fault (page on disk) | ~10,000,000 cycles |

A typical TLB has 64–1024 entries; at 4 KB per page, that covers
256 KB–4 MB of hot virtual memory. Programs with larger working sets
pay for TLB misses on top of cache misses. Using huge pages (2 MB or
1 GB) is one common mitigation; we return to this in Chapter 10.

### Page faults

A page fault is not an error — it is the mechanism through which the
kernel lazily backs virtual memory with physical pages. The first
access to newly `malloc`ed memory triggers a **minor fault**: the
kernel allocates a zeroed page and maps it in. Touching a page that
has been swapped to disk triggers a **major fault**: the kernel must
read from the swap device before the load can proceed. A major fault
is roughly ten thousand times worse than a cache miss.

You can measure them directly:

```bash
$ /usr/bin/time -v ./my_program 2>&1 | grep -i fault
Minor (reclaiming a frame) page faults: 262477
Major (requiring I/O) page faults: 0

$ sudo perf stat -e page-faults,major-faults ./my_program
       1,234      page-faults
           5      major-faults
```

When a container hits its memory limit and starts reclaiming pages,
the application keeps running — but every re-touched page costs a
fault, and p99 latency spikes. The *symptom* is latency; the *cause*
is memory pressure; the *mechanism* is page faults. We will see this
exact chain again in Chapters 7 and 10.

## 2.4 Branch Prediction and Pipelines

Modern CPUs do not execute one instruction at a time. They pipeline
fetch, decode, execute, memory access, and writeback across many
instructions in flight simultaneously. This works beautifully until
the code hits a branch — at which point the hardware does not yet
know which side of the `if` to fetch next.

The solution is **speculative execution**. A branch predictor guesses
based on history, the pipeline races ahead on the predicted side, and
when the branch actually resolves, the CPU either commits the work
(prediction was right, no penalty) or flushes the pipeline
(prediction was wrong, 15–20 cycles wasted).

Some branches are trivially predictable:

```c
for (int i = 0; i < 1000000; i++) { /* body */ }
// "loop again" is taken 999,999 times — ~100% prediction accuracy
```

Others defeat prediction entirely:

```c
if (rand() % 2 == 0) { /* A */ } else { /* B */ }
// Random — ~50% accuracy, a misprediction every other branch
```

One famous microbenchmark sums the elements of an array greater than
a threshold. On random input the branch is unpredictable and the loop
is slow. On sorted input the branch first takes one side for the
whole first half and then the other for the whole second half — the
predictor locks in on the pattern after a few iterations, and the
same code runs 3–6× faster. The algorithm did not change; the
hardware's ability to guess did.

Measure with:

```bash
$ sudo perf stat -e branches,branch-misses ./my_program
   100,000,000      branches
     5,000,000      branch-misses       # 5.0%
```

At 5 % miss rate and 15 cycles per miss, every branch costs 0.75
cycles on average. In a hot inner loop this adds up quickly.

## 2.5 The First Observability Loop

The tools you need to answer "why is my program slow?" form a short
ladder. Each rung gives you more detail, at the cost of more setup
and more overhead.

### `/usr/bin/time` — real time plus OS counters

Use the binary, not the shell builtin; the builtin cannot print the
verbose counters.

```bash
$ /usr/bin/time -v ./my_program
```

Fields worth reading:

- **User time / System time.** CPU work in user space vs kernel.
- **Elapsed (wall) time.** Includes waiting (I/O, scheduling).
- **Minor / Major page faults.** VM behavior.
- **Maximum resident set size.** Peak physical memory footprint.
- **Voluntary / involuntary context switches.** Blocking vs
  preemption.

Quick rules of thumb:

- If **elapsed ≫ user + sys**, the program is waiting on something
  external (I/O, locks, sleeping, throttling).
- If **system time** is high, the program is making many syscalls or
  causing lots of kernel work (faults, I/O).
- If **major faults > 0**, the program touched pages that required
  disk reads — often dominant in runtime when it happens.

### `perf stat` — hardware counters

```bash
$ sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
branches,branch-misses,page-faults,major-faults -r 5 \
  ./my_program
```

Useful flags: `-e` to select events, `-r N` to run `N` repeats and
report variance, `--` to separate `perf` flags from program args. The
five numbers you should learn to read are:

- **cycles** — how long (in CPU time)
- **instructions** — how much work
- **IPC = instructions / cycles** — efficiency; ~2–4 is healthy,
  below 1 usually means memory stalls
- **cache-misses / cache-references** — the miss *rate*, not the raw
  count
- **branch-misses / branches** — ditto for branches

The interpretation habit:

> If elapsed time increased, did cycles increase? If cycles increased,
> was it because there were more instructions, or because IPC dropped?
> If IPC dropped, was it cache misses or branch mispredicts?

### Valgrind tools — the VM fallback

When hardware counters are unavailable (common in VMs), Valgrind runs
your program under instrumentation. It is slow — 10–50× slower than
native — but it produces detailed, stable, reproducible output.

- `valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes ./p`
  simulates cache and branch behavior. Use the *miss rates*, not the
  absolute counts, and use it for *trends across inputs*, not for
  hardware-exact values.
- `valgrind --tool=callgrind ./p` then `callgrind_annotate` (or
  `kcachegrind`) attributes cost to functions and lines. Useful for
  answering "which line is hot?"
- `valgrind --tool=massif ./p` then `ms_print` profiles heap growth
  over time. Useful for answering "what is the peak, and who
  allocated it?"

A practical convention: always send Valgrind output to a subdirectory
you own.

```bash
valgrind --tool=cachegrind \
  --cachegrind-out-file=outputs/cg_%p.out ./qs datasets/random.txt
```

This sidesteps the common "Permission denied" bug where a prior `sudo`
run left root-owned files in the working directory.

### The investigation loop

Put together, the repeatable loop looks like this:

1. Start with timing. `/usr/bin/time -v` names the OS signals (faults,
   RSS, context switches).
2. If hardware counters work, use `perf stat` with `-r 5` to get IPC
   and miss rates across several runs.
3. If counters do not work, use `cachegrind` for cache/branch trends
   and `callgrind` for hot-spot attribution.
4. If memory growth is suspect, add `massif` and read the peak
   snapshot.

A good write-up reads:

> "Runtime increased because *X*. Evidence: metric *A* changed at
> *N* ≈ ..., which implies mechanism *M*."

Every later chapter uses this exact shape.

## 2.6 Designing Controlled Experiments

A measurement without a baseline is not a measurement. The discipline
of controlled experiments has four rules that apply in every chapter
of this book.

**One variable at a time.** If you change the input size *and* the
compiler flags *and* the CPU governor in the same run, you cannot
attribute the result. Hold everything constant and vary one axis.

**Always have a baseline.** "Is it slow?" is unanswerable without a
reference point. "Is it slower than the previous version?" is
answerable. "Is it slower than the same program on a different
input?" is answerable. Pick the baseline first.

**Run multiple trials.** A single run can be thrown off by a cold
cache, an unrelated process, a CPU frequency change. Three runs is
the minimum; five is better; `perf stat -r N` and
`/usr/bin/time` repeated in a shell loop both work. Report the
variance, not just the mean.

**Report rates, not just counts.** Counts grow with input size even
when nothing else has changed. Rates tell you what *changed*:

- IPC = instructions / cycles
- cache miss rate = cache-misses / cache-references
- LLd miss rate (cachegrind) = LLd misses / D refs
- branch miss rate = branch-misses / branches

### The CPU-bound to memory-bound transition

A concrete application of all four rules: find the point where a
program stops being CPU-bound and becomes memory-bound. The recipe:

1. Pick a workload whose working set grows with an input parameter
   `N` (quicksort on an `N`-element array is the canonical example).
2. Generate datasets of geometrically increasing `N` — e.g. 1 000,
   5 000, 10 000, 20 000, 50 000, 100 000, 200 000, 500 000.
3. For each `N`, collect wall time, cycles, instructions, cache
   references, and cache misses (or cachegrind equivalents). Run each
   point three times.
4. Compute IPC and cache miss rate.
5. Plot time and miss rate against `N` on a log-x axis. Look for the
   knee where IPC drops and miss rate climbs. That is your transition.
6. Predict the knee in advance: if each element is 4 bytes and your
   L3 cache is 8 MB, the working set exceeds L3 at `N ≈ 2 × 10⁶`.
   Does the data agree?

The quicksort lab at the end of this chapter walks through this
experiment end-to-end.

> **Warning:** Results on a laptop can be noisy. Close other
> applications, disable Turbo Boost if you can, and pin the CPU
> governor to `performance` with `sudo cpupower frequency-set
> --governor performance`. Report the configuration you used.

## Summary

Key takeaways from this chapter:

- Performance is shaped by the memory hierarchy. Cache misses, TLB
  misses, and branch mispredictions are the three mechanisms that
  dominate most surprising slowdowns.
- `perf stat` is the foundational tool. When it works, it gives you
  cycles, instructions, IPC, and miss rates in seconds. When it does
  not (common in VMs), `cachegrind` / `callgrind` / `massif` fill in
  the gap with simulation-based evidence.
- A controlled experiment requires a clear hypothesis, one variable,
  a stable baseline, and multiple trials. Without a baseline, a
  number is just a number.
- Always interpret rates, not counts. The question is never "how many
  misses?" — it is always "what fraction of accesses missed, and why
  did that fraction change?"

## Further Reading

- Gregg, B. (2020). *Systems Performance*, 2nd ed. Addison-Wesley.
  Chapter 6: CPUs.
- Drepper, U. (2007). *What Every Programmer Should Know About
  Memory.* <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
- Patterson, D. & Hennessy, J. *Computer Organization and Design*,
  Chapter 5 (memory hierarchy).
- Arpaci-Dusseau & Arpaci-Dusseau (2018). *Operating Systems: Three
  Easy Pieces*, Chapters 18–23 (virtual memory).
- Valgrind Massif manual:
  <https://valgrind.org/docs/manual/ms-manual.html>
- `perf` wiki: <https://perf.wiki.kernel.org/>
