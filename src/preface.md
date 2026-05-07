# Preface

## Why This Book Exists

Operating systems are the invisible infrastructure beneath every computation — from the process scheduler deciding which thread runs next, to the page cache absorbing your writes before they reach disk, to the cgroup enforcing a container's memory limit. These mechanisms have not changed in their essence. What has changed is the scale and context in which they operate.

Today, a single Kubernetes cluster orchestrates thousands of containers across hundreds of nodes. An LLM inference server manages gigabytes of model weights under tight latency budgets. An AI coding agent issues tool calls that look remarkably like system calls — and need the same isolation, auditing, and resource control that operating systems have provided to processes for decades.

This book teaches operating system concepts through these modern contexts. It is not a replacement for the classic OS textbook; it is what comes after. We assume you have seen processes, threads, and virtual memory before. What we add is the discipline of *measurement* — the ability to observe a running system, form a hypothesis about its behavior, design a controlled experiment, and explain the result by tracing it to an OS mechanism.

## Who This Book Is For

- **Senior undergraduates** with one prior OS course who want to connect theory to practice
- **Graduate students** in systems, cloud computing, or AI infrastructure who need to reason about performance and isolation
- **Practicing engineers** who want to understand why their containers get throttled, their p99 spikes, or their distributed writes are slow

## Pedagogical Philosophy

The recent literature on systems education and on generative AI in computing courses converges on a clear conclusion: the classical OS mechanisms — processes, scheduling, memory management, I/O, concurrency, isolation — remain the intellectual core of the field. The literature does not support replacing those topics with fashionable platform-specific content. What it does support is teaching classical mechanisms more deliberately through modern systems contexts, while redesigning assessment for a world where students have access to large language models.

This book is built around three ideas that reflect that consensus.

### Mechanism, Evidence, Judgment

Every chapter trains the same triad:

- **Mechanism.** Students understand how the system works: scheduling, memory, concurrency, I/O, durability, isolation. "What is the mechanism?" always comes first. We define it precisely, explain how it works step by step, identify the relevant kernel–hardware–user-space boundary, and show at least one failure mode.

- **Evidence.** Students can instrument, benchmark, trace, and reproduce. A claim such as "fsync is expensive" is not complete until it has a workload, a baseline, a repeat count, and a number. Every lab requires raw artifacts from the student's own environment — not screenshots from a tutorial, not output pasted from a language model.

- **Judgment.** Students can interpret results, critique tool output, and defend design decisions. This is where the course diverges most from traditional OS pedagogy. We do not just ask "what happened?" We ask "why did it happen, what alternative explanations did you rule out, and how would you verify your diagnosis?" That reasoning process is the durable skill — it transfers across tools, platforms, and decades.

The triad is deliberately ordered. Understanding without measurement is theory. Measurement without understanding is data collection. Neither produces the judgment that systems work demands.

### Modern Contexts as Applications, Not Replacements

Containers, Kubernetes, eBPF, distributed consensus, and LLM workloads appear throughout the book. They are not replacements for OS concepts — they are the best current vehicles for making those concepts legible and worth caring about.

When we discuss container isolation, the teaching target is namespaces and cgroups: what the kernel actually does when `clone()` receives `CLONE_NEWPID | CLONE_NEWNS`. When we discuss Kubernetes CPU throttling, the teaching target is CFS bandwidth control: how quota exhaustion maps to `cpu.stat:nr_throttled` and why that produces bimodal tail latency. When we discuss etcd write latency, the teaching target is `fsync` and the journal: why 2–10 ms per write is a fundamental cost of durability, not a tuning failure.

The test for whether a modern context belongs in the course is simple: does it make an OS mechanism more observable, more consequential, or more interesting? If yes, it earns its place. If it is only scenery — a name-drop that does not change the explanation — it does not.

### Assessment Designed for the AI Era

Students will use AI tools. Prohibiting them entirely is neither enforceable nor pedagogically productive. But unrestricted AI assistance encourages shallow "generate-fix-regenerate" behavior and makes traditional code-only or text-only submissions weak evidence of learning.

This book takes a structured position: AI is allowed, bounded, and made transparent. The details are in the AI Use Policy that accompanies this book, but the core principle is straightforward. Every lab is designed so that the grading weight falls on artifacts that AI cannot produce from generic knowledge:

- **Pre-run predictions** that require understanding the mechanism before seeing the data.
- **Raw evidence from the student's own environment** — traces, counters, logs, latency distributions — that are specific to a particular machine, kernel, and workload configuration.
- **Interpretation of discrepancies** between prediction and observation, including at least one alternative explanation explicitly ruled out.
- **Evidence trails** that document what was tried, what failed, what changed, and — when relevant — what an AI tool suggested and what the student independently verified.

The goal is not to detect AI use. It is to make the assessment meaningful regardless of whether AI was used. A student who uses an LLM to draft a report but cannot explain the p99 spike in their own data has not completed the lab. A student who uses an LLM to understand a man page faster and then produces a sharper diagnosis has used the tool well.

Where feasible, instructors should add oral components — even 5–8 minute checkoffs per lab. Short live explanations are the single most effective complement to written evidence in a systems course. They catch the gap between "I submitted the report" and "I understand the system."

## How to Read This Book

Each chapter has two halves: exposition and a hands-on lab. The exposition introduces the mechanism; the lab makes you measure it. We strongly recommend doing the labs — reading about tail latency is not the same as producing a p99 spike and diagnosing its cause.

The book is organized in six parts:

- **Part I** (Chapters 1–3) establishes the measurement methodology that the rest of the book relies on: tracing, profiling, percentile reasoning, the USE method, and evidence chains.
- **Part II** (Chapters 4–5) covers processes, scheduling, and Linux scheduler internals with eBPF-based observation.
- **Part III** (Chapters 6–7) moves from kernel mechanisms to container isolation and Kubernetes resource management.
- **Part IV** (Chapters 8–9) introduces distributed consensus (Paxos, Raft, etcd) and cluster-level scheduling.
- **Part V** (Chapters 10–11) covers local and distributed storage: the page cache, ext4, fsync, Redis durability, and object storage.
- **Part VI** (Chapter 12) applies OS concepts to AI agent runtimes through two complementary lenses — safety (tool calls as syscalls) and performance (agent runtime as server workload).

Parts I–III should be read in order. Parts IV and V can be read in either order. Part VI assumes familiarity with Parts I–III. The capstone projects in Appendix A are the intended vehicle for synthesizing material across parts; they expect students to apply the evidence contract from Chapter 3 and to ship reproducibility artifacts using the environment-pinning practices in Appendix C.

## A Note on the Literature

The pedagogical choices in this book are informed by several strands of recent work. The OS-teaching literature, anchored by Ebling's 2024 survey of OS instructors and course designs (ACM TOCE, 10.1145/3688853), confirms that the classical mechanism set — system calls, processes, concurrency, scheduling, virtual memory, file systems, and performance evaluation — remains the center of gravity in OS education, even as platforms evolve. The stronger recent literature on generative AI in computing education (Prather et al. 2023; Denny et al. 2024; Borges et al. 2024) converges on a practical consensus: students will use AI, scaffolded use is more productive than prohibition, and assessment must shift from artifacts to reasoning. The hands-on systems-education papers (Gebhard et al. 2024 on RISC-V teaching OS; Gu, Liu, and Zhao 2024 on the miniOS pilot class with oral defenses; Trivedi et al. 2024 on reviving storage education) reinforce that the strongest courses combine classical mechanisms with updated platforms and evidence-centered assessment.

This book's position — keep the OS core, modernize the contexts, make instrumentation central, and design assessment for AI — is a synthesis of those findings, applied to a graduate-level course.

## Acknowledgments

This book grew out of the CISC663 course at the University of Delaware. The author thanks all students who tested early versions of these labs and provided invaluable feedback.

---

*Dong Dai*
*University of Delaware*
