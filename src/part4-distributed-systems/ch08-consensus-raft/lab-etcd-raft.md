# Lab: Observing Raft in etcd

> **Estimated time:** 4–5 hours
>
> **Prerequisites:** Chapter 8 concepts (Raft, etcd); Docker in an
> Ubuntu VM
>
> **Tools used:** `docker`, `etcdctl`, etcd `benchmark`, `curl`,
> `bash`

## Objectives

- Build and operate a 3-node etcd cluster
- Inspect Raft term, leader, and log index
- Measure the latency cost of consensus (single-node vs 3-node)
- Simulate failures (leader crash, network partition) and observe
  recovery
- Watch follower catch-up after log divergence
- Predict before each measurement and rule out one alternative
  explanation grounded in your raw etcd output

## Background

This lab runs etcd v3.5.17 in Docker containers inside your Ubuntu
VM. All observations come from `etcdctl` and etcd's own
`benchmark` tool; you do not need the host-native etcd client.
Starter scripts and manifests live in `code/ch08-etcd-raft/`.

## Prerequisites

### Docker inside the VM

Install Docker Engine if you have not already (from Lab 6 / 7):

```bash
sudo apt-get update
sudo apt-get install -y curl uidmap
curl -fsSL https://get.docker.com | sudo sh
dockerd-rootless-setuptool.sh install
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
systemctl --user start docker

docker version
docker run --rm hello-world
```

### Choose the etcd image

```bash
export ETCD_IMAGE=quay.io/coreos/etcd:v3.5.17
# Fallback: gcr.io/etcd-development/etcd:v3.5.17
docker pull ${ETCD_IMAGE}
docker run --rm ${ETCD_IMAGE} etcd --version
docker run --rm ${ETCD_IMAGE} etcdctl version
```

Both commands should report `3.5.17`.

### Helper shell functions

Define once per shell session:

```bash
etcdctl_in() {
  docker exec -e ETCDCTL_API=3 "$1" etcdctl "${@:2}"
}

export CLUSTER_EP=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379
export SINGLE_EP=http://127.0.0.1:2390
export HOST_CLUSTER_EP=http://127.0.0.1:2379,http://127.0.0.1:2381,http://127.0.0.1:2382
```

`etcdctl_in` avoids a known issue: some etcd images lack
`/bin/sh`, so `docker exec <c> sh -lc '...'` fails. Calling
`etcdctl` directly sidesteps it.

### Install the benchmark tool (for Part C Phase 2)

```bash
sudo apt install -y git golang-go
mkdir -p ~/src && cd ~/src
git clone --depth 1 --branch v3.5.17 https://github.com/etcd-io/etcd.git
cd etcd
go install -v ./tools/benchmark
export PATH=$PATH:$(go env GOPATH)/bin
benchmark --help | head -5
```

## Part A: Cluster Setup and State Inspection (Required)

### A.1 Create the network and launch three nodes

A helper script automates this setup:

```bash
cd code/ch08-etcd-raft
bash scripts/cluster-up.sh
```

Or manually:

```bash
docker network create etcd-net

for i in 1 2 3; do
  port_client=$((2379 + (i-1)*2))
  docker run -d --name etcd$i --network etcd-net \
    -p ${port_client}:2379 \
    ${ETCD_IMAGE} etcd \
    --name node$i \
    --initial-advertise-peer-urls http://etcd$i:2380 \
    --listen-peer-urls http://0.0.0.0:2380 \
    --advertise-client-urls http://etcd$i:2379 \
    --listen-client-urls http://0.0.0.0:2379 \
    --initial-cluster node1=http://etcd1:2380,node2=http://etcd2:2380,node3=http://etcd3:2380 \
    --initial-cluster-state new \
    --initial-cluster-token lab7-cluster
done

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

### A.2 Inspect Raft state

```bash
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table
```

The table shows each endpoint's ID, version, DB size, whether it
is leader, Raft term, and Raft applied index.

Record:

| Node | Is leader | Raft term | Raft index |
|---|---|---|---|
| etcd1 |   |   |   |
| etcd2 |   |   |   |
| etcd3 |   |   |   |

### A.3 Watch the index advance

```bash
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} put /lab/key1 "hello"
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table
# Raft index should have advanced by at least 1.
```

### Part A Checklist

- [ ] 3-node cluster up, all nodes `Healthy`
- [ ] Leader, term, index recorded
- [ ] Index advance observed after a write

## Part B: Leader Failure and Re-election (Required)

### B.1 Identify and kill the leader

```bash
LEADER=$(etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table \
  | awk '/true/ {print $3}' | tr -d ,)
echo "Current leader container: $LEADER"

# Capture "before" snapshot
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table > status_before.txt

# Time the election
START=$(date +%s%N)
docker stop ${LEADER%:*}    # strip port if needed
sleep 3
# Query a surviving node
SURVIVOR=$(docker ps --format '{{.Names}}' | grep etcd | head -1)
etcdctl_in $SURVIVOR --endpoints=${CLUSTER_EP} endpoint status -w table > status_after.txt
END=$(date +%s%N)

echo "Election window: $(( (END-START)/1000000 )) ms"
cat status_after.txt
```

Record:

- Old leader container name.
- Old term; new term.
- Election time in milliseconds.
- Which node became the new leader.

### B.2 Restart the old leader

```bash
docker start ${LEADER%:*}
sleep 3
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table
```

The rejoining node should become a follower, not resume
leadership. Confirm with the status table.

### Part B Checklist

- [ ] Old leader stopped; new leader elected in seconds
- [ ] Term incremented
- [ ] Restarted node rejoined as follower
- [ ] Election timeline recorded in report

## Part C: Consensus Latency (Required)

**Goal:** Measure the cost of 3-node consensus vs 1-node.

### Prediction (write this before running benchmarks)

Before measuring, predict in your report:

1. By what factor do you expect 3-node write latency to exceed
   1-node? (Hint: what additional steps does a 3-node write
   require that a 1-node write does not?)
2. Will throughput (ops/s) be halved, or worse, or not that bad?
   Why?
3. Will linearizable reads be slower than serializable? By how
   much? What is the extra step?

### Phase 1 — 1-node etcd

```bash
docker run -d --name etcd-single --network etcd-net -p 2390:2379 \
  ${ETCD_IMAGE} etcd \
  --name single \
  --advertise-client-urls http://etcd-single:2379 \
  --listen-client-urls http://0.0.0.0:2379
```

Measure:

```bash
benchmark --endpoints=${SINGLE_EP} --conns=1 --clients=1 \
  put --total=10000 --key-size=16 --val-size=256
```

Record p50, p95, p99 write latency and throughput.

### Phase 2 — 3-node cluster

Make sure all three cluster nodes are running, then:

```bash
benchmark --endpoints=${HOST_CLUSTER_EP} --conns=1 --clients=1 \
  put --total=10000 --key-size=16 --val-size=256
```

Record the same percentiles. Compare:

| Metric | 1-node | 3-node | Ratio |
|---|---|---|---|
| p50 write (ms) |   |   |   |
| p99 write (ms) |   |   |   |
| Throughput (ops/s) |   |   |   |

### Phase 3 — Linearizable vs serializable reads

```bash
benchmark --endpoints=${HOST_CLUSTER_EP} --conns=1 --clients=1 \
  range /lab/key1 --consistency=l --total=1000
benchmark --endpoints=${HOST_CLUSTER_EP} --conns=1 --clients=1 \
  range /lab/key1 --consistency=s --total=1000
```

Record p50 / p99 for each.

### Part C Explanation

In the report, write one paragraph on:

- Where the extra latency in 3-node comes from (hint: Chapter 8
  §8.5 — `fsync` and network round-trip).
- Why linearizable reads cost more than serializable reads (hint:
  the ReadIndex heartbeat).

### Part C Checklist

- [ ] 1-node and 3-node benchmark numbers collected
- [ ] Linearizable vs serializable reads compared
- [ ] Mechanism paragraph written

## Part D: Writes During Leader Failure (Required)

**Goal:** Observe writes fail during an election and resume after.

### D.1 Sustained writes

In one terminal, run a tight loop:

```bash
i=0
while true; do
  i=$((i+1))
  START=$(date +%s%N)
  if etcdctl_in etcd1 --endpoints=${CLUSTER_EP} put /burst/$i x > /dev/null 2>&1; then
    END=$(date +%s%N)
    echo "$i ok $(( (END-START)/1000000 ))"
  else
    echo "$i FAIL"
  fi
done | tee write_log.txt
```

### D.2 Kill the leader mid-stream

In a second terminal, kill the leader container. Watch
`write_log.txt`:

- A window of `FAIL` or very high-latency entries (hundreds of ms
  to a few seconds).
- Writes resume once a new leader is elected.

### D.3 Count the outage

```bash
awk '/FAIL/ {c++} END {print "failed writes:", c}' write_log.txt
awk '/ok/ {print $3}' write_log.txt | sort -n | tail -5
```

Record: total failed writes, maximum successful-write latency
during the outage.

### D.4 Ruled-out alternative

A write that fails for a few seconds during a leader crash has
*at least three* plausible mechanisms, only one of which is the
election itself:

1. The election window itself — the cluster has no leader, so
   nothing can be committed (Chapter 8 §8.4).
2. Client retry / connection failure — the etcdctl client may be
   reconnecting to a different endpoint after the old leader's
   container disappears.
3. WAL `fsync` stall on the *new* leader — if the new leader's
   disk is slow, the first writes after election pay extra
   latency unrelated to consensus.

Name one of (2) or (3) as a competing explanation for your
observed outage duration, and cite one signal in your data that
excludes it. Useful evidence: the timestamps of `FAIL` lines
relative to the new-leader appearance in `endpoint status`, the
fsync time on a single-node etcd benchmark from Part C as a
lower bound for (3), or `docker logs etcd-new-leader` showing
the `become leader` line. "My election completed at t+1.8 s but
FAILs continued until t+3.2 s, so retry-storm (2) is part of the
outage; the fsync number from Part C is 4 ms, so (3) cannot
account for the gap" is the form of the argument.

### Part D Checklist

- [ ] Sustained writes script running
- [ ] Outage window visible in the log
- [ ] Failed-write count and max latency recorded
- [ ] Ruled-out alternative paragraph with supporting signal

## Part E: Network Partition (Optional)

**Goal:** Show a minority cannot commit writes while a majority
can.

```bash
# Isolate etcd3 from the other two
docker network disconnect etcd-net etcd3

# From the majority side (etcd1/etcd2), writes should still work:
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} put /partition/maj "ok"

# From the minority side, writes should hang or time out:
etcdctl_in etcd3 --endpoints=http://etcd3:2379 \
  --command-timeout=5s put /partition/min "x" || echo "expected failure"

# Reconnect and watch catch-up
docker network connect etcd-net etcd3
sleep 3
etcdctl_in etcd3 --endpoints=http://etcd3:2379 get /partition/maj
```

Confirm that `etcd3` sees the key written during its isolation,
demonstrating post-partition catch-up.

## Part F: Follower Lag and Catch-up (Optional)

**Goal:** See a follower fall behind and catch up, possibly via a
snapshot.

```bash
docker stop etcd3

# Generate many writes on the majority
for i in $(seq 1 5000); do
  etcdctl_in etcd1 --endpoints=${CLUSTER_EP} put /lag/$i x > /dev/null
done

# Restart etcd3 and watch it catch up
docker start etcd3
sleep 5
etcdctl_in etcd1 --endpoints=${CLUSTER_EP} endpoint status -w table
```

Record the Raft index on each node before and after. In large
gaps (thousands of entries) etcd will send a snapshot instead of
replaying the WAL; log output on `etcd3` will mention it.

## Deliverables

Submit:

1. **`report.md`** — narrative covering Parts A–D (and Parts E/F
   if attempted). For each part include the recorded numbers plus
   one paragraph on what Chapter 8 section explains the
   observation.
2. **Raw output** — `status_before.txt`, `status_after.txt`,
   `write_log.txt`, benchmark output.
3. **Environment block** — VM config, Docker version, etcd
   version, disk type (SSD / spinning / virtualized).

## AI Use and Evidence Trail

This lab is graded on **prediction → evidence → mechanism**, not
on polish. AI tools are allowed within
[Appendix D](../../appendices/appendix-d-ai-policy.md) (Regime 1):
they may help debug, recall flags, or polish prose; they may
**not** generate the prediction, fabricate raw data, or substitute
for your own mechanism-level explanation. Substantial use must be
disclosed in the Evidence Trail — honest disclosure is not
penalized; non-disclosure of substantial use is.

Append the following section to your report (full template and
examples in Appendix D §"The Evidence Trail"):

```markdown
## Evidence Trail

### Environment and Reproduction
- Commands used: see the Procedure sections above
- Raw output files: list paths in your submission

### AI Tool Use
- **Tool(s) used:** [tool name and version, or "None"]
- **What the tool suggested:** [one-sentence summary, or "N/A"]
- **What I independently verified:** [what you re-checked against
  your own data]
- **What I changed or rejected:** [if a suggestion was wrong or
  inapplicable]

### Failures and Iterations
- [At least one thing that did not work on the first attempt and
  what you learned from it.]
```

## Grading Rubric

| Criterion | Points |
|---|---|
| Part A cluster + inspection | 12 |
| Part B leader failure + re-election | 18 |
| Part C prediction (in advance) and latency comparison | 25 |
| Part D sustained writes; outage window measured | 15 |
| Part D ruled-out alternative with supporting signal | 10 |
| Mechanism explanations tied to Chapter 8 sections | 20 |
| **Optional** Part E or F | +10 bonus |

**Total: 100 (+10 bonus).**

The AI-resistant components are the Part C prediction and the
Part D ruled-out alternative. An LLM cannot predict your specific
VM's WAL fsync, and it cannot exclude retry-storm without
timestamps from your own write log.

## Cleanup

```bash
cd code/ch08-etcd-raft
bash scripts/cluster-down.sh
```

Or manually:

```bash
docker stop etcd1 etcd2 etcd3 etcd-single 2>/dev/null || true
docker rm   etcd1 etcd2 etcd3 etcd-single 2>/dev/null || true
docker network rm etcd-net 2>/dev/null || true
```

## Common Pitfalls

- **Image does not contain `/bin/sh`.** Use the `etcdctl_in`
  helper; do not wrap `etcdctl` in `sh -lc`.
- **Benchmark tool not on `PATH`.** Use `~/go/bin/benchmark` or
  add `$(go env GOPATH)/bin` to `PATH`.
- **`fsync` is the same speed as main memory.** Means the VM is
  not actually `fsync`'ing to durable storage — numbers are not
  representative of real hardware. Note this in the report.
- **Writes to the old leader after it is restarted.** Harmless;
  the restarted node is a follower, and requests are proxied to
  the new leader. But latency may look slightly higher.

## Reference

- etcd docs: <https://etcd.io/docs/v3.5/>
- `etcdctl` reference:
  <https://etcd.io/docs/v3.5/dev-guide/interacting_v3/>
- Raft visualization: <https://raft.github.io/>
