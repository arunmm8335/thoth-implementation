#!/usr/bin/env python3
"""
Plot Benchmark Results for Thoth System
Generates publication-quality visualizations of benchmark performance
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set publication-quality style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

# Load results
with open('benchmark_results/all_results.json') as f:
    results = json.load(f)

benchmarks = list(results.keys())
output_dir = Path('benchmark_results')

# Colors for benchmarks
colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D']
benchmark_labels = {
    'hashmap': 'Hashmap',
    'btree': 'B-Tree',
    'rbtree': 'RB-Tree',
    'swap': 'Array Swap'
}

# ============================================================================
# Figure 1: Coalescing Efficiency Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 5))

efficiencies = [results[b]['coalescing_efficiency'] for b in benchmarks]
bars = ax.bar(range(len(benchmarks)), efficiencies, color=colors, alpha=0.8, edgecolor='black')

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, efficiencies)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')

ax.set_xlabel('Benchmark Workload', fontweight='bold')
ax.set_ylabel('Coalescing Efficiency (%)', fontweight='bold')
ax.set_title('PCB Coalescing Efficiency Across Benchmarks', fontweight='bold', pad=15)
ax.set_xticks(range(len(benchmarks)))
ax.set_xticklabels([benchmark_labels[b] for b in benchmarks])
ax.set_ylim(0, 110)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.axhline(y=95, color='red', linestyle='--', alpha=0.5, label='Paper Target (95%)')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / 'benchmark_coalescing_efficiency.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_coalescing_efficiency.png")
plt.close()

# ============================================================================
# Figure 2: Write Amplification Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 5))

write_amps = [results[b]['write_amplification'] for b in benchmarks]
bars = ax.bar(range(len(benchmarks)), write_amps, color=colors, alpha=0.8, edgecolor='black')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, write_amps)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontweight='bold')

ax.set_xlabel('Benchmark Workload', fontweight='bold')
ax.set_ylabel('Write Amplification', fontweight='bold')
ax.set_title('Write Amplification: NVM Writes vs Expected', fontweight='bold', pad=15)
ax.set_xticks(range(len(benchmarks)))
ax.set_xticklabels([benchmark_labels[b] for b in benchmarks])
ax.set_ylim(0, max(write_amps) * 1.3)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No Amplification (1.0)')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / 'benchmark_write_amplification.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_write_amplification.png")
plt.close()

# ============================================================================
# Figure 3: Traffic Reduction
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 5))

reductions = [results[b]['traffic_reduction'] for b in benchmarks]
bars = ax.bar(range(len(benchmarks)), reductions, color=colors, alpha=0.8, edgecolor='black')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, reductions)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{val:.1f}×', ha='center', va='bottom', fontweight='bold')

ax.set_xlabel('Benchmark Workload', fontweight='bold')
ax.set_ylabel('Traffic Reduction Factor', fontweight='bold')
ax.set_title('NVM Write Traffic Reduction Through PCB Coalescing', fontweight='bold', pad=15)
ax.set_xticks(range(len(benchmarks)))
ax.set_xticklabels([benchmark_labels[b] for b in benchmarks])
ax.set_ylim(0, max(reductions) * 1.2)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(output_dir / 'benchmark_traffic_reduction.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_traffic_reduction.png")
plt.close()

# ============================================================================
# Figure 4: Partial Writes vs NVM Writes
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(benchmarks))
width = 0.35

partials = [results[b]['pcb_total_partials'] for b in benchmarks]
nvm_writes = [results[b]['nvm_writes'] for b in benchmarks]

bars1 = ax.bar(x - width/2, partials, width, label='8B Partial Writes', 
               color='#E63946', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x + width/2, nvm_writes, width, label='NVM Writes (64B)', 
               color='#06A77D', alpha=0.8, edgecolor='black')

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 10,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)

ax.set_xlabel('Benchmark Workload', fontweight='bold')
ax.set_ylabel('Number of Writes', fontweight='bold')
ax.set_title('Partial Writes vs Actual NVM Writes', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels([benchmark_labels[b] for b in benchmarks])
ax.legend()
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(output_dir / 'benchmark_writes_comparison.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_writes_comparison.png")
plt.close()

# ============================================================================
# Figure 5: Combined Performance Metrics (Normalized)
# ============================================================================
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Normalize metrics to 0-100 scale for comparison
def normalize(values):
    max_val = max(values)
    return [v/max_val * 100 for v in values]

# Subplot 1: Efficiency (already in %)
ax1.barh(range(len(benchmarks)), efficiencies, color=colors, alpha=0.8, edgecolor='black')
for i, val in enumerate(efficiencies):
    ax1.text(val + 1, i, f'{val:.1f}%', va='center', fontweight='bold')
ax1.set_xlabel('Coalescing Efficiency (%)', fontweight='bold')
ax1.set_title('Efficiency', fontweight='bold')
ax1.set_yticks(range(len(benchmarks)))
ax1.set_yticklabels([benchmark_labels[b] for b in benchmarks])
ax1.set_xlim(0, 110)
ax1.grid(axis='x', alpha=0.3, linestyle='--')

# Subplot 2: Write Amplification (inverted - lower is better)
write_amp_inv = [1/w if w > 0 else 0 for w in write_amps]
ax2.barh(range(len(benchmarks)), write_amp_inv, color=colors, alpha=0.8, edgecolor='black')
for i, (val, orig) in enumerate(zip(write_amp_inv, write_amps)):
    ax2.text(val + 0.5, i, f'{orig:.3f}', va='center', fontweight='bold')
ax2.set_xlabel('Inverse Write Amp (Higher is Better)', fontweight='bold')
ax2.set_title('Write Efficiency', fontweight='bold')
ax2.set_yticks(range(len(benchmarks)))
ax2.set_yticklabels([])
ax2.grid(axis='x', alpha=0.3, linestyle='--')

# Subplot 3: Traffic Reduction
ax3.barh(range(len(benchmarks)), reductions, color=colors, alpha=0.8, edgecolor='black')
for i, val in enumerate(reductions):
    ax3.text(val + 2, i, f'{val:.1f}×', va='center', fontweight='bold')
ax3.set_xlabel('Traffic Reduction Factor', fontweight='bold')
ax3.set_title('NVM Write Savings', fontweight='bold')
ax3.set_yticks(range(len(benchmarks)))
ax3.set_yticklabels([])
ax3.grid(axis='x', alpha=0.3, linestyle='--')

plt.suptitle('Benchmark Performance Comparison', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(output_dir / 'benchmark_combined_metrics.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_combined_metrics.png")
plt.close()

# ============================================================================
# Figure 6: Coalesced Blocks Breakdown
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(benchmarks))
width = 0.25

coalesced = [results[b]['pcb_coalesced_blocks'] for b in benchmarks]
flushes = [results[b]['pcb_flushes'] for b in benchmarks]
overflows = [results[b]['pcb_overflows'] for b in benchmarks]

bars1 = ax.bar(x - width, coalesced, width, label='Coalesced Blocks', 
               color='#06A77D', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x, flushes, width, label='Partial Flushes', 
               color='#F18F01', alpha=0.8, edgecolor='black')
bars3 = ax.bar(x + width, overflows, width, label='PLUB Overflows', 
               color='#E63946', alpha=0.8, edgecolor='black')

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=8)

ax.set_xlabel('Benchmark Workload', fontweight='bold')
ax.set_ylabel('Number of Blocks', fontweight='bold')
ax.set_title('PCB Block Processing: Coalesced vs Flushed vs Overflow', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels([benchmark_labels[b] for b in benchmarks])
ax.legend()
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(output_dir / 'benchmark_block_breakdown.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: benchmark_block_breakdown.png")
plt.close()

# ============================================================================
# Summary Statistics
# ============================================================================
print("\n" + "="*70)
print("BENCHMARK PLOTTING COMPLETE")
print("="*70)
print("\nGenerated 6 figures:")
print("  1. benchmark_coalescing_efficiency.png - Bar chart of efficiency")
print("  2. benchmark_write_amplification.png   - Write amplification comparison")
print("  3. benchmark_traffic_reduction.png     - Traffic reduction factors")
print("  4. benchmark_writes_comparison.png     - Partials vs NVM writes")
print("  5. benchmark_combined_metrics.png      - All metrics side-by-side")
print("  6. benchmark_block_breakdown.png       - PCB block processing")
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)

for bench in benchmarks:
    print(f"\n{benchmark_labels[bench].upper()}:")
    print(f"  Partials: {results[bench]['pcb_total_partials']:,}")
    print(f"  Coalesced: {results[bench]['pcb_coalesced_blocks']:,}")
    print(f"  NVM Writes: {results[bench]['nvm_writes']:,}")
    print(f"  Efficiency: {results[bench]['coalescing_efficiency']:.2f}%")
    print(f"  Write Amp: {results[bench]['write_amplification']:.3f}")
    print(f"  Reduction: {results[bench]['traffic_reduction']:.2f}×")

# Calculate averages
avg_efficiency = np.mean(efficiencies)
avg_write_amp = np.mean(write_amps)
avg_reduction = np.mean(reductions)

print("\n" + "="*70)
print("AVERAGES:")
print(f"  Efficiency: {avg_efficiency:.2f}%")
print(f"  Write Amplification: {avg_write_amp:.3f}")
print(f"  Traffic Reduction: {avg_reduction:.2f}×")
print("="*70)
print("\n✅ All plots saved to: benchmark_results/")
print("="*70)
