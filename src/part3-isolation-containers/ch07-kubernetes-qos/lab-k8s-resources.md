# Lab: K8s CPU Throttling and OOM

> **Estimated time:** 3–4 hours
>
> **Prerequisites:** Chapter 7 concepts; Ubuntu VM with Docker
> Engine, `kind`, and `kubectl` installed
>
> **Tools used:** `kind`, `kubectl`, `crictl`, cgroup v2 filesystem,
> `docker exec`, `dmesg`

## Objectives

- Deploy Pods with each of the three QoS classes on a local `kind`
  cluster
- Reproduce CPU throttling and read `nr_throttled` from the Pod's
  cgroup
- Reproduce a memory OOM kill and collect the kernel and kubelet
  evidence
- Connect pod-level symptoms (`OOMKilled`, high p99) to the
  specific cgroup mechanism in Chapter 7

## Background

`kind` ("Kubernetes-in-Docker") runs a full K8s control plane and
node inside a Docker container. It is not production, but it is a
fast and faithful way to see real `kubelet` behavior and real
cgroup files on Linux. Starter manifests and scripts live in
`code/ch07-k8s-resources/`.

## Prerequisites

### Install the toolchain (inside your Ubuntu VM)

```bash
# Docker Engine
sudo apt update
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/
kubectl version --client

# kind
go install sigs.k8s.io/kind@latest   # or download the release binary
kind version
```

### Create a small cluster

```bash
cat <<'EOF' > kind-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
EOF

kind create cluster --name mos-lab --config kind-cluster.yaml
kubectl cluster-info --context kind-mos-lab
```

### Find the Pod's cgroup on the node

The Pod's cgroup lives on the *kind node container*, not on your
host. Access it with `docker exec`:

```bash
NODE=$(kind get nodes --name mos-lab | grep worker)
docker exec -it $NODE bash
# Inside the node:
ls /sys/fs/cgroup/kubepods.slice/
```

Keep this shell open — you will use it repeatedly.

## Part A: QoS Class Comparison (Required)

**Goal:** Deploy Guaranteed, Burstable, and BestEffort Pods, and
verify how each is reflected in cgroup settings.

### A.1 Deploy

```bash
cd code/ch07-k8s-resources
kubectl apply -f manifests/qos-comparison.yaml
kubectl get pods -o custom-columns=\
NAME:.metadata.name,QOS:.status.qosClass
```

Expected:

```text
NAME             QOS
qos-guaranteed   Guaranteed
qos-burstable    Burstable
qos-besteffort   BestEffort
```

### A.2 Inspect Each Pod's cgroup

On the node (via `docker exec`), find each Pod's cgroup path:

```bash
# Pod UID in metadata:
kubectl get pod qos-guaranteed -o jsonpath='{.metadata.uid}'

# Cgroup directory (names are kebab-cased UIDs):
find /sys/fs/cgroup/kubepods.slice -name "*<UID>*"
```

Read the limits for each class:

```bash
cat <cgroup>/cpu.max       # Guaranteed: "100000 100000"; BestEffort: "max 100000"
cat <cgroup>/memory.max    # Guaranteed: 67108864 bytes; BestEffort: max
```

Fill in the table:

| Pod | QoS | `cpu.max` | `memory.max` |
|---|---|---|---|
| qos-guaranteed |   |   |   |
| qos-burstable |   |   |   |
| qos-besteffort |   |   |   |

### A.3 One-paragraph Explanation

Write a short paragraph mapping each Pod's YAML spec to the
kubelet's cgroup writes. Which field in the spec produces which
cgroup value? This is the "kubelet translates" step made concrete.

### Part A Checklist

- [ ] Three Pods deployed with the expected QoS labels
- [ ] Each Pod's cgroup located on the node
- [ ] Table filled in
- [ ] Paragraph explaining the translation

## Part B: CPU Throttling (Required)

**Goal:** Force a Pod to hit its CPU limit and observe `nr_throttled`
climb.

### B.1 Deploy a CPU Stress Pod

```bash
kubectl apply -f manifests/cpu-stress.yaml
# The manifest requests and limits cpu: "200m" and runs `stress-ng --cpu 2`.
```

### B.2 Watch the cgroup

In the node shell:

```bash
CG=$(find /sys/fs/cgroup/kubepods.slice -name "*cpu-stress*" -type d | head -1)
while true; do
    cat $CG/cpu.stat | grep -E "nr_throttled|throttled_usec|nr_periods"
    sleep 2
done
```

`nr_throttled` should climb fast. Collect three snapshots into
`cpu_stat.txt`.

### B.3 Measure Latency (Optional But Recommended)

Run a simple HTTP health check against the Pod from your host and
record p50/p99 during throttled vs unthrottled windows. The
easiest way: `kubectl exec` into the stress Pod and run
`./wakeup_lat` from Chapter 4's lab. You should see p99 spikes
correlated with throttling periods.

### B.4 Explain

One paragraph in the report:

- Pod's CPU limit in millicores.
- Corresponding `cpu.max` value.
- Growth rate of `nr_throttled`.
- Why CPU throttling inflates tail latency specifically (Chapter 7
  §7.3).

### Part B Checklist

- [ ] Stress Pod deployed and running
- [ ] `cpu.stat` snapshots captured before, during, after stress
- [ ] `nr_throttled` visibly climbing
- [ ] Mechanism explanation tied to CFS bandwidth control

## Part C: Memory OOM (Required)

**Goal:** Trigger a cgroup OOM, observe `OOMKilled` in pod status,
and find the matching kernel record.

### C.1 Deploy a Memory Hog with a Tight Limit

```bash
kubectl apply -f manifests/mem-stress.yaml
# The manifest sets memory limits to 128Mi and runs a program that
# allocates 256Mi.
```

### C.2 Observe the Kill

```bash
kubectl get pod mem-stress -w
# Expect: Running -> OOMKilled -> CrashLoopBackOff
kubectl describe pod mem-stress | grep -A 5 "Last State"
```

Find the kernel's view on the node:

```bash
docker exec $NODE dmesg -T | grep -i "oom\|kill" | tail -20
```

You should see a line like:

```text
Out of memory: Killed process <pid> (stress) total-vm:... rss:...
```

Cgroup counters:

```bash
cat <cgroup>/memory.events
# oom 1
# oom_kill 1
# max ...
```

### C.3 Explain

Write 1–2 paragraphs:

- What was the memory limit and how much did the process try to
  allocate?
- What path did the kernel take (reclaim → kill)?
- How does cgroup OOM differ from node-level OOM?
- Which `restartPolicy` caused the observed `CrashLoopBackOff`?

### Part C Checklist

- [ ] Pod hits `OOMKilled`
- [ ] Kernel `dmesg` line captured
- [ ] `memory.events:oom` / `oom_kill` incremented
- [ ] Mechanism explanation covers reclaim then kill

## Part D: Eviction Under Node Pressure (Optional)

**Goal:** Fill the node's memory, trigger kubelet eviction, and
verify the order matches QoS ranking.

Warning: this can destabilize your `kind` cluster. Run only if you
are comfortable recreating the cluster afterwards.

### D.1 Setup

Deploy three Pods (one per QoS class) with reasonable requests so
they all schedule successfully. Then create a memory pressure
generator:

```bash
kubectl apply -f manifests/node-pressure.yaml
```

Watch the node:

```bash
kubectl get pods -w
kubectl describe node | grep -A 10 "Allocated resources"
kubectl get events --field-selector reason=Evicted
```

### D.2 Expected

- The BestEffort Pod is evicted first.
- The Burstable Pod is evicted next, if pressure continues.
- The Guaranteed Pod survives longest.

### D.3 Write-up

Document the eviction order and cite the relevant section of the
kubelet log or events. Compare to the ordering in Chapter 7 §7.5.

## Deliverables

Submit:

1. **`report.md`** — the narrative. Include:
   - The QoS table from Part A with one-paragraph interpretation
   - `cpu.stat` snapshots from Part B and a mechanism paragraph
   - The `OOMKilled` evidence from Part C with kernel + cgroup +
     kubelet lines
   - (Optional) Eviction-order evidence from Part D
2. **Raw captures** — `qos-table.txt`, `cpu_stat.txt`,
   `oom_kernel.txt`, `oom_events.txt`.
3. **Environment block** — Kubernetes version, kernel version on
   the `kind` node, Docker version, host OS.

## Grading Rubric

| Criterion | Points |
|---|---|
| Part A table and interpretation | 20 |
| Part B throttling evidence; mechanism tied to CFS bandwidth | 30 |
| Part C OOM evidence across all three layers (kubelet, kernel, cgroup) | 30 |
| Clear narrative linking symptoms to Chapter 7 mechanisms | 20 |
| **Optional** Part D eviction ordering | +10 bonus |

**Total: 100 points (+10 bonus).**

## Common Pitfalls

- **Searching for cgroup paths on the *host*.** The Pod's cgroup
  lives on the `kind` node container, not on your Ubuntu VM. Use
  `docker exec <node> bash`.
- **Confusing request with limit.** A BestEffort Pod has *no*
  request; the scheduler treats it as 0 CPU / 0 memory. It will
  schedule onto any node with a spare slot and throttle itself to
  death if the node is busy.
- **Expecting `cpu.usage` to tell you about throttling.** It
  shows time on CPU. Throttling shows time *off* CPU, in
  `cpu.stat:nr_throttled`.
- **Deleting `kind` cluster without cleanup.** Stuck cgroups can
  linger; `kind delete cluster --name mos-lab` is the clean exit.

## Troubleshooting

- **`kubectl get pods` hangs.** The `kind` cluster did not come up
  cleanly. `kind delete cluster --name mos-lab` and try again.
- **`OOMKilled` but no `dmesg` line.** You read `dmesg` on the
  host. It is inside the `kind` node — `docker exec $NODE dmesg`.
- **Pod pending with "Insufficient cpu".** Your node is smaller
  than the Pod's request. Reduce requests or add a worker
  (`kind create cluster` with a bigger `kind-cluster.yaml`).

## Cleanup

```bash
kubectl delete -f manifests/
kind delete cluster --name mos-lab
```

## Reference: Useful Commands

```bash
kind get nodes --name mos-lab
docker exec <node> bash              # shell on the kind node
kubectl get pod -o wide
kubectl describe pod <name>
kubectl logs <pod> --previous        # last container log before kill
kubectl get events --field-selector reason=Evicted
crictl ps                            # on the kind node, list containers
cat /sys/fs/cgroup/kubepods.slice/<podpath>/cpu.stat
cat /sys/fs/cgroup/kubepods.slice/<podpath>/memory.events
```
