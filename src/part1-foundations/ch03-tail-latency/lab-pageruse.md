# Lab: PagerUSE Oncall Simulation

> **Estimated time:** 3-4 hours
>
> **Prerequisites:** Chapter 3 concepts (USE method, percentiles)
>
> **Tools used:** top, free, vmstat, iostat, dmesg, ss, ps

## Objectives

- Apply the USE method to diagnose tail latency problems in a
  simulated oncall scenario
- Practice forming hypotheses, collecting evidence, and ruling out
  alternative causes
- Build a diagnosis report with an evidence chain of two or more
  independent signals

## Background

<!-- SOURCE: week2B/lab2_instructions.md, lab2_pageruse/
     PagerUSE is a scenario-based debugging exercise. Students
     receive mock pager alerts and must diagnose the root cause
     using observation-only commands (no code changes allowed). -->

## Part A: Easy Scenario — Single Root Cause (Required)

<!-- Memory pressure causing major page faults.
     Observe with: free, vmstat, /proc/meminfo.
     Verify with page fault counters. -->

## Part B: Medium Scenario — Multiple Contributing Causes (Required)

<!-- Two interacting causes. Students must identify both and
     explain how they interact to produce the observed symptom. -->

## Part C: Hard Scenario — Misleading Symptom (Optional)

<!-- The obvious suspect is not the root cause.
     Students must rule out the misleading signal and find
     the actual mechanism. -->

## Deliverables

- For each scenario: a diagnosis report containing:
  - Symptom observed
  - Hypothesis formed
  - Evidence collected (two or more independent signals)
  - Alternative cause ruled out (one exclusion check)
  - Root cause statement
  - Proposed mitigation
