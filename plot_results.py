#!/usr/bin/env python3
"""
Generate publication-quality plots from experiment results
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
    
    def plot_stride_analysis(self):
        """Plot: Coalescing Efficiency vs. Burst Size"""
        data = self.load_results("exp1_burst_size")
        if not data or not data['results']:
            return
        
        results = data['results']
        burst_sizes = [r['burst_size'] for r in results]
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        requests_sent = [r.get('requestsSent', 0) for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Coalescing Efficiency
        ax1.plot(burst_sizes, efficiency, 'o-', linewidth=2, markersize=8, color='#2E86AB')
        ax1.set_xlabel('Burst Size (requests/burst)')
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Coalescing Efficiency vs. Burst Size')
        ax1.grid(True, alpha=0.3)
        
        # Annotate values
        for x, y in zip(burst_sizes, efficiency):
            ax1.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        # Plot 2: Requests Sent vs Write Amplification
        ax2_twin = ax2.twinx()
        l1 = ax2.plot(burst_sizes, requests_sent, 's-', linewidth=2, markersize=8, 
                     color='#F18F01', label='Requests Sent')
        l2 = ax2_twin.plot(burst_sizes, write_amp, 'D-', linewidth=2, markersize=8, 
                          color='#A23B72', label='Write Amplification')
        ax2.set_xlabel('Burst Size (requests/burst)')
        ax2.set_ylabel('Requests Sent', color='#F18F01')
        ax2_twin.set_ylabel('Write Amplification', color='#A23B72')
        ax2.set_title('Traffic Load vs. Write Amplification')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='y', labelcolor='#F18F01')
        ax2_twin.tick_params(axis='y', labelcolor='#A23B72')
        
        # Combined legend
        lines = l1 + l2
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='upper left')
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure1_burst_size_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_request_scaling(self):
        """Plot: System Scaling with Request Count"""
        data = self.load_results("exp2_request_count")
        if not data or not data['results']:
            return
        
        results = data['results']
        requests = [r['max_requests'] for r in results]
        total_partials = [r.get('pcbTotalPartials', 0) for r in results]
        nvm_writes = [r.get('nvmWrites', 0) for r in results]
        coalesced = [r.get('pcbCoalescedBlocks', 0) for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Traffic Reduction
        ax1.plot(requests, total_partials, 'o-', linewidth=2, markersize=8, 
                label='Partial Writes (8B)', color='#F18F01')
        ax1.plot(requests, nvm_writes, 's-', linewidth=2, markersize=8, 
                label='NVM Writes (After PCB)', color='#2E86AB')
        ax1.set_xlabel('Number of Requests')
        ax1.set_ylabel('Write Count')
        ax1.set_title('NVM Traffic Reduction via PCB')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')
        
        # Plot 2: Reduction Factor
        reduction = [tp / (nw + 1) for tp, nw in zip(total_partials, nvm_writes)]
        ax2.plot(requests, reduction, 'D-', linewidth=2, markersize=8, color='#6A994E')
        ax2.set_xlabel('Number of Requests')
        ax2.set_ylabel('Traffic Reduction Factor')
        ax2.set_title('PCB Traffic Reduction Factor')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=8.0, color='green', linestyle='--', alpha=0.5, label='Ideal (8×)')
        ax2.legend()
        
        # Annotate values
        for x, y in zip(requests, reduction):
            ax2.annotate(f'{y:.1f}×', (x, y), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure2_request_scaling.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_traffic_rate(self):
        """Plot: Traffic Rate Impact on Performance"""
        data = self.load_results("exp3_traffic_rate")
        if not data or not data['results']:
            return
        
        results = data['results']
        rates = [int(r['rate'].replace('GB/s', '')) for r in results]
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        overflow_rate = [r.get('overflowRate', 0) for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Efficiency vs. Rate
        ax1.plot(rates, efficiency, 'o-', linewidth=2, markersize=8, color='#2E86AB')
        ax1.set_xlabel('Traffic Rate (GB/s)')
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Coalescing Efficiency vs. Traffic Rate')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 105])
        
        # Annotate values
        for x, y in zip(rates, efficiency):
            ax1.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        # Plot 2: Overflow Rate
        ax2.plot(rates, overflow_rate, 's-', linewidth=2, markersize=8, color='#C1121F')
        ax2.set_xlabel('Traffic Rate (GB/s)')
        ax2.set_ylabel('Overflow Rate (%)')
        ax2.set_title('PCB Overflow Rate vs. Traffic Rate')
        ax2.grid(True, alpha=0.3)
        
        # Annotate values
        for x, y in zip(rates, overflow_rate):
            ax2.annotate(f'{y:.2f}%', (x, y), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure3_traffic_rate.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def plot_mixed_patterns(self):
        """Plot: Comparison of Different Access Patterns"""
        data = self.load_results("exp4_mixed_patterns")
        if not data or not data['results']:
            return
        
        results = data['results']
        patterns = [r.get('name', f"Pattern {i}") for i, r in enumerate(results, 1)]
        efficiency = [r.get('coalescingEfficiency', 0) for r in results]
        write_amp = [r.get('writeAmplification', 0) for r in results]
        nvm_writes = [r.get('nvmWrites', 0) for r in results]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Coalescing Efficiency (Bar Chart)
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#6A994E']
        bars1 = ax1.bar(patterns, efficiency, color=colors, alpha=0.8)
        ax1.set_ylabel('Coalescing Efficiency (%)')
        ax1.set_title('Coalescing Efficiency by Access Pattern')
        ax1.set_ylim([0, 105])
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, val in zip(bars1, efficiency):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=10)
        
        # Plot 2: Write Amplification
        bars2 = ax2.bar(patterns, write_amp, color=colors, alpha=0.8)
        ax2.set_ylabel('Write Amplification')
        ax2.set_title('Write Amplification by Access Pattern')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No Coalescing')
        ax2.axhline(y=0.25, color='green', linestyle='--', alpha=0.5, label='Ideal')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars2, write_amp):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10)
        
        # Plot 3: NVM Writes Comparison
        bars3 = ax3.bar(patterns, nvm_writes, color=colors, alpha=0.8)
        ax3.set_ylabel('NVM Write Count')
        ax3.set_title('NVM Writes by Access Pattern')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars3, nvm_writes):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(val)}', ha='center', va='bottom', fontsize=10)
        
        # Plot 4: Summary Radar Chart (if possible)
        if len(results) >= 3:
            categories = ['Efficiency\n(%)', 'Write Amp\n(lower better)', 
                         'NVM Writes\n(lower better)']
            
            # Normalize metrics to 0-100 scale
            norm_efficiency = efficiency
            norm_write_amp = [100 - min(wa * 100, 100) for wa in write_amp]  # Invert
            max_writes = max(nvm_writes) if max(nvm_writes) > 0 else 1
            norm_nvm = [100 - (w / max_writes * 100) for w in nvm_writes]  # Invert
            
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]
            
            ax4 = plt.subplot(224, projection='polar')
            
            for i, (pattern, color) in enumerate(zip(patterns, colors)):
                values = [norm_efficiency[i], norm_write_amp[i], norm_nvm[i]]
                values += values[:1]
                ax4.plot(angles, values, 'o-', linewidth=2, label=pattern, color=color)
                ax4.fill(angles, values, alpha=0.15, color=color)
            
            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels(categories)
            ax4.set_ylim(0, 100)
            ax4.set_title('Performance Comparison (Normalized)', pad=20)
            ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            ax4.grid(True)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data\nfor radar chart', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        plt.tight_layout()
        output_file = self.plots_dir / "figure4_mixed_patterns.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def generate_summary_table(self):
        """Generate a summary table of all experiments"""
        summary_file = self.results_dir / "experiment_summary.json"
        if not summary_file.exists():
            return
        
        with open(summary_file, 'r') as f:
            all_results = json.load(f)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table data
        table_data = [
            ['Experiment', 'Config', 'Efficiency (%)', 'Write Amp', 'NVM Writes', 'PLUB Overflow (%)']
        ]
        
        for exp_id, results in all_results.items():
            if not results:
                continue
            exp_name = exp_id.replace('_', ' ').title()
            
            for i, result in enumerate(results, 1):
                stride = result.get('stride', 'N/A')
                rate = result.get('rate', 'N/A')
                requests = result.get('max_requests', 'N/A')
                
                config = f"Stride:{stride}, Rate:{rate}, Req:{requests}"
                efficiency = f"{result.get('coalescingEfficiency', 0):.2f}"
                write_amp = f"{result.get('writeAmplification', 0):.3f}"
                nvm_writes = f"{int(result.get('nvmWrites', 0))}"
                overflow = f"{result.get('overflowRate', 0):.2f}"
                
                table_data.append([
                    f"{exp_name} #{i}",
                    config,
                    efficiency,
                    write_amp,
                    nvm_writes,
                    overflow
                ])
        
        table = ax.table(cellText=table_data, cellLoc='left', loc='center',
                        colWidths=[0.2, 0.35, 0.15, 0.1, 0.1, 0.1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)
        
        # Style header row
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#2E86AB')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            for j in range(len(table_data[0])):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.title('Experiment Results Summary', fontsize=16, weight='bold', pad=20)
        
        output_file = self.plots_dir / "summary_table.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    def generate_all_plots(self):
        """Generate all plots"""
        print("\n" + "="*70)
        print("📊 GENERATING PUBLICATION-QUALITY PLOTS")
        print("="*70 + "\n")
        
        self.plot_stride_analysis()
        self.plot_request_scaling()
        self.plot_traffic_rate()
        self.plot_mixed_patterns()
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
