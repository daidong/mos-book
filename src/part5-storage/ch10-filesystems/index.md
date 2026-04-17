# Chapter 10: File Systems, Page Cache, and Durability

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Describe the VFS abstraction and its core objects (superblock,
>   inode, dentry, file) and how Linux layers filesystems beneath
>   them
> - Trace a read and a write through the page cache, block layer,
>   and underlying device
> - Explain ext4 internals: block groups, extents, the journal,
>   and how metadata and data are separated
> - Distinguish `fsync`, `fdatasync`, `sync_file_range`, and
>   `O_DIRECT` and reason about their durability and performance
>   tradeoffs
> - Measure write amplification and use observability tools
>   (`filefrag`, `debugfs`, `/proc/meminfo`, `iostat`)

Call `write(fd, buf, 4096)`. What actually happens? The naive
answer — "the kernel writes 4 KB to the disk" — is wrong in almost
every way that matters for performance and durability. The
syscall writes into a page in kernel memory; the page is marked
dirty; the process returns to user space. The disk does not see a
byte of the write until minutes or `fsync()` later. This chapter
walks the full path from the VFS entry point to the storage
device, and explains the knobs that let databases, consensus
logs, and container runtimes make durability tradeoffs
intentionally.

## 10.1 Why File Systems Matter to Modern Systems

Most of this book has treated storage as somewhere data ends up.
That treatment was fine through Chapter 9; from here on it is
not. Filesystems are the **durability substrate** for every
system that needs its state to survive a power failure:

- A database writes its write-ahead log with `fsync` every commit.
- etcd (Chapter 8) writes its Raft log with `fsync` per entry —
  which is why write latency is 2–8 ms.
- A container runtime copies image layers on first write
  (OverlayFS), which can produce enormous bursts of disk I/O.
- A queue (Kafka, Redis AOF) chooses between synchronous,
  async-batched, and best-effort durability — and the choice
  changes throughput by orders of magnitude.

In each case, filesystem behavior leaks directly into application
latency distributions. Chapter 11 will measure those
distributions end to end; this chapter builds the vocabulary to
explain them.

## 10.2 The VFS Abstraction

Linux supports dozens of filesystems — ext4, xfs, btrfs, tmpfs,
OverlayFS, NFS, FUSE — and every user program talks to them
through the same syscalls: `open`, `read`, `write`, `close`,
`stat`, `mkdir`. The trick is the **Virtual File System (VFS)**,
an indirection layer that dispatches each syscall to the
underlying filesystem's implementation. Same pattern as the
scheduler class chain from Chapter 5: one interface, many
backends.

### Four core objects

| Object | Represents | Lifetime |
|---|---|---|
| `superblock` | A mounted filesystem instance | Mount to unmount |
| `inode` | A file or directory (metadata + data pointers) | As long as referenced |
| `dentry` | A path component, cached name→inode mapping | Cached, evictable |
| `file` | An open file descriptor | `open()` to `close()` |

Each filesystem registers a struct of function pointers:

```c
struct file_operations {
    ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write)(struct file *, const char __user *, size_t, loff_t *);
    int     (*fsync)(struct file *, loff_t, loff_t, int);
    ...
};
```

When the VFS receives a `read()`, it follows the `file`'s `f_op`
pointer to the right filesystem's function and calls in. That is
the entirety of the dispatch mechanism. Overlays, FUSE mounts,
and network filesystems plug in by supplying their own
`file_operations` — the VFS does not care.

### Walking a path

`open("/home/user/notes.txt", O_RDWR)`:

1. Parse into components: `/`, `home`, `user`, `notes.txt`.
2. For each component, look up a **dentry**. The dentry cache
   eliminates disk I/O on hot paths.
3. On the final component, read the inode, allocate a `struct
   file`, set its `f_op` to the filesystem's file operations,
   return the file descriptor.

After this, `read(fd, ...)` dispatches through `f_op->read` —
typically `ext4_file_read_iter` — which handles the page cache
lookup, readahead, and block I/O described in §10.3.

### Inodes, directories, hard links

Crucial detail: **the filename is not in the inode**. The inode
holds metadata (permissions, size, timestamps, extent pointers);
the name lives in a directory entry that maps `(name → inode#)`.
That separation is what makes hard links possible — two
directory entries can point at the same inode, which is why
`ls -l` shows multiple names for one underlying file.

A directory is just a file whose content is a table of `(name,
inode#)` pairs. Early filesystems stored it as a linked list
(O(n) lookup); modern ones use hash trees (ext4 HTree) or B+
trees (XFS) for O(log n) or O(1) lookup. Combined with the
dentry cache, path resolution on a hot directory is effectively
free.

## 10.3 The Page Cache: Read and Write Paths

The **page cache** is the kernel's file cache in RAM. Every read
and write passes through it (unless you explicitly use
`O_DIRECT`). Clean pages match disk; dirty pages are
modifications that have not been written back yet.

### Read path

```c
ssize_t n = read(fd, buf, 4096);
```

1. VFS dispatches to `ext4_file_read_iter`.
2. Look up the page in the page cache.
   - **Hit:** `memcpy` to the user buffer, return (~µs).
   - **Miss:** allocate a page, submit block I/O, wait. When the
     I/O completes, copy to the user buffer, return (~ms).
3. **Readahead.** On a sequential read, the kernel prefetches
   subsequent pages so future reads find them warm in cache.

A sequential read through a large file thus pays the disk cost
only once per readahead window, even though the user issues many
small `read` calls.

### Write path

```c
ssize_t n = write(fd, buf, 4096);
```

1. VFS dispatches to `ext4_file_write_iter`.
2. Find or allocate the page in the cache.
3. `memcpy` the user buffer into the page; mark the page
   **dirty**.
4. Return to user space. `write()` returns *here*, before any
   disk I/O.
5. Later — minutes or hours — a writeback thread picks up the
   dirty page, submits block I/O, and marks it clean on
   completion.

The consequence for correctness is stark: **`write()` does not
durably persist anything by itself.** A crash between steps 4 and
5 loses the write. Applications that care about durability must
call `fsync()` (§10.5).

### Writeback triggers

Linux flushes dirty pages under four conditions:

- `vm.dirty_ratio` exceeded (default 20 % of memory — writing
  processes **block** until writeback catches up).
- `vm.dirty_background_ratio` exceeded (default 10 % — kicks off
  background writeback without blocking writers).
- Age: a dirty page older than `dirty_expire_centisecs` (default
  30 s) is flushed.
- Explicit `sync()`, `fsync(fd)`, or `fdatasync(fd)`.

Tuning these tunables is a tradeoff between throughput (high
ratios keep more data in cache) and data-at-risk window (low
ratios flush sooner). Databases usually set them low to bound
recovery time after a crash.

### Observing the page cache

```bash
$ free -h
              total   used   free   shared   buff/cache   available
Mem:          7.7Gi  1.2Gi  4.1Gi  200Mi     2.4Gi        6.0Gi

$ grep -E "Dirty|Writeback|Cached" /proc/meminfo
Cached:          2380124 kB
Dirty:              1284 kB
Writeback:             0 kB
```

`buff/cache` in `free` includes the page cache; `Dirty` in
`/proc/meminfo` is data written but not yet on stable storage.
The `sync` command forces all dirty pages to disk, and
`echo 3 > /proc/sys/vm/drop_caches` evicts clean pages for
experiments.

### Memory pressure and I/O storms

When RAM gets tight, the kernel must evict pages. Clean pages
are cheap to drop; dirty pages must be written back *first*.
Under sustained memory pressure, the kernel enters a mode where
it is flushing dirty pages as fast as it can *while* the
application keeps demanding reads. The result is an I/O storm: a
burst of device writes that interferes with the application's
own I/O and spikes latency. Chapter 3 saw the application side
of this (major faults); §10.5 will show the device side.

## 10.4 Ext4 Internals

ext4 is the default filesystem on Ubuntu, Debian, and RHEL. It
descends from the FFS lineage (FFS → ext2 → ext3 → ext4) and
incorporates thirty years of filesystem-design lessons.

Every filesystem must answer three questions:

| Decision | ext4's answer |
|---|---|
| Index structure (offset → block) | **Extent tree** (contiguous runs, not per-block pointers) |
| Free-space tracking | **Block-group bitmaps** |
| Locality | **Block groups** + **delayed allocation** |

### Disk layout

```text
┌────────┬──────────────┬──────────────┬───────────┬─────┐
│ Boot   │ Block Group 0│ Block Group 1│ Block Gr 2│ ... │
│ Sector │              │              │           │     │
└────────┴──────────────┴──────────────┴───────────┴─────┘

Block Group:
┌──────┬────────┬──────────┬───────────┬──────────┬────────────┐
│Super │ Group  │ Block    │ Inode     │ Inode    │ Data       │
│block │ Desc.  │ Bitmap   │ Bitmap    │ Table    │ Blocks     │
│(copy)│        │          │           │          │            │
└──────┴────────┴──────────┴───────────┴──────────┴────────────┘
```

A **block group** is a locality unit. The allocator prefers to
place a file's inode and its data blocks in the same group, and
to place files from the same directory in the same group. That
is how ext4 earns sequential-read performance: keeping related
data close minimizes seeks (on spinning media) and keeps reads
within the same SSD erase block (on flash).

### Extents vs block pointers

ext2/ext3 addressed files through per-block pointers — direct,
indirect, double-indirect, triple-indirect — which worked but
produced gigantic metadata for large files. ext4 uses **extents**:

```text
extent = (logical_offset, physical_offset, length)
```

One extent represents a contiguous run of blocks. A 1 GB
sequential file fits in one or two extents instead of thousands
of block pointers. You can see the layout directly:

```bash
$ filefrag -v largefile.dat
Filesystem type is: ef53
File size of largefile.dat is 104857600 (25600 blocks of 4096 bytes)
 ext:   logical: physical:  length:   expected: flags:
   0:     0.. 25599:  34816.. 60415:  25600:             last,eof
```

One extent of length 25 600 = near-perfect allocation. A
fragmented file shows many small extents; the lab has you
produce such a file deliberately.

### Delayed allocation

ext4 does not choose physical blocks at the moment of `write()`.
It marks the pages dirty, tracks how many blocks are needed, and
chooses the physical location at **writeback** time. Two
benefits:

- The allocator sees the full picture — the writer's eventual
  size — and can allocate one big extent instead of many small
  ones.
- Short-lived files (create, write, delete) never hit the disk
  at all.

Delayed allocation is why `dd if=/dev/zero of=x bs=1M count=10`
typically produces exactly one extent, not many.

### Journaling: crash consistency

Without a journal, a crash between writing data and updating
metadata can leave the filesystem inconsistent — e.g., an inode
pointing at a block that was never actually written. ext4 solves
this with a **journal**: a write-ahead log of intended changes,
committed to disk before the actual changes.

Three modes:

| Mode | What is journaled | Safety | Performance |
|---|---|---|---|
| `journal` | Data + metadata | Highest | Slowest |
| `ordered` *(default)* | Metadata only; data is written *before* metadata is committed | Good | Good |
| `writeback` | Metadata only; no ordering | Lowest | Fastest |

`data=ordered` is why `write()` + `fsync()` is a coherent
durability primitive: the data has to hit disk *before* the
metadata that points at it can be committed. A crash during the
window cannot leave you with metadata that points at garbage.

## 10.5 Durability: fsync and Its Friends

### The durability spectrum

| Operation | Guarantee | Typical latency |
|---|---|---|
| `write()` | Data in page cache (volatile) | ~1 µs |
| `fdatasync(fd)` | Data blocks + strictly required metadata on stable storage | 0.5–5 ms |
| `fsync(fd)` | Data + *all* metadata on stable storage | 0.5–10 ms |
| `O_SYNC` | Every write blocks for stable storage | 0.5–10 ms per write |
| `O_DIRECT` | Bypass page cache (**not** durability) | 100 µs–1 ms |

Two common misconceptions:

- **`O_DIRECT` is not a durability primitive.** It bypasses the
  page cache, but the device may still have a write cache. You
  still need `fsync` (or `O_SYNC | O_DIRECT`) for durability.
- **`close(fd)` does not imply fsync.** A file closed without
  fsync can lose recent writes on crash.

### Why fsync is slow

```text
fsync(fd):
  1. Flush the file's dirty pages from the page cache
     (submit block I/O, wait for completion).
  2. Flush the filesystem journal (may include other files' metadata!).
  3. Issue a device cache-flush command (FUA / FLUSH) so the
     device's internal write cache reaches stable media.
  4. Return.
```

Steps 2 and 3 are the surprises. `fsync` pays for the current
journal commit, which may contain metadata from other files
updated by other processes. And most SSDs and disks have an
internal write cache that the kernel must explicitly flush.

### The bimodal latency distribution

Measured fsync latency is almost never a tight distribution. A
typical shape looks like:

```text
│ ████                        p50 ≈ 0.5 ms
│          ██                 p99 ≈ 5 ms
│                 █           max ≈ 50 ms
└───────────────────────────────▶
0.1 ms    1 ms    10 ms    100 ms
```

The tail comes from background writeback contention, other
processes' journal commits, device queue saturation, and SSD
garbage collection. Every one of these is "somebody else is
doing I/O on the same device". The fix, if you have the option,
is a dedicated device for the durability-critical workload
(why etcd in production runs on a dedicated SSD).

### The "fsync lies" problem

Not every storage stack honors fsync. SSDs with broken power-
loss protection, virtual disks on hypervisors with host-side
caching, and some network-attached storage have all been caught
acknowledging fsync without actually persisting the data. In
production, test your stack: a crash consistency test (write,
fsync, kill power, verify) is the only authoritative answer.

PostgreSQL famously had a subtle bug here (2018): it assumed
that a failed `fsync()` meant the dirty pages were still in
cache to retry. On some kernels, a failed `fsync` instead
*discards* the dirty pages, silently losing the write. The
lesson is that the contract between application and kernel
is narrower than it looks.

## 10.6 Write Amplification

Your application writes 4 KB. The device writes more. The ratio
is the **write amplification factor (WAF)**:

```text
Application write:          4 KB
+ Journal entry:            4 KB (write-ahead log)
+ Inode update:             ~256 B (metadata)
+ Block bitmap update:      ~4 B
+ SSD FTL rewrite:          variable (GC, wear-leveling)
──────────────────────────────
Total device writes:        8–16 KB  → WAF = 2–4×
```

Amplification matters for three reasons:

- **SSD endurance.** Flash cells wear out after a finite number
  of writes. Higher WAF shortens drive life.
- **Throughput.** More bytes on the wire per logical write means
  less available bandwidth for useful work.
- **Tail latency.** More I/O means more queue depth and worse
  p99 — the same mechanism Chapter 3 saw in memory pressure.

Overlay filesystems (Chapter 6) add another layer: a write to a
file in the lower layer triggers a **copy-up** of the entire
file into the upper layer. A 1-byte change to a 100 MB file
costs 100 MB of I/O on first write. That is why cold-start
container latency is sometimes dominated by disk, not CPU.

## 10.7 Observability: Peering Into the Stack

Five tools cover almost every investigation:

- **`filefrag -v`.** Shows a file's extent layout. One extent =
  contiguous; many extents = fragmented.
- **`debugfs`.** Read-only inspection of ext4 internals:
  ```bash
  sudo debugfs -R "stat <${inode_number}>" /dev/sdXN
  ```
  Prints the inode's raw fields, including its extent tree.
- **`/proc/meminfo`** (`grep -E "Dirty|Writeback|Cached"`). Shows
  how much data is in the cache and how much is at risk.
- **`iostat -x 1`.** Per-device I/O stats: IOPS, MB/s, average
  wait (`await`), device utilization (`%util`). `await` is your
  latency signal; `%util` is your saturation signal.
- **eBPF tools.** `biolatency` for block-I/O latency
  histograms; `ext4slower` for ext4 operations slower than a
  threshold; `bpftrace` one-liners for fsync latency
  distributions.

A practical investigation recipe:

1. Record application-side latency (the lab's `write_latency.c`).
2. Cross-check with `iostat` — did `await` spike at the same
   time?
3. Cross-check with `/proc/meminfo` — was `Dirty` building up
   during the spike?
4. If needed, drill into `bpftrace` to see fsync-per-thread
   distributions.

The evidence-chain discipline from Chapter 3 applies here
without modification.

## Summary

Key takeaways from this chapter:

- The VFS gives Linux one API for many filesystems by
  dispatching through function-pointer tables on inode, file,
  and directory objects. Overlay filesystems and FUSE slot in at
  this layer.
- The page cache sits on the common path for every I/O. Reads
  hit first, miss second; writes return after a `memcpy` into
  kernel memory, leaving the durability question for later.
- ext4 uses extents (one entry per contiguous run), block groups
  (locality), delayed allocation (better packing), and a journal
  (crash consistency with `data=ordered` by default).
- `fsync` is the primary durability primitive, and it is slow
  for fundamental reasons: flush dirty pages, flush the journal
  (including *other* files' metadata), flush the device's write
  cache. Its latency distribution is bimodal; the tail is
  contention.
- Write amplification makes naive benchmarks misleading; the
  tools in §10.7 are how you see the actual device-side cost.

## Further Reading

- Arpaci-Dusseau & Arpaci-Dusseau (2018). *OSTEP*, Part III
  (Persistence). Free online.
- McKusick, M. et al. (1984). *A fast file system for UNIX.* ACM
  TOCS 2(3). (The FFS paper — still worth reading.)
- Prabhakaran, V. et al. (2005). *IRON file systems.* SOSP.
- Rodeh, O., Bacik, J., Mason, C. (2013). *BTRFS: The Linux
  B-Tree Filesystem.* ACM TOS 9(3).
- Linux kernel: `Documentation/filesystems/ext4.rst`.
- PostgreSQL fsync-bug post-mortem (2018):
  <https://wiki.postgresql.org/wiki/Fsync_Errors>
- Jonas Bonér, *Fsyncgate:* a good non-technical summary.
