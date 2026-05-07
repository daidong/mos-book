# Lab Report: <chapter title> — <lab title>

**Name:**
**Date:**
**Chapter / Lab:**

---

## 1. Environment

Fill in the table below before running any measurements. This is
the minimum required reproducibility record (see Appendix C).

| Property | Value |
|----------|-------|
| OS / kernel (`uname -a`) | |
| Distribution (`lsb_release -a`) | |
| CPU model (`lscpu` — Model name, cores, sockets) | |
| RAM (`free -h`) | |
| Storage device (SSD / HDD / virtual; `lsblk -d`) | |
| Filesystem (`df -T /`) | |
| Host (bare metal / cloud instance / VirtualBox / UTM) | |
| Key tool versions (per the chapter) | |

If you ran in a VM, also paste the VM configuration (vCPUs, RAM,
disk controller).

---

## 2. Part A (Required)

### 2.1 Procedure

Describe the exact commands and inputs you used. Paste them as
code blocks so a peer can copy-paste.

```bash
# commands go here
```

### 2.2 Results

Include at least one table and — where applicable — one figure.
Tables summarize, figures show distributions.

| Metric | Value |
|--------|-------|
| | |

### 2.3 Analysis

Explain *why* the result is what it is. Connect the numbers back
to the mechanism described in the chapter.

---

## 3. Part B (Required)

Same structure: Procedure, Results, Analysis.

---

## 4. Part C (Required or Optional — see lab stub)

Same structure.

---

## 5. Evidence Contract

For each performance or correctness claim in this report, fill in
the table below. The claim is only supported if there are two
independent signals and one exclusion check (see §3 of Chapter 3).

| Claim | Signal 1 | Signal 2 | Excluded |
|-------|----------|----------|----------|
| | | | |
| | | | |

---

## 6. Evidence Trail

See Appendix D for the full AI Use Policy.

### AI Tool Use

- **Tool(s) used:** [e.g., "ChatGPT for debugging a Makefile
  error" / "GitHub Copilot for boilerplate in the plotting script"
  / "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you checked, re-ran, or
  confirmed against your own data]
- **What I changed or rejected:** [if the suggestion was wrong or
  inapplicable, note it here]

### Failures and Iterations

- [Briefly describe at least one thing that did not work on the
  first attempt and what you learned from it.]

---

## 7. Reflection

- One thing that surprised you:
- How this connects to earlier chapters:
- One question you still have:

---

## 8. Artifact

List every file submitted alongside this report. A peer should be
able to regenerate every figure and table from this list.

| File | Description |
|------|-------------|
| `results/run-1.csv` | |
| `scripts/plot.py` | |
| `README.md` | |
