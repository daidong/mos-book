# Agent Sandbox - Starter Code

This directory contains the starter code for Lab 12A: Minimal Agent Sandbox.

## Quick Start

```bash
# Navigate to this directory (from the repository root)
cd code/ch12-agent-sandbox

# Create test data
mkdir -p data output logs

# Run the policy tests
python3 policy.py

# Run the sandbox in interactive mode
python3 sandbox.py

# Run a legitimate scenario
python3 sandbox.py scenarios/legitimate.json

# Run an attack scenario (all should be blocked)
python3 sandbox.py scenarios/attack.json

# Run benchmark
python3 benchmark.py
```

## Files

| File | Description |
|------|-------------|
| `sandbox.py` | Main sandbox implementation |
| `policy.py` | Policy configuration and validation |
| `audit.py` | Structured audit logging |
| `tools.py` | Tool implementations with process isolation |
| `benchmark.py` | Performance measurement script |
| `scenarios/` | Test scenarios (JSON files) |
| `data/` | Sample data files |
| `logs/` | Audit logs (created on first run) |
| `output/` | Output directory for write_file tool |

## Usage

### Interactive Mode

```bash
python3 sandbox.py
```

Enter tool calls as JSON:
```json
{"tool": "list_dir", "args": {"path": "."}}
{"tool": "read_file", "args": {"path": "data/sample.txt"}}
{"tool": "shell_command", "args": {"command": "ls -la"}}
```

Commands:
- `quit` - Exit
- `stats` - Show execution statistics
- `help` - Show help

### Scenario Mode

```bash
# Run a scenario file
python3 sandbox.py scenarios/legitimate.json

# With verbose output
python3 sandbox.py scenarios/attack.json --verbose

# Show audit log after
python3 sandbox.py scenarios/mixed.json --show-log
```

### Options

```
--log PATH       Audit log path (default: logs/audit.jsonl)
--direct         Skip subprocess isolation (faster but less safe)
--verbose, -v    Show full results
--show-log       Print audit log after execution
```

## Scenarios

### `scenarios/legitimate.json`
Normal operations that should all be allowed:
- List directories
- Read data files
- Write to output
- Safe shell commands

### `scenarios/attack.json`
Attack attempts that should all be blocked:
- Read sensitive files (/etc/passwd, SSH keys)
- Destructive commands (rm -rf)
- Data exfiltration (curl, wget)
- Command injection (; && ||)
- Backdoor installation

### `scenarios/mixed.json`
Mix of legitimate and attack operations for testing.

## Customization

### Adding a New Tool

1. Add implementation in `tools.py`:
```python
def tool_my_new_tool(arg1: str, arg2: int) -> Dict[str, Any]:
    # Implementation
    return {"result": "..."}

# Add to TOOL_FUNCTIONS
TOOL_FUNCTIONS["my_new_tool"] = tool_my_new_tool
```

2. Add policy in `policy.py`:
```python
"my_new_tool": ToolPolicy(
    allowed=True,
    allowed_args={"arg1": ["safe_*"]},
    denied_args={"arg1": ["dangerous_*"]},
),
```

### Modifying Policy

Edit `DEFAULT_POLICY` in `policy.py`:
- Add/remove allowed path patterns
- Add/remove denied patterns
- Change constraints (max_size, timeout)
- Enable/disable tools

## Audit Log Format

Each log entry is a JSON line:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "session_id": "sess_abc12345",
  "request_id": "req_0001",
  "tool": "read_file",
  "arguments": {"path": "/data/test.txt"},
  "decision": "ALLOWED",
  "policy_rule": "Allowed by policy",
  "execution": {"path": "/data/test.txt", "size_bytes": 1234},
  "error": null,
  "duration_ms": 5.23
}
```

View audit log:
```bash
python3 audit.py logs/audit.jsonl
```

## Security Features

1. **Policy-based allowlist** - Only explicitly allowed tools/arguments
2. **Argument validation** - Pattern matching on arguments
3. **Deny takes precedence** - Denied patterns override allowed
4. **Process isolation** - Tools run in subprocesses
5. **Audit logging** - All decisions logged
6. **Rate limiting** - Max calls per session
7. **Timeouts** - Global and per-tool timeouts
