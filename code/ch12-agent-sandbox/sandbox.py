#!/usr/bin/env python3
"""
Minimal Agent Sandbox
Intercepts tool calls, validates against policy, logs all decisions,
and executes approved calls in isolated processes.

Usage:
    python sandbox.py                           # Interactive mode
    python sandbox.py scenario.json             # Run scenario from file
    python sandbox.py scenario.json --direct    # Run without subprocess isolation
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from policy import SandboxPolicy, DEFAULT_POLICY, validate_tool_call
from audit import AuditLogger, print_audit_log
from tools import execute_tool, ToolExecutionError


@dataclass
class ToolCallRequest:
    """A request to execute a tool."""
    tool: str
    arguments: Dict[str, Any]


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    allowed: bool
    reason: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class AgentSandbox:
    """
    Agent sandbox that validates and executes tool calls.
    
    Security features:
    1. Policy-based allowlist validation
    2. Argument pattern matching
    3. Structured audit logging
    4. Process isolation for tool execution
    5. Rate limiting (max calls per session)
    """
    
    def __init__(
        self,
        policy: SandboxPolicy = DEFAULT_POLICY,
        log_path: str = "logs/audit.jsonl",
        use_subprocess: bool = True,
    ):
        self.policy = policy
        self.logger = AuditLogger(log_path)
        self.use_subprocess = use_subprocess
        self.call_count = 0
        self.blocked_count = 0
        self.allowed_count = 0
        self.error_count = 0
    
    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        """
        Execute a tool call request.
        
        Pipeline:
        1. Check rate limit
        2. Validate against policy
        3. Log the decision
        4. If allowed, execute in subprocess
        5. Log the result
        6. Return result
        """
        self.call_count += 1
        
        # Check rate limit
        if self.call_count > self.policy.max_calls_per_session:
            self.blocked_count += 1
            reason = f"Session rate limit exceeded ({self.policy.max_calls_per_session} calls)"
            self.logger.log_decision(request.tool, request.arguments, False, reason)
            return ToolCallResult(allowed=False, reason=reason)
        
        # Validate against policy
        allowed, reason = validate_tool_call(
            self.policy, request.tool, request.arguments
        )
        
        # Log the decision
        request_id = self.logger.log_decision(
            request.tool, request.arguments, allowed, reason
        )
        
        if not allowed:
            self.blocked_count += 1
            return ToolCallResult(allowed=False, reason=reason)
        
        self.allowed_count += 1
        
        # Execute the tool
        try:
            result, duration_ms = execute_tool(
                request.tool,
                request.arguments,
                use_subprocess=self.use_subprocess,
                timeout=self.policy.global_timeout_seconds,
            )
            
            # Log successful execution
            # Truncate result for logging if too large
            log_result = result.copy()
            if "content" in log_result and len(str(log_result["content"])) > 1000:
                log_result["content"] = str(log_result["content"])[:1000] + "...(truncated)"
            
            self.logger.log_execution(
                request_id, request.tool, request.arguments,
                log_result, duration_ms
            )
            
            return ToolCallResult(
                allowed=True,
                reason=reason,
                result=result,
                duration_ms=duration_ms,
            )
            
        except ToolExecutionError as e:
            self.error_count += 1
            
            # Log failed execution
            self.logger.log_execution(
                request_id, request.tool, request.arguments,
                {}, 0.0, error=str(e)
            )
            
            return ToolCallResult(
                allowed=True,
                reason=reason,
                error=str(e),
            )
    
    def close(self):
        """Close the sandbox and finalize logs."""
        self.logger.close()
    
    def get_stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return {
            "total_calls": self.call_count,
            "allowed": self.allowed_count,
            "blocked": self.blocked_count,
            "errors": self.error_count,
        }


def format_result(result: ToolCallResult, verbose: bool = False) -> str:
    """Format a tool call result for display."""
    lines = []
    
    if result.allowed:
        status = "\033[92m✓ ALLOWED\033[0m"  # Green
    else:
        status = "\033[91m✗ BLOCKED\033[0m"  # Red
    
    lines.append(f"{status}: {result.reason}")
    
    if result.result and verbose:
        result_str = json.dumps(result.result, indent=2)
        if len(result_str) > 500:
            result_str = result_str[:500] + "\n  ...(truncated)"
        lines.append(f"  Result: {result_str}")
    elif result.result:
        # Brief summary
        if "count" in result.result:
            lines.append(f"  Result: {result.result.get('count', '?')} items")
        elif "bytes_written" in result.result:
            lines.append(f"  Result: wrote {result.result['bytes_written']} bytes")
        elif "content" in result.result:
            content_len = len(result.result["content"])
            lines.append(f"  Result: read {content_len} characters")
        elif "stdout" in result.result:
            stdout = result.result["stdout"].strip()
            if len(stdout) > 100:
                stdout = stdout[:100] + "..."
            lines.append(f"  Output: {stdout}")
    
    if result.error:
        lines.append(f"  \033[93mError: {result.error}\033[0m")  # Yellow
    
    if result.duration_ms:
        lines.append(f"  Duration: {result.duration_ms:.2f}ms")
    
    return "\n".join(lines)


def run_scenario(sandbox: AgentSandbox, calls: List[Dict], verbose: bool = False) -> List[ToolCallResult]:
    """Run a scenario of tool calls through the sandbox."""
    results = []
    
    for i, call in enumerate(calls, 1):
        tool = call.get("tool", "unknown")
        args = call.get("args", {})
        comment = call.get("_comment", "")
        
        print(f"\n[{i}/{len(calls)}] {tool}({args})")
        if comment:
            print(f"  Comment: {comment}")
        
        request = ToolCallRequest(tool=tool, arguments=args)
        result = sandbox.execute(request)
        results.append(result)
        
        print(format_result(result, verbose=verbose))
    
    return results


def interactive_mode(sandbox: AgentSandbox):
    """Run sandbox in interactive mode."""
    print("Agent Sandbox - Interactive Mode")
    print("=" * 50)
    print("Enter tool calls as JSON:")
    print('  {"tool": "list_dir", "args": {"path": "."}}')
    print("Commands: 'quit', 'stats', 'help'")
    print()
    
    while True:
        try:
            line = input("\033[94m> \033[0m").strip()
            
            if not line:
                continue
            
            if line.lower() == "quit":
                break
            
            if line.lower() == "stats":
                stats = sandbox.get_stats()
                print(f"Total: {stats['total_calls']}, "
                      f"Allowed: {stats['allowed']}, "
                      f"Blocked: {stats['blocked']}, "
                      f"Errors: {stats['errors']}")
                continue
            
            if line.lower() == "help":
                print("Available tools: read_file, write_file, list_dir, shell_command")
                print("Example: {\"tool\": \"list_dir\", \"args\": {\"path\": \".\"}}")
                continue
            
            call = json.loads(line)
            request = ToolCallRequest(
                tool=call.get("tool", "unknown"),
                arguments=call.get("args", {}),
            )
            
            result = sandbox.execute(request)
            print(format_result(result, verbose=True))
            
        except json.JSONDecodeError as e:
            print(f"\033[91mInvalid JSON: {e}\033[0m")
        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except EOFError:
            break


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Minimal Agent Sandbox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sandbox.py                           Interactive mode
  python sandbox.py scenarios/attack.json     Run attack scenario
  python sandbox.py scenario.json --verbose   Show full results
  python sandbox.py scenario.json --direct    Skip subprocess isolation
        """
    )
    parser.add_argument("scenario", nargs="?", help="JSON file with tool calls")
    parser.add_argument("--log", default="logs/audit.jsonl", help="Audit log path")
    parser.add_argument("--direct", action="store_true", 
                        help="Run without subprocess isolation (faster but less safe)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full results")
    parser.add_argument("--show-log", action="store_true",
                        help="Print audit log after execution")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
    
    # Create sandbox
    sandbox = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path=args.log,
        use_subprocess=not args.direct,
    )
    
    print(f"Agent Sandbox initialized")
    print(f"  Subprocess isolation: {'OFF' if args.direct else 'ON'}")
    print(f"  Audit log: {args.log}")
    
    try:
        if args.scenario:
            # Load and run scenario from file
            with open(args.scenario) as f:
                calls = json.load(f)
            
            print(f"\nRunning scenario: {args.scenario}")
            print(f"  {len(calls)} tool calls")
            print("=" * 50)
            
            results = run_scenario(sandbox, calls, verbose=args.verbose)
            
            print("\n" + "=" * 50)
            stats = sandbox.get_stats()
            print(f"Summary: Total={stats['total_calls']}, "
                  f"Allowed={stats['allowed']}, "
                  f"Blocked={stats['blocked']}, "
                  f"Errors={stats['errors']}")
            
        else:
            # Interactive mode
            interactive_mode(sandbox)
    
    finally:
        sandbox.close()
        print(f"\nAudit log written to: {args.log}")
        
        if args.show_log:
            print("\n" + "=" * 50)
            print("AUDIT LOG")
            print("=" * 50)
            print_audit_log(args.log)


if __name__ == "__main__":
    main()
