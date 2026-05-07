# PagerUSE Checklist

## Scenario

- Scenario ID:
- Start time observed in UI:
- Primary symptom:
- Baseline or threshold:
- Failed SLI:
- SLO risk:
- Blast radius:

## Incident Card Before Investigation

### Initial hypotheses

1. Hypothesis A:
   - Resource or request path:
   - Why plausible:
   - Signal that would support it:
2. Hypothesis B:
   - Resource or request path:
   - Why plausible:
   - Signal that would support it:

### First three commands

| Command | Why this command first? | Which hypothesis does it test? |
|---|---|---|
| 1. |  |  |
| 2. |  |  |
| 3. |  |  |

## RED Pass

| Signal | Observation | Interpretation | Missing information |
|---|---|---|---|
| Rate |  |  |  |
| Errors |  |  |  |
| Duration |  |  |  |

## USE Pass

| Resource | Utilization | Saturation | Errors | Notes |
|---|---|---|---|---|
| CPU |  |  |  |  |
| Memory |  |  |  |  |
| Disk |  |  |  |  |
| Network |  |  |  |  |

## Evidence Chain

### Primary diagnosis

- Symptom:
- Hypothesis:
- Signal 1:
- Signal 2:
- Exclusion:
- Mechanism:
- Mitigation:
- Verification 1:
- Verification 2:

### Alternative explanation considered

- Alternative:
- Why it looked plausible:
- What ruled it out:

### Interaction, if more than one mechanism is real

- Mechanism 1:
- Mechanism 2:
- How they compose:
- Which mitigation should happen first and why:

## Command Log Pointers

| Command | Key output line(s) | Why it matters |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |

## Part I Synthesis

| Question | Answer |
|---|---|
| What was the mechanism? |  |
| Which layer exposed the first symptom: application, runtime, kernel, or hardware? |  |
| Which command or dashboard observation measured the user-facing symptom? |  |
| Which command measured the mechanism-facing signal? |  |
| Which alternative did you rule out? |  |
| What would you verify after mitigation? |  |
