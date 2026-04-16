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

## 4.1 The Process Abstraction

<!-- fork/exec/wait/exit lifecycle.
     Process control block (task_struct in Linux).
     Process states: running, ready, blocked.
     SOURCE: week3 figs/process-2.png, fork.png, exec.png, wait.png -->

## 4.2 Context Switching

<!-- What happens during a context switch: save/restore registers,
     switch page tables, flush TLB (or use PCID).
     Cost: typically 1-10 microseconds. -->

## 4.3 Threads and Concurrency

<!-- Why threads? Shared address space, lighter than processes.
     Kernel threads (1:1 model) vs user-level threads (M:N model).
     Linux: threads are processes that share an address space
     (clone with CLONE_VM). -->

## 4.4 Scheduler Fundamentals

<!-- Scheduling policies: FIFO, SJF, Round Robin, MLFQ.
     Tradeoffs: throughput vs latency vs fairness.
     Starvation and priority inversion. -->

## 4.5 Preemption and Atomicity

<!-- Timer interrupts trigger preemption.
     Voluntary vs involuntary context switches.
     Why atomicity matters: race conditions from preemption.
     Connection to locks (preview of synchronization). -->

## 4.6 Scheduling Latency

<!-- Definition: time a task spends runnable but not running.
     This is the core source of tail latency in most systems.
     Measured as wake-to-switch delay.
     Why overloaded CPUs cause p99 spikes. -->

## Summary

Key takeaways from this chapter:

- A process is the OS's unit of resource ownership and protection;
  a thread is the unit of scheduling.
- Context switches are the mechanism that enables time-sharing, but
  they have measurable cost.
- Scheduling latency (runqueue delay) is often the dominant cause of
  tail latency — understanding it is essential for diagnosing p99
  problems.

## Further Reading

- Arpaci-Dusseau & Arpaci-Dusseau (2018). *OSTEP*, Chapters 4-8
  (Processes and Scheduling), Chapters 26-28 (Concurrency).
- Love, R. (2010). *Linux Kernel Development*, 3rd ed. Chapters 3-4.
