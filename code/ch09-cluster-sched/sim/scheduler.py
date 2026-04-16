"""Starter skeleton for the Chapter 9 scheduling simulator.

Students implement FIFO and Backfill schedulers against the
same Job/Cluster interface and compare metrics across workloads.
See lab-cluster-scheduling.md Part A and Part B for requirements.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Job:
    job_id: str
    arrival: float
    duration: float
    cpu: int
    start: float | None = None
    finish: float | None = None


@dataclass
class Cluster:
    cpu_capacity: int
    running: list[Job] = field(default_factory=list)

    def free_cpu(self) -> int:
        return self.cpu_capacity - sum(j.cpu for j in self.running)

    def can_fit(self, job: Job) -> bool:
        return job.cpu <= self.free_cpu()


def fifo(jobs: list[Job], cluster: Cluster) -> list[Job]:
    """TODO: strict FIFO order. Head-of-line blocks the queue."""
    raise NotImplementedError


def backfill(jobs: list[Job], cluster: Cluster) -> list[Job]:
    """TODO: EASY-style backfill. A later job may run ahead of the
    head-of-line job as long as it does not delay that job's
    reservation."""
    raise NotImplementedError


def metrics(jobs: list[Job]) -> dict[str, float]:
    """Return makespan, avg completion time, avg wait, utilization."""
    raise NotImplementedError


def run(workload: list[Job], algo: Callable, cpu: int) -> dict[str, float]:
    cluster = Cluster(cpu_capacity=cpu)
    completed = algo(list(workload), cluster)
    return metrics(completed)


if __name__ == "__main__":
    # Minimal smoke test once students fill in the algorithms.
    demo = [
        Job("a", arrival=0, duration=10, cpu=8),
        Job("b", arrival=1, duration=2, cpu=2),
        Job("c", arrival=2, duration=2, cpu=2),
    ]
    print("FIFO:    ", run(demo, fifo, cpu=8))
    print("Backfill:", run(demo, backfill, cpu=8))
