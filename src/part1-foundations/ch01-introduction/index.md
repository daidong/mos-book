# Chapter 1: Introduction — OS in the Cloud-Native and AI Era

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why OS concepts remain relevant in the age of containers,
>   orchestrators, and AI agents
> - Describe the three core skills this book develops: Understand,
>   Measure, Explain
> - Set up a reproducible experiment environment (Ubuntu VM with perf,
>   strace, and basic observability tools)
> - Run your first performance measurement and interpret the output

## 1.1 Why Operating Systems Still Matter

<!-- SOURCE: week1 slides + week0 reading_map.md -->
<!-- Cover: OS as the layer between hardware and applications,
     now extended to containers, K8s, and agent runtimes -->

## 1.2 The Modern OS Landscape

<!-- Cover: From monolithic kernels to cloud-native stacks.
     Processes -> containers -> pods -> agents.
     The OS boundary has expanded, not disappeared. -->

## 1.3 Three Core Skills

<!-- Understand: know the mechanism (how does CFS work?)
     Measure: design controlled experiments (perf stat, strace)
     Explain: connect observed numbers to mechanisms -->

## 1.4 How This Book Is Organized

<!-- Map of parts and chapters, reading paths,
     how labs integrate with exposition -->

## 1.5 A First Look: What Happens When You Run a Program

<!-- Walkthrough: fork/exec, virtual memory setup, scheduling,
     context switches — a preview of concepts to come.
     Show with strace output. -->

## Summary

Key takeaways from this chapter:

- The OS is not just the kernel — it is the full stack of resource
  management from hardware to application.
- Modern systems (containers, Kubernetes, AI agents) reuse and extend
  OS concepts like isolation, scheduling, and resource control.
- This book emphasizes measurement-driven understanding: every claim
  about system behavior is backed by reproducible evidence.

## Further Reading

- Arpaci-Dusseau, R. H. & Arpaci-Dusseau, A. C. (2018).
  *Operating Systems: Three Easy Pieces.* Introduction and Chapter 2.
  Available at https://pages.cs.wisc.edu/~remzi/OSTEP/
- Gregg, B. (2020). *Systems Performance*, 2nd ed. Addison-Wesley.
  Chapter 1: Introduction.
