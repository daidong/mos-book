# Lab F: Profile and Optimize a ReAct Agent

> **Estimated time:** 4–6 hours
>
> **Prerequisites:** Chapter 12 §12.9–12.13; Chapter 2
> (measurement methodology); Python 3.10+ with `asyncio`;
> familiarity with `time.perf_counter` and JSONL files
>
> **Tools used:** Python standard library only (`asyncio`,
> `json`, `time`, `hashlib`, `uuid`, `contextvars`); the starter
> skeleton in `code/ch12-react-perf/`; optionally `matplotlib`
> for waterfall plots

## Objectives

- Take a baseline ~150-LoC sequential ReAct agent, instrument it
  with OpenTelemetry-style `gen_ai.*` spans, and render a trace
  waterfall
- Diagnose the trace against the latency identity and name which
  of the four common slow-trace patterns it shows
- Apply each of the three classical levers — parallelism,
  caching, timeout + LLM-mediated fallback — and measure
  before/after p50, p95, and p99 over many runs
- Produce a one-page perf report with one paragraph of
  diagnosis per lever and a synthesis paragraph

## Background

The chapter argued that an agent task is a tree, and that three
levers cover most fixes. This lab asks you to *show it*. You
take the same scripted task — *"classify and summarize the three
docs in `./data`"* — and apply each lever in turn, measuring the
effect against the baseline. The lever that helps most depends
on the task; you need to read the trace to know which one to
pick first.

The starter agent uses a **mock LLM** (scripted, with simulated
prefill and decode) and **local tools** (file read, word count,
classify, summarize). No API keys, no network, no `pip install`.
Everything reproduces deterministically on a laptop.

The starter code lives in `code/ch12-react-perf/`:

```text
code/ch12-react-perf/
├── agent.py        # baseline (do not edit; copy)
├── tracer.py       # 30-line OTel-shaped span recorder
├── waterfall.py    # text waterfall renderer
├── data/           # doc1.txt, doc2.txt, doc3.txt
└── README.md
```

The lab has four parts. Part 1 is mostly instrumentation; Parts
2–4 are one lever each.

## Part 1: Profile — OTel-Style Spans and a Waterfall (45–60 min)

**Goal:** Add `gen_ai.*` instrumentation to the baseline agent,
render a waterfall, and diagnose the trace.

### 1.1 Sanity-check the baseline

```bash
cd code/ch12-react-perf
python3 agent.py
# answer  : Three docs analyzed.
# messages: 16
# wall    : 6.1 s   (±0.3 s on most laptops)
```

Before you instrument, **predict on paper**: how many LLM calls
and how many tool calls did the agent make? Which dominates
wall time? You will grade your intuition against the trace at
the end of Part 1.

### 1.2 Instrument the agent

Copy `agent.py` to `agent_p1.py` and add three things.

**(a) Import the tracer:**

```python
from tracer import Tracer
import hashlib

tracer = Tracer("traces/baseline.jsonl")

def args_hash(args: dict) -> str:
    return hashlib.sha256(
        json.dumps(args, sort_keys=True, default=str).encode()
    ).hexdigest()[:8]
```

**(b) Wrap the LLM call:**

```python
with tracer.span("gen_ai.client.request",
                 **{"gen_ai.system": "mock",
                    "gen_ai.request.model": "mock-1"}) as s:
    resp = llm.chat(messages)
    s["attrs"]["gen_ai.usage.input_tokens"]  = resp["input_tokens"]
    s["attrs"]["gen_ai.usage.output_tokens"] = resp["output_tokens"]
    s["attrs"]["gen_ai.response.finish_reasons"] = (
        ["tool_calls"] if resp.get("tool_calls") else ["stop"])
```

**(c) Wrap each tool call:**

```python
with tracer.span("tool.call",
                 **{"tool.name": name,
                    "tool.args_hash": args_hash(args)}) as s:
    try:
        result = fn(**args)
        s["attrs"]["tool.status"] = "ok"
    except Exception as e:
        s["attrs"]["tool.status"] = "error"
        s["attrs"]["error"] = str(e)
        raise
```

**(d) Wrap the whole loop body:**

```python
with tracer.span("agent.task", user_goal=user_goal):
    ...   # the existing for-loop
```

Use the attribute names verbatim — they are the OTel `gen_ai.*`
semantic conventions and any compliant backend will recognize
them.

### 1.3 Render the waterfall

```bash
python3 agent_p1.py
python3 waterfall.py traces/baseline.jsonl
```

You should see one fat `agent.task` bar and a staircase of
alternating `gen_ai.client.request` and `tool:*` bars beneath
it. Confirm the bars sum (within orchestration overhead) to the
total wall time.

### 1.4 Diagnose

Compute, from your trace:

| Term | Value |
|---|---|
| Number of LLM calls |   |
| Number of tool calls |   |
| $\sum T_{\text{LLM}}$ |   |
| $\sum T_{\text{tool}}$ |   |
| $T_{\text{orch}}$ (= total − LLM − tool) |   |
| Dominant term (%) |   |

### Part 1 deliverables

In `reports/perf_report.md`:

1. The per-term table above.
2. **One sentence** naming which of the four patterns
   (prefill explosion, slow-tool tail, sequential dependency,
   repeated work) this trace matches and why.
3. **One sentence** predicting which lever (parallelism, cache,
   timeout) you expect to help most, and why.

## Part 2: Parallelize — Same-Turn Parallel Tool Calls (30–45 min)

**Goal:** Convert the sequential script into a wide-DAG version
where the three reads run in parallel and the three classifies
run in parallel. Measure the speedup; compute the Amdahl
ceiling; explain any gap.

### 2.1 Make a parallel copy

```bash
cp agent_p1.py agent_p2.py
```

Three changes:

**(a) Async tool dispatch.** Wrap tool execution so that within
one turn, all `tool_calls` are launched concurrently with
`asyncio.gather`:

```python
import asyncio

async def _run_one_tool(name, args, tools, tracer):
    with tracer.span("tool.call",
                     **{"tool.name": name,
                        "tool.args_hash": args_hash(args)}) as s:
        result = await asyncio.to_thread(tools[name], **args)
        s["attrs"]["tool.status"] = "ok"
        return name, result

async def dispatch_calls(calls, tools, tracer):
    coros = [_run_one_tool(c["name"], c["arguments"], tools, tracer)
             for c in calls if c["name"] != "final_answer"]
    return await asyncio.gather(*coros)
```

**(b) New script that batches.** Replace `DEFAULT_SCRIPT` with
a 3-turn version:

```python
PARALLEL_SCRIPT = [
    # Turn 1: read all three docs in parallel.
    {"tool_calls": [
        {"name": "read_file", "arguments": {"path": "data/doc1.txt"}},
        {"name": "read_file", "arguments": {"path": "data/doc2.txt"}},
        {"name": "read_file", "arguments": {"path": "data/doc3.txt"}},
    ]},
    # Turn 2: classify all three in parallel.
    {"tool_calls": [
        {"name": "classify", "arguments": {"text": "<<doc1>>"}},
        {"name": "classify", "arguments": {"text": "<<doc2>>"}},
        {"name": "classify", "arguments": {"text": "<<doc3>>"}},
    ]},
    # Turn 3: summarize (serial — depends on classify results).
    {"tool_calls": [{"name": "summarize",
                     "arguments": {"text": "<<all>>"}}]},
    # Turn 4: final
    {"tool_calls": [{"name": "final_answer",
                     "arguments": {"text": "Three docs analyzed."}}]},
]
```

**(c) Make `run_agent` async with one event loop covering the
whole run.** Why: Part 3's timeout depends on it. If `run_agent`
is sync and you `asyncio.run(dispatch_calls(...))` per turn,
each per-turn loop's executor shutdown blocks until orphan
threads finish — silently undoing any timeout. With one
long-lived event loop the orphan finishes in the background and
the next turn proceeds.

### 2.2 Verify and measure

```bash
python3 agent_p2.py
python3 waterfall.py traces/parallel.jsonl
```

The visual signature of correct parallel dispatch: the three
`read_file` bars are **stacked at the same x-offset**, and the
same for the three `classify` bars.

Run baseline and parallel five times each. Record wall time:

| Variant | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Mean |
|---|---|---|---|---|---|---|
| Baseline (Part 1) |   |   |   |   |   |   |
| Parallel (Part 2) |   |   |   |   |   |   |

Compute the **Amdahl ceiling**: from your Part 1 numbers, what
fraction $p$ of total time was spent in tools? What is
$1/(1-p)$ — the upper bound on speedup if tool time went to
zero?

You will likely measure a speedup *larger* than the ceiling.
That is not a measurement error — `PARALLEL_SCRIPT` also folded
six LLM rounds into two, so you simultaneously got (a) parallel
tool execution and (b) fewer LLM round-trips. Pure tool
parallelism would give a tiny win (LLM dominates the baseline);
the dominant effect is round-folding. This is what wide-DAG
batching delivers in real systems: you cannot get parallel
tool calls without telling the model "here are N things you can
do at once," which by construction is one fewer LLM turn.

### Part 2 deliverables

1. The 5×2 table of wall times + mean speedup.
2. Amdahl ceiling for tool-only parallelism, observed speedup,
   and a sentence attributing the gap to round-folding.
3. **One paragraph:** *"Why didn't parallelism move p99 much?
   What kind of task would it have moved?"*

## Part 3: Tame the Tail — Timeout + LLM-Mediated Fallback (45–60 min)

**Goal:** Inject a flaky tool, add timeout + structured fallback,
measure the effect on p50, p95, p99 over 30 runs.

### 3.1 Add a flaky tool

```bash
cp agent_p2.py agent_p3.py
```

```python
def tool_classify_flaky(text: str) -> dict:
    """Same as classify, but 10% of the time takes 2.0 s instead of 50 ms."""
    if random.random() < 0.10:
        time.sleep(2.0)
    else:
        time.sleep(0.05)
    return {"label": "neutral", "len": len(text)}

TOOLS["classify_flaky"] = tool_classify_flaky
```

Update `PARALLEL_SCRIPT` to call `classify_flaky` instead of
`classify`. Set `random.seed()` to a *different* value each run
so you actually sample the tail.

### 3.2 Measure the baseline tail

Run the agent **30 times** and record wall time per run. Compute
p50, p95, p99. (For 30 samples, p99 = max; that is fine for the
lab — note the limitation in your report.)

```python
import statistics

def run_once():
    llm = MockLLM(PARALLEL_SCRIPT_FLAKY)
    t0 = time.perf_counter()
    asyncio.run(run_agent(llm, "...", tracer))
    return time.perf_counter() - t0

times = sorted(run_once() for _ in range(30))
p50, p95, p99 = times[15], times[28], times[29]
```

Plot a histogram (matplotlib, or text). Most runs should cluster
near ~3.0 s with a few outliers near ~5.0 s. **That is the tail.**

### 3.3 Add timeout + structured fallback

```python
TIMEOUT_S = 1.0

async def _run_one_tool(name, args, tools, tracer):
    with tracer.span("tool.call",
                     **{"tool.name": name,
                        "tool.args_hash": args_hash(args)}) as s:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(tools[name], **args),
                timeout=TIMEOUT_S)
            s["attrs"]["tool.status"] = "ok"
            return name, result
        except asyncio.TimeoutError:
            s["attrs"]["tool.status"] = "timeout"
            s["attrs"]["timeout_s"] = TIMEOUT_S
            # The "LLM fallback" — for the lab, a deterministic stand-in.
            return name, {"error": "timeout", "elapsed_s": TIMEOUT_S,
                          "fallback_label": "unknown",
                          "hint": "tool unavailable; downstream proceeded"}
```

Do **not** raise the exception. The runtime returns a structured
observation; in production the LLM decides what to do with it.

**Orphan-thread caveat (read this even if your numbers look right).**
When `asyncio.wait_for` raises `TimeoutError`, the underlying
`asyncio.to_thread(...)` is cancelled at the asyncio level only
— the OS thread keeps running the original `time.sleep(2.0)`
in the executor pool until it returns. The wall-time win is
real because `run_agent` is async with one event loop; the
orphan finishes in the background while the next turn proceeds.
Two consequences worth remembering:

1. If you regressed `run_agent` to synchronous and called
   `asyncio.run` per turn, the per-turn loop's executor
   shutdown would block until the orphan finishes — silently
   undoing the timeout. This is a common production bug.
2. In real systems an orphan thread can hold a database
   connection, write half a file, or burn API quota. Production
   code combines `wait_for` with cooperative cancellation (a
   `cancel_token` the tool checks) and resource-cap circuit
   breakers. Out of scope for the lab; mention it in your
   report's open-question paragraph.

### 3.4 Re-measure

| Variant | p50 (s) | p95 (s) | p99 (s) | # timeouts observed |
|---|---|---|---|---|
| Flaky-tool baseline |   |   |   |   |
| + timeout + fallback |   |   |   |   |

Open `traces/flaky_with_timeout.jsonl` from a run that hit a
timeout. Find the `tool.call` span with `tool.status = "timeout"`.
Verify its duration ≈ `TIMEOUT_S × 1000` ms.

### Part 3 deliverables

1. The p50 / p95 / p99 table.
2. **One paragraph:** *"Did p50 change? Why or why not? Did p99
   change? By how much?"*
3. **One paragraph:** *"What would happen to correctness — to
   the final answer's accuracy — if the flaky tool were actually
   load-bearing? How would you defend against silently-wrong
   fallbacks?"*

## Part 4: Cache — Tool-Result Cache for Repeated Work (30 min)

**Goal:** Add a tool-result cache keyed on `tool_name + args_hash`,
verify cache hits in the trace, measure repeat-task speedup.

### 4.1 What to cache

| Tool | Cache it? | Why |
|---|---|---|
| `read_file` | Yes | Pure read |
| `word_count` | Yes | Pure |
| `classify` | Yes | Pure |
| `summarize` | Yes | Pure |
| `classify_flaky` | **Maybe** | Pure but stochastic — caching freezes one outcome |
| (hypothetical) `write_file` | **No** | Side effect |

For the lab, cache the four pure tools and **revert the script
back to `classify`** (not `classify_flaky`) for a clean cache
demonstration.

### 4.2 Add an in-process cache

```bash
cp agent_p3.py agent_p4.py
```

```python
_TOOL_CACHE: dict[str, dict] = {}
CACHEABLE = {"read_file", "word_count", "classify", "summarize"}

async def _run_one_tool(name, args, tools, tracer):
    key = f"{name}:{args_hash(args)}"
    if name in CACHEABLE:
        if key in _TOOL_CACHE:
            with tracer.span("tool.call",
                             **{"tool.name": name,
                                "tool.args_hash": args_hash(args),
                                "tool.cache": "hit",
                                "tool.status": "ok"}):
                return name, _TOOL_CACHE[key]
        cache_attr = {"tool.cache": "miss"}
    else:
        cache_attr = {"tool.cache": "skip"}
    with tracer.span("tool.call",
                     **{"tool.name": name,
                        "tool.args_hash": args_hash(args),
                        **cache_attr}) as s:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(tools[name], **args),
                timeout=TIMEOUT_S)
            s["attrs"]["tool.status"] = "ok"
            if name in CACHEABLE:
                _TOOL_CACHE[key] = result
            return name, result
        except asyncio.TimeoutError:
            s["attrs"]["tool.status"] = "timeout"
            return name, {"error": "timeout", "elapsed_s": TIMEOUT_S,
                          "fallback_label": "unknown"}
```

### 4.3 Repeat-task scenario

Run the **same task three times in a row** in one process. Use
**one** `Tracer` outside the loop so all three runs append to
the same JSONL file:

```python
if __name__ == "__main__":
    tracer = Tracer("traces/cached.jsonl")
    times = []
    for run in range(3):
        llm = MockLLM(PARALLEL_SCRIPT)
        t0 = time.perf_counter()
        asyncio.run(run_agent(llm, "...", tracer))
        times.append(time.perf_counter() - t0)
        print(f"run {run+1}: {times[-1]:.2f} s")
```

Confirm cache hits:

```bash
python3 agent_p4.py
grep '"tool.cache": "hit"'  traces/cached.jsonl | wc -l
grep '"tool.cache": "miss"' traces/cached.jsonl | wc -l
```

| Run | Wall time (s) | Cache hits | Cache misses |
|---|---|---|---|
| 1 (cold) |   |   |   |
| 2 (warm) |   |   |   |
| 3 (warm) |   |   |   |

### Part 4 deliverables

1. The 3×3 table.
2. **One paragraph:** *"What would go wrong if you also cached
   `classify_flaky`?"* Hint: think about what cache hits do to
   the *distribution* of observed latencies and to the trace
   patterns from §12.11.
3. **One sentence:** *"Which term in the latency identity does
   the cache attack here?"* — and check it against your numbers.

## Final Deliverable: `perf_report.md`

```text
# Lab F Report

Name: ...
Date: ...

## Part 1 — Profile
- Latency identity table (LLM / tool / orchestration / total)
- Trace pattern this matches: ...
- Predicted dominant lever: ...
- Waterfall: traces/baseline.jsonl (attached) or screenshot

## Part 2 — Parallelize
- 5×2 wall-time table + mean speedup
- Amdahl ceiling = ...; achieved ...×; gap explained by ...
- Why p99 didn't move much: ...

## Part 3 — Tame the tail
- p50 / p95 / p99 before vs after
- Diagnosis of p50 / p99 movement
- Open question on fallback correctness

## Part 4 — Cache
- 3-run wall-time table + cache hit/miss counts
- Risks of caching a stochastic tool
- Latency identity term attacked

## Synthesis (1 paragraph)
- Which lever helped most for THIS task, and why?
- Would the answer change for a task that was 80% LLM time? 80% one slow API?
```

## AI Use and Evidence Trail

This lab is graded on **prediction → evidence → mechanism**, not
on polish. AI tools are allowed within
[Appendix D](../../appendices/appendix-d-ai-policy.md) (Regime 1):
they may help debug, recall flags, or polish prose; they may
**not** generate the prediction, fabricate raw data, or substitute
for your own mechanism-level explanation. Substantial use must be
disclosed in the Evidence Trail — honest disclosure is not
penalized; non-disclosure of substantial use is.

Append the following section to your report (full template and
examples in Appendix D §"The Evidence Trail"):

```markdown
## Evidence Trail

### Environment and Reproduction
- Commands used: see the Procedure sections above
- Raw output files: list paths in your submission

### AI Tool Use
- **Tool(s) used:** [tool name and version, or "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you re-checked against
  your own data]
- **What I changed or rejected:** [if a suggestion was wrong or
  inapplicable]

### Failures and Iterations
- [At least one thing that did not work on the first attempt and
  what you learned from it.]
```

## Grading Rubric

| Criterion | Points |
|---|---|
| Part 1 — instrumentation correct, OTel attribute names match | 20 |
| Part 1 — diagnosis paragraph identifies dominant term | 10 |
| Part 2 — parallel dispatch works, traces show overlap | 15 |
| Part 2 — speedup measured + Amdahl analysis | 10 |
| Part 3 — timeout + structured fallback (no exceptions) | 15 |
| Part 3 — p50 / p99 before-vs-after with discussion | 10 |
| Part 4 — cache hits visible in trace; correctness preserved | 10 |
| Synthesis paragraph | 10 |
| **Total** | **100** |

**Bonus (+10):** render waterfalls as PNGs (`matplotlib.barh`) and
embed them in the report.

**Bonus (+10):** tiny load test: 10 concurrent agent tasks via
`asyncio.gather`, plot the p50 / p99 of *task wall time under
load* with vs. without timeout. (Previews the multi-tenancy
question — what happens to a slow-tool tail when many sessions
share a runtime.)

## Evidence Contract

Performance claims need evidence. For each claim in your report:

1. **The number** — measured wall time, p50, p99, hit count.
2. **The trace** — the JSONL file the number came from, with
   the relevant span attributes (`tool.cache: "hit"`,
   `tool.status: "timeout"`, etc.) cited by line.
3. **The mechanism** — *why* the number changed, in one
   sentence. *"Cache hits skip the 50 ms `time.sleep` in
   `tool_classify`"* counts; *"the cache made it faster"* does
   not.

If any of those three is missing for a claim, the claim is a
hope, not a proof.

## Common Pitfalls

- **Truncating the trace by accident.** `Tracer.__init__` opens
  the file in `"w"` mode and truncates. For Part 4 you want one
  Tracer outside the loop so three runs append to the same file
  — see §4.3.
- **Per-turn `asyncio.run`.** Defeats Part 3's timeout silently.
  Make `run_agent` async and use one event loop per agent task.
  See §2.1(c).
- **Wrong span name capitalization.** `gen_ai.client.request` is
  the OTel convention; `Gen_AI.Client.Request` is not. Use the
  exact lowercase form so any compliant backend recognizes it.
- **Logging pretty-printed JSON.** Spans must be one line per
  record so `grep` and dashboards can parse them.
- **Caching `classify_flaky` and reporting "p99 dropped to 50 ms".**
  You froze one outcome at first observation; you are measuring
  noise, not the tool. Pure stochastic tools must be marked
  non-cacheable or have their seed folded into the cache key.

## Troubleshooting

- **`AttributeError: module 'asyncio' has no attribute 'to_thread'`.**
  You are on Python ≤ 3.8. Upgrade to 3.10+.
- **Spans are missing parent links under `asyncio.gather`.** The
  starter `tracer.py` uses `contextvars.ContextVar`; if you
  rewrote it with a shared list, switch back. See the
  README in `code/ch12-react-perf/`.
- **Wall time is much higher than 6.1 s on baseline.** The mock
  LLM's `decode_s` defaults to 0.7 s. If your laptop is slow,
  drop it to 0.3 s — but report the constant you used.

## Reference

- OpenTelemetry GenAI semantic conventions:
  <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
- Yao, S. et al. (2022). *ReAct: Synergizing Reasoning and
  Acting in Language Models.* arXiv:2210.03629.
- OpenAI parallel function calling:
  <https://platform.openai.com/docs/guides/function-calling>
- Anthropic prompt caching:
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching>
- Python `asyncio` docs:
  <https://docs.python.org/3/library/asyncio.html>
- Production OTel auto-instrumentation: OpenLLMetry,
  OpenInference, OpenAI Agents SDK built-in tracing.
