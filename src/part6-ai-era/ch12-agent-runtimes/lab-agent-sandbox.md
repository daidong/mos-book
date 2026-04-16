# Lab: Build an Agent Sandbox

> **Estimated time:** 6-8 hours
>
> **Prerequisites:** Chapters 6 and 12; Linux with cgroups v2,
> user namespaces, and `libseccomp` available
>
> **Tools used:** Python, `subprocess`, `unshare`, `seccomp`,
> `cgroup` v2 interface, `strace`, the reference skeleton in
> `code/ch12-agent-sandbox/`

## Objectives

- Build a tool-call executor that runs each tool in a child
  process, validates arguments, and produces a structured audit log
- Demonstrate that a prompt-injection attack which worked against
  a naive executor is blocked by your sandbox
- (Optional) Add `seccomp` and `cgroup` confinement, and measure
  the per-call overhead

## Background

<!-- SOURCE: week11/lab_e_instructions.md, week11/sandbox/
     Four-part lab. Parts A-C are required for all students.
     Part D is optional and intended for graduate students
     or those with prior Linux security experience. -->

## Part A: Process Isolation for Tool Execution (Required)

<!-- Implement a Python `run_tool(name, args)` function that:
       1. Looks up the tool definition in an allowlist dict.
       2. Validates args against the declared schema.
       3. Spawns a child process to execute the tool.
       4. Captures stdout/stderr with timeouts.
       5. Returns a structured result.
     Skeleton in code/ch12-agent-sandbox/sandbox.py.
     SOURCE: week11/sandbox/sandbox.py -->

## Part B: Allowlist Validation (Required)

<!-- Define an allowlist covering at least: read_file, list_dir,
     run_shell (with a fixed command list), http_get (with a URL
     allowlist).
     For each tool, declare:
       - argument names and types
       - post-canonicalization (path resolution, URL parse)
       - rejection rules (traversal, shell metacharacters)
     Write unit tests that prove each validator rejects its
     attack class. -->

## Part C: Audit Logging + Attack Scenario (Required)

<!-- Every tool call appends a JSON line to an audit log:
       { ts, tool, args_raw, args_canonical, outcome, duration_ms }
     Write a short "attacker transcript": a sequence of tool
     calls that, on a naive executor, would read ~/.ssh/id_rsa or
     exfiltrate /etc/passwd. Show that your sandbox blocks it,
     and that the audit log captures the attempt.
     SOURCE: week11/lab_e_instructions.md attack scenarios -->

## Part D: seccomp + cgroup Isolation (Optional, Advanced)

<!-- Before exec:
       - Enter a new mount + pid + net namespace (unshare).
       - Apply a seccomp filter that allows only a minimal
         syscall set for the tool family.
       - Attach the child to a cgroup v2 group with memory.max
         and cpu.max limits.
     Measure per-call overhead vs Part A baseline:
       p50, p99, and CPU cost.
     Discuss which tools need which level of confinement. -->

## Deliverables

- A working `sandbox.py` (or equivalent) with tests that pass
  against the provided attack transcripts.
- An audit log excerpt showing at least three blocked attack
  attempts with canonicalized arguments.
- A short writeup (1-2 pages) explaining the defense layers
  and which attack each layer stops.
- (Optional) A performance table comparing Part A vs Part D
  overhead, plus a per-tool confinement matrix.

## Evidence Contract Reminder

Security claims also need evidence. For each blocked attack,
show (a) the attempted call, (b) the rejection reason from your
validator, and (c) the audit log entry confirming the rejection
was recorded.
