# Chapter 2: Performance Measurement Methodology

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain how the memory hierarchy shapes runtime even when the source
>   code is unchanged
> - Distinguish hardware effects such as cache misses and branch
>   mispredictions from OS effects such as page faults, scheduling, and
>   placement
> - Use `perf stat`, `/usr/bin/time -v`, and Valgrind appropriately,
>   including in VM-constrained environments
> - Design a controlled experiment that survives noisy machines and shared
>   infrastructure

Performance work begins with a simple discipline: a number is evidence, and
a mechanism is an explanation. If a report says "the program is 2× slower"
but cannot say whether it did more work, stalled more often, or waited on an
OS slow path, the report is not finished.

## 2.1 Why the Memory Hierarchy Dominates So Many Performance Questions

A modern core can retire billions of instructions per second. DRAM is far
slower than the core that wants to read it, and storage is slower again.
Without a hierarchy of fast, small memories above slower, larger ones, the
CPU would spend most of its time idle.

Typical order-of-magnitude latencies look like this:

| Level | Approx. latency | Typical size | What it means for software |
|---|---:|---:|---|
| registers | ~0 cycles | ~1 KB | values already in the execution core |
| L1 cache | ~4 cycles | 32–64 KB / core | hot inner-loop data |
| L2 cache | ~12 cycles | 256 KB–2 MB / core | warm working set |
| LLC / L3 | ~40–70 cycles | MBs shared per socket | cross-core shared data |
| DRAM | ~150–300 cycles | GBs | main-memory working set |
| SSD | tens of microseconds | hundreds of GB | page-in, file reads, sync writeback |

The exact numbers vary by machine. The structure does not. Crossing one
boundary in that table can dominate runtime even when the algorithmic
complexity stays the same.

This is not an academic corner case. A log-processing pipeline, an analytics
query, an in-memory cache, and an LLM inference server all care about the
same question: does the hot working set fit in the fast level of memory the
CPU can currently reach cheaply?

![Memory hierarchy pyramid showing registers, L1, L2, L3, DRAM, and storage with increasing latency and capacity](figures/memory_hierarchy_pyramid.png)
*Figure 2.1: The memory hierarchy is a stack of trade-offs. Higher levels are smaller and faster; lower levels are larger and far more expensive to touch on the critical path.*

> **Key insight:** Many "mysterious" slowdowns are just working sets crossing
> a boundary: L1 to L2, LLC to DRAM, RAM to swap, or local core to another
> socket.

## 2.2 Caches, Cache Lines, and Locality

A **cache** is a small, fast store that keeps recently used data close to the
core. The unit of transfer is not a byte but a **cache line**, typically 64
bytes. When the CPU reads one byte, the hardware usually fetches the whole
line containing it.

That is why **locality** matters.

- **Temporal locality:** access the same item again soon.
- **Spatial locality:** access nearby items soon.

A textbook example is summing a matrix in row-major versus column-major
order:

```c
for (int i = 0; i < N; i++)
    for (int j = 0; j < N; j++)
        sum += arr[i][j];

for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++)
        sum += arr[i][j];
```

The arithmetic is identical. The memory path is not. In C, rows are stored
contiguously, so the first loop reuses fetched cache lines. The second loop
jumps by a stride large enough to evict useful data and trigger misses.

![Row-major array layout showing contiguous storage by rows rather than by columns](figures/row_major_memory_layout.png)
*Figure 2.2: The row-major layout explains why sequential row traversal is cache-friendly. Column-wise access reads the same data structure through a much worse memory path.*

The hardware enforces this at the cache-line level. When a CPU core requests
a single byte, the memory controller fetches the entire 64-byte cache line
containing it. Sequential access reuses that fetched data; strided access
wastes it.

![Cache line fetch: the CPU requests byte 10 and the hardware fetches the full 64-byte block into the L1 data cache](figures/cache_line_fetch.png)
*Figure 2.4: A cache miss fetches an entire 64-byte line, not just the requested byte. Sequential access exploits the remaining bytes; strided or random access discards them.*

This pattern appears constantly in real systems.

| Workload | Good locality looks like | Bad locality looks like |
|---|---|---|
| log scan / grep | sequential read through buffers | pointer chasing across fragmented structures |
| columnar analytics | batch-friendly scans | repeatedly materializing scattered rows |
| inference serving | contiguous tensor layout | layout conversions and cache-thrashing copies |
| kernel networking | per-CPU queues and hot metadata | bouncing shared state across cores |

You can often see the effect in `perf stat`:

```bash
$ sudo perf stat -e cache-references,cache-misses ./program
```

Interpret the **rate**, not the raw count. A million misses may be harmless
if there were a billion accesses. A 10% miss rate is expensive even when the
absolute count looks modest.

### Pricing a miss

A miss rate sounds abstract until you translate it into cycles:

```text
effective access cost = hit_rate * hit_cost + miss_rate * miss_cost
                      = 0.9 * 4 + 0.1 * 200
                      = 23.6 cycles
```

Ten percent misses turned a 4-cycle access into a 23.6-cycle access. That is
a 6× slowdown at the point of use.

## 2.3 Virtual Memory, the TLB, and Page Faults

A process does not address physical RAM directly. It sees a **virtual
address space**. The hardware **MMU** translates virtual addresses to
physical frames using page tables, and the OS defines what those mappings
mean.

The bookkeeping unit is usually a 4 KB **page**. Because page-table walks
would be too expensive on every load, CPUs keep a small cache of recent
translations called the **TLB**.

| Event | Typical cost | Who owns it? |
|---|---:|---|
| TLB hit | ~1 cycle | hardware |
| TLB miss, page-table walk | 10–100+ cycles | hardware walk over OS-managed tables |
| minor page fault | ~1,000+ cycles | kernel allocates/maps a page |
| major page fault | microseconds to milliseconds | kernel must wait on storage |

This boundary is where OS and hardware interact most directly.

- The hardware detects that a translation is missing.
- The kernel decides whether the access is legal and how to satisfy it.
- If the page is merely unallocated but valid, the kernel can map a zeroed
  page: minor fault.
- If the page must be read from disk or swap, the process blocks and waits:
  major fault.

![Virtual-to-physical address translation diagram showing virtual page number, page-table lookup, physical page number, and page offset](figures/virtual_memory_translation.png)
*Figure 2.3: Address translation is a hardware–kernel handshake. The MMU raises the question, the page tables encode the answer, and faults invoke kernel policy when the answer is missing.*

![The TLB is a small SRAM cache that holds recent virtual-to-physical page translations, sitting between the CPU and the full page table in DRAM](figures/tlb.png)
*Figure 2.5: The TLB caches recent page-table entries in fast SRAM. A TLB hit avoids the full page-table walk. A TLB miss forces the hardware to walk the page table in DRAM — or, if the page is not resident, the kernel handles a fault.*

![Minor page faults map a page already in memory; major page faults require loading from disk and a context switch](figures/minor_vs_major_fault.png)
*Figure 2.6: Minor faults are cheap (kernel maps a page already in physical memory). Major faults are expensive: the kernel must issue disk I/O, context-switch the process off-CPU, and resume it only when the page arrives.*

That is why page faults belong in an OS textbook, not just an architecture
course. The TLB is hardware. The page-fault path is kernel policy in action.

In production, this distinction matters because many memory incidents look
like latency incidents first. A container near `memory.max` may keep serving
requests while reclaim and major faults quietly inflate the tail. The
application symptom is p99 latency; the mechanism is virtual-memory pressure.

Measure it with:

```bash
$ /usr/bin/time -v ./program
$ sudo perf stat -e page-faults,major-faults ./program
```

## 2.4 Branch Prediction and Pipelines

CPUs pipeline many instructions at once. Branches disrupt that flow because
the machine must guess which path to fetch before the branch fully resolves.
A **branch predictor** makes the guess. A correct guess is cheap. A wrong one
flushes work already in flight.

![CPU pipelining and branch prediction: a 5-stage pipeline overlaps instructions, but a misprediction flushes the pipeline and wastes 15–20 cycles](figures/cpu_pipeline_branch.png)
*Figure 2.7: Pipelining overlaps instruction stages for throughput. A correct branch prediction keeps the pipeline full; a misprediction flushes speculative work and costs ~15–20 cycles to recover.*

A predictable loop branch is easy for the hardware to learn. A branch on
random data is much harder. That difference shows up in hot inner loops,
parsers, packet filters, query operators, and threshold-based code in ML or
signal-processing pipelines.

```bash
$ sudo perf stat -e branches,branch-misses ./program
```

Again, use the rate. A branch-miss rate of 5% can be expensive if the branch
sits on the critical path of a tight loop.

A useful failure question is: did runtime increase because the program did
more instructions, or because each instruction stream became less efficient?
Branch misses are one answer to the second half of that question.

## 2.5 What the Hardware Does, and What the OS Does

Students often blur architecture and OS boundaries in performance work. Do
not. The boundary is part of the explanation.

| Phenomenon | Hardware role | OS role | First signal to inspect |
|---|---|---|---|
| cache miss | fetch next level of hierarchy | influences layout indirectly via allocation, placement, scheduling | `cache-misses`, IPC |
| branch mispredict | speculates and flushes pipeline | none directly | `branch-misses`, IPC |
| TLB miss | walks page tables | defines mappings and permissions | `dTLB-*` events, IPC |
| minor fault | traps on missing mapping | allocates/maps page | `page-faults`, `/usr/bin/time -v` |
| major fault | traps, then waits on device | schedules I/O and blocks task | `major-faults`, `iostat`, tail latency |
| CPU migration | executes on new core | scheduler load-balances task | `cpu-migrations`, affinity settings |
| throttling | hardware enforces time already charged | kernel/cgroup policy sets quota | `cpu.stat`, `schedstat` |

This table is the difference between a shallow and a defensible answer.
"The cache caused it" is incomplete if the real reason was that the scheduler
moved the task across cores and destroyed locality. "The OS caused it" is
incomplete if the dominant signal is a data-dependent branch predictor miss.

## 2.6 The First Observability Loop

For Part I, you only need a short tool ladder.

### `/usr/bin/time -v`

Start here when you want OS-facing signals: wall time, user/system split,
page faults, resident-set size, and context switches.

```bash
$ /usr/bin/time -v ./program
```

Use it to answer questions such as:

- Is wall time much larger than user + system time?
- Did the run incur major faults?
- Did context switches spike because the program blocked?

### `perf stat`

Use `perf stat` when PMU counters are available and you need low-overhead
hardware-side evidence.

```bash
$ sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
branches,branch-misses,page-faults,major-faults -r 5 ./program
```

The key reading habit is:

1. If runtime changed, did cycles change?
2. If cycles changed, was it because instructions increased or IPC fell?
3. If IPC fell, do cache misses, branch misses, or faults explain it?

### Valgrind fallback for VMs

Many student VMs expose hardware counters poorly or not at all. If `perf`
prints `<not supported>` or zeros for PMU events, do not invent an
interpretation. Switch tools.

- `cachegrind` for cache and branch trends
- `callgrind` for hot-function attribution
- `massif` for heap growth

Valgrind is slower than native execution, but it is stable and explainable.
That makes it a good teaching fallback.

## 2.7 Designing Controlled Experiments on Real Machines

A good experiment has four non-negotiable properties.

**One variable.** Change one axis at a time: input size, data layout,
compiler flag, memory limit, or CPU placement. Not all of them together.

**Baseline.** Decide what the comparison point is before you measure.
"Slower than what?" must have a precise answer.

**Repeats.** A single run is a story. Several runs let you see variance.
Three is the minimum; five is better.

**Rates, not just counts.** Report IPC, miss rates, and fault rates, not
just raw counters that scale with input size.

On shared systems, add a fifth property: **hygiene**.

| Source of noise | Why it matters | Mitigation |
|---|---|---|
| frequency scaling / Turbo | same code runs at different clocks | set governor to `performance` when allowed |
| CPU migration | loses cache warmth, changes NUMA locality | pin with `taskset`, check migrations |
| container quota | task is throttled rather than CPU-bound | inspect cgroup `cpu.stat` |
| noisy neighbor | shared LLC, memory bandwidth, I/O contention | repeat runs; prefer quiet host or dedicated VM |
| PMU virtualization gaps | counters missing or multiplexed | use Valgrind fallback; report limitation |

Industrial practice adds one more distinction: staging measurements and
production measurements serve different goals. In staging you want control.
In production you often accept less control in exchange for realism. Good
engineers know which one they are doing.

> **Warning:** If your measurement method cannot survive background noise,
> scheduler movement, and unavailable counters, it is not robust enough for
> modern systems work.

## Summary

Key takeaways from this chapter:

- The memory hierarchy dominates performance because crossing a boundary in
  that hierarchy can multiply access cost even when the algorithm is
  unchanged.
- Caches, TLBs, and branch predictors are hardware mechanisms, but their
  performance consequences often interact with OS decisions about mapping,
  placement, and scheduling.
- `perf stat` is the fastest route to cycles, instructions, IPC, and miss
  rates. `/usr/bin/time -v` is the fastest route to OS-visible waiting and
  fault behavior. Valgrind is the right fallback when VM counters are weak.
- A defensible experiment requires one variable, a baseline, multiple runs,
  rates rather than counts, and explicit control of major noise sources.

## Further Reading

- Gregg, B. (2020). *Systems Performance*, 2nd ed. Addison-Wesley.
  Chapters 2 and 6.
- Drepper, U. (2007). *What Every Programmer Should Know About Memory.*
  <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
- Arpaci-Dusseau, R. H. & Arpaci-Dusseau, A. C. (2018).
  *Operating Systems: Three Easy Pieces.* Chapters 18–23.
- Valgrind manuals: <https://valgrind.org/docs/manual/>
- Linux `perf` wiki: <https://perf.wiki.kernel.org/>
