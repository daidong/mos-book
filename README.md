# Modern Operating Systems

**Operating Systems for the Cloud-Native and AI Era**

A free, open-source textbook for senior undergraduate and graduate CS students.

📖 **Read online:** <https://daidong.github.io/mos-book/>
📄 **Download PDF:** [book.pdf](book.pdf) (single-volume print edition)

---

## What This Book Is About

Operating systems remain the foundation of every computing stack — from
laptops to Kubernetes clusters to LLM inference servers. Yet most OS
textbooks stop at the kernel boundary. This book goes further: it teaches
core OS concepts (processes, memory, scheduling, I/O, security) through
the lens of **modern systems** — containers, orchestrators, distributed
consensus, storage engines, and AI agent runtimes.

Every chapter follows the same discipline:

1. **Understand** the mechanism (how does CFS schedule? how does fsync
   reach disk?)
2. **Measure** it with real tools (perf, eBPF, cgroup v2 stats, etcd
   metrics)
3. **Explain** the result — connect the numbers to the mechanism

Each chapter ends with a hands-on lab that produces reproducible,
measurable results on a standard Ubuntu VM.

## Target Audience

- Senior undergraduate CS students with basic OS exposure (processes,
  threads, virtual memory)
- Graduate students in systems, cloud computing, or AI infrastructure
- Practicing engineers who want to understand *why* their containers get
  throttled or their p99 spikes

**Prerequisites:** C programming, basic Linux command line, willingness
to run experiments in a VM.

## Table of Contents

### Part I: Foundations

| Chapter | Topic | Lab |
|---------|-------|-----|
| 1 | [Introduction: OS in the Cloud-Native and AI Era](src/part1-foundations/ch01-introduction/index.md) | Environment Setup |
| 2 | [Performance Measurement Methodology — Memory, Translation, and Evidence](src/part1-foundations/ch02-measurement-methodology/index.md) | Quicksort Performance Analysis |
| 3 | [Systematic Debugging of Tail Latency — A Memory-Pressure Case Study](src/part1-foundations/ch03-tail-latency/index.md) | PagerUSE Oncall Simulation |

### Part II: Process Management and Scheduling

| Chapter | Topic | Lab |
|---------|-------|-----|
| 4 | [Processes, Threads, and Concurrency](src/part2-process-scheduling/ch04-processes-threads/index.md) | Scheduling Latency Under Contention |
| 5 | [Linux Scheduler Internals and Observability](src/part2-process-scheduling/ch05-linux-scheduler/index.md) | SchedLab: eBPF Scheduler Tracing |

### Part III: Isolation and Containers

| Chapter | Topic | Lab |
|---------|-------|-----|
| 6 | [Container Foundations: Namespaces and Cgroups](src/part3-isolation-containers/ch06-namespaces-cgroups/index.md) | Build a Mini Container Runtime |
| 7 | [Kubernetes as a Resource Manager](src/part3-isolation-containers/ch07-kubernetes-qos/index.md) | K8s CPU Throttling and OOM |

### Part IV: Distributed Systems

| Chapter | Topic | Lab |
|---------|-------|-----|
| 8 | [Distributed Consensus: Paxos, Raft, and etcd](src/part4-distributed-systems/ch08-consensus-raft/index.md) | Observing Raft in etcd |
| 9 | [Kubernetes Scheduling and the Control Plane](src/part4-distributed-systems/ch09-k8s-scheduling/index.md) | Cluster Scheduling Simulation |

### Part V: Storage

| Chapter | Topic | Lab |
|---------|-------|-----|
| 10 | [File Systems, Page Cache, and Durability](src/part5-storage/ch10-filesystems/index.md) | fsync Latency Measurement |
| 11 | [Distributed Storage: From KV Store to Object Store](src/part5-storage/ch11-distributed-storage/index.md) | Redis and etcd Benchmarks |

### Part VI: Operating Systems for the AI Era

| Chapter | Topic | Labs |
|---------|-------|------|
| 12 | [Agent Runtimes: A New Substrate for OS Thinking](src/part6-ai-era/ch12-agent-runtimes/index.md) | Lab E: Build an Agent Sandbox; Lab F: Profile and Optimize a ReAct Agent |

### Appendices

- [A — Capstone Projects](src/appendices/appendix-a-projects.md)
- [B — Tool Reference](src/appendices/appendix-b-tool-reference.md)
- [C — Environment Setup Guide](src/appendices/appendix-c-environment-setup.md)
- [D — AI Use Policy](src/appendices/appendix-d-ai-policy.md)

## How to Build

This book uses [mdBook](https://rust-lang.github.io/mdBook/) to generate
HTML, PDF, and EPUB outputs. Every push to `main` triggers a GitHub
Actions workflow ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml))
that publishes the rendered site to GitHub Pages, so the public URL
above always tracks the latest commit.

```bash
# Install mdBook (requires Rust)
cargo install mdbook

# Build HTML (one-shot, exits cleanly)
make html

# Build, then open the rendered book in your browser
# (no live-reload server — does not hang)
make preview

# Live-reload server at http://localhost:3000
# (long-running; stop with Ctrl-C)
make serve

# Same as `make serve`, but auto-stops after T seconds
# (safe for agents, scripts, smoke tests)
make serve-bounded T=30

# Validate all internal links and code blocks
make check

# Build PDF via headless Chrome on print.html
make pdf
```

See [Appendix C](src/appendices/appendix-c-environment-setup.md) for
the lab environment (Ubuntu VM + tools).

## How to Contribute

We welcome contributions! Please read:

- [CONTRIBUTING.md](CONTRIBUTING.md) — workflow, PR process, chapter ownership
- [STYLE_GUIDE.md](STYLE_GUIDE.md) — markdown conventions, figures, code blocks

## Authors

- **Dong Dai** — University of Delaware, Department of Computer and
  Information Sciences

## License

This work is licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE)
(CC BY-SA 4.0). You are free to share and adapt this material for any
purpose, including commercially, as long as you give appropriate credit
and distribute your contributions under the same license.

Code samples in the `code/` directory are licensed under the
[MIT License](code/LICENSE) unless otherwise noted.
