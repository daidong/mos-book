#!/usr/bin/env python3

"""Compute percentiles from a CSV file.

Expected input: a CSV with a column named `latency_ms` (or pass --col).

Example:
  python3 latency_percentiles.py results/lat.csv --col latency_ms
"""

import argparse
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--col", default="latency_ms")
    ap.add_argument("--out", default=None, help="optional output markdown file")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    if args.col not in df.columns:
        raise SystemExit(f"missing column {args.col}; have: {list(df.columns)}")

    x = df[args.col].dropna().astype(float)
    p50 = x.quantile(0.50)
    p95 = x.quantile(0.95)
    p99 = x.quantile(0.99)

    txt = (
        f"count: {len(x)}\n"
        f"p50:  {p50:.3f} ms\n"
        f"p95:  {p95:.3f} ms\n"
        f"p99:  {p99:.3f} ms\n"
    )

    print(txt, end="")
    if args.out:
        with open(args.out, "w") as f:
            f.write("```\n")
            f.write(txt)
            f.write("```\n")


if __name__ == "__main__":
    main()
