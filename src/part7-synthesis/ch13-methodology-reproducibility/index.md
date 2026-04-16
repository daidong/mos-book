# Chapter 13: Systems Research Methodology and Reproducibility

> **Learning objectives**
>
> After completing this chapter, you will be able to:
>
> - Design a systems experiment that isolates the variable you
>   actually care about from the ones you do not
> - Apply the evidence contract introduced in Chapter 3 —
>   two independent signals plus one exclusion check — to any
>   performance or correctness claim in your own work
> - Produce a reproducibility artifact (code, data, configuration,
>   and script) that lets a peer reproduce your result from scratch
> - Review a peer's artifact the way a program committee would:
>   does the code run, does it reproduce the claim, are the
>   claims the paper makes actually supported by the evidence?

## 13.1 What Makes a Systems Experiment

<!-- A systems experiment is a controlled comparison.
     Independent variable: the thing you change (batch size,
       scheduler, fsync policy).
     Dependent variable: the thing you measure (latency, throughput,
       correctness).
     Controlled variables: everything else (hardware, kernel, noise).
     SOURCE: week12/README.md; week12/grading_rubric.md -->

## 13.2 The Evidence Contract

<!-- Every performance claim must come with:
       1. Two independent signals (application timing + kernel
          counter; client-side latency + server-side metric).
       2. One exclusion check (ruled out cache effect, CPU
          saturation, network variability, clock skew).
     A claim with only one signal is a hypothesis, not a result.
     Recap and elaboration of the contract from Chapter 3.
     SOURCE: week12/grading_rubric.md; week2B material -->

## 13.3 Reproducibility Standards

<!-- At minimum, a reproducible artifact provides:
       - Exact OS / kernel / library / tool versions.
       - A script that sets up the environment from scratch
         (Dockerfile, ansible, or a documented `setup.sh`).
       - The raw data the plots are derived from.
       - The analysis script that produces every figure.
       - A README that states: "to reproduce Figure N, run X."
     ACM Badging: Available, Functional, Reusable, Reproduced.
     SOURCE: week12/README.md reproducibility section -->

## 13.4 Common Pitfalls

<!-- Cold vs warm caches.
     Measurement overhead changing the thing being measured.
     Turbo frequency, CPU affinity, NUMA effects.
     Noisy neighbors (Chapter 7) and interrupts.
     P50 hiding tail behavior (Chapter 3).
     Cherry-picked runs. -->

## 13.5 Peer Review as a Systems Skill

<!-- Read the abstract and write down what claims it makes.
     For each claim, check the evidence. Missing signal? Missing
     exclusion? Is the workload realistic?
     Try to reproduce the headline number. If you can't, that
     alone is a useful review comment.
     SOURCE: week12/grading_rubric.md peer review criteria -->

## 13.6 From Student to Practitioner

<!-- These habits outlast any specific technology.
     Systems come and go — fsync, Raft, cgroups, agents —
     but disciplined measurement and honest reporting do not.
     The point of the course and of this book.
     SOURCE: week12/README.md conclusion -->

## Summary

Key takeaways from this chapter and the book:

- Good systems work is the habit of matching every claim to
  evidence, and every result to a reproducible artifact.
- The evidence contract is the through-line from Chapter 3 to
  here; it is the habit that transfers most durably to practice.
- Reproducibility is a gift to your future self and to the
  community; the cost of building the artifact is almost always
  less than the cost of rebuilding it later.

## Further Reading

- ACM Artifact Review and Badging. `www.acm.org/publications/policies/artifact-review-and-badging-current`.
- Collberg, C. and Proebsting, T. A. (2016). Repeatability in
  computer systems research. *CACM* 59(3).
- Jain, R. (1991). *The Art of Computer Systems Performance
  Analysis.* Wiley. (Dated but still the best single reference.)
- Heiser, G. (2020). Systems benchmarking crimes.
  `www.cse.unsw.edu.au/~gernot/benchmarking-crimes.html`.
