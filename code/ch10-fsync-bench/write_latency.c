/*
 * write_latency.c — measure per-write latency under four modes.
 *
 *   Mode 0: buffered write, no fsync.
 *   Mode 1: buffered write + fsync per write.
 *   Mode 2: buffered write + fdatasync per write.
 *   Mode 3: O_DIRECT write (page-aligned buffer).
 *
 * Writes N records of RECORD_SIZE bytes to the file given on the
 * command line and prints per-write latency (ns) to stdout, one
 * per line. Pipe through the Python helper in scripts/ to get
 * p50/p99/p99.9 summaries and CDFs.
 *
 * Build: see Makefile in this directory.
 * See src/part5-storage/ch10-filesystems/lab-fsync-latency.md.
 */

#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#define RECORD_SIZE 4096
#define DEFAULT_N   10000

static long long ns_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static void die(const char *msg) {
    perror(msg);
    exit(1);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr,
                "usage: %s <path> <mode 0..3> [count]\n"
                "  0: buffered, no sync\n"
                "  1: buffered + fsync\n"
                "  2: buffered + fdatasync\n"
                "  3: O_DIRECT\n",
                argv[0]);
        return 1;
    }

    const char *path = argv[1];
    int mode = atoi(argv[2]);
    long n = (argc >= 4) ? atol(argv[3]) : DEFAULT_N;

    int flags = O_WRONLY | O_CREAT | O_TRUNC;
    if (mode == 3) flags |= O_DIRECT;

    int fd = open(path, flags, 0644);
    if (fd < 0) die("open");

    void *buf;
    if (posix_memalign(&buf, RECORD_SIZE, RECORD_SIZE) != 0)
        die("posix_memalign");
    memset(buf, 'x', RECORD_SIZE);

    for (long i = 0; i < n; i++) {
        long long t0 = ns_now();
        if (write(fd, buf, RECORD_SIZE) != RECORD_SIZE) die("write");
        if (mode == 1 && fsync(fd) < 0) die("fsync");
        if (mode == 2 && fdatasync(fd) < 0) die("fdatasync");
        long long t1 = ns_now();
        printf("%lld\n", t1 - t0);
    }

    free(buf);
    close(fd);
    return 0;
}
