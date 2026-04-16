#!/usr/bin/env python3
"""Summarize write_latency stdout into p50/p99/p99.9.

Usage:
    ./write_latency /tmp/f 1 10000 | scripts/percentiles.py
"""
import sys
import statistics


def main() -> int:
    samples = [int(line) for line in sys.stdin if line.strip()]
    if not samples:
        print("no samples", file=sys.stderr)
        return 1
    samples.sort()

    def q(p: float) -> int:
        idx = min(len(samples) - 1, int(len(samples) * p))
        return samples[idx]

    print(f"n       = {len(samples)}")
    print(f"min ns  = {samples[0]}")
    print(f"p50 ns  = {q(0.50)}")
    print(f"p99 ns  = {q(0.99)}")
    print(f"p999 ns = {q(0.999)}")
    print(f"max ns  = {samples[-1]}")
    print(f"mean ns = {int(statistics.mean(samples))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
