# Lab: fsync Latency Measurement

> **Estimated time:** 4–6 hours
>
> **Prerequisites:** Chapter 10 concepts; a Linux VM with ext4 and
> root access
>
> **Tools used:** `dd`, `filefrag`, `debugfs`, `/proc/meminfo`,
> `iostat`, `strace`, `write_latency.c` (provided in
> `code/ch10-fsync-bench/`)

## Objectives

- Inspect how a file is physically laid out on disk
- Observe the page cache in action (hit/miss, dirty, writeback)
- Measure write-latency distributions with and without `fsync`
- Quantify how concurrent work inflates the fsync tail

## Background

Four parts, progressing from passive inspection to active
measurement to interference. Emphasis: the evidence contract
from Chapter 3 — every performance claim needs two signals and
one exclusion.

### VirtualBox / hypervisor caveat

VirtualBox's virtual disk may cache writes at the host level.
Expected effect on your results: the buffered-vs-fsync gap will
be ~10–100× rather than the ~1000× you would see on real
hardware. The *shape* of the distribution is still instructive;
the absolute numbers are not production numbers. If fsync
latency reads as < 0.01 ms, you are almost certainly on tmpfs —
check `df -T /tmp`.

## Prerequisites

```bash
df -T /                        # expect ext4
which filefrag                  # ships with e2fsprogs
iostat -V                       # sudo apt install sysstat if missing
strace --version
grep Dirty /proc/meminfo        # read access to /proc
df -h /tmp                      # need ~1 GB free
```

Create a working directory:

```bash
mkdir -p ~/lab9/{data,results}
cd ~/lab9
```

## Part A: File Layout Inspection (Required, 20 min)

### A.1 Create test files

```bash
cd ~/lab9/data

# A sequential file — should be nearly one extent
dd if=/dev/zero of=sequential.dat bs=1M count=10

# A file written in small random-offset chunks — should be fragmented
python3 -c "
import os, random
fd = os.open('fragmented.dat', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
for _ in range(2560):
    os.lseek(fd, random.randint(0, 10*1024*1024 - 4096), os.SEEK_SET)
    os.write(fd, b'X' * 4096)
os.close(fd)
"
```

### A.2 Inspect with `filefrag`

```bash
filefrag -v sequential.dat
filefrag -v fragmented.dat
```

Record: extent count for each, longest extent length, what this
says about ext4's allocator (delayed allocation for the
sequential case; fragmentation forced by random-offset writes).

### A.3 Inspect with `debugfs`

```bash
DEV=$(df / | tail -1 | awk '{print $1}')
INO=$(ls -i ~/lab9/data/sequential.dat | awk '{print $1}')
sudo debugfs -R "stat <${INO}>" "${DEV}"
```

Record: inode fields present, extent-tree depth, block count vs
file size.

### A.4 Hard links

```bash
ln ~/lab9/data/sequential.dat ~/lab9/data/seq_link.dat
ls -i ~/lab9/data/sequential.dat ~/lab9/data/seq_link.dat
stat ~/lab9/data/sequential.dat | grep Links
```

Both names share one inode; link count is 2. Explain in the
report why filenames are not in the inode.

### Part A Checklist

- [ ] Two files created (sequential, fragmented)
- [ ] `filefrag` output captured for each
- [ ] `debugfs` inode dump captured for one file
- [ ] Hard-link experiment performed; link count explained

## Part B: Page Cache Observation (Required, 20 min)

### B.1 Watch dirty pages in real time

Terminal 1:

```bash
watch -n 0.5 'grep -E "Dirty|Writeback|MemFree|Cached" /proc/meminfo'
```

Terminal 2:

```bash
dd if=/dev/zero of=/tmp/dirty_test bs=1M count=200
```

Record: peak `Dirty` value, time until `Dirty` starts dropping
(writeback engaged), value after `dd` completes.

### B.2 Force writeback

```bash
sync
grep Dirty /proc/meminfo
```

`Dirty` should drop to near zero.

### B.3 Drop caches and demonstrate cache effect

```bash
sync && sudo sysctl vm.drop_caches=3

# Cold read
time cat ~/lab9/data/sequential.dat > /dev/null

# Warm read
time cat ~/lab9/data/sequential.dat > /dev/null
```

Record the cold-vs-warm ratio. Explain using Chapter 10 §10.3.

### Part B Checklist

- [ ] `Dirty` climb and fall observed and recorded
- [ ] `sync` emptied `Dirty`
- [ ] Cold-vs-warm read timed

## Part C: Write Latency Measurement (Required, 30 min)

### C.1 Build `write_latency`

Source in `code/ch10-fsync-bench/write_latency.c`:

```bash
cd code/ch10-fsync-bench
make
# or: gcc -O2 -o write_latency write_latency.c
```

The program performs N writes to a file, optionally calling
`fsync` or `fdatasync` after each, and reports min/p50/p90/p99/
max. CSV output via `-c`.

### C.2 Three baselines

Between runs, drop caches to keep conditions comparable:

```bash
# Buffered (no sync)
sync && sudo sysctl vm.drop_caches=3
./write_latency -n 10000 -c ~/lab9/results/baseline_buffered.csv /tmp/testfile

# fsync per write
sync && sudo sysctl vm.drop_caches=3
./write_latency -n 10000 -f -c ~/lab9/results/baseline_fsync.csv /tmp/testfile

# fdatasync per write
sync && sudo sysctl vm.drop_caches=3
./write_latency -n 10000 -d -c ~/lab9/results/baseline_fdatasync.csv /tmp/testfile
```

### C.3 Fill the table

| Configuration | p50 | p90 | p99 | max |
|---|---|---|---|---|
| Buffered (no fsync) |   |   |   |   |
| fsync |   |   |   |   |
| fdatasync |   |   |   |   |

Explain in 1–2 paragraphs:

- Why is buffered write so much faster? Trace the kernel steps
  that differ (Chapter 10 §10.3).
- Why is fdatasync faster than fsync? What metadata does fsync
  force that fdatasync can sometimes skip?
- Comment on the magnitude of the gap vs what Chapter 10 quotes
  (~1000× on real hardware). Explain any discrepancy from your
  VM environment.

### Part C Checklist

- [ ] Three CSVs produced
- [ ] Percentile table filled
- [ ] Mechanism explanation written

## Part D: Interference Experiments (Required, 20 min)

Pick **at least two** of the following. Run each while measuring
fsync latency in a second terminal.

### D.1 Background sequential I/O

```bash
# Terminal 1 — background writer
dd if=/dev/zero of=/tmp/bg_write bs=1M count=500 conv=fdatasync &
BG=$!

# Terminal 2 — measure
./write_latency -n 10000 -f -c ~/lab9/results/interf_bg_io.csv /tmp/testfile

# Cleanup
kill $BG 2>/dev/null; rm -f /tmp/bg_write
```

### D.2 Memory pressure

```bash
python3 -c "
import time
blocks = []
try:
    while True:
        blocks.append(b'X' * (50 * 1024 * 1024))
        time.sleep(0.5)
except MemoryError:
    time.sleep(999)
" &
MEM=$!

./write_latency -n 5000 -f -c ~/lab9/results/interf_memory.csv /tmp/testfile
kill $MEM 2>/dev/null
```

### D.3 Concurrent fsync from peers

```bash
PIDS=()
for i in 1 2 3 4; do
  bash -c "while true; do dd if=/dev/zero of=/tmp/conc_$i bs=4096 count=100 conv=fsync 2>/dev/null; done" &
  PIDS+=($!)
done

./write_latency -n 10000 -f -c ~/lab9/results/interf_concurrent.csv /tmp/testfile

for pid in "${PIDS[@]}"; do kill $pid 2>/dev/null; done
rm -f /tmp/conc_*
```

### D.4 Periodic cache drops

```bash
while true; do sync; sudo sysctl vm.drop_caches=3; sleep 2; done &
DROP=$!

./write_latency -n 5000 -f -c ~/lab9/results/interf_cold.csv /tmp/testfile

kill $DROP 2>/dev/null
```

### D.5 Fill the interference table

| Experiment | p50 | p90 | p99 | max | p99 ratio vs baseline |
|---|---|---|---|---|---|
| Baseline (fsync) |   |   |   |   | 1× |
| Background I/O |   |   |   |   |   |
| Memory pressure |   |   |   |   |   |
| Concurrent fsync |   |   |   |   |   |
| Cold cache |   |   |   |   |   |

### Part D Checklist

- [ ] At least two interference experiments run
- [ ] CSVs preserved
- [ ] Table filled
- [ ] Each experiment has a one-paragraph explanation of the
      mechanism

## Part E: System-Level Observation (Optional, Bonus)

### E.1 `iostat`

```bash
# Terminal 1
iostat -x 1

# Terminal 2 — run any Part D experiment
```

Record `await` and `%util` during the experiment. Do they
correlate with the application-level spike?

### E.2 `strace -T`

```bash
strace -T -e fsync ./write_latency -n 100 -f /tmp/testfile 2>&1 | tail -20
```

`-T` prints per-syscall durations. Look for outliers; cross-check
with your application-level histogram.

## Deliverables

Submit a `lab9/` directory:

```text
lab9/
├── write_latency.c
├── results/
│   ├── baseline_buffered.csv
│   ├── baseline_fsync.csv
│   ├── baseline_fdatasync.csv
│   └── interf_*.csv        (at least 2)
└── lab9_report.md
```

Your `report.md` must include:

- Part A: filefrag + debugfs output with interpretation.
- Part B: `Dirty` timeline, `sync` effect, cold-vs-warm read.
- Part C: percentile table for the three modes, mechanism
  paragraph.
- Part D: interference table with p99 ratios, one paragraph per
  experiment linking the ratio to a mechanism.
- (Optional) Part E: `iostat` / `strace` corroboration.

## Grading Rubric

| Criterion | Points |
|---|---|
| Part A: layout inspection with filefrag + debugfs | 15 |
| Part B: page cache observations with `/proc/meminfo` timeline | 15 |
| Part C: three baselines measured; table filled | 20 |
| Part D: at least two interference experiments with evidence | 25 |
| Analysis depth — mechanism explanations tied to Chapter 10 | 25 |

**Total: 100 points.**

## Evidence Contract Reminder

For every performance claim in your report, include:

- **Two independent signals** (e.g., `write_latency`'s p99 *and*
  `iostat`'s `await` during the same window).
- **One exclusion check** (e.g., confirm the page cache was cold
  via `sync && drop_caches` *before* the measurement, so the
  hit/miss variable is ruled out).

## Common Issues

- **`filefrag: command not found`** — `sudo apt install
  e2fsprogs`.
- **`debugfs` says nothing** — wrong device path; check `df /`.
- **fsync latency < 10 µs** — almost certainly on tmpfs.
  Switch to an ext4 path; check `df -T /tmp`.
- **Wild variance between runs** — expected, especially in VMs.
  Run each experiment at least twice and report the range.

## Reference: Useful Commands

```bash
filefrag -v <file>                # extent layout
sudo debugfs -R "stat <inode>" /dev/sdX
grep -E "Dirty|Cached|Writeback" /proc/meminfo
sync; sudo sysctl vm.drop_caches=3
iostat -x 1
strace -T -e fsync ./program
```
