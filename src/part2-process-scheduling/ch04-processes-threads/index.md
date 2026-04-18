# Chapter 4: Processes, Threads, and Concurrency

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain the process abstraction and how the kernel implements it
>   (fork, exec, wait, exit)
> - Compare kernel threads and user-level threads, including their
>   scheduling tradeoffs
> - Describe how preemption works (timer interrupts, voluntary vs
>   involuntary context switches)
> - Explain why scheduling latency is a primary source of tail latency

Chapter 3 introduced the notion of an OS "slow path" — a rare,
expensive event that inflates p99. This chapter looks at the most
common slow path of all: a thread that is ready to run but has to
wait for the scheduler to pick it. To talk about that precisely we
first need the vocabulary of processes and threads, the mechanism of
context switching, and the basic shape of the scheduling policies
Linux descended from. Chapter 5 will then open the scheduler itself.

## 4.1 The Process Abstraction

A **process** is an instance of a program in execution, running with
limited privileges and isolated from other processes. From the
kernel's point of view, a process is a bookkeeping record plus a
pile of resources:

- **Machine state.** CPU registers (program counter, stack pointer,
  general-purpose registers, floating-point state).
- **Address space.** A private virtual memory layout — code, data,
  heap, stack — realized through page tables that map virtual
  addresses to physical frames.
- **Open files and other resources.** File descriptors, current
  working directory, credentials, signal handlers.

Linux keeps all of this in a per-process structure called
`task_struct` (the kernel's name for the **process control block**).
Task structs are linked into the kernel's runnable and wait queues,
and they carry the saved register context the scheduler uses to
resume a paused process.

### The lifecycle: fork, exec, wait, exit

The Unix process API is unusual in splitting creation
(`fork`) from program loading (`exec`). `fork()` duplicates the
calling process; both parent and child return from the same call,
the parent receiving the child's PID and the child receiving 0:

```c
pid_t rc = fork();
if (rc < 0)          { /* fork failed */ }
else if (rc == 0)    { /* child */ }
else                 { /* parent (rc = child PID) */ }
```

`exec()` then *replaces* the current process image with a new
program. On success, it does not return — control transfers to the
new program's entry point.

The split looks redundant until you try to implement shell
redirection. Between `fork` and `exec`, the child can rearrange its
file descriptors before running the program:

```c
if (fork() == 0) {
    close(1);
    open("out.txt", O_CREAT|O_WRONLY|O_TRUNC, 0644);  // dup into fd 1
    execvp("wc", argv);
}
wait(NULL);
```

Because `open` always returns the lowest available descriptor, the
new `fd 1` is `out.txt`; because open descriptors survive `exec`,
`wc` writes to the file without knowing about the redirection. This
composition — `fork` for duplication, `exec` for replacement, `wait`
for completion — is the Unix design at its most elegant.

`wait()` reaps a terminated child. Until the parent waits, the
kernel keeps a small "zombie" record with the child's exit status —
a design choice that is also the reason `ps` sometimes shows `Z` in
the status column.

### Process states

A process moves through three main states:

- **Running** — currently executing on a CPU.
- **Runnable (Ready)** — ready to execute, waiting for a CPU.
- **Blocked (Sleeping)** — waiting on an event (I/O completion,
  timer, futex, signal).

![Task state timeline showing SLEEPING → RUNNABLE (on runqueue, waiting) → RUNNING (on CPU), with tracepoints sched_wakeup and sched_switch marking the transitions, and scheduling latency defined as t(RUNNING) − t(RUNNABLE)](figures/task_state_timeline.png)
*Figure 4.1: The three main process states and the transitions between them. Scheduling latency is the time spent in the RUNNABLE state — between the wakeup event and the context switch that actually delivers the CPU.*

The next section is about the transition between **Runnable** and
**Running**. That transition is where scheduling latency lives.

## 4.2 Context Switching

A **context switch** suspends one thread's execution on a CPU and
resumes another. The kernel must, atomically, save everything that
lets the outgoing thread resume later, and restore everything the
incoming thread was holding when it last ran:

1. Transition user → kernel on the outgoing thread's kernel stack
   (either a syscall, an interrupt, or a preemption point).
2. Save the outgoing thread's CPU register state.
3. Switch to the new thread's kernel context (its stack, its
   register image).
4. Return to user mode on the new thread's kernel stack, restoring
   its user-space registers.

Linux does this in assembly via a routine conventionally called
`switch_to` or `swtch`. In pseudo-code the core looks like:

```text
context_switch(prev, next):
    switch_mm(prev->mm, next->mm)       // install next's page tables
    switch_to(prev, next):
        save prev's callee-saved registers to prev->thread
        save prev's stack pointer        to prev->thread.sp
        load next's stack pointer        from next->thread.sp
        load next's callee-saved registers from next->thread
        // execution now continues on next's kernel stack
    barrier()                            // compiler must not reorder
```

The transition looks deceptively small, but a context switch is
rarely free:

- **Direct cost.** Saving and restoring registers plus some kernel
  bookkeeping: hundreds of nanoseconds to a few microseconds on
  modern hardware.
- **Indirect cost.** The outgoing thread's working set — the L1/L2
  lines and TLB entries it had warm — is displaced by the incoming
  thread. On resumption, the thread refills caches from DRAM.

The total cost depends on the working-set sizes of the two threads.
A tight ping-pong between two processes sharing a pipe might cost
1–2 µs end-to-end; a switch between two cache-hungry processes that
clobber each other's L3 can cost 10× more *in the next several
milliseconds* as the caches refill. Lab 1 (Part C) demonstrates the
accounting side; Chapter 5's eBPF lab will let you see the scheduler
side directly.

### Voluntary vs involuntary

Context switches fall into two categories:

- **Voluntary.** The thread asked to stop: it called `sleep`, blocked
  on a futex, waited on I/O, or yielded. `/proc/<pid>/status` reports
  these as `voluntary_ctxt_switches`.
- **Involuntary.** The kernel preempted the thread — typically on a
  timer tick because its quantum expired, or because a
  higher-priority task woke. Reported as
  `nonvoluntary_ctxt_switches`.

A high *involuntary* rate means there is CPU contention; a high
*voluntary* rate usually means lots of I/O or synchronization. Both
can hurt tail latency, but for different reasons — which is why the
USE method in Chapter 3 treats them as separate signals.

## 4.3 Threads and Concurrency

Where a process is the unit of resource ownership, a **thread** is
the unit of scheduling. A thread is a single execution sequence —
registers and a stack — that the OS can schedule independently.
Threads inside the same process share the address space, file
descriptors, and most other resources.

Threads matter because programs often need to do several things at
once: handle connections, wait on I/O, run background work. A
single-threaded model forces you into event loops and callbacks; a
threaded model lets you write each task as sequential code and trust
the OS to interleave them.

### Kernel threads vs user-level threads

Two implementation models, both still in use:

- **Kernel threads (1:1).** Each user thread corresponds to a kernel
  scheduling entity. Linux uses this model: `pthread_create` calls
  `clone()` with `CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND`
  to create a new kernel task that shares its creator's address space.
  Context switches go through the kernel, so they are heavier than
  pure user-space switches, but blocking syscalls only block the
  calling thread.
- **User-level threads (N:1).** Implemented in a library without
  syscalls. Switches are fast (no kernel transition), but one
  blocking syscall blocks the whole process. Early pthreads
  implementations did this; it is rarely the right choice today.
- **Hybrid (M:N).** Many user-level schedulers multiplex N user
  threads onto M kernel threads. Go's `goroutine` runtime is the
  prominent modern example — goroutines are scheduled in user space
  by the Go runtime on top of a pool of kernel threads (the G/M/P
  model). The JVM, tokio, libuv use variations of the same pattern.

For the rest of this book, "thread" means Linux kernel thread unless
we explicitly say otherwise.

### POSIX threads in a page

```c
pthread_create(&t, NULL, worker, arg);
pthread_join(t, NULL);
pthread_exit(status);   // terminates only this thread
exit(status);           // terminates the whole process
```

`pthread_create` spawns a thread running `worker(arg)`.
`pthread_join` waits for it and collects its return value. The
lifecycle is intentionally similar to `fork`/`wait` — the difference
is that threads share the address space, so the parent and child can
communicate through memory directly.

### Why concurrency bugs are hard

Two threads reading and writing the same variable can observe each
other's partially completed updates. A **race condition** is a
situation where the result depends on the interleaving. The fix is
to make the critical section **atomic** — typically with a mutex,
which puts contenders onto a wait queue until the holder releases.
This is the topic of any OS textbook's concurrency chapters, and we
will not repeat it here. What matters for this book is that *every
lock is another queue*, and queues are where tail latency lives.

## 4.4 Scheduler Fundamentals

Before Chapter 5 dives into Linux's Completely Fair Scheduler, it is
worth sketching the classical policies that every scheduler has to
navigate. None of them is quite right by itself; a modern scheduler
is a negotiation among them.

### What is the scheduler optimizing?

Several, conflicting, goals:

- **Response time.** How quickly does a newly runnable task get to
  run?
- **Turnaround time.** How long until a task completes?
- **Throughput.** How much work per unit time?
- **Fairness.** Does every task get a share? No starvation?
- **Overhead.** How cheap is the decision itself? Too many context
  switches kill throughput.

A scheduler is a *policy* (the rules) implemented by a *mechanism*
(the code that enqueues, picks, and switches). The policy decisions
can be studied in isolation.

### Classical policies

**FIFO / First-Come First-Served.** Run tasks in arrival order. Cheap
and starvation-free, but a short job stuck behind a long one pays
the convoy's price — bad average response time.

**Shortest Job First (SJF).** Optimal for average response time if
you know job length. Starves long jobs; requires an oracle for
length.

![FIFO vs SJF Gantt charts: under FIFO, one long task delays all short tasks (convoy effect); under SJF, short tasks finish first and the long task runs last](figures/badFIFO.png)
*Figure 4.2: The convoy effect under FIFO. Short tasks wait behind a long one, inflating average turnaround time. SJF reverses the order and minimizes average wait — but only if job lengths are known in advance.*

**Round Robin (RR).** Give each task a time quantum. Preempt when
the quantum expires and rotate. Cures starvation; the quantum choice
is a tradeoff between context-switch overhead (short quantum = many
switches) and responsiveness (long quantum = bad for I/O-bound tasks
that only need a short burst of CPU).

![Round Robin with 1 ms vs 100 ms time slices: shorter slices give better responsiveness for short tasks but add more context-switch overhead](figures/badFIFORR.png)
*Figure 4.3: The quantum tradeoff in Round Robin. A 1 ms slice gives every task quick access but multiplies context switches. A 100 ms slice amortizes switch cost but delays short tasks behind long ones — converging toward FIFO behavior.*

**Multi-Level Feedback Queue (MLFQ).** Multiple priority levels.
New tasks start high; tasks that use a full quantum drop a level;
tasks that yield quickly stay high (rewarding interactivity). Most
real-world schedulers — Windows, macOS, pre-CFS Linux — are MLFQ
variants. The Completely Fair Scheduler replaced MLFQ in Linux 2.6.23
with a different idea (virtual runtime) that Chapter 5 will cover.

![MLFQ with four priority levels: new and I/O-bound tasks enter at the top; tasks that exhaust their time slice drop to lower levels with longer slices](figures/mfq.png)
*Figure 4.4: A four-level MLFQ. New or I/O-bound tasks start at priority 1 with short slices. CPU-hungry tasks that consume their quantum drop to lower levels with progressively longer slices. The result is automatic classification of interactive vs batch work.*

A scheduler must also handle the common case where CPU-bound and
I/O-bound tasks share the same machine. I/O-bound tasks use short
CPU bursts between blocking waits; CPU-bound tasks consume their
full quantum. A good scheduler lets the I/O-bound task run quickly
when it wakes, then gives the CPU-bound task the remaining time.

![Workload mixture: one I/O-bound task issues short CPU bursts between I/O waits, while two CPU-bound tasks consume full quanta in the gaps](figures/mixture.png)
*Figure 4.5: A mixed I/O-bound and CPU-bound workload. The I/O-bound task gets quick access on wakeup; CPU-bound tasks fill the remaining time. MLFQ and CFS both handle this well, but for different reasons.*

### Multi-CPU: per-CPU runqueues

A single global runqueue does not scale. Every CPU looking at the
same data structure contends for the lock that protects it. Modern
kernels maintain a **per-CPU runqueue**, with periodic **load
balancing** that migrates tasks when queue lengths diverge.

![Per-CPU runqueue: CPU 0 runs task X on-CPU while tasks A, B, C wait in the RUNNABLE queue; RUNNABLE is not the same as running](figures/one_cpu_one_runqueue.png)
*Figure 4.6: One CPU, one runqueue. Task X is on-CPU; tasks A, B, C are RUNNABLE but waiting. Each additional CPU gets its own runqueue; load balancing migrates tasks between them.* This
introduces a new axis of tension: migrations improve fairness but
destroy cache locality. Pinning a latency-sensitive thread to a CPU
(`taskset`, `sched_setaffinity`) reduces migrations at the cost of
flexibility.

### Practical knobs for experiments

Three knobs we use repeatedly in labs:

- **nice.** A classic UNIX priority hint. Lower nice = higher
  priority. `nice -n 19 ./batch_job` drops the background job almost
  to the floor. No privilege needed for `+` values; `-20` requires
  root.
- **CPU affinity.** `taskset -c 0 ./probe` pins the probe to CPU 0;
  `sched_setaffinity` is the syscall. Useful for isolating
  latency-sensitive work from background load.
- **cgroup CPU controllers.** `cpu.weight` and `cpu.max` bound a
  cgroup's CPU share. Chapter 7's Kubernetes lab turns this into a
  resource-management story.

## 4.5 Preemption and Atomicity

**Preemption** is what makes multi-tasking fair. A periodic timer
interrupt — typically 100–1000 Hz on Linux, configurable via
`CONFIG_HZ` — gives the kernel a chance to re-evaluate which thread
should run. If the current thread's time is up, or a higher-priority
thread has woken, the interrupt handler sets a "need resched" flag;
on return to user space (or at the next preemption point), the
scheduler switches.

This mechanism is why atomicity matters in threaded code. Between
two consecutive C statements, a timer interrupt can arrive, the
scheduler can run, and a different thread can execute arbitrary
code. If the first thread was in the middle of updating a data
structure, the second thread may observe it half-updated. That is
what a mutex, spinlock, or atomic instruction exists to prevent.

Inside the kernel itself, the problem is worse: the scheduler's
data structures (run queues, wait queues) are shared across CPUs
and modified from interrupt context. Linux uses a combination of
spinlocks, interrupt-disable regions, and RCU to keep them
consistent. The details are beyond this book; the fact that the
scheduler's own code must be concurrency-safe is why its
instrumentation (Chapter 5) ends up being a non-trivial exercise.

## 4.6 Scheduling Latency

We have the vocabulary to make the definition precise.

> **Scheduling latency** is the time a thread spends in the
> **Runnable** state — between the moment it becomes ready to run
> and the moment the kernel actually dispatches it to a CPU.

In Linux kernel tracing terms, this is the interval between the
`sched:sched_wakeup` event (thread becomes runnable) and the
`sched:sched_switch` event in which that same thread becomes the
`next` task. Chapter 5 will measure this directly with eBPF.

Why does this matter? Because in any system that is not 100 %
loaded, scheduling latency is the *dominant* source of tail
latency. The math:

- On an idle CPU, a woken thread runs almost immediately —
  scheduling latency is a few microseconds.
- On a contended CPU, a woken thread waits behind however many
  runnable threads are already on the runqueue. Even at 60 %
  average CPU utilization, **micro-bursts** — short windows where
  several threads become runnable together — regularly push
  runqueue depth to 3–5. At 1 ms per quantum, that is milliseconds
  of queuing for something that takes microseconds to compute.
- p99 latency sees those micro-bursts. p50 does not.

This is the classic "CPU utilization is fine, but p99 is terrible"
incident. A real-world example:

> **Incident sketch.** A payment service runs on 4-core nodes at ~55 %
> average CPU. A nightly log-compaction job starts at 02:00 and
> consumes 2 full cores. Average CPU rises to ~70 % — still below
> alarm threshold. But the payment service's p99 jumps from 8 ms to
> 120 ms. The cause: on the two shared cores, the payment handler
> now shares a runqueue with compaction threads. Each time the
> handler wakes from a network read, it waits behind a compaction
> thread's quantum. The fix: `nice -n 19` the compaction job so the
> scheduler gives it leftover CPU without blocking the payment
> handler's wakeups.

The average is fine; the variance is the problem. The
symptom is latency; the mechanism is runqueue queueing; the fix is
to reduce the queue (by nicing background work, pinning the
latency-sensitive task to its own CPU, or isolating it in a cgroup
with guaranteed CPU).

The lab at the end of this chapter is a minimal scheduling-latency
experiment: a periodic probe that measures how late it wakes up,
a background load generator that creates contention, and a
mitigation (nice or affinity) that visibly restores p99. You will
see the theory and the numbers agree.

> **Key insight:** Tail latency is often scheduling latency. If you
> see a p99 spike on a service whose average CPU is far below
> 100 %, runqueue contention is the first place to look.

## Summary

Key takeaways from this chapter:

- A process is the unit of resource ownership; a thread is the unit
  of scheduling. Linux implements threads as lightweight processes
  sharing an address space (`clone` with `CLONE_VM`).
- `fork`/`exec`/`wait`/`exit` compose cleanly: `fork` duplicates,
  `exec` replaces, `wait` reaps. The split is what makes shell
  redirection and job control possible.
- Context switches are the mechanism that enables time-sharing, but
  they have real cost — direct (register save/restore) and indirect
  (cache/TLB refill).
- Scheduling policies navigate competing goals (response,
  turnaround, throughput, fairness, overhead). MLFQ-style ideas
  dominated until Linux 2.6.23 replaced them with the Completely
  Fair Scheduler (Chapter 5).
- **Scheduling latency** — runnable-but-not-running time — is the
  dominant source of tail latency on systems that are not 100 %
  loaded. The lab shows it directly.

## Further Reading

- Arpaci-Dusseau & Arpaci-Dusseau (2018). *OSTEP*, Chapters 4–8
  (Processes and Scheduling), Chapters 26–28 (Concurrency).
- Love, R. (2010). *Linux Kernel Development*, 3rd ed. Chapters 3–4.
- `man 2 fork`, `man 2 clone`, `man 2 execve`, `man 2 sched_setaffinity`.
- `man 7 sched` — Linux scheduling policies and APIs.
- `perf sched` documentation: <https://perf.wiki.kernel.org/>
