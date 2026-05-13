# Preface

A checkout pod has just gone from 8 ms to 180 ms at p99. CPU is below
its request, memory is below its limit, no restarts. One engineer
escalates to the application team. Another opens a shell on the node,
reads `cpu.stat`, watches `nr_throttled` climbing, and asks which CFS
period ran out of quota first. Within minutes she has named the kernel
mechanism, the control surface above it, and the fix.

The gap between those two responses is what this book teaches.

## Why This Book Exists

The classical mechanisms of an operating system — processes, scheduling,
memory, I/O, concurrency, isolation — have not changed in their essence.
Their scale and context have. A single Kubernetes cluster orchestrates
thousands of containers across hundreds of nodes. An LLM inference
server manages gigabytes of model weights under a tight latency budget.
An AI coding agent issues tool calls that look remarkably like system
calls and need the same isolation, auditing, and resource control the
kernel has provided to processes for decades.

This book teaches operating systems through those contexts. It assumes
you have already seen processes, threads, and virtual memory in a prior
course. What it adds is *measurement*: observing a running system,
forming a hypothesis about its behavior, designing a controlled
experiment, and tracing the result back to a kernel mechanism.

## Who This Book Is For

- **Senior undergraduates** with one prior OS course who want to connect
  theory to practice
- **Graduate students** in systems, cloud computing, or AI infrastructure
  who need to reason about performance and isolation
- **Practicing engineers** who want to understand why their containers
  get throttled, their p99 spikes, or their distributed writes are slow

## How the Book Teaches

Every chapter trains the same three habits, in order: understand the
mechanism, gather evidence about it, exercise judgment over the result.

**Mechanism comes first.** We define the abstraction precisely, walk
through how it works step by step, identify the kernel–hardware–user-space
boundary that owns each piece, and show at least one failure mode. A
reader who finishes a section should be able to draw the picture from
memory.

**Evidence comes second.** A claim like "fsync is expensive" is
incomplete until it has a workload, a baseline, a repeat count, and a
number. Every lab requires raw artifacts from the student's own
environment — not screenshots from a tutorial, not output pasted from a
chatbot.

**Judgment is where the book diverges from most OS courses.** Rather than
asking only "what happened?", every lab asks why it happened, what
alternative explanations the student ruled out, and how the diagnosis
would be verified. The specific tool of 2025 will be obsolete by the
time most readers finish their careers; that habit will not.

### Modern Contexts as Vehicles

Containers, Kubernetes, eBPF, distributed consensus, and LLM workloads
appear throughout the book because they make OS mechanisms more
observable, more consequential, and more interesting to teach. When we
discuss container isolation, the teaching target is namespaces and
cgroups: what the kernel does when `clone()` receives
`CLONE_NEWPID | CLONE_NEWNS`. When we discuss Kubernetes CPU throttling,
the teaching target is CFS bandwidth control: how quota exhaustion maps
to `cpu.stat:nr_throttled` and produces bimodal tail latency. When we
discuss etcd write latency, the teaching target is `fsync` and the
journal: 2–10 ms per write is a fundamental cost of durability, not a
tuning failure.

A platform name earns its place in a chapter when it changes the
explanation. When it is only scenery, we leave it out.

### Labs Built for an AI-Saturated Class

Students will use AI tools. Banning them is neither enforceable nor
pedagogically useful, but unrestricted use encourages a shallow
generate-fix-regenerate loop and turns plain code or plain text
submissions into weak evidence of learning.

Every lab in this book is graded on artifacts an LLM cannot produce
from generic knowledge. Each one asks for a pre-run prediction; raw
evidence from the student's own machine — traces, counters, logs,
latency distributions tied to a specific kernel and workload; an
interpretation of any gap between prediction and observation; and at
least one alternative explanation explicitly ruled out. Where
instructors can manage it, a five-to-eight-minute oral check per lab
catches the gap between "I submitted the report" and "I understand the
system." The full policy is in Appendix D.

## How to Read This Book

Each chapter has two halves: exposition and a hands-on lab. The
exposition introduces the mechanism; the lab makes you measure it.
Reading about tail latency is not the same as producing a p99 spike and
diagnosing its cause, and the chapters are written assuming you do both.

The book is in six parts:

- **Part I (Chapters 1–3)** establishes the measurement methodology the
  rest of the book relies on: tracing, profiling, percentile reasoning,
  the USE method, and evidence chains.
- **Part II (Chapters 4–5)** covers processes, scheduling, and Linux
  scheduler internals, observed through eBPF.
- **Part III (Chapters 6–7)** moves from kernel mechanisms to container
  isolation and Kubernetes resource management.
- **Part IV (Chapters 8–9)** introduces distributed consensus (Paxos,
  Raft, etcd) and cluster-level scheduling.
- **Part V (Chapters 10–11)** covers local and distributed storage: the
  page cache, ext4, fsync, Redis durability, and object storage.
- **Part VI (Chapter 12)** applies OS concepts to AI agent runtimes
  through two lenses: safety (tool calls as syscalls) and performance
  (agent runtime as server workload).

Parts I–III should be read in order. Parts IV and V can be read in
either order. Part VI assumes Parts I–III. The capstone projects in
Appendix A synthesize material across parts and expect students to
apply the evidence contract from Chapter 3 and the environment-pinning
practices in Appendix C.

## A Note on the Literature

The pedagogical choices here are informed by several strands of recent
work. Ebling's 2024 survey of OS instructors and course designs (ACM
TOCE, 10.1145/3688853) shows that the classical mechanism set — system
calls, processes, concurrency, scheduling, virtual memory, file systems,
performance evaluation — remains the center of gravity in OS education
even as platforms evolve. Work on generative AI in computing classrooms
(Prather et al. 2023; Denny et al. 2024; Borges et al. 2024) reports
that students use AI tools regardless of policy, that scaffolded use
outperforms prohibition, and that assessment must shift from artifacts
toward reasoning. The hands-on systems-education papers (Gebhard et al.
2024 on RISC-V teaching OS; Gu, Liu, and Zhao 2024 on the miniOS pilot
with oral defenses; Trivedi et al. 2024 on reviving storage education)
report that the strongest courses combine the classical mechanism set
with updated platforms and evidence-centered assessment.

Keep the OS core, modernize the contexts, make instrumentation central,
and design assessment to remain meaningful when AI is in the room. That
is the position this book takes.

## Acknowledgments

This book grew out of the CISC663 course at the University of Delaware.
I thank the students who tested early versions of these labs and
provided detailed, often unsparing, feedback.

---

*Dong Dai*
*University of Delaware*
