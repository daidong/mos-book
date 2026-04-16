#!/usr/bin/env python3
"""
analyze_throttling.py - Analyze CPU throttling data from Lab 5

Usage:
    python3 analyze_throttling.py cpu_throttle_data.csv
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_throttling.py <csv_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Load data
    df = pd.read_csv(filename)
    
    # Calculate deltas (metrics are cumulative)
    df['delta_periods'] = df['nr_periods'].diff().fillna(0)
    df['delta_throttled'] = df['nr_throttled'].diff().fillna(0)
    df['delta_usec'] = df['throttled_usec'].diff().fillna(0)
    
    # Calculate throttle ratio per interval
    df['throttle_ratio'] = df['delta_throttled'] / df['delta_periods'].replace(0, 1)
    
    # Summary statistics
    total_periods = df['delta_periods'].sum()
    total_throttled = df['delta_throttled'].sum()
    total_usec = df['delta_usec'].sum()
    
    if total_periods > 0:
        overall_ratio = total_throttled / total_periods
    else:
        overall_ratio = 0
    
    print("=" * 50)
    print("CPU Throttling Analysis")
    print("=" * 50)
    print(f"Data file: {filename}")
    print(f"Duration: {len(df)} samples")
    print()
    print("Summary:")
    print(f"  Total periods:     {int(total_periods)}")
    print(f"  Throttled periods: {int(total_throttled)}")
    print(f"  Total throttle time: {total_usec/1000:.2f} ms")
    print(f"  Overall throttle ratio: {overall_ratio*100:.1f}%")
    print()
    
    if total_throttled > 0:
        avg_throttle_per_period = total_usec / total_throttled
        print(f"  Avg throttle time per throttled period: {avg_throttle_per_period/1000:.2f} ms")
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot 1: Throttle ratio over time
    axes[0].plot(range(len(df)), df['throttle_ratio'] * 100, 'b-', linewidth=1)
    axes[0].axhline(y=overall_ratio*100, color='r', linestyle='--', label=f'Average: {overall_ratio*100:.1f}%')
    axes[0].set_xlabel('Sample')
    axes[0].set_ylabel('Throttle Ratio (%)')
    axes[0].set_title('CPU Throttle Ratio Over Time')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Throttled time per interval
    axes[1].bar(range(len(df)), df['delta_usec']/1000, color='orange', alpha=0.7)
    axes[1].set_xlabel('Sample')
    axes[1].set_ylabel('Throttled Time (ms)')
    axes[1].set_title('Throttled Time Per Interval')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('throttling_analysis.png', dpi=150)
    print(f"\nVisualization saved to: throttling_analysis.png")

if __name__ == '__main__':
    main()
