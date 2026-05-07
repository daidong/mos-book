"""
agent.py — minimal sequential ReAct agent (~150 LoC).
Mock LLM; local tools; no network.
"""

import json, time, random
from typing import Any, Callable, Optional

# --------------- Mock LLM ---------------
# A scripted "LLM" that returns a fixed sequence of tool_calls / final_answer.
# Each chat() call simulates: prefill (scales with input bytes) + decode (fixed).

class MockLLM:
    def __init__(self, script: list[dict],
                 decode_s: float = 0.7,
                 prefill_us_per_char: float = 10.0):
        self.script = script
        self.step = 0
        self.decode_s = decode_s
        self.prefill_us_per_char = prefill_us_per_char

    def chat(self, messages: list[dict]) -> dict:
        input_chars = sum(len(json.dumps(m, default=str)) for m in messages)
        time.sleep(input_chars * self.prefill_us_per_char / 1e6)  # prefill
        time.sleep(self.decode_s)                                  # decode
        if self.step >= len(self.script):
            return {"role": "assistant", "tool_calls": None,
                    "content": "Done.", "input_tokens": input_chars // 4,
                    "output_tokens": 1}
        out = dict(self.script[self.step])
        out["input_tokens"] = input_chars // 4
        out["output_tokens"] = 50
        self.step += 1
        return out


# --------------- Tools ---------------
# Pure (no side effects) unless noted.

def tool_read_file(path: str) -> dict:
    time.sleep(0.005)                                              # ~5 ms
    with open(path) as f:
        return {"path": path, "content": f.read()}

def tool_word_count(text: str) -> dict:
    time.sleep(0.01)                                               # ~10 ms
    return {"word_count": len(text.split())}

def tool_classify(text: str) -> dict:
    time.sleep(0.05)                                               # ~50 ms
    label = "tail_latency" if "tail" in text.lower() else "general"
    return {"label": label, "len": len(text)}

def tool_summarize(text: str) -> dict:
    time.sleep(0.20)                                               # ~200 ms
    words = text.split()
    return {"summary": " ".join(words[:25]) +
            ("..." if len(words) > 25 else "")}

TOOLS: dict[str, Callable[..., dict]] = {
    "read_file": tool_read_file,
    "word_count": tool_word_count,
    "classify": tool_classify,
    "summarize": tool_summarize,
}


# --------------- Sequential ReAct loop ---------------

def run_agent(llm: MockLLM, user_goal: str,
              tools: dict = TOOLS, max_steps: int = 12) -> dict:
    """
    Runs the ReAct loop. Returns {answer, messages}.
    Each step: LLM produces tool_calls (or final). Runtime executes them.
    """
    messages = [{"role": "user", "content": user_goal}]
    answer = None
    for _ in range(max_steps):
        resp = llm.chat(messages)
        messages.append({"role": "assistant",
                         "tool_calls": resp.get("tool_calls"),
                         "content": resp.get("content")})
        calls = resp.get("tool_calls")
        if not calls:
            answer = resp.get("content")
            break
        for c in calls:
            name, args = c["name"], c["arguments"]
            if name == "final_answer":
                answer = args.get("text", "")
                return {"answer": answer, "messages": messages}
            fn = tools[name]
            result = fn(**args)
            messages.append({"role": "tool", "name": name,
                             "content": result})
    return {"answer": answer, "messages": messages}


# --------------- Default scripted task ---------------
# Goal: "Classify and summarize each of the three docs in ./data"

DEFAULT_SCRIPT = [
    # Turn 1: read doc1
    {"tool_calls": [{"name": "read_file",
                     "arguments": {"path": "data/doc1.txt"}}]},
    # Turn 2: classify doc1
    {"tool_calls": [{"name": "classify",
                     "arguments": {"text": "<<doc1>>"}}]},
    # Turn 3: read doc2
    {"tool_calls": [{"name": "read_file",
                     "arguments": {"path": "data/doc2.txt"}}]},
    # Turn 4: classify doc2
    {"tool_calls": [{"name": "classify",
                     "arguments": {"text": "<<doc2>>"}}]},
    # Turn 5: read doc3
    {"tool_calls": [{"name": "read_file",
                     "arguments": {"path": "data/doc3.txt"}}]},
    # Turn 6: classify doc3
    {"tool_calls": [{"name": "classify",
                     "arguments": {"text": "<<doc3>>"}}]},
    # Turn 7: summarize all three concatenated
    {"tool_calls": [{"name": "summarize",
                     "arguments": {"text": "<<all>>"}}]},
    # Turn 8: final answer
    {"tool_calls": [{"name": "final_answer",
                     "arguments": {"text": "Three docs analyzed."}}]},
]

if __name__ == "__main__":
    llm = MockLLM(DEFAULT_SCRIPT)
    t0 = time.perf_counter()
    out = run_agent(llm, "Classify and summarize the three docs in ./data")
    elapsed = time.perf_counter() - t0
    print(f"answer  : {out['answer']}")
    print(f"messages: {len(out['messages'])}")
    print(f"wall    : {elapsed:.2f} s")
