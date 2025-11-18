#!/usr/bin/env python3
"""
Automated Experiment Suite for Thoth PCB Coalescing
Runs multiple experiments and collects statistics
"""

import os
import subprocess
import re
import json
import time
from pathlib import Path

# Experiment configurations
# Note: MetadataTrafficGen parameters are: burst_size, burst_interval, request_latency
EXPERIMENTS = {
    "exp1_burst_size": {
        "name": "Burst Size Analysis",
        "description": "How burst size affects coalescing efficiency",
        "variations": [
            {"burst_size": 25, "burst_interval": "1ms", "request_latency": "4us", "name": "Small"},
            {"burst_size": 50, "burst_interval": "1ms", "request_latency": "4us", "name": "Medium"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "4us", "name": "Large"},
            {"burst_size": 200, "burst_interval": "1ms", "request_latency": "4us", "name": "VeryLarge"},
            {"burst_size": 400, "burst_interval": "1ms", "request_latency": "4us", "name": "Huge"},
        ]
    },
    "exp2_burst_interval": {
        "name": "Burst Interval Scaling",
        "description": "How burst timing affects coalescing",
        "variations": [
            {"burst_size": 100, "burst_interval": "500us", "request_latency": "4us", "name": "Fast"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "4us", "name": "Normal"},
            {"burst_size": 100, "burst_interval": "2ms", "request_latency": "4us", "name": "Slow"},
            {"burst_size": 100, "burst_interval": "5ms", "request_latency": "4us", "name": "VerySlow"},
            {"burst_size": 100, "burst_interval": "10ms", "request_latency": "4us", "name": "Lazy"},
        ]
    },
    "exp3_request_latency": {
        "name": "Request Latency Impact",
        "description": "How request spacing affects performance",
        "variations": [
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "1us", "name": "Dense"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "4us", "name": "Normal"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "10us", "name": "Sparse"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "20us", "name": "VerySparse"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "50us", "name": "Scattered"},
        ]
    },
    "exp4_mixed_workloads": {
        "name": "Mixed Workload Patterns",
        "description": "Various realistic workload patterns",
        "variations": [
            {"burst_size": 50, "burst_interval": "1ms", "request_latency": "4us", "name": "LowLoad"},
            {"burst_size": 100, "burst_interval": "1ms", "request_latency": "4us", "name": "MediumLoad"},
            {"burst_size": 200, "burst_interval": "2ms", "request_latency": "4us", "name": "HighLoad"},
            {"burst_size": 400, "burst_interval": "5ms", "request_latency": "10us", "name": "BurstyLoad"},
        ]
    }
}

class ExperimentRunner:
    def __init__(self):
        self.gem5_binary = "./build/RISCV/gem5.opt"
        self.config_template = "configs/example/thoth_full_demo.py"
        self.results_dir = Path("experiment_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def create_config(self, params, config_path):
        """Create a modified config file with specific parameters"""
        with open(self.config_template, 'r') as f:
            content = f.read()
        
        # Replace MetadataTrafficGen parameters
        if 'burst_size' in params:
            content = re.sub(r'burst_size=\d+', 
                            f'burst_size={params["burst_size"]}', content)
        if 'burst_interval' in params:
            content = re.sub(r'burst_interval=["\'][^"\']+["\']', 
                            f'burst_interval=\'{params["burst_interval"]}\'', content)
        if 'request_latency' in params:
            content = re.sub(r'request_latency=["\'][^"\']+["\']', 
                            f'request_latency=\'{params["request_latency"]}\'', content)
        
        with open(config_path, 'w') as f:
            f.write(content)
    
    def run_simulation(self, config_path, output_dir):
        """Run gem5 simulation"""
        cmd = [
            self.gem5_binary,
            f"--outdir={str(output_dir)}",
            str(config_path)
        ]
        
        print(f"  Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minute timeout
                text=True
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("  ⚠️  Simulation timeout!")
            return False
    
    def parse_stats(self, stats_file):
        """Parse statistics from m5out/stats.txt"""
        stats = {}
        
        if not os.path.exists(stats_file):
            return stats
        
        with open(stats_file, 'r') as f:
            content = f.read()
        
        # Extract key statistics
        patterns = {
            'pcbTotalPartials': r'system\.metadata_cache\.pcbTotalPartials\s+(\d+)',
            'pcbCoalescedBlocks': r'system\.metadata_cache\.pcbCoalescedBlocks\s+(\d+)',
            'pcbPartialFlushes': r'system\.metadata_cache\.pcbPartialFlushes\s+(\d+)',
            'pcbOverflows': r'system\.metadata_cache\.pcbOverflows\s+(\d+)',
            'plubPartials': r'system\.metadata_cache\.plubPartials\s+(\d+)',
            'nvmWrites': r'system\.metadata_cache\.nvmWrites\s+(\d+)',
            'nvmBytesWritten': r'system\.metadata_cache\.nvmBytesWritten\s+(\d+)',
            'writeAmplification': r'system\.metadata_cache\.writeAmplification\s+([\d.]+)',
            'overflowRate': r'system\.metadata_cache\.overflowRate\s+([\d.]+)',
            'plubOverhead': r'system\.metadata_cache\.plubOverhead\s+([\d.]+)',
            'cacheHits': r'system\.metadata_cache\.cacheHits\s+(\d+)',
            'cacheMisses': r'system\.metadata_cache\.cacheMisses\s+(\d+)',
            'requestsSent': r'system\.traffic_gen\.requestsSent\s+(\d+)',
            'burstsCompleted': r'system\.traffic_gen\.burstsCompleted\s+(\d+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                try:
                    stats[key] = float(match.group(1))
                except ValueError:
                    stats[key] = 0
            else:
                stats[key] = 0
        
        # Calculate derived metrics
        if stats.get('pcbTotalPartials', 0) > 0:
            stats['coalescingEfficiency'] = (stats.get('pcbCoalescedBlocks', 0) / 
                                            stats['pcbTotalPartials']) * 100
            stats['hitRate'] = (stats.get('cacheHits', 0) / 
                               (stats.get('cacheHits', 0) + stats.get('cacheMisses', 0) + 1)) * 100
        else:
            stats['coalescingEfficiency'] = 0
            stats['hitRate'] = 0
        
        return stats
    
    def run_experiment_set(self, exp_id, exp_config):
        """Run a complete experiment set"""
        print(f"\n{'='*70}")
        print(f"🔬 Experiment: {exp_config['name']}")
        print(f"   {exp_config['description']}")
        print(f"{'='*70}\n")
        
        results = []
        
        for i, params in enumerate(exp_config['variations'], 1):
            print(f"[{i}/{len(exp_config['variations'])}] Running variation: {params}")
            
            # Create output directory
            var_name = params.get('name', f"var{i}")
            output_dir = self.results_dir / exp_id / var_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create config
            config_path = output_dir / "config.py"
            self.create_config(params, config_path)
            
            # Run simulation
            start_time = time.time()
            success = self.run_simulation(config_path, output_dir)
            elapsed = time.time() - start_time
            
            if success:
                # Parse results
                stats = self.parse_stats(output_dir / "stats.txt")
                stats.update(params)
                stats['elapsed_time'] = elapsed
                results.append(stats)
                
                print(f"  ✅ Success! (took {elapsed:.1f}s)")
                print(f"     Efficiency: {stats.get('coalescingEfficiency', 0):.2f}%")
                print(f"     Write Amp: {stats.get('writeAmplification', 0):.3f}")
            else:
                print(f"  ❌ Failed!")
        
        # Save results
        results_file = self.results_dir / f"{exp_id}_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'experiment': exp_config['name'],
                'description': exp_config['description'],
                'results': results
            }, f, indent=2)
        
        print(f"\n✅ Experiment complete! Results saved to {results_file}")
        return results

    def run_all_experiments(self):
        """Run all experiments"""
        print("\n" + "="*70)
        print("🚀 THOTH PCB COALESCING - AUTOMATED EXPERIMENT SUITE")
        print("="*70)
        
        all_results = {}
        
        for exp_id, exp_config in EXPERIMENTS.items():
            results = self.run_experiment_set(exp_id, exp_config)
            all_results[exp_id] = results
        
        # Save summary
        summary_file = self.results_dir / "experiment_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print("\n" + "="*70)
        print("🎉 ALL EXPERIMENTS COMPLETE!")
        print(f"   Results directory: {self.results_dir}")
        print(f"   Summary file: {summary_file}")
        print("="*70 + "\n")
        
        return all_results

def main():
    runner = ExperimentRunner()
    
    # Check if gem5 binary exists
    if not os.path.exists(runner.gem5_binary):
        print(f"❌ Error: gem5 binary not found at {runner.gem5_binary}")
        print("   Please build gem5 first: yes | scons build/RISCV/gem5.opt -j$(nproc)")
        return
    
    # Check if config exists
    if not os.path.exists(runner.config_template):
        print(f"❌ Error: Config template not found at {runner.config_template}")
        return
    
    # Run all experiments
    results = runner.run_all_experiments()
    
    print("\n📊 Next step: Run plot_results.py to generate graphs!")

if __name__ == "__main__":
    main()
