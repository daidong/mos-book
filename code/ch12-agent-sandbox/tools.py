"""
Tool implementations with process isolation.
Each tool runs in a subprocess for isolation.
"""

import os
import subprocess
import json
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


def execute_in_subprocess(
    func_name: str,
    args: Dict[str, Any],
    timeout: float = 30.0,
) -> Tuple[Dict[str, Any], float]:
    """
    Execute a tool function in a subprocess.
    
    Returns:
        (result_dict, duration_ms)
    """
    # Get the directory containing this module
    module_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a small Python script to run the tool
    script = f'''
import json
import sys
import os
sys.path.insert(0, '{module_dir}')
from tools import {func_name}
args = json.loads(sys.argv[1])
try:
    result = {func_name}(**args)
    print(json.dumps({{"status": "success", "result": result}}))
except Exception as e:
    print(json.dumps({{"status": "error", "error": str(e)}}))
'''
    
    start_time = time.perf_counter()
    
    try:
        result = subprocess.run(
            ["python3", "-c", script, json.dumps(args)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),  # Run in current directory
        )
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                raise ToolExecutionError(f"Subprocess failed: {stderr}")
            raise ToolExecutionError(f"Subprocess exited with code {result.returncode}")
        
        stdout = result.stdout.strip()
        if not stdout:
            raise ToolExecutionError("Tool returned no output")
        
        try:
            output = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"Invalid tool output: {e}\nOutput was: {stdout[:200]}")
        
        if output["status"] == "error":
            raise ToolExecutionError(output["error"])
        
        return output["result"], duration_ms
        
    except subprocess.TimeoutExpired:
        duration_ms = (time.perf_counter() - start_time) * 1000
        raise ToolExecutionError(f"Tool execution timed out after {timeout}s")


# ============ Tool Implementations ============

def tool_read_file(path: str, max_size: int = 1_000_000) -> Dict[str, Any]:
    """Read a file and return its contents."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    
    size = path.stat().st_size
    if size > max_size:
        raise ValueError(f"File too large: {size} bytes > {max_size} bytes limit")
    
    content = path.read_text()
    
    return {
        "path": str(path.absolute()),
        "size_bytes": size,
        "lines": content.count('\n') + 1,
        "content": content,
    }


def tool_write_file(path: str, content: str, max_size: int = 1_000_000) -> Dict[str, Any]:
    """Write content to a file."""
    if len(content) > max_size:
        raise ValueError(f"Content too large: {len(content)} bytes > {max_size} bytes limit")
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    
    return {
        "path": str(path.absolute()),
        "bytes_written": len(content),
    }


def tool_list_dir(path: str) -> Dict[str, Any]:
    """List contents of a directory."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")
    
    entries = []
    for entry in sorted(path.iterdir()):
        try:
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": stat.st_size if entry.is_file() else None,
            })
        except PermissionError:
            entries.append({
                "name": entry.name,
                "type": "unknown",
                "size": None,
                "error": "permission denied",
            })
    
    return {
        "path": str(path.absolute()),
        "count": len(entries),
        "entries": entries,
    }


def tool_shell_command(command: str, timeout: int = 10) -> Dict[str, Any]:
    """Execute a shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        return {
            "command": command,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        raise ToolExecutionError(f"Command timed out after {timeout}s")


# Map tool names to functions
TOOL_FUNCTIONS = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "shell_command": tool_shell_command,
}


def execute_tool(
    tool: str, 
    args: Dict[str, Any], 
    use_subprocess: bool = True,
    timeout: float = 30.0,
) -> Tuple[Dict[str, Any], float]:
    """
    Execute a tool with the given arguments.
    
    Args:
        tool: Tool name
        args: Tool arguments
        use_subprocess: If True, run in subprocess for isolation
        timeout: Timeout in seconds
        
    Returns:
        (result_dict, duration_ms)
    """
    if tool not in TOOL_FUNCTIONS:
        raise ToolExecutionError(f"Unknown tool: {tool}")
    
    if use_subprocess:
        func_name = f"tool_{tool}"
        return execute_in_subprocess(func_name, args, timeout=timeout)
    else:
        # Direct execution (less safe, for comparison)
        start_time = time.perf_counter()
        func = TOOL_FUNCTIONS[tool]
        result = func(**args)
        duration_ms = (time.perf_counter() - start_time) * 1000
        return result, duration_ms


if __name__ == "__main__":
    # Quick test
    print("Testing tools...")
    
    # Test list_dir
    print("\nlist_dir('.'):")
    result, duration = execute_tool("list_dir", {"path": "."}, use_subprocess=False)
    print(f"  Found {result['count']} entries in {duration:.2f}ms")
    
    # Test with subprocess
    print("\nlist_dir('.') with subprocess:")
    result, duration = execute_tool("list_dir", {"path": "."}, use_subprocess=True)
    print(f"  Found {result['count']} entries in {duration:.2f}ms")
    
    # Test shell_command
    print("\nshell_command('pwd'):")
    result, duration = execute_tool("shell_command", {"command": "pwd"}, use_subprocess=False)
    print(f"  Output: {result['stdout'].strip()}, took {duration:.2f}ms")
