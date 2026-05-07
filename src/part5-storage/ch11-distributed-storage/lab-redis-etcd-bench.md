# Lab: Redis and etcd Benchmarks

> **Estimated time:** 5–6 hours
>
> **Prerequisites:** Chapters 8, 10, 11; Docker in an Ubuntu VM;
> Redis, etcd, optionally MinIO
>
> **Tools used:** `redis-benchmark`, `redis-cli`, `etcdctl`, etcd
> `benchmark`, `iostat`, `pidstat`, `mc` (MinIO client)

## Objectives

- Measure how Redis's AOF `fsync` policy changes throughput and
  p99 latency, and connect the result to Chapter 10's fsync
- Observe `BGSAVE` fork + copy-on-write using `/proc/[pid]/smaps`
  and `pidstat`
- Benchmark etcd write throughput, watch WAL growth, and measure
  interference during compaction
- (Optional) Compare MinIO, Redis, and etcd at the same payload
  size on the same machine

## Background

This lab exercises the durability stack you built up across
Chapters 8 and 10 on real production-grade software. Starter
scripts live in `code/ch11-redis-etcd/`.

## Prerequisites

```bash
# Docker inside the VM
sudo apt update
sudo apt install -y docker.io redis-tools sysstat
sudo usermod -aG docker $USER && newgrp docker

# etcd benchmark tool (from Chapter 8's lab — reuse if already built)
export PATH=$PATH:$(go env GOPATH)/bin
benchmark --help | head -3

# MinIO client (optional, for Part D)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/
```

## Part A: Redis AOF fsync Benchmark (Required)

**Goal:** Measure the throughput-vs-durability tradeoff from
three `appendfsync` policies.

### A.0 Predict before you measure

Using only your fsync numbers from Lab 10 (Chapter 10) and the
AOF semantics from Chapter 11 §11.3, write the following
prediction in your report:

> *"At pipeline depth 1, `appendfsync no` will sustain ____
> ops/s; `everysec` will sustain ____ ops/s; `always` will
> sustain ____ ops/s. The throughput ratio
> `no : everysec : always` will be approximately ____ : ____ : ____,
> because ____."*

Fill in three throughput numbers and the ratio. The reasoning
blank must explain *which writes pay an fsync each* (only the
background writer / once per second / every command's reply) —
not just "`always` is slower".

A reasonable starting model on enterprise SSD: `everysec` is
essentially free per command (one fsync amortizes over
~10 000–50 000 commands), while `always` pays one fsync per
command. If your Lab 10 measured ~1 ms per fdatasync, then
stand-alone `always` cannot exceed 1 / 0.001 = 1000 ops/s, and
your predicted `everysec : always` ratio should be at least 10×
(often 50–100× on consumer hardware).

Then predict the second-order effect:

> *"At pipeline depth 16, the `everysec : always` ratio will
> shrink / stay the same / grow, because ____."*

Pick one. The Chapter 10 mental model of fsync is what tells
you the answer; record your reasoning explicitly.

After measuring (§A.4), tag each prediction as confirmed,
off-but-correct-direction, or wrong, and explain any gap larger
than 2× in one sentence.

### A.1 Launch Redis in each mode

A helper script sets up all three instances with clean port assignments:

```bash
cd code/ch11-redis-etcd
bash scripts/redis-lab-up.sh ~/lab11/redis
```

This creates:
- `redis-no` on port **6379** (appendfsync no)
- `redis-everysec` on port **6380** (appendfsync everysec)
- `redis-always` on port **6381** (appendfsync always)

Verify:

```bash
redis-cli -p 6379 PING
redis-cli -p 6380 PING
redis-cli -p 6381 PING
```

### A.2 Benchmark each

For each policy, run:

```bash
redis-benchmark -h 127.0.0.1 -p <port> -t set -n 200000 -c 50 -P 1 \
  --csv > results_${policy}.csv
```

Record ops/s and p50/p95/p99. Then re-run with `-P 16`
(pipelining) to see how much batching can hide fsync cost under
`everysec` and `always`.

### A.3 Cross-check with iostat

Run `iostat -x 1` in another terminal while the `always`
benchmark runs. Capture one window of output. Observe:

- `w/s` (writes per second to the disk).
- `await` (per-I/O latency).
- `%util` (device saturation).

### A.4 Fill the table

| Policy | Throughput (ops/s) | p50 (ms) | p99 (ms) | `iostat await` (ms) |
|---|---|---|---|---|
| `no` |   |   |   |   |
| `everysec` |   |   |   |   |
| `always` |   |   |   |   |

### A.5 Explain

Two paragraphs:

- Why is `always` ~100× slower than `everysec`? Refer to
  Chapter 10 §10.5 (fsync cost: flush cache, flush journal,
  flush device cache).
- What does the `iostat await` number tell you that
  `redis-benchmark` alone cannot?

### Part A Checklist

- [ ] Three Redis instances running
- [ ] Throughput and latency recorded for each policy
- [ ] `iostat` cross-check captured
- [ ] Mechanism explanation written

## Part B: Redis BGSAVE and COW Observation (Required)

**Goal:** Watch fork + copy-on-write in action when Redis takes
an RDB snapshot.

### B.1 Load data

```bash
# Populate ~1 GB
redis-cli -p 6379 DEBUG POPULATE 10000000 x 100
redis-cli -p 6379 INFO memory | grep used_memory_human
```

### B.2 Trigger BGSAVE and measure

```bash
REDIS_PID=$(docker exec redis-no pidof redis-server)
cat /proc/$REDIS_PID/status | grep -E "VmRSS|Threads"

# Capture a "before" snapshot
cat /proc/$REDIS_PID/smaps | awk '
  /^Private_Dirty/ {pd+=$2}
  /^Shared_Clean/  {sc+=$2}
  END { print "Private_Dirty:", pd, "kB;  Shared_Clean:", sc, "kB" }
'

# Trigger a background save
redis-cli -p 6379 BGSAVE

# Periodically poll the child (while BGSAVE is in flight)
while pgrep -f "redis-server.*rdb" > /dev/null; do
    ps -o pid,rss,comm -C redis-server
    sleep 1
done
```

### B.3 While the snapshot runs, add write pressure

```bash
redis-benchmark -p 6379 -t set -n 100000 -c 20
```

This forces COW fragmentation: every page the parent modifies
during the snapshot has to be copied.

### B.4 Record

- `fork` duration (`BGSAVE` sets `lastsave_time`; or watch
  process creation in `ps`).
- Peak RSS of parent plus child during the snapshot.
- Growth of `Private_Dirty` from before to after the write
  pressure (each new dirty private page is a COW fault).

### B.5 Explain

One paragraph: why the Redis guidance "`maxmemory` ≤ 50 % of
RAM" exists. Tie it to fork, COW, and the writeback pressure
from Chapter 10 §10.3.

### Part B Checklist

- [ ] BGSAVE captured; fork time and peak RSS recorded
- [ ] `Private_Dirty` before/after measured
- [ ] Mechanism paragraph references Chapter 4 (fork),
      Chapter 6 (cgroups), Chapter 10 (writeback)

## Part C: etcd Write Throughput and Compaction (Required)

**Goal:** Benchmark etcd writes, watch WAL grow, and measure
write latency during compaction.

### C.1 Launch a single-node etcd

```bash
docker run -d --name etcd-lab -p 2390:2379 \
  quay.io/coreos/etcd:v3.5.17 etcd \
  --name lab \
  --listen-client-urls http://0.0.0.0:2379 \
  --advertise-client-urls http://127.0.0.1:2390

export SINGLE_EP=http://127.0.0.1:2390
```

### C.2 Baseline benchmark

```bash
benchmark --endpoints=${SINGLE_EP} --conns=10 --clients=100 \
  put --total=200000 --key-size=16 --val-size=256 \
  > ~/lab11/etcd_baseline.txt
```

Record p50, p99, throughput.

### C.3 Watch the WAL grow

```bash
docker exec etcd-lab ls -l /var/lib/etcd/member/wal/
docker exec etcd-lab du -sh /var/lib/etcd
```

Run the benchmark again with more operations (e.g., `--total=2000000`) and watch WAL size climb.

### C.4 Trigger compaction during a write benchmark

Terminal 1: start a longer benchmark:

```bash
benchmark --endpoints=${SINGLE_EP} --conns=10 --clients=100 \
  put --total=1000000 --key-size=16 --val-size=256 \
  > ~/lab11/etcd_during_compaction.txt
```

Terminal 2: partway through, compact and defrag:

```bash
REV=$(etcdctl --endpoints=${SINGLE_EP} endpoint status --write-out=json \
  | jq '.[0].Status.header.revision')
etcdctl --endpoints=${SINGLE_EP} compact $REV
etcdctl --endpoints=${SINGLE_EP} defrag
```

Record:

- Baseline p99.
- p99 during the benchmark that experienced compaction.
- DB size before and after defrag (`du -sh /var/lib/etcd` on
  the node).

### C.5 Explain

One paragraph: why compaction inflates write p99 (defrag rewrites
the bbolt file; writes wait behind the rewrite), and what the
equivalent mechanism was in Chapter 10 (journal commits
contending for disk).

### Part C Checklist

- [ ] etcd baseline benchmark recorded
- [ ] WAL growth observed
- [ ] Compaction performed during a live benchmark
- [ ] p99 comparison recorded
- [ ] DB size before/after defrag

## Part D: MinIO Comparison (Optional)

**Goal:** See where an object store sits on the storage spectrum
next to Redis and etcd.

### D.1 Launch MinIO

```bash
docker run -d --name minio-lab -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin -e MINIO_ROOT_PASSWORD=password \
  minio/minio server /data --console-address ":9001"

mc alias set local http://127.0.0.1:9000 admin password
mc mb local/lab
```

### D.2 Measure small-object PUT latency

```bash
# 256-byte objects to match Redis/etcd payload
for i in $(seq 1 1000); do
  dd if=/dev/urandom of=/tmp/obj_$i bs=256 count=1 2>/dev/null
done

time for i in $(seq 1 1000); do
  mc cp /tmp/obj_$i local/lab/ > /dev/null
done
```

Compute average per-PUT latency. Expect tens of milliseconds —
mostly HTTP overhead and MinIO's own fsync.

### D.3 Compare

| System | Payload | Throughput (ops/s) | p50 (ms) | Use case |
|---|---|---|---|---|
| Redis (everysec) | 256 B |   |   | Cache |
| etcd (single) | 256 B |   |   | Coordination |
| MinIO (single) | 256 B |   |   | Object store |

### D.4 Explain

One paragraph on why each system is, or is not, a good fit for a
256-byte workload. Reference Chapter 11 §11.1 (the spectrum) and
§11.5 (object-store design).

## Deliverables

Submit a `lab11/` directory containing:

```text
lab11/
├── redis/
│   ├── results_no.csv
│   ├── results_everysec.csv
│   └── results_always.csv
├── redis_bgsave_log.txt
├── etcd_baseline.txt
├── etcd_during_compaction.txt
├── (optional) minio_put_log.txt
└── lab11_report.md
```

`report.md` must include:

- Part A: table of fsync-policy tradeoffs with iostat
  cross-check and mechanism paragraph.
- Part B: fork + COW timeline with `Private_Dirty` evidence.
- Part C: etcd baseline vs during-compaction p99 with WAL and DB
  size evidence.
- (Optional) Part D: comparison table across Redis/etcd/MinIO.

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
| Part A: three fsync policies measured; mechanism explained | 35 |
| Part B: fork/COW observed with smaps or pidstat evidence | 25 |
| Part C: etcd benchmark and compaction impact recorded | 25 |
| Evidence contract (two signals + one exclusion) followed | 15 |
| **Optional** MinIO comparison | +10 bonus |

**Total: 100 (+10 bonus).**

## Common Pitfalls

- **Redis AOF not actually enabled.** Check
  `redis-cli CONFIG GET appendonly` → `yes`.
- **Measuring on tmpfs.** MinIO's `/data` mount, etcd's data
  dir, or Redis's `/data` on a tmpfs volume will give
  unrealistic numbers. Mount a real disk path.
- **BGSAVE on a warm dataset.** If Redis has been idle, there
  are few dirty pages; the COW expansion is tiny. Add writes
  during the snapshot to see the effect.
- **Compaction on a fresh etcd.** If the DB has few revisions,
  compaction does nothing. Generate tens of thousands of
  writes first.

## Cleanup

```bash
cd code/ch11-redis-etcd
bash scripts/redis-lab-down.sh
docker stop etcd-lab minio-lab 2>/dev/null || true
docker rm   etcd-lab minio-lab 2>/dev/null || true
rm -rf ~/lab11
```

## Reference

- Redis persistence docs:
  <https://redis.io/docs/management/persistence/>
- etcd benchmark:
  <https://etcd.io/docs/v3.5/op-guide/performance/>
- MinIO docs: <https://min.io/docs/>
- `man 5 proc` for `/proc/[pid]/smaps` fields
