#!/usr/bin/env python3
"""
fairness.py - Analyze per-task fairness from SchedLab CSV.

Usage:
    python3 fairness.py <fairness.csv>

Input format (from schedlab --mode fairness --output):
    pid,run_time_ms,wait_time_ms,switches,wakeups

Computes CPU share per task, prints a summary table, and reports the
coefficient of variation as a fairness metric.
"""

import csv
import math
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <fairness.csv>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    tasks = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pid = int(row["pid"])
                run_ms = float(row["run_time_ms"])
                wait_ms = float(row["wait_time_ms"])
                switches = int(row["switches"])
                wakeups = int(row.get("wakeups", 0))
            except (ValueError, KeyError):
                continue
            tasks.append({
                "pid": pid,
                "run_ms": run_ms,
                "wait_ms": wait_ms,
                "switches": switches,
                "wakeups": wakeups,
            })

    if not tasks:
        print("No task data found.", file=sys.stderr)
        return 1

    # Filter to tasks with meaningful run time (> 1 ms)
    significant = [t for t in tasks if t["run_ms"] > 1.0]

    if not significant:
        print("No tasks with >1 ms run time.", file=sys.stderr)
        print(f"Total tasks in file: {len(tasks)}")
        return 0

    # Compute CPU share for each significant task
    for t in significant:
        total = t["run_ms"] + t["wait_ms"]
        t["share"] = t["run_ms"] / total if total > 0 else 0.0

    # Sort by run time descending
    significant.sort(key=lambda t: t["run_ms"], reverse=True)

    # Print table
    print(f"{'PID':<10} {'RunTime(ms)':<15} {'WaitTime(ms)':<15} "
          f"{'Switches':<10} {'CPU Share':<12}")
    print(f"{'---':<10} {'-----------':<15} {'------------':<15} "
          f"{'--------':<10} {'---------':<12}")

    for t in significant:
        print(f"{t['pid']:<10} {t['run_ms']:<15.2f} {t['wait_ms']:<15.2f} "
              f"{t['switches']:<10} {t['share']:<12.4f}")

    print()

    # Fairness metrics
    shares = [t["share"] for t in significant]
    run_times = [t["run_ms"] for t in significant]

    mean_share = sum(shares) / len(shares)
    mean_run = sum(run_times) / len(run_times)

    if mean_run > 0 and len(run_times) > 1:
        variance = sum((r - mean_run) ** 2 for r in run_times) / (len(run_times) - 1)
        std_run = math.sqrt(variance)
        cv = std_run / mean_run
    else:
        cv = 0.0

    print(f"Tasks with >1 ms run time: {len(significant)}")
    print(f"Mean CPU share: {mean_share:.4f}")
    print(f"Run time coefficient of variation: {cv:.4f}")

    if cv < 0.10:
        print("  -> Very fair (CV < 0.10)")
    elif cv < 0.30:
        print("  -> Reasonably fair (CV < 0.30)")
    else:
        print("  -> Unfair (CV >= 0.30)")

    # If exactly 2 significant tasks, print the ratio
    if len(significant) == 2:
        a, b = significant[0], significant[1]
        if b["run_ms"] > 0:
            ratio = a["run_ms"] / b["run_ms"]
            print(f"\nRun time ratio (PID {a['pid']} / PID {b['pid']}): {ratio:.2f}x")
            print("Compare this to the expected weight ratio from the nice-to-weight table.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
