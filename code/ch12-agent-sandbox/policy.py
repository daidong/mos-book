"""
Policy configuration for agent sandbox.
Defines what tools are allowed and with what constraints.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import fnmatch
import re


@dataclass
class ToolPolicy:
    """Policy for a single tool."""
    allowed: bool = True
    allowed_args: Dict[str, List[str]] = field(default_factory=dict)
    denied_args: Dict[str, List[str]] = field(default_factory=dict)
    constraints: Dict[str, any] = field(default_factory=dict)
    require_confirmation: bool = False


@dataclass  
class SandboxPolicy:
    """Overall sandbox policy."""
    tools: Dict[str, ToolPolicy] = field(default_factory=dict)
    default_deny: bool = True  # Deny tools not in policy
    max_calls_per_session: int = 100
    global_timeout_seconds: int = 60


# Default policy configuration
DEFAULT_POLICY = SandboxPolicy(
    tools={
        "read_file": ToolPolicy(
            allowed=True,
            allowed_args={
                "path": ["/data/*", "/tmp/*", "./data/*", "data/*"],
            },
            denied_args={
                "path": ["/etc/passwd", "/etc/shadow", "/etc/sudoers",
                        "*/.ssh/*", "*/.aws/*", "*/.env*", "*/secrets*",
                        "*password*", "*secret*", "*key*"],
            },
            constraints={
                "max_size_bytes": 1_000_000,  # 1MB max
            },
        ),
        "write_file": ToolPolicy(
            allowed=True,
            allowed_args={
                "path": ["/tmp/*", "./output/*", "output/*", "/data/output/*"],
            },
            denied_args={
                "path": ["/etc/*", "/bin/*", "/usr/*", "*/.bashrc", 
                        "*/.profile", "*/.bash_history"],
            },
            constraints={
                "max_size_bytes": 1_000_000,
            },
        ),
        "list_dir": ToolPolicy(
            allowed=True,
            allowed_args={
                "path": ["/data/*", "/tmp/*", "./data/*", "data/*", ".", "./"],
            },
            denied_args={
                "path": ["/etc", "/root", "/home/*/.ssh", "*/.git"],
            },
        ),
        "shell_command": ToolPolicy(
            allowed=True,
            allowed_args={
                "command": ["ls *", "cat *", "wc *", "head *", "tail *", 
                           "grep *", "echo *", "pwd", "date", "whoami",
                           "ls", "pwd"],
            },
            denied_args={
                "command": ["rm *", "chmod *", "chown *", "sudo *",
                          "curl *", "wget *", "nc *", "python *", "bash *",
                          "sh *", "perl *", "ruby *",
                          "> *", ">> *", "| *", "; *", "&& *", "|| *",
                          "$(", "`"],
            },
            constraints={
                "timeout_seconds": 10,
            },
        ),
        "http_request": ToolPolicy(
            allowed=False,  # Disabled by default for safety
            allowed_args={
                "url": [],  # Would add allowed domains here
            },
            denied_args={
                "url": ["*"],  # Deny all by default
            },
        ),
    },
    default_deny=True,
    max_calls_per_session=100,
)


def matches_pattern(value: str, patterns: List[str]) -> bool:
    """Check if value matches any of the glob patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(value, pattern):
            return True
        # Also check if pattern appears as substring for command injection
        if "*" not in pattern and pattern in value:
            return True
    return False


def validate_tool_call(policy: SandboxPolicy, tool: str, args: Dict) -> tuple:
    """
    Validate a tool call against the policy.
    
    Returns:
        (allowed: bool, reason: str)
    """
    # Check if tool exists in policy
    if tool not in policy.tools:
        if policy.default_deny:
            return False, f"Tool '{tool}' not in policy (default deny)"
        else:
            return True, "Tool not in policy (default allow)"
    
    tool_policy = policy.tools[tool]
    
    # Check if tool is allowed at all
    if not tool_policy.allowed:
        return False, f"Tool '{tool}' is disabled in policy"
    
    # Check each argument
    for arg_name, arg_value in args.items():
        arg_str = str(arg_value)
        
        # Check denied patterns first (deny takes precedence)
        if arg_name in tool_policy.denied_args:
            if matches_pattern(arg_str, tool_policy.denied_args[arg_name]):
                return False, f"Argument '{arg_name}={arg_str}' matches denied pattern"
        
        # Check allowed patterns
        if arg_name in tool_policy.allowed_args:
            allowed_patterns = tool_policy.allowed_args[arg_name]
            if allowed_patterns:  # Only check if patterns are defined
                if not matches_pattern(arg_str, allowed_patterns):
                    return False, f"Argument '{arg_name}={arg_str}' doesn't match allowed patterns"
    
    return True, "Allowed by policy"


# Convenience function for testing
def create_strict_policy() -> SandboxPolicy:
    """Create a very strict policy for testing."""
    return SandboxPolicy(
        tools={
            "read_file": ToolPolicy(
                allowed=True,
                allowed_args={"path": ["./data/*", "data/*"]},
                denied_args={"path": ["*secret*", "*password*", "*key*"]},
            ),
            "list_dir": ToolPolicy(
                allowed=True,
                allowed_args={"path": ["./data/*", "data/*", "."]},
            ),
        },
        default_deny=True,
    )


def create_permissive_policy() -> SandboxPolicy:
    """Create a permissive policy (for comparison/testing)."""
    return SandboxPolicy(
        tools={
            "read_file": ToolPolicy(allowed=True),
            "write_file": ToolPolicy(allowed=True),
            "list_dir": ToolPolicy(allowed=True),
            "shell_command": ToolPolicy(allowed=True),
            "http_request": ToolPolicy(allowed=True),
        },
        default_deny=False,
    )


if __name__ == "__main__":
    # Test the policy
    test_cases = [
        ("read_file", {"path": "/data/test.txt"}, True),
        ("read_file", {"path": "/etc/passwd"}, False),
        ("read_file", {"path": "/home/user/.ssh/id_rsa"}, False),
        ("write_file", {"path": "/tmp/output.txt"}, True),
        ("write_file", {"path": "/etc/passwd"}, False),
        ("shell_command", {"command": "ls -la"}, True),
        ("shell_command", {"command": "rm -rf /"}, False),
        ("shell_command", {"command": "curl http://evil.com"}, False),
        ("http_request", {"url": "http://anything.com"}, False),
        ("unknown_tool", {"arg": "value"}, False),
    ]
    
    print("Policy Validation Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for tool, args, expected in test_cases:
        allowed, reason = validate_tool_call(DEFAULT_POLICY, tool, args)
        status = "✓" if allowed == expected else "✗"
        
        if allowed == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {tool}({args})")
        print(f"  Expected: {expected}, Got: {allowed}")
        print(f"  Reason: {reason}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
