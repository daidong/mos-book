# Lab: Environment Setup

> **Estimated time:** 2-3 hours
>
> **Prerequisites:** VirtualBox installed, Ubuntu 22.04 or 24.04 ISO
>
> **Tools used:** VirtualBox, apt, perf, strace, gcc

## Objectives

- Set up an Ubuntu VM suitable for all labs in this book
- Install and verify core observability tools (perf, strace, bpftrace)
- Run a first `perf stat` measurement and interpret the output
- Establish habits for reproducible experiments

## Background

All labs in this book run inside an Ubuntu VM on VirtualBox. This
ensures a consistent, reproducible environment regardless of your host
OS. We avoid WSL and Docker because they restrict access to kernel
tracing interfaces that later labs require.

The policy is deliberately strict. Concretely:

| Environment | Problem | Result |
|---|---|---|
| WSL2 | Limited kernel feature surface | eBPF and perf may fail silently |
| Docker (as your OS) | BPF capabilities are restricted | No PMU, limited `/proc` |
| macOS / Windows | Different kernel | No `/proc`, no perf, no cgroups |

The only supported environment is an **Ubuntu VM (VirtualBox or
equivalent)**, or native Ubuntu. Later labs (Kubernetes, eBPF,
cgroup experiments) will not work reliably anywhere else.

> **Warning:** Kernel 5.10 is the minimum this book assumes; 5.15+
> is strongly recommended (this is the Ubuntu 22.04 LTS default).
> Ubuntu 20.04 often runs 5.4 and will miss features used in later
> labs. Verify with `uname -r` before starting.

## Part A: VM Installation and Tool Setup (Required)

### A.1 Create the VM

1. Install VirtualBox from <https://www.virtualbox.org/>.
   On Apple Silicon hosts where VirtualBox is unstable, UTM is an
   acceptable substitute.
2. Download Ubuntu 22.04 LTS or 24.04 LTS. Use the desktop ISO for
   x86_64 hosts; use the ARM server ISO on Apple Silicon.
3. In VirtualBox, create a new VM:

   | Setting | Recommended value |
   |---|---|
   | Name | `mos-book-vm` |
   | Type | Linux |
   | Version | Ubuntu (64-bit) |
   | RAM | 4 GB minimum (8 GB if your host allows) |
   | CPU | 2 cores |
   | Disk | 25 GB or more |

4. Attach the Ubuntu ISO and install with the default options.
   Remember the username and password you set.
5. After install, remove the ISO and reboot into the installed system.

### A.2 Install the Week-1 Toolchain

Open a terminal inside the VM and run:

```bash
sudo apt update
sudo apt install -y build-essential git curl wget
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
sudo apt install -y strace
```

Install the "Stage 2" tools that Chapter 2 will need, so that you do
not hit surprises next week:

```bash
sudo apt install -y python3 python3-pip valgrind
```

### A.3 Verify Everything Works

Run each of these and confirm you get version output or a clean exit:

```bash
gcc --version
make --version
git --version
sudo perf stat ls
strace --version
```

Then run the course environment check script. A copy lives in the
course source tree (`week1/env_check.sh`); a mirror suitable for this
book is in `code/ch01-envcheck/env_check.sh` once you clone this
book's companion repo. Save its output:

```bash
bash env_check.sh | tee lab0_env_check.txt
```

Read the output carefully:

- `[OK]` for gcc, make, and perf means you are ready for Chapter 2.
- `[WARN]` for eBPF, Kubernetes, or security tooling is fine — those
  tools are installed in later stages (see the course source's
  `lab0_instructions.md` for the full staged-install list).
- `[ERROR]` must be fixed before you continue. The most common cause
  is a kernel older than 5.10; upgrade Ubuntu, or create a fresh VM
  on a newer LTS.

### A.4 Part A Checklist

- [ ] Ubuntu VM boots and you can log in
- [ ] `gcc --version` prints a version
- [ ] `sudo perf stat ls` runs without "command not found"
- [ ] `strace --version` prints a version
- [ ] `env_check.sh` produces `lab0_env_check.txt` with no critical
      errors

## Part B: First Measurement with perf stat (Required)

### B.1 Write the Program

Create `hello.c`:

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("Hello from process %d\n", getpid());
    return 0;
}
```

Compile and run it:

```bash
gcc -o hello hello.c
./hello
```

### B.2 Trace the System Calls

```bash
strace ./hello 2>&1 | tee strace_hello.txt
```

Skim the output. You should see `execve` at the top, a handful of
`openat`/`read`/`mmap` calls as the dynamic linker loads libc, a
single `write(1, ...)` for the output line, and `exit_group` at the
end.

**Question:** What syscall does `printf` ultimately invoke to deliver
bytes to the terminal?

### B.3 Measure with perf stat (Three Runs)

Run `perf stat` three times in a row and record the numbers. Three
runs are the minimum needed to notice whether values are stable or
noisy.

```bash
sudo perf stat ./hello 2>&1 | tee -a perf_stat_hello.txt
sudo perf stat ./hello 2>&1 | tee -a perf_stat_hello.txt
sudo perf stat ./hello 2>&1 | tee -a perf_stat_hello.txt
```

Fill in a table like this:

| Run | task-clock (ms) | page-faults | cycles | instructions | IPC |
|---|---|---|---|---|---|
| 1 |   |   |   |   |   |
| 2 |   |   |   |   |   |
| 3 |   |   |   |   |   |

IPC is simply `instructions / cycles`.

### B.4 Explanation Questions

Write answers to these in your report. Two or three sentences each is
enough; the point is that the answer names a mechanism.

1. Are the numbers consistent across runs? If not, which counters
   varied most, and why might that be?
2. What is your IPC? Is it closer to 1.0 (memory-bound) or closer to
   2.0+ (compute-bound)? Is that what you would expect for a program
   that mostly calls `printf`?
3. A program this small still produces dozens of page faults on the
   first run. What are those faults for? (Hint: what does `mmap`
   actually give you, and when does the kernel allocate real
   physical pages?)

### B.5 Part B Checklist

- [ ] `hello.c` compiled and ran
- [ ] `strace ./hello` output captured
- [ ] `perf stat ./hello` run three times, numbers recorded
- [ ] Explanation questions answered in complete sentences

## Part C: Context Switch Observation (Optional)

### C.1 The Program

Create `ctx_switch_test.c`:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    int n = (argc > 1) ? atoi(argv[1]) : 1000;

    int pipefd[2];
    if (pipe(pipefd) < 0) { perror("pipe"); return 1; }

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }

    if (pid == 0) {
        close(pipefd[1]);
        char buf;
        for (int i = 0; i < n; i++) {
            if (read(pipefd[0], &buf, 1) < 0) { perror("read"); _exit(1); }
        }
        _exit(0);
    } else {
        close(pipefd[0]);
        char buf = 'x';
        for (int i = 0; i < n; i++) {
            if (write(pipefd[1], &buf, 1) < 0) { perror("write"); return 1; }
        }
        close(pipefd[1]);
        wait(NULL);
    }
    return 0;
}
```

Compile:

```bash
gcc -O2 -o ctx_switch_test ctx_switch_test.c
```

### C.2 Measure at Three Problem Sizes

```bash
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 100
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 1000
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 10000
```

Record:

| n | context-switches | cpu-migrations | wall time (s) |
|---|---|---|---|
| 100 |   |   |   |
| 1,000 |   |   |   |
| 10,000 |   |   |   |

### C.3 Explain

1. **Scaling:** How does context-switch count grow with `n`? Is it
   linear, sub-linear, or super-linear? Why?
2. **Mechanism:** Why does this program force context switches at all?
   Think about what the child does when the pipe buffer is empty, and
   what the parent does when it is full.
3. **Prediction:** If the parent wrote 1,024 bytes per `write()`
   instead of 1 byte, what would happen to the context-switch count,
   and why?

### C.4 Part C Checklist

- [ ] Program compiled and ran for three values of `n`
- [ ] Results tabulated
- [ ] Scaling and mechanism explained in the report

## Deliverables

Submit a ZIP archive containing:

| File | Required? | Purpose |
|---|---|---|
| `lab0_report.md` | Yes | Your written report with results and answers |
| `lab0_env_check.txt` | Recommended | Raw `env_check.sh` output |
| `hello.c` | Recommended | The program you measured |
| `strace_hello.txt` | Optional | Raw strace output |
| `perf_stat_hello.txt` | Optional | Raw perf stat output (three runs) |
| `ctx_switch_test.c` | Optional | Source, if you did Part C |

Your `lab0_report.md` should include:

- A short paragraph on environment setup, noting any issues you hit
  and how you resolved them
- The strace answer for Part B
- Your three-run `perf stat` table, with IPC computed
- Your written answers to the three Part B questions (mechanism-level,
  not just restating the numbers)
- If you did Part C, your scaling table and explanation

Grading follows the course rubric: 30 points for Part A (environment),
60 points for Part B (measurement + explanation), 10 bonus points for
Part C.
