#!/usr/bin/env python3
"""
Benchmark sandbox overhead.
Compares direct execution vs subprocess-isolated execution.
"""

import time
import statistics
import os
from sandbox import AgentSandbox, ToolCallRequest
from policy import DEFAULT_POLICY


def benchmark(sandbox: AgentSandbox, request: ToolCallRequest, iterations: int = 100):
    """Run a benchmark and return statistics."""
    latencies = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        result = sandbox.execute(request)
        end = time.perf_counter()
        
        if result.allowed and not result.error:
            latencies.append((end - start) * 1000)  # ms
    
    if not latencies:
        return None
    
    return {
        "count": len(latencies),
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies),
        "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 100 else max(latencies),
    }


def print_stats(name: str, stats: dict):
    """Print statistics in a formatted way."""
    print(f"  Mean:   {stats['mean_ms']:.2f}ms")
    print(f"  Median: {stats['median_ms']:.2f}ms")
    print(f"  Stdev:  {stats['stdev_ms']:.2f}ms")
    print(f"  Min:    {stats['min_ms']:.2f}ms")
    print(f"  Max:    {stats['max_ms']:.2f}ms")
    print(f"  p95:    {stats['p95_ms']:.2f}ms")


def main():
    print("=" * 60)
    print("Agent Sandbox Performance Benchmark")
    print("=" * 60)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/sample.txt"):
        with open("data/sample.txt", "w") as f:
            f.write("Test content\n" * 100)
    
    iterations = 50
    
    # Test 1: list_dir
    print(f"\n[Test 1] list_dir('.') - {iterations} iterations")
    print("-" * 40)
    
    request_list = ToolCallRequest(tool="list_dir", arguments={"path": "."})
    
    # With subprocess
    sandbox_sub = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_sub.jsonl",
        use_subprocess=True,
    )
    print("\nWith subprocess isolation:")
    stats_sub = benchmark(sandbox_sub, request_list, iterations)
    if stats_sub:
        print_stats("subprocess", stats_sub)
    sandbox_sub.close()
    
    # Without subprocess
    sandbox_direct = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_direct.jsonl",
        use_subprocess=False,
    )
    print("\nWithout subprocess isolation:")
    stats_direct = benchmark(sandbox_direct, request_list, iterations)
    if stats_direct:
        print_stats("direct", stats_direct)
    sandbox_direct.close()
    
    if stats_sub and stats_direct:
        overhead = stats_sub['mean_ms'] - stats_direct['mean_ms']
        overhead_pct = (overhead / stats_direct['mean_ms']) * 100 if stats_direct['mean_ms'] > 0 else 0
        print(f"\nOverhead: {overhead:.2f}ms ({overhead_pct:.1f}%)")
    
    # Test 2: read_file
    print(f"\n[Test 2] read_file('data/sample.txt') - {iterations} iterations")
    print("-" * 40)
    
    request_read = ToolCallRequest(tool="read_file", arguments={"path": "data/sample.txt"})
    
    sandbox_sub2 = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_sub2.jsonl",
        use_subprocess=True,
    )
    print("\nWith subprocess isolation:")
    stats_sub2 = benchmark(sandbox_sub2, request_read, iterations)
    if stats_sub2:
        print_stats("subprocess", stats_sub2)
    sandbox_sub2.close()
    
    sandbox_direct2 = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_direct2.jsonl",
        use_subprocess=False,
    )
    print("\nWithout subprocess isolation:")
    stats_direct2 = benchmark(sandbox_direct2, request_read, iterations)
    if stats_direct2:
        print_stats("direct", stats_direct2)
    sandbox_direct2.close()
    
    if stats_sub2 and stats_direct2:
        overhead2 = stats_sub2['mean_ms'] - stats_direct2['mean_ms']
        overhead_pct2 = (overhead2 / stats_direct2['mean_ms']) * 100 if stats_direct2['mean_ms'] > 0 else 0
        print(f"\nOverhead: {overhead2:.2f}ms ({overhead_pct2:.1f}%)")
    
    # Test 3: shell_command
    print(f"\n[Test 3] shell_command('pwd') - {iterations} iterations")
    print("-" * 40)
    
    request_shell = ToolCallRequest(tool="shell_command", arguments={"command": "pwd"})
    
    sandbox_sub3 = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_sub3.jsonl",
        use_subprocess=True,
    )
    print("\nWith subprocess isolation:")
    stats_sub3 = benchmark(sandbox_sub3, request_shell, iterations)
    if stats_sub3:
        print_stats("subprocess", stats_sub3)
    sandbox_sub3.close()
    
    sandbox_direct3 = AgentSandbox(
        policy=DEFAULT_POLICY,
        log_path="/tmp/bench_direct3.jsonl",
        use_subprocess=False,
    )
    print("\nWithout subprocess isolation:")
    stats_direct3 = benchmark(sandbox_direct3, request_shell, iterations)
    if stats_direct3:
        print_stats("direct", stats_direct3)
    sandbox_direct3.close()
    
    if stats_sub3 and stats_direct3:
        overhead3 = stats_sub3['mean_ms'] - stats_direct3['mean_ms']
        overhead_pct3 = (overhead3 / stats_direct3['mean_ms']) * 100 if stats_direct3['mean_ms'] > 0 else 0
        print(f"\nOverhead: {overhead3:.2f}ms ({overhead_pct3:.1f}%)")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nSubprocess isolation adds overhead for process creation,")
    print("but provides better fault isolation and security.")
    print("\nFor tool calls that are already slow (network, disk I/O),")
    print("the relative overhead is smaller.")
    print("\nFor simple in-memory operations, consider if isolation is needed.")


if __name__ == "__main__":
    main()
