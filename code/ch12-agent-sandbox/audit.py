"""
Structured audit logging for agent sandbox.
Logs all tool call decisions and results in JSON Lines format.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    session_id: str
    request_id: str
    tool: str
    arguments: Dict[str, Any]
    decision: str  # ALLOWED, BLOCKED, ERROR, EXECUTED, INFO
    policy_rule: Optional[str]
    execution: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: Optional[float]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), default=str)


class AuditLogger:
    """Audit logger that writes to JSON Lines file."""
    
    def __init__(self, log_path: str, session_id: Optional[str] = None):
        self.log_path = Path(log_path)
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self.request_counter = 0
        
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write session start marker
        self._write_entry(AuditEntry(
            timestamp=self._now(),
            session_id=self.session_id,
            request_id="session_start",
            tool="__session__",
            arguments={"action": "start"},
            decision="INFO",
            policy_rule=None,
            execution=None,
            error=None,
            duration_ms=None,
        ))
    
    def _now(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def _next_request_id(self) -> str:
        """Generate next request ID."""
        self.request_counter += 1
        return f"req_{self.request_counter:04d}"
    
    def _write_entry(self, entry: AuditEntry):
        """Write an entry to the log file."""
        with open(self.log_path, "a") as f:
            f.write(entry.to_json() + "\n")
    
    def log_decision(
        self,
        tool: str,
        arguments: Dict[str, Any],
        allowed: bool,
        reason: str,
    ) -> str:
        """Log a policy decision. Returns request_id."""
        request_id = self._next_request_id()
        
        entry = AuditEntry(
            timestamp=self._now(),
            session_id=self.session_id,
            request_id=request_id,
            tool=tool,
            arguments=arguments,
            decision="ALLOWED" if allowed else "BLOCKED",
            policy_rule=reason,
            execution=None,
            error=None,
            duration_ms=None,
        )
        
        self._write_entry(entry)
        return request_id
    
    def log_execution(
        self,
        request_id: str,
        tool: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: float,
        error: Optional[str] = None,
    ):
        """Log tool execution result."""
        entry = AuditEntry(
            timestamp=self._now(),
            session_id=self.session_id,
            request_id=request_id,
            tool=tool,
            arguments=arguments,
            decision="EXECUTED" if error is None else "ERROR",
            policy_rule=None,
            execution=result if error is None else None,
            error=error,
            duration_ms=duration_ms,
        )
        
        self._write_entry(entry)
    
    def close(self):
        """Write session end marker."""
        self._write_entry(AuditEntry(
            timestamp=self._now(),
            session_id=self.session_id,
            request_id="session_end",
            tool="__session__",
            arguments={"action": "end", "total_requests": self.request_counter},
            decision="INFO",
            policy_rule=None,
            execution=None,
            error=None,
            duration_ms=None,
        ))


def print_audit_log(log_path: str, max_entries: int = 100):
    """Pretty print an audit log."""
    with open(log_path, "r") as f:
        for i, line in enumerate(f):
            if i >= max_entries:
                print(f"... (truncated, {max_entries} entries shown)")
                break
            
            entry = json.loads(line)
            decision = entry.get("decision", "?")
            tool = entry.get("tool", "?")
            args = entry.get("arguments", {})
            
            # Color coding (ANSI)
            if decision == "BLOCKED":
                color = "\033[91m"  # Red
            elif decision == "ALLOWED":
                color = "\033[92m"  # Green
            elif decision == "ERROR":
                color = "\033[93m"  # Yellow
            else:
                color = "\033[94m"  # Blue
            reset = "\033[0m"
            
            if tool == "__session__":
                print(f"{color}[{decision}]{reset} SESSION {args.get('action', '?').upper()}")
            else:
                # Truncate long args for display
                args_str = str(args)
                if len(args_str) > 60:
                    args_str = args_str[:60] + "..."
                
                print(f"{color}[{decision}]{reset} {tool}({args_str})")
                
                if entry.get("policy_rule"):
                    print(f"  Rule: {entry['policy_rule']}")
                
                if entry.get("execution"):
                    exec_str = str(entry['execution'])
                    if len(exec_str) > 80:
                        exec_str = exec_str[:80] + "..."
                    print(f"  Result: {exec_str}")
                
                if entry.get("error"):
                    print(f"  Error: {entry['error']}")
                
                if entry.get("duration_ms"):
                    print(f"  Duration: {entry['duration_ms']:.2f}ms")
            
            print()


def analyze_audit_log(log_path: str) -> Dict[str, Any]:
    """Analyze an audit log and return statistics."""
    stats = {
        "total_entries": 0,
        "by_decision": {},
        "by_tool": {},
        "blocked_reasons": {},
        "total_duration_ms": 0,
        "avg_duration_ms": 0,
    }
    
    execution_count = 0
    
    with open(log_path, "r") as f:
        for line in f:
            entry = json.loads(line)
            stats["total_entries"] += 1
            
            decision = entry.get("decision", "UNKNOWN")
            stats["by_decision"][decision] = stats["by_decision"].get(decision, 0) + 1
            
            tool = entry.get("tool", "UNKNOWN")
            if tool != "__session__":
                stats["by_tool"][tool] = stats["by_tool"].get(tool, 0) + 1
            
            if decision == "BLOCKED":
                reason = entry.get("policy_rule", "unknown")
                stats["blocked_reasons"][reason] = stats["blocked_reasons"].get(reason, 0) + 1
            
            duration = entry.get("duration_ms")
            if duration:
                stats["total_duration_ms"] += duration
                execution_count += 1
    
    if execution_count > 0:
        stats["avg_duration_ms"] = stats["total_duration_ms"] / execution_count
    
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
        print(f"=== Audit Log: {log_path} ===\n")
        print_audit_log(log_path)
        
        print("\n=== Statistics ===\n")
        stats = analyze_audit_log(log_path)
        print(f"Total entries: {stats['total_entries']}")
        print(f"By decision: {stats['by_decision']}")
        print(f"By tool: {stats['by_tool']}")
        if stats['blocked_reasons']:
            print(f"Blocked reasons: {stats['blocked_reasons']}")
        if stats['avg_duration_ms'] > 0:
            print(f"Avg duration: {stats['avg_duration_ms']:.2f}ms")
    else:
        print("Usage: python audit.py <log_path>")
