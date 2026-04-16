# Preface

Operating systems are the invisible infrastructure beneath every
computation — from the process scheduler deciding which thread runs
next, to the page cache absorbing your writes before they reach disk,
to the cgroup enforcing a container's memory limit. These mechanisms
have not changed in their essence. What has changed is the scale and
context in which they operate.

Today, a single Kubernetes cluster orchestrates thousands of containers
across hundreds of nodes. An LLM inference server manages gigabytes of
model weights under tight latency budgets. An AI coding agent issues
tool calls that look remarkably like system calls — and need the same
isolation, auditing, and resource control that operating systems have
provided to processes for decades.

This book teaches operating system concepts through these modern
contexts. It is not a replacement for the classic OS textbook; it is
what comes after. We assume you have seen processes, threads, and
virtual memory before. What we add is the discipline of **measurement**
— the ability to observe a running system, form a hypothesis about its
behavior, design a controlled experiment, and explain the result by
tracing it to an OS mechanism.

## Who This Book Is For

- **Senior undergraduates** with one prior OS course who want to
  connect theory to practice
- **Graduate students** in systems, cloud computing, or AI
  infrastructure who need to reason about performance and isolation
- **Practicing engineers** who want to understand why their containers
  get throttled, their p99 spikes, or their distributed writes are slow

## How to Read This Book

Each chapter has two halves: exposition and a hands-on lab. The
exposition introduces the mechanism; the lab makes you measure it. We
strongly recommend doing the labs — reading about tail latency is not
the same as producing a p99 spike and diagnosing its cause.

The book is organized in seven parts that build on each other:

- **Part I** (Chapters 1-3) establishes the measurement methodology
  that the rest of the book relies on.
- **Part II** (Chapters 4-5) covers processes, scheduling, and Linux
  scheduler internals.
- **Part III** (Chapters 6-7) moves from kernel mechanisms to
  container isolation and Kubernetes resource management.
- **Part IV** (Chapters 8-9) introduces distributed consensus and
  cluster-level scheduling.
- **Part V** (Chapters 10-11) covers local and distributed storage.
- **Part VI** (Chapter 12) applies OS concepts to AI agent runtimes.
- **Part VII** (Chapter 13) synthesizes everything into systems
  research methodology.

You can read Parts I-III linearly. Parts IV and V can be read in either
order. Part VI assumes familiarity with Parts I-III.

## Acknowledgments

This book grew out of the CISC663 course at the University of Delaware.
The author thanks all students who tested early versions of these labs
and provided invaluable feedback.

---

*Dong Dai*
*University of Delaware*
