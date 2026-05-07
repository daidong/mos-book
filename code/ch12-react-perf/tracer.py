"""
tracer.py — minimal OTel-shaped span recorder.
Writes one JSON object per span to a JSONL file.

Uses contextvars for the parent-span pointer so parent-child links are
correct in BOTH synchronous code (Part 1) and under asyncio (Parts 2-4).
With asyncio.gather, each child Task copies the current context at
creation, so concurrent tool spans correctly attribute parentage to the
enclosing agent.task / gen_ai.client.request span instead of to whichever
sibling happened to enter the span first.
"""
import json, time, uuid, threading, contextvars
from contextlib import contextmanager
from typing import Optional

_lock = threading.Lock()
_current_parent: contextvars.ContextVar[Optional[str]] = (
    contextvars.ContextVar("current_parent", default=None))


class Tracer:
    def __init__(self, path: str):
        self.path = path
        # Truncate at start of each run.
        open(self.path, "w").close()

    @contextmanager
    def span(self, name: str, **attrs):
        span_id = uuid.uuid4().hex[:8]
        parent = _current_parent.get()
        token = _current_parent.set(span_id)
        t0 = time.perf_counter()
        record = {"span_id": span_id, "parent": parent, "name": name,
                  "start_s": t0, "attrs": dict(attrs)}
        try:
            yield record
        finally:
            record["end_s"] = time.perf_counter()
            record["duration_ms"] = (record["end_s"] - t0) * 1000
            with _lock, open(self.path, "a") as f:
                f.write(json.dumps(record, default=str) + "\n")
            _current_parent.reset(token)
