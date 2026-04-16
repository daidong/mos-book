# Chapter 10: File Systems, Page Cache, and Durability

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Describe the VFS abstraction and its core objects (superblock,
>   inode, dentry, file) and how Linux layers filesystems beneath them
> - Trace a read and a write through the page cache, block layer,
>   and underlying device
> - Explain ext4 internals: block groups, extents, the journal,
>   and how metadata and data are separated
> - Distinguish `fsync`, `fdatasync`, `sync_file_range`, and `O_DIRECT`
>   and reason about their durability and performance tradeoffs
> - Measure write amplification and use observability tools
>   (`filefrag`, `debugfs`, `/proc/meminfo`, `iostat`, `blktrace`)

## 10.1 Why File Systems Matter to Modern Systems

<!-- Filesystems are the durability substrate for databases, queues,
     and distributed systems. Their design choices (page cache,
     journaling, fsync semantics) leak into application latency
     distributions — the foundation for Chapter 11.
     SOURCE: week9_fs/week9_slides.md intro sections -->

## 10.2 The VFS Abstraction

<!-- The Virtual File System: superblock (mounted FS instance),
     inode (metadata), dentry (name -> inode), file (open handle).
     One interface, many backends (ext4, xfs, tmpfs, fuse).
     SOURCE: week9_fs/week9_slides.md VFS section;
     week9_fs/week9_teaching_notes.md -->

## 10.3 The Page Cache: Read and Write Paths

<!-- Read path: page cache lookup -> miss -> readahead -> block layer.
     Write path: dirty page -> writeback (background or fsync) ->
     journal -> device. `/proc/meminfo` Cached, Dirty, Writeback.
     SOURCE: week9_fs/week9_slides.md page cache sections;
     comm-figs/ page-cache diagrams -->

## 10.4 Ext4 Internals

<!-- Block groups, extents (vs indirect blocks), HTree directories,
     journal modes (data=writeback/ordered/journal).
     Contrast briefly with FFS (cylinder groups) and FAT (linked list).
     SOURCE: week9_fs/week9_slides.md ext4 section;
     week9_fs/figs/ FFS, FAT, COW figures -->

## 10.5 Durability: fsync, fdatasync, O_DIRECT

<!-- fsync forces file data + metadata to stable storage.
     fdatasync skips metadata if unchanged (cheaper).
     O_DIRECT bypasses the page cache entirely.
     The "fsync lies" problem: write caches, power-loss protection.
     SOURCE: week9_fs/week9_slides.md durability section;
     week9_fs/lab9_instructions.md background -->

## 10.6 Write Amplification

<!-- One application write -> multiple physical writes
     (journal + data + metadata + FTL in SSD).
     How amplification shows up in benchmarks and bills.
     SOURCE: week9_fs/week9_slides.md WAF discussion -->

## 10.7 Observability: Peering Into the Stack

<!-- filefrag: physical block layout.
     debugfs: inspect inodes and the journal.
     /proc/meminfo: cache state.
     iostat, blktrace, biosnoop (eBPF): block-level latency.
     SOURCE: week9_fs/lab9_instructions.md tool sections -->

## Summary

Key takeaways from this chapter:

- The page cache is the common path for every I/O; understanding
  when a write leaves it is the key to reasoning about durability.
- `fsync` is the primary durability primitive, and its latency
  dominates any system that commits on every write (databases,
  consensus logs — see Chapter 11).
- Write amplification makes naive benchmarks misleading; the
  observability tools in §10.7 are how you see the real picture.

## Further Reading

- Rodeh, O., Bacik, J., and Mason, C. (2013). BTRFS: The Linux
  B-Tree filesystem. *ACM Transactions on Storage* 9(3).
- McKusick, M. et al. (1984). A fast file system for UNIX.
  *ACM TOCS* 2(3). (The FFS paper — still worth reading.)
- Prabhakaran, V. et al. (2005). IRON file systems. *SOSP '05.*
- Linux kernel documentation: `Documentation/filesystems/ext4.rst`.
