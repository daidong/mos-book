# MOS-BOOK Build Plan

**Last updated:** 2026-04-16
**Status:** Prose-complete — all 13 chapters (index + lab) and
Appendices A–C are drafted from course materials, ~10 200 lines
across 28 files. `mdbook build` succeeds end-to-end with mdbook
v0.5.2. Next phase: expand lab worked examples, wire up CI, add
PDF/EPUB outputs.

---

## Vision

Create a public e-book called **"Modern Operating Systems: Operating Systems
for the Cloud-Native and AI Era"** based on the CISC663 course at the
University of Delaware (`/Users/daidong/Documents/rp-writings/OS-CISC663`).

- Target audience: senior UG / graduate CS students
- Each chapter = theory + integrated hands-on lab
- Content is fully based on the existing course (read-only source)
- Do NOT use anything from `outdated/` or `archive/` folders in the source
- Built with mdBook, written in Markdown

---

## Course-to-Book Mapping

| Book Chapter | Source Week(s) | Topic | Lab |
|---|---|---|---|
| Ch 1 | Week 0 + Week 1 | Introduction — OS in the Cloud-Native and AI Era | Environment Setup (Lab 0) |
| Ch 2 | Week 2A | Performance Measurement Methodology — Memory, Translation, and Evidence | Quicksort Performance Analysis (Lab 1) |
| Ch 3 | Week 2B | Tail Latency and Systematic Debugging | PagerUSE Oncall Simulation (Lab 2) |
| Ch 4 | Week 3 | Processes, Threads, and Concurrency | Scheduling Latency Under Contention (Lab 3) |
| Ch 5 | Week 4 | Linux Scheduler Internals and Observability | SchedLab — eBPF Tracing (Lab 4) |
| Ch 6 | Week 5 | Container Foundations — Namespaces and Cgroups | Build a Mini Container Runtime (Lab 5) |
| Ch 7 | Week 6 | Kubernetes as a Resource Manager | K8s CPU Throttling and OOM (Lab 6) |
| Ch 8 | Week 7 | Distributed Consensus — Paxos, Raft, and etcd | Observing Raft in etcd (Lab 7) |
| Ch 9 | Week 8 | Kubernetes Scheduling and the Control Plane | Cluster Scheduling Simulation (Lab 8) |
| Ch 10 | Week 9 | File Systems, Page Cache, and Durability | fsync Latency Measurement (Lab 9) |
| Ch 11 | Week 10 | Distributed Storage — From KV Store to Object Store | Redis and etcd Benchmarks (Lab 10) |
| Ch 12 | Week 11 | Agent Runtimes — A New Substrate for OS Thinking | Lab E: Build an Agent Sandbox + Lab F: Profile and Optimize a ReAct Agent |
| App A | projects/ | Capstone Projects (4 options) | — |
| App B | Various | Tool Reference (perf, eBPF, cgroup, kubectl) | — |
| App C | Week 0 | Environment Setup Guide | — |
| App D | Week 0 | AI Use Policy | — |

*Removed 2026-04-30:* Ch 13 / Part VII ("Systems Research
Methodology and Reproducibility"). Its essential material —
evidence contract and reproducibility artifacts — is covered
by Chapter 3 §3 and Appendix C respectively, which is
sufficient for the current scope.

---

## Directory Structure

```
mos-book/
├── README.md                           # Book overview, TOC, build instructions
├── CONTRIBUTING.md                     # Contributor guide (workflow, PR rules)
├── STYLE_GUIDE.md                      # Markdown conventions, figure rules
├── PLAN.md                             # This file
├── book.yaml                           # Book metadata
├── Makefile                            # Build targets: html, pdf, epub, serve
│
├── src/                                # All book content
│   ├── SUMMARY.md                      # mdBook table of contents
│   ├── preface.md                      # Author preface
│   │
│   ├── part1-foundations/
│   │   ├── ch01-introduction/
│   │   │   ├── index.md                # Chapter text
│   │   │   ├── lab-environment-setup.md
│   │   │   └── figures/
│   │   ├── ch02-measurement-methodology/
│   │   │   ├── index.md
│   │   │   ├── lab-quicksort-perf.md
│   │   │   └── figures/
│   │   └── ch03-tail-latency/
│   │       ├── index.md
│   │       ├── lab-pageruse.md
│   │       └── figures/
│   │
│   ├── part2-process-scheduling/
│   │   ├── ch04-processes-threads/
│   │   │   ├── index.md
│   │   │   ├── lab-sched-latency.md
│   │   │   └── figures/
│   │   └── ch05-linux-scheduler/
│   │       ├── index.md
│   │       ├── lab-schedlab-ebpf.md
│   │       └── figures/
│   │
│   ├── part3-isolation-containers/
│   │   ├── ch06-namespaces-cgroups/
│   │   │   ├── index.md
│   │   │   ├── lab-mini-container.md
│   │   │   └── figures/
│   │   └── ch07-kubernetes-qos/
│   │       ├── index.md
│   │       ├── lab-k8s-resources.md
│   │       └── figures/
│   │
│   ├── part4-distributed-systems/
│   │   ├── ch08-consensus-raft/
│   │   │   ├── index.md
│   │   │   ├── lab-etcd-raft.md
│   │   │   └── figures/
│   │   └── ch09-k8s-scheduling/
│   │       ├── index.md
│   │       ├── lab-cluster-scheduling.md
│   │       └── figures/
│   │
│   ├── part5-storage/
│   │   ├── ch10-filesystems/
│   │   │   ├── index.md               # STUB NEEDED
│   │   │   ├── lab-fsync-latency.md   # STUB NEEDED
│   │   │   └── figures/
│   │   └── ch11-distributed-storage/
│   │       ├── index.md               # STUB NEEDED
│   │       ├── lab-redis-etcd-bench.md # STUB NEEDED
│   │       └── figures/
│   │
│   ├── part6-ai-era/
│   │   └── ch12-agent-runtimes/
│   │       ├── index.md
│   │       ├── lab-agent-sandbox.md
│   │       ├── lab-react-perf.md
│   │       └── figures/
│   │
│   └── appendices/
│       ├── appendix-a-projects.md      # STUB NEEDED
│       ├── appendix-b-tool-reference.md # STUB NEEDED
│       └── appendix-c-environment-setup.md # STUB NEEDED
│
├── code/                               # Lab source code by chapter
│   ├── ch02-quicksort/                 # from week2A/lab1_quicksort/
│   ├── ch03-pageruse/                  # from week2B/lab2_pageruse/
│   ├── ch04-sched-latency/             # from week3/lab3_sched_latency/
│   ├── ch05-schedlab/                  # from week4/schedlab/
│   ├── ch06-minictl/                   # from week5/minictl/
│   ├── ch07-k8s-resources/             # from week6+week7 K8s manifests
│   ├── ch08-etcd-raft/                 # from week7 etcd scripts
│   ├── ch09-cluster-sched/             # from week8 simulator + manifests
│   ├── ch10-fsync-bench/               # from week9 write_latency.c
│   ├── ch11-redis-etcd/                # from week10 benchmark scripts
│   └── ch12-agent-sandbox/             # from week11/sandbox/
│
├── projects/                           # Capstone project descriptions
│   ├── 01-incident-observability/      # Red/Blue Oncall Game
│   ├── 02-multihop-k8s/               # Multi-hop Service Tail Latency
│   ├── 03-llm-inference/              # LLM Inference Server Profiling
│   └── 04-swe-agent/                  # SWE-agent Runtime Profiling
│
├── templates/                          # Report templates
│   ├── lab-report-template.md
│   ├── final-report-template.md
│   └── reproduction-report-template.md
│
└── scripts/
    ├── build.sh
    └── check-links.sh
```

---

## Completion Status

### Done

- [x] Full directory structure created (all folders + .gitkeep files)
- [x] `README.md` — book overview, TOC table, build instructions, license note
- [x] `CONTRIBUTING.md` — fork/PR workflow, branch naming, commit conventions,
      chapter ownership, PR checklist, figure guidelines
- [x] `STYLE_GUIDE.md` — heading levels, code blocks, callout boxes, figure
      naming/alt text, lab tiered structure, terminology table, citation format
- [x] `book.toml` — mdBook metadata and build configuration
      (converted from earlier `book.yaml`, which has been removed)
- [x] `Makefile` — targets for html, serve, pdf, epub, check, clean
- [x] `src/SUMMARY.md` — full mdBook table of contents
- [x] `src/preface.md` — author preface with reading guide
- [x] Chapter stubs (index.md + lab .md) for **Chapters 1-13** (Parts I-VII)
      and **Appendices A-C**
      - Each stub has: learning objectives, numbered section headings with
        `<!-- SOURCE: -->` comments pointing to course material, summary,
        further reading, and lab structure (Parts A/B/C + deliverables)

### Completed — Chapter Stubs (2026-04-16)

- [x] `src/part5-storage/ch10-filesystems/index.md` — File Systems, Page Cache, Durability
- [x] `src/part5-storage/ch10-filesystems/lab-fsync-latency.md`
- [x] `src/part5-storage/ch11-distributed-storage/index.md` — Distributed Storage
- [x] `src/part5-storage/ch11-distributed-storage/lab-redis-etcd-bench.md`
- [x] `src/part6-ai-era/ch12-agent-runtimes/index.md` — Agent Runtimes (safety + performance lenses)
- [x] `src/part6-ai-era/ch12-agent-runtimes/lab-agent-sandbox.md` (Lab E)
- [x] `src/part6-ai-era/ch12-agent-runtimes/lab-react-perf.md` (Lab F — from week11)
- [removed 2026-04-30] `src/part7-synthesis/ch13-methodology-reproducibility/`
- [x] `src/appendices/appendix-a-projects.md`
- [x] `src/appendices/appendix-b-tool-reference.md`
- [x] `src/appendices/appendix-c-environment-setup.md`

### Completed — Other (2026-04-16)

- [x] Copied lab source code into `code/` (ch02-ch07, ch12 from course
      week dirs; ch08/ch09/ch10/ch11 have starter READMEs and
      skeletons where the lab is instruction-driven or tool-driven).
- [x] Copied 4 project descriptions into `projects/`.
- [x] Copied `final-report-template.md` and `reproduction-report-template.md`
      from week12; wrote a generic `lab-report-template.md`.
- [x] Copied targeted figures (ch02 memory/paging, ch04 process
      lifecycle, ch05 scheduler+eBPF, ch06 containers, ch09 K8s
      architecture, ch10 filesystem). Other chapter `figures/`
      dirs are intentionally empty until the prose references
      specific images.
- [x] Added `.gitignore` covering mdBook output, macOS metadata,
      node_modules, Python caches, and lab compiled binaries.
- [x] Converted `book.yaml` → `book.toml` (mdBook native format).
- [x] `mdbook build` succeeds end-to-end (mdbook v0.5.2); output
      lands in `book/`.

### Prose Fill Pass (2026-04-16)

- [x] Fill chapter prose: replace SOURCE comments with text drawn
      from the referenced course materials.
      All 13 chapters (index + lab) and Appendices A–C now have
      complete prose, written to the quality bar set by Chapter 1.
      `mdbook build` succeeds end-to-end. Total: ~10 200 lines
      across 28 prose files.

### Next Phase

- [ ] Expand lab deliverable sections with worked examples.
- [ ] Wire up CI to run `mdbook build` + `mdbook test` on PR.
- [ ] Decide on PDF / EPUB backends and test those paths.

---

## Content Gaps and Recommendations

These topics are not fully covered in the current course but could strengthen
the book in future editions:

| Topic | Current Status | Recommendation |
|---|---|---|
| Memory management (paging, VM in depth) | Brief in Ch 2 (Week 2A) | Could expand into its own chapter between Ch 2 and Ch 3 |
| Network data plane | Listed in README schedule but no dedicated week content | Consider adding a chapter if content is developed |
| I/O subsystem (block I/O, device drivers) | Implicit in Ch 10 (Week 9) | Could add a section before filesystems |
| Classical OS security (access control, capabilities) | Only agent security in Ch 12 | Could bridge classical -> agent security |
| GPU / accelerator scheduling | Mentioned in LLM context | Natural extension of Ch 12 |
| IPC (pipes, shared memory, sockets) | Not explicitly covered | Consider adding if relevant labs exist |

**Recommendation:** Ship the 13-chapter book first. Mark gaps as "Future
Chapters" in a public roadmap.

---

## Key Design Decisions

1. **Chapters organized by theme, not by week.** Weekly ordering is for
   semester pacing; book readers need logical conceptual progression.

2. **Labs integrated in each chapter**, not separated into an appendix.
   The lab is the second half of the chapter, not a separate artifact.

3. **Figures co-located with chapters** (`ch*/figures/`), not in a global
   dump. Easier to maintain, review, and attribute.

4. **Code separated from prose** (`code/` vs `src/`). Chapters reference
   code via relative links. This keeps prose clean and code runnable.

5. **Tiered lab difficulty** (A=basic required, B=intermediate required,
   C=advanced optional). Serves both UG and graduate audiences.

6. **Evidence contract** throughout: every claim backed by 2 independent
   signals + 1 exclusion check. This is the course's core methodology.

7. **mdBook** as the build tool — lightweight, Rust-based, widely used
   for technical books. Outputs HTML (primary), PDF, EPUB.

---

## Source Material Reference

All content comes from: `/Users/daidong/Documents/rp-writings/OS-CISC663/`

**Excluded:** `outdated/`, `archive/`, `old_markdowns/` directories.

**Key source files per chapter:**

- Ch 1: week0/reading_map.md, week1/week1_slides.md, week1/lab0_instructions.md
- Ch 2: week2A/week2A_slides.md, week2A/reading_guide_week2.md, week2A/lab1_instructions.md
- Ch 3: week2B/week2B_slides.md, week2B/reading_guide.md, week2B/lab2_instructions.md
- Ch 4: week3/week3_slides.md, week3/reading_guide.md, week3/lab3_instructions.md
- Ch 5: week4/week4_slides_v2.md, week4/ebpf_quickstart.md, week4/lab3_instructions.md
- Ch 6: week5/week5_slides_v2.md, week5/reading_guide.md, week5/lab5_instructions.md
- Ch 7: week6/week6_final_slides.md, week6/lab6_rubric.md
- Ch 8: week7/week7_paxos.md, week7/reading_guide.md, week7/lab7_raft_instructions.md
- Ch 9: week8_real/week8_v3.md, week8_real/lab8_scheduling_instructions.md
- Ch 10: week9_fs/week9_slides.md, week9_fs/lab9_instructions.md
- Ch 11: week10_dist/week10_slides.md, week10_dist/lab10_instructions.md
- Ch 12: week11/week11_slides.md, week11/lab_f/lab_f_instructions.md, week11/starter/ (agent.py, tracer.py, waterfall.py); legacy security version retained in week11/*.bak_security_version
- Ch 13: week12/README.md, week12/grading_rubric.md, week12/final_report_template.md

**Figures available:**
- `comm-figs/` — 217 shared figures (memory, sync, FS, networking, etc.)
- `week2A/images/` — 15 PNGs (memory hierarchy, TLB, paging, pipelines)
- `week3/figs/` — 4 PNGs (process lifecycle)
- `week4/figures/` — 20+ diagrams (scheduler, eBPF)
- `week5/figures/` — 4 SVGs (container architecture)
- `week6/figs/` — 150+ images (broad OS topics)
- `week9_fs/figs/` — 10 images (COW, FFS, FAT, links, I/O bus)
