# Appendix D: AI Use Policy for Labs and Projects

This appendix defines the AI use policy for all labs and projects
in this book. It is designed for instructors to adopt directly or
adapt to their institution's academic integrity framework.

## Guiding Principle

AI tools — large language models, code assistants, search-enhanced
chatbots — are allowed in this course. They are not allowed to
replace the learning that the course is designed to produce.

The distinction is simple: **AI may help you work faster, but the
understanding must be yours.** Every lab is graded on evidence of
understanding — predictions, raw artifacts, mechanism-level
explanations, and exclusion of alternatives — not on the polish of
the final document. A beautifully written report that the student
cannot explain in a live conversation has not met the standard.

## Two Regimes

### Regime 1: Core Mechanism Labs (Parts I–V)

These labs teach specific OS mechanisms through measurement and
interpretation. AI use is **allowed but bounded**.

**Allowed:**
- Explaining OS concepts, man pages, tool flags, and error messages
- Debugging build failures, syntax errors, and environment issues
- Drafting shell commands and small utility scripts
- Reviewing and improving prose clarity in the report

**Not allowed:**
- Generating the pre-run prediction (the prediction must reflect
  the student's own reasoning about the mechanism)
- Fabricating raw data, traces, or measurement artifacts
- Generating the mechanism-level explanation or the alternative-
  exclusion argument without the student's own analytical work
- Submitting an AI-generated report without substantial original
  interpretation

**Required disclosure:**
If an AI tool contributed to any part of the report beyond trivial
editing, the student must note this in the Evidence Trail section
(see below). The disclosure is not penalized. Failure to disclose
when the contribution is substantial is an integrity violation.

### Regime 2: Capstone Projects and Open-Ended Work

These exercises (Appendix A capstone projects) involve design,
experimentation, and defense. AI use is **broadly allowed**.

**Allowed:**
- Design brainstorming and alternative-generation
- Script scaffolding and boilerplate code
- Documentation drafting and literature discovery
- Generating initial analysis code or visualization templates

**Required:**
- Every empirical claim must be verified by the student's own
  measurement — AI-generated numbers are not evidence
- The student must be able to defend every design decision orally
- The final deliverable must include a development trajectory
  (commit history, milestone notes, or a brief design journal)
  showing how the work evolved

## The Evidence Trail

Every lab report must include a short **Evidence Trail** section.
This replaces the traditional "I did not use AI" pledge with a
more honest and more useful record.

### Template

Add this section to every lab report, after the Evidence Contract
table:

```markdown
## Evidence Trail

### Environment and Reproduction
- All commands used are recorded in the Procedure sections above.
- Raw output files are listed in the Artifact section.

### AI Tool Use
- **Tool(s) used:** [e.g., "ChatGPT for debugging a Makefile
  error" / "GitHub Copilot for boilerplate in the plotting script"
  / "None"]
- **What the tool suggested:** [one-sentence summary of the
  suggestion, or "N/A"]
- **What I independently verified:** [what you checked, re-ran,
  or confirmed against your own data]
- **What I changed or rejected:** [if the suggestion was wrong or
  inapplicable, note it here]

### Failures and Iterations
- [Briefly describe at least one thing that did not work on the
  first attempt and what you learned from it.]
```

### Why This Matters

The Evidence Trail serves three purposes:

1. **Metacognition.** Writing down what AI suggested and what you
   verified forces you to distinguish between "I understand this"
   and "I pasted this."

2. **Honest signal.** Instructors can calibrate grading: a student
   who used AI to understand a man page and then produced a sharp
   original diagnosis is doing better work than one who avoided AI
   but wrote a shallow report.

3. **Integrity without surveillance.** The policy does not try to
   detect AI use through stylometric analysis or output detectors
   (which are unreliable). It makes disclosure the norm and
   penalizes only non-disclosure of substantial use.

## What Counts as "Substantial" AI Contribution

A rule of thumb: if removing the AI-assisted content would leave a
gap in the report that the student could not fill from their own
understanding, the contribution is substantial and must be
disclosed.

Examples:

| Scenario | Substantial? | Action |
|---|---|---|
| Used AI to recall the correct `perf stat` flags | No | No disclosure needed |
| Used AI to understand what `nr_throttled` means | No | No disclosure needed |
| Used AI to generate the entire mechanism paragraph | **Yes** | Must disclose; must also be able to explain it |
| Used AI to produce the prediction section | **Yes** | Must disclose; prediction must reflect own reasoning |
| Used AI to debug a segfault in the lab code | No | No disclosure needed |
| Used AI to write the shell script for data collection | Borderline | Disclose briefly |
| Used AI to generate a plot from CSV data | No | No disclosure needed |

## Oral Checkoffs (Instructor Guidance)

The single most effective complement to written evidence is a short
live conversation. Even 5–8 minutes per student per lab changes the
assessment dynamic fundamentally.

### Suggested format

1. The student opens their report and raw artifacts.
2. The instructor asks 2–3 questions drawn from the report:
   - "Walk me through why p99 spiked in your contention run."
   - "Your prediction said X but you measured Y. What happened?"
   - "You ruled out CPU saturation — how?"
3. The student explains using their own data.
4. The instructor assigns a checkoff grade (pass / partial / fail)
   that modifies the written grade.

### Why this works for systems courses

Systems courses have a natural advantage: the evidence is
inherently specific to the student's environment. A student's
`perf stat` output, their VM's kernel version, their fsync
latency distribution — these are unique artifacts. An oral
checkoff asks the student to interpret *their own* data, which is
something an AI cannot do in advance.

### Scaling

For large sections, consider:
- Checkoffs on 2–3 selected labs per semester, not every lab
- TA-led checkoffs with a rubric card
- Group checkoffs where each student explains one part
- Recorded video explanations as an async alternative (less
  effective but better than nothing)

## Academic Integrity

This policy is designed to be compatible with most university
academic integrity codes. The key adaptations:

- **AI use is not inherently dishonest.** The policy explicitly
  permits it within bounds.
- **Non-disclosure of substantial use is dishonest.** This is the
  integrity boundary.
- **Fabrication of data or artifacts is always a violation.**
  This is unchanged from pre-AI policy.
- **Submitting work you cannot explain is not a passing
  submission.** The oral checkoff or the Evidence Trail makes this
  enforceable.

Instructors should include a link to their institution's academic
integrity policy alongside this appendix in their syllabus.

## Summary

| Principle | Implementation |
|---|---|
| AI is a tool, not a substitute | Allowed but bounded per regime |
| Understanding is the target | Graded on prediction, evidence, interpretation |
| Disclosure over detection | Evidence Trail section in every report |
| Live verification when possible | Oral checkoffs on selected labs |
| Honesty is structural | Non-disclosure is the integrity violation, not use itself |

The goal is a course where AI makes students more productive
without making them less knowledgeable. The assessment structure —
predictions before data, raw artifacts from the student's own
system, mechanism-level explanations with exclusion checks, and
periodic oral verification — is designed to remain meaningful
regardless of how capable the tools become.
