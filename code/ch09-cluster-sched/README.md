# code/ch09-cluster-sched

The Chapter 9 lab (*Cluster Scheduling Simulation and Observation*)
has two halves:

- **Part A/B (simulator)** — students implement FIFO, Backfill,
  and DRF scheduling in Python. The starter file
  `sim/scheduler_sim.py` provides the data model (`Job`, `Machine`),
  workload generator (`mixed_workload()`), metrics code
  (`compute_metrics()`), and three function stubs to fill in.
- **Part C/D (real K8s)** — uses stock `kind`, `kubectl`, and
  `etcdctl`. Manifests live in `manifests/`.

See `src/part4-distributed-systems/ch09-k8s-scheduling/lab-cluster-scheduling.md`
for the full lab instructions.

## Layout

```
code/ch09-cluster-sched/
├── README.md
├── sim/
│   ├── scheduler_sim.py    # starter for Parts A and B
│   └── scheduler.py        # (legacy skeleton — use scheduler_sim.py)
└── manifests/
    ├── pending-pod.yaml         # always-Pending Pod for testing
    └── node-affinity-demo.yaml  # Part C.5 affinity exercise
```

## Quick start

```bash
cd sim
python3 scheduler_sim.py    # runs all three algorithms (stubs → NotImplementedError)
```
