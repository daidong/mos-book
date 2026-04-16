# code/ch09-cluster-sched

The Chapter 9 lab (*Cluster Scheduling Simulation and Observation*)
has two halves:

- **Part A/B (simulator)** — students implement FIFO and Backfill
  scheduling in Python. A starter file is provided at
  `sim/scheduler.py`; the completed implementation is the lab's
  primary deliverable.
- **Part C/D (real K8s)** — uses stock `kind`, `kubectl`, and
  `etcdctl`. The manifests used in Part C live in `manifests/`
  so they can be reused across runs.

See `src/part4-distributed-systems/ch09-k8s-scheduling/lab-cluster-scheduling.md`
for the full lab instructions.

## Layout

```
code/ch09-cluster-sched/
├── README.md           # this file
├── sim/
│   └── scheduler.py    # skeleton for Parts A and B
└── manifests/
    └── pending-pod.yaml  # minimal manifest that should go Pending
```
