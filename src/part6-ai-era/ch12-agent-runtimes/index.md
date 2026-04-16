# Chapter 12: Agent Runtimes — Tool Calls as System Calls

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Explain why an LLM agent's tool-calling loop is structurally
>   analogous to a process making system calls, and why this
>   reframing lets classical OS techniques apply
> - Reason about the agent threat model: prompt injection, confused
>   deputy, resource exhaustion, data exfiltration, and tool chaining
> - Design defenses using allowlists, argument validation, structured
>   audit logging, and capability-based security
> - Apply Linux isolation primitives (namespaces, seccomp, cgroups
>   from Chapter 6) to confine agent tool execution
> - Measure the performance cost of isolation and reason about
>   tradeoffs for interactive agents

## 12.1 Why Agents Are an Operating Systems Problem

<!-- An agent is a supervisor loop: receive input, decide action,
     invoke tool, observe result, repeat. This is isomorphic to
     the process -> syscall -> kernel -> result loop.
     The "kernel" for an agent is its tool runtime.
     Whoever runs the tool runtime is the security principal.
     SOURCE: week11/week11_slides.md opening;
     week11/reading_guide.md intro -->

## 12.2 Tool Calls as System Calls

<!-- Syscalls: fixed number, defined interface, validated args,
     returned via registers/errno, audit via auditd/ebpf.
     Tool calls: open-ended schema, JSON args, returned as text,
     often not audited. What goes wrong when we skip the
     validation and audit steps.
     SOURCE: week11/week11_slides.md tool-calls section -->

## 12.3 Threat Model

<!-- Prompt injection: attacker controls model input, model
     "willingly" calls destructive tools.
     Confused deputy: the agent has authority the user does not.
     Resource exhaustion: infinite tool-call loops, token burn.
     Data exfiltration: tools that read then write elsewhere.
     Tool chaining: small capabilities composed into large ones.
     SOURCE: week11/week11_slides.md threat model;
     week11/reading_guide.md -->

## 12.4 Defenses: Allowlisting and Validation

<!-- Allowlist tools by name and argument shape.
     Validate arguments with a schema BEFORE invoking the tool.
     Canonicalize paths to block traversal.
     Reject out-of-band characters (shell metacharacters, newlines).
     SOURCE: week11/week11_slides.md defenses section;
     week11/sandbox/ reference implementation -->

## 12.5 Audit Logging

<!-- Every tool call must produce a structured log record:
     tool name, full args (post-canonicalization), caller,
     timestamp, outcome, duration.
     Logs are append-only and tamper-evident.
     This is the agent equivalent of auditd. -->

## 12.6 Capability-Based Security

<!-- Hand out unforgeable, least-privilege handles instead of
     ambient authority. A file-read capability names exactly
     one file. Contrast with UNIX uid-based authority.
     Reference: Capsicum, seL4, SPKI/SDSI.
     Why capabilities compose better than ACLs in tool runtimes. -->

## 12.7 Applying Linux Isolation Primitives

<!-- Namespaces (Chapter 6): isolate mount, network, pid, user.
     seccomp-bpf: reduce the kernel attack surface to an allowlist
     of syscalls.
     cgroups v2 (Chapter 6): bound CPU, memory, IO.
     Putting it together: a minimal sandbox for one tool call.
     SOURCE: week11/sandbox/ code; week11/facilitator_notes.md -->

## 12.8 Performance Cost of Isolation

<!-- fork+exec per call: ~ms overhead.
     Namespace setup: additional ms.
     seccomp filter: near-zero hot-path cost after setup.
     Tradeoffs for interactive agents where latency matters. -->

## Summary

Key takeaways from this chapter:

- An agent's tool-calling loop is a system-calls problem in a new
  wrapper; OS isolation techniques are the right starting point.
- Prompt injection and confused deputy are not hypothetical —
  they are the dominant real-world agent failure modes.
- Defenses must combine allowlisting, argument validation,
  structured audit, and process-level isolation. No one layer
  is sufficient on its own.

## Further Reading

- Greenberg, A. et al. (2024). Prompt injection attacks and
  defenses in LLM-integrated applications. (Survey.)
- Watson, R. N. M. et al. (2010). Capsicum: Practical capabilities
  for UNIX. *USENIX Security '10.*
- Corbet, J. (2009). Seccomp and sandboxing. *LWN.net.*
- OWASP Top 10 for LLM Applications. `owasp.org/www-project-top-10-for-large-language-model-applications/`
