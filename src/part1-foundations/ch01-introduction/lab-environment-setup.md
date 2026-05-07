# Lab: Environment Setup

> **Estimated time:** 2–3 hours
>
> **Prerequisites:** VirtualBox, UTM, or another VM platform; Ubuntu
> 22.04 or 24.04 image
>
> **Tools used:** `apt`, `gcc`, `make`, `strace`, `perf`,
> `/usr/bin/time`, Valgrind

## Objectives

- Build a reproducible Ubuntu environment for Part I of the book
- Verify the core measurement tools used in Chapters 1–3
- Produce your first syscall trace and your first counter-based
  measurement
- Establish the evidence habits this book expects: machine
  fingerprint, prediction, raw artifacts, and explanation

## Background

All required labs in Part I assume either native Ubuntu or an Ubuntu VM.
That is a deliberate constraint. Later chapters depend on Linux-specific
interfaces such as `/proc`, cgroup files, `perf`, and kernel tracing. WSL,
Docker-on-a-laptop, and non-Linux hosts are useful engineering tools, but
they are poor foundations for an OS measurement course because they hide or
restrict exactly the interfaces we want to inspect.

| Environment | Typical problem | Consequence |
|---|---|---|
| WSL2 | incomplete kernel feature surface | tracing results may be missing or misleading |
| Docker as the main lab environment | containerized view of `/proc` and PMU restrictions | later labs become brittle |
| macOS / Windows host without Linux VM | different kernel | no direct access to Linux counters and cgroups |

> **Warning:** Kernel 5.10 is the minimum supported baseline for this
> book. Ubuntu 22.04 or 24.04 is the safest choice.

## Part A: Build and Verify the Environment (Required)

### A.1 Create the VM

Create a VM with these minimum settings:

| Setting | Recommendation |
|---|---|
| Name | `mos-book-vm` |
| RAM | 4 GiB minimum; 8 GiB preferred |
| vCPUs | 2 minimum |
| Disk | 25 GiB minimum |
| Guest OS | Ubuntu 22.04 LTS or 24.04 LTS |

Install Ubuntu with the default options. Record the username, kernel
version, VM memory, and vCPU count in your report.

### A.2 Install the Part I Toolchain

Inside the VM, run:

```bash
sudo apt update
sudo apt install -y build-essential git curl wget time strace valgrind
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
```

For Chapter 3, also install Node.js and npm now so that you do not hit a
separate setup failure later in Part I:

```bash
sudo apt install -y nodejs npm
```

### A.3 Run the Environment Check

This repository includes a local check script at
`code/ch01-envcheck/env_check.sh`.

```bash
bash code/ch01-envcheck/env_check.sh | tee lab0_env_check.txt
```

The script prints `[OK]`, `[WARN]`, or `[ERROR]` lines. Fix every
`[ERROR]` before continuing. A `[WARN]` is acceptable only if you explain it
briefly in your report.

Then verify the core tools manually:

```bash
gcc --version
make --version
git --version
strace --version
valgrind --version
node --version
sudo perf stat true
```

### A.4 Machine Fingerprint

Before doing any measurements, create a short reproducibility record.
Paste the commands and keep the output in your report.

```bash
uname -a
lsb_release -a
lscpu | egrep 'Model name|CPU\(s\)|Thread|Core|Socket'
free -h
lsblk -d
```

### A.5 Part A Checklist

- [ ] Ubuntu boots reliably
- [ ] `code/ch01-envcheck/env_check.sh` runs and produces
      `lab0_env_check.txt`
- [ ] `sudo perf stat true` works
- [ ] `strace`, `valgrind`, and `node` are available
- [ ] Machine fingerprint captured in the report

## Part B: First Trace and First Measurement (Required)

### B.1 Write a Prediction Before You Run Anything

Create a short section in `lab0_report.md` titled **Prediction** and answer:

1. Which system call do you expect will actually send bytes to the terminal?
2. Do you expect the program below to show many context switches? Why or why
   not?
3. Do you expect zero page faults, a few page faults, or dozens? Give a
   mechanism-level reason.
4. Name one alternative explanation you might have to rule out if the first
   run looks noisy.

This section is graded. Write it before collecting data.

### B.2 Write and Run the Program

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
gcc -O2 -o hello hello.c
./hello
```

### B.3 Capture a System Call Trace

```bash
strace ./hello 2>&1 | tee strace_hello.txt
```

In your report, answer this question in one or two precise sentences:

> What syscall ultimately carries the output of `printf()` to the terminal,
> and why is that a user-space → kernel boundary crossing?

### B.4 Measure Three Runs with `perf stat`

```bash
sudo perf stat ./hello 2>&1 | tee perf_run1.txt
sudo perf stat ./hello 2>&1 | tee perf_run2.txt
sudo perf stat ./hello 2>&1 | tee perf_run3.txt
```

Fill in this table:

| Run | task-clock (ms) | context-switches | page-faults | cycles | instructions | IPC |
|---|---:|---:|---:|---:|---:|---:|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

Compute `IPC = instructions / cycles`.

### B.5 Interpret the Result

Answer all four prompts in complete sentences.

1. Which counters were stable across the three runs, and which were noisy?
2. Did the evidence match your prediction about context switches? Why?
3. Why can such a tiny program still incur page faults on its first run?
4. Which alternative explanation did you consider, and what observation lets
   you rule it out?

A good answer names a mechanism. "The number changed a little" is not a
mechanism. "The first touch of pages for the program image and shared
libraries produced the faults" is a mechanism.

### B.6 Evidence Table

Add this table to your report.

| Claim | Signal 1 | Signal 2 | Alternative ruled out |
|---|---|---|---|
| `printf()` crosses into the kernel through `write()` | `strace` line | program output behavior | direct user-space device access |
| first-run cost includes page setup | `page-faults` counter | trace shows mapping activity | "the program allocates a large heap" |

You may revise the wording, but keep the structure.

### B.7 Part B Checklist

- [ ] Prediction written before measurement
- [ ] `hello.c` compiled and ran
- [ ] `strace_hello.txt` captured
- [ ] Three `perf stat` runs saved as raw artifacts
- [ ] Interpretation connects counters to mechanisms
- [ ] At least one alternative explanation ruled out

## Part C: Observe Context Switches Deliberately (Optional)

### C.1 Build a Small Ping-Pong Program

Create `ctx_switch_test.c`:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    int n = (argc > 1) ? atoi(argv[1]) : 1000;
    int pipefd[2];
    if (pipe(pipefd) < 0) return 1;

    pid_t pid = fork();
    if (pid < 0) return 1;

    if (pid == 0) {
        close(pipefd[1]);
        char buf;
        for (int i = 0; i < n; i++) read(pipefd[0], &buf, 1);
        _exit(0);
    }

    close(pipefd[0]);
    char buf = 'x';
    for (int i = 0; i < n; i++) write(pipefd[1], &buf, 1);
    close(pipefd[1]);
    wait(NULL);
    return 0;
}
```

Compile and measure:

```bash
gcc -O2 -o ctx_switch_test ctx_switch_test.c
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 100
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 1000
sudo perf stat -e context-switches,cpu-migrations ./ctx_switch_test 10000
```

Record the scaling and explain why pipe-based handoff produces scheduler
activity that the `hello` program did not.

### C.2 Part C Checklist

- [ ] Results recorded for three values of `n`
- [ ] Scaling explained in terms of blocking and wakeup behavior

## Deliverables

Submit a ZIP archive containing:

| File | Required? | Purpose |
|---|---|---|
| `lab0_report.md` | Yes | prediction, environment record, results, interpretation |
| `lab0_env_check.txt` | Yes | raw environment-check output |
| `strace_hello.txt` | Yes | raw syscall trace |
| `perf_run1.txt`, `perf_run2.txt`, `perf_run3.txt` | Yes | raw counter output |
| `hello.c` | Yes | measured program |
| `ctx_switch_test.c` | Optional | Part C source |

Your report must contain:

1. machine fingerprint;
2. the pre-run prediction;
3. the three-run table with IPC;
4. a mechanism-level explanation of the trace and counters;
5. one alternative explanation explicitly ruled out.

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

## Grading Rubric (100 pts)

| Area | Points | Criterion |
|---|---:|---|
| Environment integrity | 25 | VM works; toolchain verified; raw check output included |
| Prediction quality | 15 | prediction is specific and mechanism-based |
| Evidence quality | 25 | raw trace and raw counter output are present and used correctly |
| Explanation quality | 25 | answers connect observations to process creation, faults, and syscall boundaries |
| Alternative ruled out | 10 | a plausible wrong explanation is named and excluded |
