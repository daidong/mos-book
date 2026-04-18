"""
Chapter 9: Cluster Scheduling Simulator

Students implement schedule_fifo, schedule_backfill, and schedule_drf.
The framework provides Job, Machine, mixed_workload(), compute_metrics(),
and a Gantt-chart printer.

Usage:
    python3 scheduler_sim.py
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────

@dataclass
class Job:
    """A single schedulable unit of work."""
    job_id: str
    user: str               # owner (for DRF fairness)
    submit_time: float       # earliest possible start
    duration: float          # wall-clock runtime once started
    cpu: int                 # CPU cores required per node
    mem: int                 # memory (MiB) required per node
    nodes_required: int = 1  # gang-scheduling: need this many nodes at once

    # filled in by the scheduler:
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    assigned_machines: list[int] = field(default_factory=list)


@dataclass
class Machine:
    """One node in the cluster."""
    machine_id: int
    total_cpu: int
    total_mem: int

    # timeline of (free_time, cpu_used, mem_used) — simplification:
    # we track the time at which each allocation ends.
    _allocs: list[tuple[float, int, int]] = field(default_factory=list)

    def next_free_time(self) -> float:
        """Earliest time this machine has *any* freed capacity."""
        if not self._allocs:
            return 0.0
        return min(end for end, _, _ in self._allocs)

    def free_at(self, t: float) -> tuple[int, int]:
        """Return (free_cpu, free_mem) at time t."""
        used_cpu = sum(c for end, c, _ in self._allocs if end > t)
        used_mem = sum(m for end, _, m in self._allocs if end > t)
        return self.total_cpu - used_cpu, self.total_mem - used_mem

    def can_fit(self, job: Job, t: float) -> bool:
        fc, fm = self.free_at(t)
        return fc >= job.cpu and fm >= job.mem

    def allocate(self, job: Job, start: float) -> None:
        end = start + job.duration
        self._allocs.append((end, job.cpu, job.mem))

    def earliest_fit(self, job: Job, after: float) -> float:
        """Find the earliest time >= after when this machine can fit job."""
        # Collect event times when capacity changes
        times = sorted({after} | {end for end, _, _ in self._allocs if end > after})
        for t in times:
            if self.can_fit(job, t):
                return t
        # If nothing frees, try after all current allocs end
        if self._allocs:
            t = max(end for end, _, _ in self._allocs)
            if self.can_fit(job, t):
                return t
        return after  # empty machine


def _make_cluster(n_machines: int, cpu: int, mem: int) -> list[Machine]:
    return [Machine(i, cpu, mem) for i in range(n_machines)]


# ──────────────────────────────────────────────
# Workload
# ──────────────────────────────────────────────

def mixed_workload() -> list[Job]:
    """
    A mixed workload with three users.

    Alice: many small, short jobs (interactive / CI style).
    Bob:   a few large, long jobs including gang-scheduled ones.
    Charlie: medium jobs, moderate resource needs.
    """
    jobs = [
        # Alice — small, fast
        Job("a1", "alice", submit_time=0,  duration=4,  cpu=1, mem=256),
        Job("a2", "alice", submit_time=1,  duration=3,  cpu=1, mem=256),
        Job("a3", "alice", submit_time=2,  duration=2,  cpu=2, mem=512),
        Job("a4", "alice", submit_time=5,  duration=3,  cpu=1, mem=256),
        Job("a5", "alice", submit_time=8,  duration=2,  cpu=1, mem=256),

        # Bob — large, long, some gang-scheduled
        Job("b1", "bob", submit_time=0,  duration=12, cpu=4, mem=2048, nodes_required=2),
        Job("b2", "bob", submit_time=3,  duration=8,  cpu=4, mem=1024),
        Job("b3", "bob", submit_time=6,  duration=10, cpu=4, mem=2048, nodes_required=3),

        # Charlie — medium
        Job("c1", "charlie", submit_time=1,  duration=5, cpu=2, mem=512),
        Job("c2", "charlie", submit_time=4,  duration=4, cpu=2, mem=512),
        Job("c3", "charlie", submit_time=7,  duration=6, cpu=3, mem=1024),
    ]
    return jobs


# ──────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────

def compute_metrics(jobs: list[Job], machines: list[Machine]) -> dict:
    """Compute scheduling quality metrics from completed jobs."""
    completed = [j for j in jobs if j.end_time is not None]
    if not completed:
        return {"makespan": 0, "avg_completion_time": 0,
                "avg_wait_time": 0, "utilization": 0,
                "jain_fairness": 0}

    makespan = max(j.end_time for j in completed)
    avg_ct = sum(j.end_time - j.submit_time for j in completed) / len(completed)
    avg_wt = sum(j.start_time - j.submit_time for j in completed) / len(completed)

    # Utilization: total CPU·time used / total CPU·time available
    total_cpu_time = sum(j.cpu * j.duration * max(1, j.nodes_required) for j in completed)
    total_capacity = sum(m.total_cpu for m in machines) * makespan if makespan > 0 else 1
    util = total_cpu_time / total_capacity

    # Jain's fairness on per-user CPU time
    users: dict[str, float] = {}
    for j in completed:
        cpu_time = j.cpu * j.duration * max(1, j.nodes_required)
        users[j.user] = users.get(j.user, 0) + cpu_time
    vals = list(users.values())
    n = len(vals)
    if n > 0 and sum(vals) > 0:
        jain = (sum(vals) ** 2) / (n * sum(v ** 2 for v in vals))
    else:
        jain = 1.0

    return {
        "makespan": makespan,
        "avg_completion_time": round(avg_ct, 2),
        "avg_wait_time": round(avg_wt, 2),
        "utilization": round(util, 4),
        "jain_fairness": round(jain, 4),
    }


def per_user_cpu_time(jobs: list[Job]) -> dict[str, float]:
    """CPU·time per user (for DRF analysis)."""
    users: dict[str, float] = {}
    for j in jobs:
        if j.end_time is not None:
            ct = j.cpu * j.duration * max(1, j.nodes_required)
            users[j.user] = users.get(j.user, 0) + ct
    return users


# ──────────────────────────────────────────────
# Gantt chart (text)
# ──────────────────────────────────────────────

def print_gantt(jobs: list[Job], title: str, width: int = 60) -> None:
    """Print a simple text Gantt chart."""
    completed = [j for j in jobs if j.end_time is not None]
    if not completed:
        print(f"\n=== {title}: no jobs scheduled ===")
        return

    makespan = max(j.end_time for j in completed)
    scale = width / makespan if makespan > 0 else 1

    print(f"\n{'=' * (width + 20)}")
    print(f"  {title}")
    print(f"{'=' * (width + 20)}")

    for j in sorted(completed, key=lambda x: x.submit_time):
        left = int(j.start_time * scale)
        bar = max(1, int(j.duration * scale))
        line = " " * left + "█" * bar
        print(f"  {j.job_id:>4s} |{line:<{width}}| "
              f"t=[{j.start_time:.0f},{j.end_time:.0f})")

    # time ruler
    print(f"       |{'─' * width}|")
    ruler = ""
    for t in range(0, int(makespan) + 1, max(1, int(makespan) // 10)):
        pos = int(t * scale)
        if pos < width:
            ruler += " " * (pos - len(ruler)) + str(t)
    print(f"       |{ruler:<{width}}|")
    print()


# ──────────────────────────────────────────────
# Student implementations — stubs
# ──────────────────────────────────────────────

def schedule_fifo(jobs: list[Job], machines: list[Machine]) -> list[Job]:
    """
    TODO: Schedule jobs in strict submit_time order (FIFO).

    For each job in submit_time order:
      - Find the earliest time >= submit_time when nodes_required
        machines can all fit the job simultaneously.
      - Allocate the job on those machines.

    Gang-scheduled jobs (nodes_required > 1) must start on all
    their nodes at the same time.

    Returns the list of jobs with start_time, end_time, and
    assigned_machines filled in.
    """
    raise NotImplementedError("Implement schedule_fifo")


def schedule_backfill(jobs: list[Job], machines: list[Machine]) -> list[Job]:
    """
    TODO: EASY-style backfill.

    1. Sort jobs by submit_time (FIFO order).
    2. Try to schedule the head-of-queue job.  If it cannot start
       now, compute its *reservation time* (the earliest it can
       start).
    3. Scan remaining jobs: any job that can start NOW and will
       FINISH before the reservation time is a legal backfill.
       Schedule those backfills.
    4. Advance time and repeat.

    The key invariant: backfilling must NOT delay the head job's
    reservation.

    Returns jobs with start_time, end_time, assigned_machines.
    """
    raise NotImplementedError("Implement schedule_backfill")


def schedule_drf(jobs: list[Job], machines: list[Machine]) -> list[Job]:
    """
    TODO: Dominant Resource Fairness.

    At each scheduling point:
      1. Compute each user's dominant share:
         dominant_share = max(cpu_share, mem_share)
         where cpu_share = user's total running CPU / cluster CPU
         and   mem_share = user's total running mem / cluster mem.
      2. Pick the user with the smallest dominant share.
      3. From that user's unscheduled jobs (sorted by submit_time),
         find the first that fits on any machine NOW.
      4. Schedule it.
      5. If nothing fits for anyone, advance time to the next event
         (a running job finishes).
      6. Repeat until all jobs are scheduled.

    Returns jobs with start_time, end_time, assigned_machines.
    """
    raise NotImplementedError("Implement schedule_drf")


# ──────────────────────────────────────────────
# Main: run all three and compare
# ──────────────────────────────────────────────

CLUSTER_NODES = 4
CPU_PER_NODE = 8
MEM_PER_NODE = 4096  # MiB


def run_all():
    algos = [
        ("FIFO", schedule_fifo),
        ("Backfill", schedule_backfill),
        ("DRF", schedule_drf),
    ]

    print("Cluster: {} nodes × {} CPU × {} MiB".format(
        CLUSTER_NODES, CPU_PER_NODE, MEM_PER_NODE))
    print()

    results = {}

    for name, fn in algos:
        jobs = mixed_workload()
        machines = _make_cluster(CLUSTER_NODES, CPU_PER_NODE, MEM_PER_NODE)
        try:
            scheduled = fn(jobs, machines)
            print_gantt(scheduled, name)
            m = compute_metrics(scheduled, machines)
            results[name] = m
            print(f"  Per-user CPU·time: {per_user_cpu_time(scheduled)}")
            print()
        except NotImplementedError:
            print(f"\n  {name}: not yet implemented (stub)\n")
            results[name] = None

    # Comparison table
    print("\n" + "=" * 70)
    print(f"  {'Metric':<25s}  {'FIFO':>10s}  {'Backfill':>10s}  {'DRF':>10s}")
    print("  " + "-" * 65)
    for key in ["makespan", "avg_completion_time", "avg_wait_time",
                "utilization", "jain_fairness"]:
        row = f"  {key:<25s}"
        for name in ["FIFO", "Backfill", "DRF"]:
            if results.get(name):
                row += f"  {results[name][key]:>10}"
            else:
                row += f"  {'—':>10s}"
        print(row)
    print("=" * 70)


if __name__ == "__main__":
    run_all()
