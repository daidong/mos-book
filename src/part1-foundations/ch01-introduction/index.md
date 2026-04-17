# Chapter 1: Introduction — OS in the Cloud-Native and AI Era

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why OS concepts remain relevant in the age of containers,
>   orchestrators, and AI agents
> - Describe the three core skills this book develops: Understand,
>   Measure, Explain
> - Set up a reproducible experiment environment (Ubuntu VM with perf,
>   strace, and basic observability tools)
> - Run your first performance measurement and interpret the output

## 1.1 Why Operating Systems Still Matter

Ask ten engineers what an "operating system" is in 2026 and you will
get ten different answers. Some will point at the Linux kernel. Others
will name Kubernetes, or their cloud provider, or the container
runtime their application ships inside. Each answer is partially
right, and together they describe a real change: the boundary between
"the OS" and "the platform" has blurred.

The boundary has blurred, but the problems on either side of it have
not. A Kubernetes pod that gets OOM-killed is solving the same memory
accounting problem the kernel has solved for decades — with one extra
layer of policy on top. A p99 latency spike in an LLM inference server
looks exotic until you realize it is a page fault, a runqueue wait, or
a lock contention event that an OS textbook from 2005 would have
recognized. The context has expanded. The mechanisms have not.

This book takes that observation seriously. Every chapter introduces a
classical OS concept — processes, scheduling, isolation, storage,
consensus — and then applies it to a modern case: a container being
throttled, an etcd cluster losing quorum, an agent runtime executing a
tool call that behaves suspiciously like a privileged syscall. The
concepts are not nostalgia. They are the vocabulary you need to debug
what you actually run in production.

> **Key insight:** When someone says "Kubernetes is throttling my pod,"
> they are describing a CFS bandwidth control event. When they say
> "my inference server p99 got worse," they are usually describing
> tail latency caused by scheduling, memory pressure, or I/O. The
> names change; the underlying OS mechanisms do not.

## 1.2 The Modern OS Landscape

The traditional OS course draws a three-layer picture: applications on
top, system calls in the middle, kernel at the bottom. That picture is
still accurate, but it is no longer complete. In a modern deployment,
there are at least two more layers sitting above the kernel and
below the application.

```text
┌─────────────────────────────────────────────────┐
│            Control Plane                        │
│  (K8s scheduler, controllers, orchestration)    │
├─────────────────────────────────────────────────┤
│              Runtimes                           │
│  (container runtime, eBPF programs, language    │
│   runtime, agent runtime)                       │
├─────────────────────────────────────────────────┤
│              Kernel                             │
│  (scheduler, memory, fs, net, isolation)        │
├─────────────────────────────────────────────────┤
│              Hardware                           │
└─────────────────────────────────────────────────┘
```

Each layer reuses concepts from the layer below. A **container** is a
process plus a bundle of namespaces and a cgroup. A **pod** is a small
group of containers scheduled together. A **controller** is an event
loop that reconciles desired state with observed state — conceptually
the same feedback pattern the kernel uses to keep the page cache near
its target size.

This reuse matters because it tells you where to look when things
break. A pod stuck in `CrashLoopBackOff` is ultimately a process
repeatedly failing to start. A Service with slow DNS is ultimately a
socket, a syscall, and a runqueue. The control plane can make a
problem easier to describe, but it rarely invents a new kind of
failure — it inherits its failure modes from the kernel underneath.

> **Note:** The three-layer picture (kernel / runtime / control plane)
> is one useful lens, not the only one. Networking people draw
> different pictures; database people draw different pictures again.
> Use whichever lens makes the current problem tractable.

## 1.3 Three Core Skills

This book trains three skills, in a deliberate order.

**Understand** — know the mechanism. When we say Linux uses the
Completely Fair Scheduler, you should be able to state what CFS
actually does: it picks the runnable task with the smallest virtual
runtime. When we say containers use cgroup v2 for memory limits, you
should know that cgroup v2 accounts memory at the page level and
invokes the OOM killer when `memory.max` is exceeded. Mechanisms first,
names second.

**Measure** — design controlled experiments. Given a claim ("fsync is
expensive"), you should be able to write a script that quantifies the
cost: how many microseconds, over how many samples, with what
variance, compared to what baseline. A measurement without a baseline
is not a measurement; it is an anecdote.

**Explain** — connect numbers back to mechanisms. A good explanation
names the specific OS concept responsible for the observation. "p99
latency increased from 2 ms to 15 ms when the memory limit dropped to
512 MB, because page reclaim (kswapd) was woken every 100 ms" is an
explanation. "The container got slower" is not.

Every symptom you will meet in practice decomposes into these three
skills. A few worked examples:

| Symptom | OS concept to understand | Tool to measure | What a good explanation looks like |
|---|---|---|---|
| p99 latency spike | Scheduling, page fault | perf, eBPF | "Runqueue wait > 5 ms during GC pause" |
| Container OOM | Memory accounting, cgroups | cgroup stats | "RSS crossed memory.max at t=42s" |
| CPU throttling | CFS bandwidth control | /proc, /sys | "cpu.stat shows 80 throttled periods" |
| Slow Service call | TCP stack, context switch | tcpdump, bpftrace | "200 ms delay from Nagle + delayed ACK" |

You do not need to be fluent in every tool at the start of this book.
You do need to commit to the habit: whenever you claim a system
behaves a certain way, back the claim with a number and a cause.

## 1.4 How This Book Is Organized

The book has thirteen chapters grouped into seven parts. Chapter 1
(this one) and the labs in Part I establish the methodology;
everything after uses it.

Each chapter has two halves. The first half is exposition: concepts,
mechanisms, and enough detail to reason about what is happening. The
second half is a lab, split into three tiers:

- **Part A (Basic, required):** the minimum experiment that
  demonstrates the concept
- **Part B (Intermediate, required):** a deeper measurement or
  comparison that forces you to think in evidence chains
- **Part C (Advanced, optional):** an open-ended extension for
  students who want more

The labs are not an afterthought. They are where the concepts become
yours. Reading about a p99 spike is not the same as producing one on
your own VM and diagnosing it. Where you can, do the labs on the same
machine you use for everything else — reproducibility is itself a
skill the labs teach.

A reading guide:

- Read Chapters 1–5 in order. They build on each other.
- Chapter 6 (containers) depends on Chapters 4–5 (scheduling).
- Chapter 7 (Kubernetes) depends on Chapter 6.
- Chapters 8–9 (consensus, cluster scheduling) can be read after
  Chapter 7, or skipped if you are only interested in the single-node
  story.
- Chapters 10–11 (storage) are independent of Chapters 8–9 and can be
  read after Chapter 5.
- Chapter 12 (agent runtimes) assumes Chapters 1–7.
- Chapter 13 (methodology) ties everything together and is best read
  last.

## 1.5 A First Look: What Happens When You Run a Program

To set the tone for the rest of the book, consider what actually
happens when you run a single command. Take the simplest program
imaginable:

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("Hello from process %d\n", getpid());
    return 0;
}
```

Compile it and run it under `strace`:

```bash
$ gcc -o hello hello.c
$ strace ./hello
```

The output is longer than you might expect. Trimmed to its essentials,
it looks like this:

```text
execve("./hello", ["./hello"], ...)     = 0
brk(NULL)                               = 0x55a7...
mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f...
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
read(3, "...", 832)                     = 832
...
write(1, "Hello from process 12345\n", 25) = 25
exit_group(0)                           = ?
```

Every line is a transition across the user–kernel boundary. The
kernel loads the binary (`execve`), lets the dynamic linker map
shared libraries into the address space (`mmap`, `openat`, `read`),
runs your code, and hands the output string to the terminal
(`write`). Your `printf` turned into a single `write(1, ...)` syscall
— everything above that was the OS preparing the ground for your
program to exist at all.

Now measure the same program with `perf stat`:

```bash
$ sudo perf stat ./hello
```

```text
 Performance counter stats for './hello':

          0.42 msec task-clock
             1      context-switches
             0      cpu-migrations
            54      page-faults
       912,345      cycles
       456,789      instructions
```

Six numbers, each one pointing at an OS mechanism:

| Counter | Mechanism |
|---|---|
| task-clock | CPU time charged to the process by the scheduler |
| context-switches | Times the scheduler preempted the process |
| cpu-migrations | Times the process was moved between CPUs |
| page-faults | Memory pages the kernel had to allocate or load |
| cycles | CPU clock cycles the hardware executed |
| instructions | Machine instructions the CPU retired |

These are the units in which we will speak for the rest of the book.
When Chapter 5 explains scheduler latency, you will measure it with
the same `task-clock` counter you just saw. When Chapter 10 explains
the page cache, you will ask why the `page-faults` count changes
between cold and warm runs. The tools do not get much more complicated
than this; the questions do.

## Summary

Key takeaways from this chapter:

- The OS is not just the kernel — it is the full stack of resource
  management from hardware to application, now including container
  runtimes and cluster-level control planes.
- Modern systems (containers, Kubernetes, AI agents) reuse and extend
  OS concepts like isolation, scheduling, and resource control.
  Learning the modern context without the classical mechanism gives
  you names without understanding.
- This book emphasizes measurement-driven understanding: every claim
  about system behavior is backed by reproducible evidence, not
  folklore.
- The three core skills are **understand**, **measure**, and
  **explain**. The rest of the book is a sequence of chances to
  practice all three.

## Further Reading

- Arpaci-Dusseau, R. H. & Arpaci-Dusseau, A. C. (2018).
  *Operating Systems: Three Easy Pieces.* Introduction and Chapter 2.
  Available at <https://pages.cs.wisc.edu/~remzi/OSTEP/>
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Addison-Wesley.
  Chapter 1: Introduction.
- Linux `perf` wiki: <https://perf.wiki.kernel.org/>
- `man 1 strace`, `man 1 perf-stat`, `man 7 credentials` — the Linux
  manual is a reference you will return to often.
