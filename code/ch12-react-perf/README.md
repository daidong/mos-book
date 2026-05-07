# Lab F — Profile and Optimize a ReAct Agent (Starter)

This directory is the starting point for **Lab F** of Chapter 12.
The lab walks you from a sequential ~150-LoC ReAct agent to a
parallelized, timeout-protected, cache-aware agent. You measure
the effect of each lever against the latency identity and write
a one-page perf report.

No API keys, no network, no third-party packages required.
Standard library only.

## Quick start

```bash
# Sanity check (should print wall ≈ 6.1 s)
python3 agent.py

# Render an empty trace (will print "(empty trace)" until you instrument)
python3 waterfall.py traces/baseline.jsonl    # placeholder
```

## Files you start with

| File | Purpose |
|---|---|
| `agent.py` | Baseline sequential ReAct agent. Mock LLM, four local tools, scripted task. **Do not edit; copy to `agent_p1.py` and edit the copy.** |
| `tracer.py` | Minimal OTel-shaped span recorder (~30 LoC). Uses `contextvars` so parent-child links survive `asyncio.gather`. |
| `waterfall.py` | Render a JSONL trace as a text waterfall. |
| `data/doc1.txt` … `doc3.txt` | The corpus the scripted task analyzes. |

## Files you produce

| File | When | Purpose |
|---|---|---|
| `agent_p1.py` | Part 1 | `agent.py` + tracer instrumentation |
| `agent_p2.py` | Part 2 | + parallel function calling |
| `agent_p3.py` | Part 3 | + flaky tool + timeout + structured fallback |
| `agent_p4.py` | Part 4 | + tool-result cache |
| `traces/baseline.jsonl` | Part 1 | Trace of `agent_p1.py` |
| `traces/parallel.jsonl` | Part 2 | Trace of `agent_p2.py` |
| `traces/flaky_with_timeout.jsonl` | Part 3 | Trace with timeouts visible |
| `traces/cached.jsonl` | Part 4 | Three runs in one trace; second/third should be all cache hits |
| `reports/perf_report.md` | All parts | One paragraph diagnosis per part + synthesis |

## Why hand-write a tracer?

In production you would not. Real teams `pip install`
`openllmetry`, `openinference`, the OpenAI Agents SDK, or
LangChain's tracing and get OTel `gen_ai.*` spans from one
`Instrumentor().instrument()` call. The 30 lines in `tracer.py`
are the conceptual core those libraries hide. Once you have
written it, the dashboards become a renderer over data you
understand.

## Why `contextvars` and not a plain stack?

In Part 1 the agent is single-threaded and synchronous; either
would work. In Parts 2–4 you launch tool calls concurrently with
`asyncio.gather`. A shared list races: if coroutine A enters its
span and then B enters, B sees A on top of the stack and
mis-records A as its parent. `contextvars.ContextVar` is the
standard fix — each `asyncio.Task` copies the current context at
creation, so each concurrent tool span correctly attributes
parentage to the enclosing `agent.task` span. The real
OpenTelemetry SDK uses the same pattern.

## Where the time goes (baseline)

Out of the box the baseline is dominated by LLM time:

```text
agent.task               ████████████████████████████████████████  6612 ms
gen_ai.client.request    █                                          714 ms
tool:read_file           ▏                                            7 ms
gen_ai.client.request     █                                          722 ms
tool:classify            ▏                                           52 ms
...
tool:summarize             █                                        205 ms
```

Eight LLM calls × ~720 ms = ~5.7 s out of ~6.1 s wall time. Tool
time is < 6%. Predict: parallelism will help most when it folds
LLM rounds (Part 2). Cache helps on repeated runs (Part 4).
Timeout matters when a tool has a long tail (Part 3).
