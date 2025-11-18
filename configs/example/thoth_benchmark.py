#!/usr/bin/env python3
"""
Thoth System with Benchmark-Inspired Traffic Patterns
Simulates metadata write patterns characteristic of real workloads
"""

import m5
from m5.objects import *
from m5.util import convert

# Benchmark characteristics (approximate metadata write patterns)
BENCHMARK_PARAMS = {
    'hashmap': {
        'description': 'Hash table with random access, high update rate',
        'burst_size': 100,       # Frequent small bursts
        'burst_interval': '1ms', # High frequency updates
        'num_operations': 100000
    },
    'btree': {
        'description': 'B-tree with sequential insertions, moderate locality',
        'burst_size': 50,        # Medium bursts
        'burst_interval': '2ms', # Moderate frequency
        'num_operations': 50000
    },
    'rbtree': {
        'description': 'Red-black tree with rebalancing, mixed access',
        'burst_size': 75,        # Medium-large bursts
        'burst_interval': '1.5ms',
        'num_operations': 50000
    },
    'swap': {
        'description': 'Array swapping with contiguous access (worst case)',
        'burst_size': 200,       # Large contiguous bursts
        'burst_interval': '500us', # Very frequent
        'num_operations': 25000
    }
}

# System configuration
class ThothBenchmarkSystem(System):
    def __init__(self, benchmark_name, params):
        super().__init__()
        
        # Basic system setup
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '3GHz'
        self.clk_domain.voltage_domain = VoltageDomain()
        
        self.mem_mode = 'timing'
        self.mem_ranges = [AddrRange('8GB', '12GB')]  # Metadata region
        
        # Memory bus
        self.membus = SystemXBar()
        self.membus.width = 64
        
        # Metadata traffic generator (simulates benchmark metadata writes)
        self.traffic_gen = MetadataTrafficGen()
        self.traffic_gen.burst_size = params['burst_size']
        self.traffic_gen.burst_interval = params['burst_interval']
        self.traffic_gen.request_latency = '10us'
        self.traffic_gen.start_addr = 0x200000000  # 8GB start
        self.traffic_gen.end_addr = 0x201000000    # 8GB + 16MB range
        
        # Metadata Cache (PCB coalescing buffer)
        self.metadata_cache = MetadataCache()
        self.metadata_cache.access_latency = '10ns'
        
        # NVMain PCM backend
        self.nvmain = NVMainControl()
        self.nvmain.range = self.mem_ranges[0]
        self.nvmain.nvmain_config = 'ext/NVMain/Config/PCM_ISSCC_2012_4GB.config'
        
        # Wire connections
        # TrafficGen -> Cache -> NVMain
        self.traffic_gen.port = self.metadata_cache.port
        self.metadata_cache.nvmain_port = self.nvmain.port

# Create system
import sys
import os

if len(sys.argv) < 2:
    print("Usage: gem5.opt thoth_benchmark.py <benchmark>")
    print("Benchmarks: hashmap, btree, rbtree, swap")
    sys.exit(1)

benchmark = sys.argv[1]

if benchmark not in BENCHMARK_PARAMS:
    print(f"Error: Unknown benchmark '{benchmark}'")
    print(f"Available: {', '.join(BENCHMARK_PARAMS.keys())}")
    sys.exit(1)

params = BENCHMARK_PARAMS[benchmark]
print(f"=== Thoth System with {benchmark.upper()} Benchmark ===")
print(f"Description: {params['description']}")
print(f"Parameters: burst_size={params['burst_size']}, interval={params['burst_interval']}")

# Instantiate system
root = Root(full_system=False)
root.system = ThothBenchmarkSystem(benchmark, params)

# Instantiate
m5.instantiate()

print(f"\nBeginning simulation with {benchmark} metadata pattern...")
exit_event = m5.simulate()

print(f"\nExiting @ tick {m5.curTick()} because {exit_event.getCause()}")
print("\n=== PCB Statistics ===")
print(f"Total Partial Writes: {root.system.metadata_cache.pcb_total_partials.value}")
print(f"Coalesced Blocks: {root.system.metadata_cache.pcb_coalesced_blocks.value}")
print(f"Overflow to PLUB: {root.system.metadata_cache.pcb_overflows.value}")
print(f"PCB Flushes: {root.system.metadata_cache.pcb_flushes.value}")
print(f"NVM Writes: {root.system.metadata_cache.nvm_writes.value}")

# Calculate efficiency
if root.system.metadata_cache.pcb_total_partials.value > 0:
    efficiency = (root.system.metadata_cache.pcb_coalesced_blocks.value / 
                  root.system.metadata_cache.pcb_total_partials.value) * 100
    print(f"Coalescing Efficiency: {efficiency:.2f}%")
    
    # Write amplification
    expected_writes = (root.system.metadata_cache.pcb_total_partials.value * 8) / 64
    write_amp = root.system.metadata_cache.nvm_writes.value / expected_writes if expected_writes > 0 else 0
    print(f"Write Amplification: {write_amp:.3f}")
    
    # Traffic reduction
    reduction = root.system.metadata_cache.pcb_total_partials.value / root.system.metadata_cache.nvm_writes.value if root.system.metadata_cache.nvm_writes.value > 0 else 0
    print(f"Traffic Reduction: {reduction:.2f}x")
else:
    print("WARNING: No partial writes detected!")

