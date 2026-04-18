# Lab: Cluster Scheduling Simulation and Observation

> **Estimated time:** 4–5 hours
>
> **Prerequisites:** Chapter 9 concepts; Python 3.8+; `kind` and
> `kubectl` installed in your Ubuntu VM
>
> **Tools used:** Python, `kind`, `kubectl`, `etcdctl` (optional)

## Objectives

- Implement FIFO, Backfill, and DRF scheduling algorithms in a
  Python simulator and compare their behavior
- Observe the real Kubernetes scheduler in a `kind` cluster:
  successful scheduling, Pending states, and failure messages
- Connect scheduler decisions to etcd state from Chapter 8

## Background

Two halves: a simulator to practice scheduling-algorithm design
under full observability, and a live `kind` cluster to practice
reading the real scheduler's decisions. The simulator teaches the
mechanisms; the real cluster teaches how those mechanisms surface
as events and diagnostic output. Starter code lives in
`code/ch09-cluster-sched/`.

## Part A: Implement Three Schedulers (Required)

**Goal:** Implement FIFO, Backfill, and DRF in a Python simulator
and run them on the same mixed workload.

### A.1 The framework

`scheduler_sim.py` ships with the data structures (`Job`,
`Machine`), a mixed workload generator (`mixed_workload()`), and
metrics code (`compute_metrics()`). Three function stubs need
bodies:

- `schedule_fifo(jobs, machines)` — pure FIFO by submit time.
- `schedule_backfill(jobs, machines)` — FIFO with backfill of
  small jobs into gaps.
- `schedule_drf(jobs, machines)` — Dominant Resource Fairness.

### A.2 FIFO

The simplest of the three. Process jobs in `submit_time` order;
for each job, find the earliest time ≥ `submit_time` when
`nodes_required` machines can *simultaneously* fit its CPU and
memory demand. Use `machine.next_free_time()` and
`machine.can_fit()` as helpers. Gang-scheduled jobs
(`nodes_required > 1`) must start on all their nodes at the same
time.

### A.3 Backfill

Start from FIFO. When the head-of-queue job cannot start now,
compute its reservation time (the earliest time it *can* start).
Then scan the rest of the queue: any job that can start now and
*finish before the reservation time* is a legal backfill. Execute
backfills, then continue FIFO.

The intuition is "do not waste a gap the reservation is not yet
using". Good backfill reduces `avg_wait_time` without delaying the
head job.

### A.4 DRF

Dominant Resource Fairness. At each scheduling point:

1. Compute each user's *dominant share* — the maximum of their
   CPU share and memory share across all currently running jobs.
2. Pick the user with the *smallest* dominant share.
3. Schedule that user's earliest-submitted unscheduled job that
   fits.
4. If nothing fits, advance time to the next event.

DRF prevents one user's big jobs from monopolizing the cluster,
but it may not win on makespan or utilization.

### A.5 Run and compare

```bash
cd code/ch09-cluster-sched/sim
python3 scheduler_sim.py
```

You should get three Gantt charts and a comparison table like:

```text
 Metric                     FIFO       Backfill        DRF
 -------------------------  ---------  ---------  ---------
 makespan                           ?          ?          ?
 avg_completion_time                ?          ?          ?
 avg_wait_time                      ?          ?          ?
 utilization                        ?          ?          ?
 jain_fairness                      ?          ?          ?
```

### A.6 Sanity checks

- **FIFO.** Bob's big gang-scheduled jobs should cause head-of-
  line blocking — Alice's small jobs pile up waiting.
- **Backfill.** Alice's small jobs should fill the gaps left by
  Bob's reservations, driving utilization up.
- **DRF.** Per-user CPU-time should be more evenly distributed
  across Alice, Bob, and Charlie.

### Part A Checklist

- [ ] FIFO, Backfill, and DRF implemented
- [ ] Gantt charts printed for each
- [ ] Comparison table filled

## Part B: Workload Analysis (Required)

**Goal:** Connect the numbers to the mechanisms.

Answer in your report:

1. **Backfill vs FIFO.** By how much did backfill reduce makespan?
   Which specific jobs were backfilled (ran earlier than under
   FIFO)? What property of those jobs made them good backfill
   candidates?
2. **DRF's fairness impact.** Compare per-user CPU-time. Under
   FIFO, does Bob (big jobs) dominate? How does DRF change the
   distribution? Does it cost you makespan?
3. **Tradeoffs.** Which algorithm wins on makespan? On fairness?
   On utilization? Can any one algorithm win on all three? Why
   not?
4. **Gang scheduling.** Bob's `b1` needs 2 nodes, `b3` needs 3.
   How does each algorithm handle them? Does gang scheduling
   create extra waiting for other users?

**Bonus.** Construct a workload where DRF produces a *worse*
makespan than FIFO. Explain why. (Hint: fairness can force
suboptimal packing.)

### Part B Checklist

- [ ] Four analysis questions answered with specific numbers
- [ ] Tradeoff table present
- [ ] (Optional) bonus workload described

## Part C: Real K8s Scheduling Observation (Required)

**Goal:** Watch the real scheduler make and *fail* to make
decisions.

### C.1 Create a resource-constrained cluster

```yaml
# kind-scheduling-lab.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
  kubeadmConfigPatches:
  - |
    kind: KubeletConfiguration
    systemReserved:
      cpu: "500m"
      memory: "500Mi"
- role: worker
  kubeadmConfigPatches:
  - |
    kind: KubeletConfiguration
    systemReserved:
      cpu: "500m"
      memory: "500Mi"
```

```bash
kind create cluster --name sched-lab --config kind-scheduling-lab.yaml
```

### C.2 Watch events in real time

In a second terminal:

```bash
kubectl get events --watch --field-selector reason=Scheduled
```

In the first, schedule a trivial Pod and verify:

```bash
kubectl run small-job --image=busybox --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"small-job","image":"busybox","command":["sleep","300"],"resources":{"requests":{"cpu":"100m","memory":"64Mi"}}}]}}'
kubectl get pod small-job -o wide
```

### C.3 Create fragmentation

Fill the cluster with medium Pods:

```bash
for i in $(seq 1 6); do
  kubectl run filler-$i --image=busybox --restart=Never \
    --overrides="{\"spec\":{\"containers\":[{\"name\":\"filler-$i\",\"image\":\"busybox\",\"command\":[\"sleep\",\"600\"],\"resources\":{\"requests\":{\"cpu\":\"500m\",\"memory\":\"256Mi\"}}}]}}"
done

kubectl describe nodes | grep -A 5 "Allocated resources"
```

Now try to schedule a Pod that will not fit:

```bash
kubectl run big-job --image=busybox --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"big-job","image":"busybox","command":["sleep","300"],"resources":{"requests":{"cpu":"2","memory":"1Gi"}}}]}}'

kubectl get pod big-job
kubectl describe pod big-job | grep -A 10 Events
```

You should see `FailedScheduling` with a message like
`0/3 nodes are available: 2 Insufficient cpu`. Record it.

### C.4 Free resources and watch the Pod schedule

```bash
kubectl delete pod filler-1 filler-2 filler-3
kubectl get pod big-job -w
```

Record:

- How long was `big-job` Pending?
- Which Filter message blocked it?
- Which node did it land on after resources freed?

### C.5 Exercise affinity (optional but recommended)

Apply `manifests/node-affinity-demo.yaml`, which adds a
`nodeAffinity` rule preferring one worker. Check which node the
Pod lands on and which Score plugin you think tipped the decision.

### Part C Checklist

- [ ] `kind` cluster up with constrained workers
- [ ] `FailedScheduling` event captured for `big-job`
- [ ] Transition Pending → Running observed after freeing
- [ ] Filter message quoted verbatim in the report

## Part D: etcd Connection (Optional)

**Goal:** Confirm that the scheduler's binding is persisted in
etcd via Raft (Chapter 8).

`kind` ships etcd inside the control-plane container. You can
peek at it:

```bash
docker exec -it sched-lab-control-plane sh -c "
  ETCDCTL_API=3 etcdctl \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/apiserver-etcd-client.crt \
    --key=/etc/kubernetes/pki/apiserver-etcd-client.key \
    get /registry/pods/default/small-job --prefix"
```

The output is the Pod object including `spec.nodeName` — the same
string the scheduler wrote via Bind. Compare it to
`kubectl get pod small-job -o yaml`.

One paragraph in your report: **what Chapter 8 guarantee ensures
that kubelet on node-a and kubelet on node-b cannot disagree about
which node should run `small-job`?**

## Deliverables

Submit:

1. **`scheduler_sim.py`** — your implementations of `schedule_fifo`,
   `schedule_backfill`, and `schedule_drf`.
2. **`report.md`** — narrative covering all parts:
   - Part A: Gantt charts (text is fine), metrics table, code
     approach description for each algorithm.
   - Part B: answers to the four analysis questions, bonus if
     attempted.
   - Part C: `FailedScheduling` event verbatim, timeline of the
     Pending → Running transition, interpretation tied to the
     Filter phase.
   - Part D (optional): etcd dump, consistency paragraph.
3. **Environment block** — kernel, Kubernetes, `kind`, Python
   versions; cluster config used.

## Grading Rubric

| Criterion | Points |
|---|---|
| FIFO, Backfill, DRF implemented and produce Gantt charts | 30 |
| Workload analysis answers connect numbers to mechanisms | 20 |
| `kind` cluster set up; `FailedScheduling` captured | 20 |
| Pending → Running transition observed with interpretation | 15 |
| Mechanism explanations tied to Chapter 9 | 15 |
| **Optional** etcd persistence analysis | +10 bonus |

**Total: 100 (+10 bonus).**

## Common Pitfalls

- **FIFO implementation that schedules at time 0 only.**
  Remember `Job.submit_time`; a job that arrives at `t=5` cannot
  start before `t=5`.
- **Gang scheduling wrongly implemented per-machine.** Need
  `nodes_required` machines at the *same* time.
- **Backfill that delays the head job.** Check your reservation
  time carefully — the small job must *finish* before the head
  job's reservation starts.
- **DRF without a time-stepping loop.** Running jobs free
  resources when they end; advance a simulated clock.
- **`kind` cluster too large.** If your node has 4 CPU, you
  cannot reproduce "Insufficient cpu" with 100m Pods. Use
  `systemReserved` to shrink effective capacity.

## Troubleshooting

- **`kubectl get events --watch` shows nothing.** Field selector
  typo, or events are old. Drop the `--field-selector`.
- **`kind create cluster` hangs.** `docker` daemon not running
  or out of disk. `docker system prune` may help.
- **Simulator numbers off by one.** Remember inclusive/exclusive
  intervals: `end_time = start_time + duration`, not `start + duration - 1`.

## Cleanup

```bash
kind delete cluster --name sched-lab
```

## Reference: Useful Commands

```bash
kubectl get pods -o wide
kubectl describe pod <name>
kubectl describe node <name>
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl top node
kubectl logs -n kube-system -l component=kube-scheduler --tail=50
```
