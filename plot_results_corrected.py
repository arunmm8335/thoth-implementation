#!/usr/bin/env python3
"""
Generate publication-quality plots from CORRECTED experiment results
Updated for MetadataTrafficGen parameters: burst_size, burst_interval, request_latency
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

# Set publication-quality defaults
matplotlib.rcParams['font.size'] = 12
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['axes.labelsize'] = 14
matplotlib.rcParams['axes.titlesize'] = 16
matplotlib.rcParams['xtick.labelsize'] = 12
matplotlib.rcParams['ytick.labelsize'] = 12
matplotlib.rcParams['legend.fontsize'] = 11
matplotlib.rcParams['figure.figsize'] = (10, 6)

class ResultsPlotter:
    def __init__(self, results_dir="experiment_results"):
        self.results_dir = Path(results_dir)
        self.plots_dir = self.results_dir / "plots"
        self.plots_dir.mkdir(exist_ok=True)
        
    def load_results(self, exp_id):
        """Load experiment results from JSON"""
        results_file = self.results_dir / f"{exp_id}_results.json"
        if not results_file.exists():
            print(f"⚠️  Results file not found: {results_file}")
            return None
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        return data
    
    def plot_burst_size_analysis(self):
        """Plot: Burst Size Impact on Performance"""
        data = self.load_results("exp1_burst_size")
        if not data or not data['results']:
            return
        
        results = data['results']
        burst_sizes = [r['burst_size'] for r in results]
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        nvm_writes = [r.get('nvmWrites', 0) for r in results]
        requests_sent = [r.get('requestsSent', 0) for r in results]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Efficiency vs Burst Size
        ax1.plot(burst_sizes, efficiency, 'o-', linewidth=2, markersize=10, color='#2E86AB')
        ax1.set_xlabel('Burst Size (requests/burst)')
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('PCB Coalescing Efficiency vs. Burst Size')
        ax1.grid(True, alpha=0.3)
        for x, y in zip(burst_sizes, efficiency):
            ax1.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        # Plot 2: Write Amplification vs Burst Size  
        ax2.plot(burst_sizes, write_amp, 's-', linewidth=2, markersize=10, color='#A23B72')
        ax2.set_xlabel('Burst Size (requests/burst)')
        ax2.set_ylabel('Write Amplification')
        ax2.set_title('Write Amplification vs. Burst Size')
        ax2.axhline(y=0.25, color='green', linestyle='--', alpha=0.5, label='Ideal (8B→64B)')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No Coalescing')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        for x, y in zip(burst_sizes, write_amp):
            ax2.annotate(f'{y:.3f}', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        # Plot 3: Traffic Reduction
        ax3.bar(burst_sizes, requests_sent, alpha=0.5, color='#F18F01', label='Requests Sent')
        ax3.bar(burst_sizes, nvm_writes, alpha=0.8, color='#2E86AB', label='NVM Writes')
        ax3.set_xlabel('Burst Size (requests/burst)')
        ax3.set_ylabel('Write Count')
        ax3.set_title('Traffic Reduction (Requests vs. NVM Writes)')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Reduction Factor
        reduction = [req / (nvm + 1) for req, nvm in zip(requests_sent, nvm_writes)]
        ax4.plot(burst_sizes, reduction, 'D-', linewidth=2, markersize=10, color='#6A994E')
        ax4.set_xlabel('Burst Size (requests/burst)')
        ax4.set_ylabel('Traffic Reduction Factor')
        ax4.set_title('PCB Traffic Reduction vs. Burst Size')
        ax4.axhline(y=8.0, color='green', linestyle='--', alpha=0.5, label='Ideal (8×)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        for x, y in zip(burst_sizes, reduction):
            ax4.annotate(f'{y:.1f}×', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure1_burst_size_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_burst_interval_analysis(self):
        """Plot: Burst Interval Impact"""
        data = self.load_results("exp2_burst_interval")
        if not data or not data['results']:
            return
        
        results = data['results']
        # Extract interval values (convert from string like '1ms' to number)
        intervals = []
        for r in results:
            interval_str = r['burst_interval']
            if 'ms' in interval_str:
                intervals.append(float(interval_str.replace('ms', '')))
            elif 'us' in interval_str:
                intervals.append(float(interval_str.replace('us', '')) / 1000)
        
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        nvm_writes = [r.get('nvmWrites', 0) for r in results]
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
        
        # Plot 1: Efficiency
        ax1.plot(intervals, efficiency, 'o-', linewidth=2, markersize=10, color='#2E86AB')
        ax1.set_xlabel('Burst Interval (ms)')
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Efficiency vs. Burst Interval')
        ax1.grid(True, alpha=0.3)
        for x, y in zip(intervals, efficiency):
            ax1.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        # Plot 2: Write Amplification
        ax2.plot(intervals, write_amp, 's-', linewidth=2, markersize=10, color='#A23B72')
        ax2.set_xlabel('Burst Interval (ms)')
        ax2.set_ylabel('Write Amplification')
        ax2.set_title('Write Amp vs. Burst Interval')
        ax2.axhline(y=0.25, color='green', linestyle='--', alpha=0.5, label='Ideal')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        for x, y in zip(intervals, write_amp):
            ax2.annotate(f'{y:.3f}', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        # Plot 3: NVM Writes
        ax3.plot(intervals, nvm_writes, 'D-', linewidth=2, markersize=10, color='#F18F01')
        ax3.set_xlabel('Burst Interval (ms)')
        ax3.set_ylabel('NVM Writes')
        ax3.set_title('NVM Writes vs. Burst Interval')
        ax3.grid(True, alpha=0.3)
        for x, y in zip(intervals, nvm_writes):
            ax3.annotate(f'{int(y)}', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure2_burst_interval_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_request_latency_analysis(self):
        """Plot: Request Latency Impact"""
        data = self.load_results("exp3_request_latency")
        if not data or not data['results']:
            return
        
        results = data['results']
        # Extract latency values
        latencies = []
        for r in results:
            lat_str = r['request_latency']
            if 'us' in lat_str:
                latencies.append(float(lat_str.replace('us', '')))
            elif 'ms' in lat_str:
                latencies.append(float(lat_str.replace('ms', '')) * 1000)
        
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Efficiency vs Latency
        ax1.plot(latencies, efficiency, 'o-', linewidth=2, markersize=10, color='#2E86AB')
        ax1.set_xlabel('Request Latency (μs)')
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Coalescing Efficiency vs. Request Spacing')
        ax1.grid(True, alpha=0.3)
        for x, y in zip(latencies, efficiency):
            ax1.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        # Plot 2: Write Amplification vs Latency
        ax2.plot(latencies, write_amp, 's-', linewidth=2, markersize=10, color='#A23B72')
        ax2.set_xlabel('Request Latency (μs)')
        ax2.set_ylabel('Write Amplification')
        ax2.set_title('Write Amplification vs. Request Spacing')
        ax2.axhline(y=0.25, color='green', linestyle='--', alpha=0.5, label='Ideal (8B→64B)')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No Coalescing')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        for x, y in zip(latencies, write_amp):
            ax2.annotate(f'{y:.3f}', (x, y), textcoords="offset points", 
                        xytext=(0,8), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure3_request_latency_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_mixed_workloads(self):
        """Plot: Mixed Workload Comparison"""
        data = self.load_results("exp4_mixed_workloads")
        if not data or not data['results']:
            return
        
        results = data['results']
        workloads = [r.get('name', f"Workload {i}") for i, r in enumerate(results, 1)]
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        nvm_writes = [r.get('nvmWrites', 0) for r in results]
        requests = [r.get('requestsSent', 0) for r in results]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#6A994E']
        
        # Plot 1: Efficiency Comparison
        bars1 = ax1.bar(workloads, efficiency, color=colors[:len(workloads)], alpha=0.8)
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Coalescing Efficiency by Workload')
        ax1.set_ylim([0, 105])
        ax1.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars1, efficiency):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=10)
        
        # Plot 2: Write Amplification
        bars2 = ax2.bar(workloads, write_amp, color=colors[:len(workloads)], alpha=0.8)
        ax2.set_ylabel('Write Amplification')
        ax2.set_title('Write Amplification by Workload')
        ax2.axhline(y=0.25, color='green', linestyle='--', alpha=0.5, label='Ideal')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No Coalescing')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars2, write_amp):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10)
        
        # Plot 3: Traffic Comparison
        x = np.arange(len(workloads))
        width = 0.35
        bars3a = ax3.bar(x - width/2, requests, width, label='Requests', color='#F18F01', alpha=0.7)
        bars3b = ax3.bar(x + width/2, nvm_writes, width, label='NVM Writes', color='#2E86AB', alpha=0.7)
        ax3.set_ylabel('Write Count')
        ax3.set_title('Traffic Comparison (Requests vs. NVM Writes)')
        ax3.set_xticks(x)
        ax3.set_xticklabels(workloads)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Reduction Factor
        reduction = [req / (nvm + 1) for req, nvm in zip(requests, nvm_writes)]
        bars4 = ax4.bar(workloads, reduction, color=colors[:len(workloads)], alpha=0.8)
        ax4.set_ylabel('Traffic Reduction Factor')
        ax4.set_title('PCB Traffic Reduction by Workload')
        ax4.axhline(y=8.0, color='green', linestyle='--', alpha=0.5, label='Ideal (8×)')
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars4, reduction):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}×', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure4_mixed_workloads.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def generate_summary_table(self):
        """Generate comprehensive summary table"""
        summary_file = self.results_dir / "experiment_summary.json"
        if not summary_file.exists():
            return
        
        with open(summary_file, 'r') as f:
            all_results = json.load(f)
        
        fig, ax = plt.subplots(figsize=(16, 10))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table data
        table_data = [
            ['Experiment', 'Configuration', 'Requests', 'Efficiency (%)', 'Write Amp', 'NVM Writes', 'Reduction']
        ]
        
        for exp_id, results in all_results.items():
            if not results:
                continue
            exp_name = exp_id.replace('_', ' ').replace('exp', 'Exp').title()
            
            for result in results:
                name = result.get('name', '')
                burst_size = result.get('burst_size', '-')
                burst_interval = result.get('burst_interval', '-')
                request_latency = result.get('request_latency', '-')
                
                config = f"BS:{burst_size}, BI:{burst_interval}, RL:{request_latency}"
                if name:
                    config = f"{name}: {config}"
                
                requests = f"{int(result.get('requestsSent', 0))}"
                efficiency = f"{result.get('coalescingEfficiency', 0):.2f}"
                write_amp = f"{result.get('writeAmplification', 0):.3f}"
                nvm_writes = f"{int(result.get('nvmWrites', 0))}"
                reduction = f"{result.get('requestsSent', 0) / (result.get('nvmWrites', 1)):.1f}×"
                
                table_data.append([
                    exp_name,
                    config,
                    requests,
                    efficiency,
                    write_amp,
                    nvm_writes,
                    reduction
                ])
        
        table = ax.table(cellText=table_data, cellLoc='left', loc='center',
                        colWidths=[0.15, 0.30, 0.10, 0.10, 0.10, 0.10, 0.10])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.5)
        
        # Style header row
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#2E86AB')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            for j in range(len(table_data[0])):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.title('Thoth PCB Coalescing - Comprehensive Experiment Results', 
                 fontsize=18, weight='bold', pad=20)
        
        output_file = self.plots_dir / "summary_table.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def generate_all_plots(self):
        """Generate all plots"""
        print("\n" + "="*70)
        print("📊 GENERATING CORRECTED PUBLICATION-QUALITY PLOTS")
        print("="*70 + "\n")
        
        self.plot_burst_size_analysis()
        self.plot_burst_interval_analysis()
        self.plot_request_latency_analysis()
        self.plot_mixed_workloads()
        self.generate_summary_table()
        
        print("\n" + "="*70)
        print(f"🎉 ALL PLOTS GENERATED!")
        print(f"   Output directory: {self.plots_dir}")
        print(f"   Files:")
        for plot_file in sorted(self.plots_dir.glob("*.png")):
            print(f"   - {plot_file.name}")
        print("="*70 + "\n")

def main():
    plotter = ResultsPlotter()
    plotter.generate_all_plots()

if __name__ == "__main__":
    main()
