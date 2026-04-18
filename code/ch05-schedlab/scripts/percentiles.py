#!/usr/bin/env python3
"""
percentiles.py - Compute scheduling latency percentiles from SchedLab CSV.

Usage:
    python3 percentiles.py <latency.csv>

Input format (from schedlab --mode latency --output):
    bucket_us,count
    0.00,142
    1.00,8830
    ...

Prints p50, p90, p99, p99.9 to stdout.
"""

import csv
import math
import sys


def percentile_from_histogram(buckets, counts, p):
    """Compute the p-th percentile from histogram data."""
    total = sum(counts)
    if total == 0:
        return 0.0
    target = total * p / 100.0
    cumulative = 0
    for bucket, count in zip(buckets, counts):
        cumulative += count
        if cumulative >= target:
            return bucket
    return buckets[-1] if buckets else 0.0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <latency.csv>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    buckets = []
    counts = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("Empty CSV file.", file=sys.stderr)
            return 1

        # Support both histogram format (bucket_us,count) and
        # raw-sample format (latency_us).
        if "bucket_us" in reader.fieldnames and "count" in reader.fieldnames:
            for row in reader:
                try:
                    buckets.append(float(row["bucket_us"]))
                    counts.append(int(row["count"]))
                except (ValueError, KeyError):
                    pass
        elif "latency_us" in reader.fieldnames:
            # Raw samples — build a simple sorted list and compute directly
            vals = []
            for row in reader:
                try:
                    vals.append(float(row["latency_us"]))
                except (ValueError, KeyError):
                    pass
            if not vals:
                print("No latency samples found.", file=sys.stderr)
                return 1
            vals.sort()
            n = len(vals)
            def pct(p):
                k = (n - 1) * p / 100.0
                lo = int(math.floor(k))
                hi = int(math.ceil(k))
                if lo == hi:
                    return vals[lo]
                return vals[lo] * (hi - k) + vals[hi] * (k - lo)

            print(f"count={n}")
            print(f"p50_us={pct(50):.2f}")
            print(f"p90_us={pct(90):.2f}")
            print(f"p99_us={pct(99):.2f}")
            print(f"p99.9_us={pct(99.9):.2f}")
            return 0
        else:
            print(
                "CSV must contain either (bucket_us, count) or (latency_us) columns.",
                file=sys.stderr,
            )
            return 2

    if not buckets:
        print("No histogram data found.", file=sys.stderr)
        return 1

    total = sum(counts)
    if total == 0:
        print("All counts are zero.", file=sys.stderr)
        return 1

    # Weighted mean
    weighted_sum = sum(b * c for b, c in zip(buckets, counts))
    mean = weighted_sum / total

    p50 = percentile_from_histogram(buckets, counts, 50)
    p90 = percentile_from_histogram(buckets, counts, 90)
    p99 = percentile_from_histogram(buckets, counts, 99)
    p999 = percentile_from_histogram(buckets, counts, 99.9)

    print(f"count={total}")
    print(f"mean_us={mean:.2f}")
    print(f"p50_us={p50:.2f}")
    print(f"p90_us={p90:.2f}")
    print(f"p99_us={p99:.2f}")
    print(f"p99.9_us={p999:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
