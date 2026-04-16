# Final Project Report Template

**Project Title:**  
**Team Members:**  
**Date:**  

---

## Abstract (150 words max)

One paragraph summarizing: problem, approach, key result, main insight.

---

## 1. Introduction

### 1.1 Problem Statement

What phenomenon or problem are you investigating? Why does it matter?

Be specific:
- "We investigate why p99 latency increases by 3x when adding a service mesh sidecar to a containerized service."
- NOT: "We study container networking performance."

### 1.2 Hypothesis

What do you expect to observe, and why?

Example:
- "We hypothesize that the latency increase is primarily due to additional context switches introduced by the sidecar proxy process."

### 1.3 Scope and Limitations (Upfront)

What is explicitly out of scope? What assumptions are you making?

---

## 2. Background (1–2 pages)

### 2.1 Relevant OS Mechanisms

Explain the OS concepts relevant to your project. Reference course materials.

Example sections:
- CFS bandwidth control and CPU throttling
- Page cache and fsync semantics
- Network namespace and veth pairs
- Seccomp BPF filter execution

### 2.2 Related Work

What prior work exists? How does your investigation differ?

---

## 3. Methodology (2–3 pages)

### 3.1 Experimental Setup

#### Hardware

| Component | Specification |
|-----------|---------------|
| CPU | |
| RAM | |
| Storage | SSD / HDD |
| Network | |

#### Software

| Component | Version |
|-----------|---------|
| OS | |
| Kernel | |
| Key dependencies | |

### 3.2 Baseline Configuration

Describe your baseline. Why is this a valid baseline?

### 3.3 Intervention(s)

What variable(s) did you change? Why?

| Experiment | Baseline | Intervention | What Changes |
|------------|----------|--------------|--------------|
| Exp 1 | | | |
| Exp 2 | | | |

### 3.4 Workload

Describe the workload used for testing:
- Type (synthetic / realistic)
- Parameters (request rate, concurrency, data size)
- Duration and warmup period

### 3.5 Metrics

| Metric | Definition | Collection Method | Units |
|--------|------------|-------------------|-------|
| Latency p50 | | | ms |
| Latency p95 | | | ms |
| Latency p99 | | | ms |
| Throughput | | | req/s |
| CPU usage | | | % |
| Memory | | | MiB |

### 3.6 Measurement Protocol

1. Step-by-step procedure
2. How many runs?
3. How did you handle warmup?
4. How did you ensure isolation from background processes?

---

## 4. Results (2–3 pages)

### 4.1 Main Results

Present your key findings with data.

#### Table: Summary Statistics

| Metric | Baseline | Intervention | Δ | Δ% |
|--------|----------|--------------|---|-----|
| p50 (ms) | | | | |
| p95 (ms) | | | | |
| p99 (ms) | | | | |
| Throughput | | | | |

#### Figures

Include graphs with:
- Clear axis labels and units
- Legend
- Error bars or confidence intervals where appropriate

Figure 1: [Description]

Figure 2: [Description]

### 4.2 Secondary Findings

Any unexpected observations? Anomalies?

### 4.3 Statistical Significance (If Applicable)

How confident are you in the results? What is the variance across runs?

---

## 5. Interpretation (1–2 pages)

### 5.1 Mechanism Explanation

Why do you see these results? Point to specific OS mechanisms.

**Good:**
- "The 2.5x p99 increase correlates with a 3x increase in context switches, as measured by `perf stat`. This is consistent with the sidecar proxy handling each request in a separate process context."

**Bad:**
- "The sidecar makes things slower."

### 5.2 Evidence Chain

Connect your metrics to your explanation:

1. Observation: [metric]
2. Supporting evidence: [tracing data, perf counters, logs]
3. Mechanism: [OS component]

### 5.3 Alternative Explanations

What else could explain your results? Why do you favor your explanation?

---

## 6. Limitations (0.5–1 page)

Be honest. What could change your conclusions?

### 6.1 Threats to Validity

- Internal validity: measurement artifacts, confounding variables
- External validity: does this generalize to other environments?

### 6.2 What You Would Do Differently

If you had more time/resources, what would you improve?

---

## 7. Conclusion (0.5 page)

### 7.1 Summary of Findings

Restate your main result in 2–3 sentences.

### 7.2 Implications

What should practitioners take away from this?

### 7.3 Future Work

What questions remain open?

---

## References

Use a consistent citation format.

---

## Appendix A: Reproduction Instructions

(This can reference your separate README, but include a summary here)

### Quick Start

```bash
# Clone repository
git clone [url]
cd [project]

# Setup environment
./setup.sh

# Run experiments
./run_experiments.sh

# Generate figures
./analyze.sh
```

### Expected Runtime

- Setup: ~X minutes
- Experiments: ~Y minutes per configuration
- Total: ~Z minutes

### Expected Results

Include reference values for key metrics so reproducers can compare.

---

## Appendix B: Raw Data

Either include or reference location of:
- Raw measurement logs
- Configuration files used
- Any scripts not in main repo
