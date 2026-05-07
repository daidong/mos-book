"""
waterfall.py — render a JSONL trace as a text waterfall.
Each span is one row; X axis is time in ms; bar = duration.
"""
import json, sys

def render(path: str, width: int = 60) -> None:
    spans = [json.loads(l) for l in open(path)]
    if not spans:
        print("(empty trace)"); return
    t0 = min(s["start_s"] for s in spans)
    total_ms = max(s["end_s"] for s in spans) - t0
    total_ms *= 1000
    print(f"trace: {path}   total: {total_ms:.0f} ms   spans: {len(spans)}")
    print("-" * (width + 30))
    spans.sort(key=lambda s: s["start_s"])
    for s in spans:
        start_ms = (s["start_s"] - t0) * 1000
        dur_ms   = s["duration_ms"]
        left  = int(start_ms / total_ms * width)
        barlen = max(1, int(dur_ms / total_ms * width))
        bar = " " * left + "█" * barlen
        label = s["name"]
        if s["name"] == "tool.call":
            label = f"tool:{s['attrs'].get('tool.name','?')}"
        print(f"{label:<24}{bar:<{width}} {dur_ms:7.1f} ms")

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "traces/baseline.jsonl")
