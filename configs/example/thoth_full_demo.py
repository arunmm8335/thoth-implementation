"""
Complete End-to-End Thoth Demo
Integrates: Traffic Generator → Metadata Cache → NVMain

This demonstrates the full flow:
1. MetadataTrafficGen generates burst traffic (250 requests/burst @ 1ms intervals)
2. Metadata writes go to MetadataCache (4-way set-associative, 1MB)
3. Cache evictions flow to write queue
4. NVMain PCM backend for persistence

Run with: ./build/RISCV/gem5.opt configs/example/thoth_full_demo.py
"""

import m5
from m5.objects import *

# Create system
system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('8GB')]

# Create memory bus
system.membus = SystemXBar()

# System port
system.system_port = system.membus.cpu_side_ports

# Create Metadata Traffic Generator (burst pattern: 50 requests/burst, 1ms apart)
system.traffic_gen = MetadataTrafficGen(
    start_addr=0x100000000,      # Start at 4GB
    end_addr=0x100100000,        # 1MB range
    burst_size=50,               # 50 partials per burst (reduced to prevent routing table overflow)
    burst_interval='1ms',        # 1ms between bursts = 50k partials/sec
    request_latency='20us'       # 20us between requests in burst (slower to allow responses)
)

# Create Metadata Cache (1MB, 4-way set-associative with PCB coalescing)
system.metadata_cache = MetadataCache(
    num_sets=4096,               # 4096 sets
    num_ways=4,                  # 4-way associative
    block_size='64B',            # 64-byte cache lines
    access_latency='2ns',        # 2ns SRAM access
    write_queue_capacity=64      # 64-entry write queue for evictions
)

# Create AES-CTR Generator (for encryption context)
system.aes_gen = AESCTRGenerator(
    key_seed=0xDEADBEEFCAFEBABE,
    start_counter=1000,
    test_requests=0              # Don't self-generate, rely on traffic gen
)

# Create NVMain PCM backend for metadata persistence
system.nvmain = NVMainControl(
    nvmain_config='ext/NVMain/Config/PCM_ISSCC_2012_4GB.config',
    range=AddrRange('8GB', size='4GB')  # 8GB-12GB range for persistent metadata
)

# Simple memory for traffic generator working range (4GB-8GB)
system.mem_ctrl = SimpleMemory()
system.mem_ctrl.range = AddrRange(start='4GB', size='4GB')  # 4GB-8GB for active metadata

# Wire system:
# Traffic Gen → Cache → System Bus → Memory
# This makes cache actively intercept and process all metadata writes

# 1. Traffic Generator → Metadata Cache (RequestPort → ResponsePort)
#    Cache receives all metadata write requests and processes through PCB
system.traffic_gen.port = system.metadata_cache.port

# 2. Memory controller connects to system bus
system.mem_ctrl.port = system.membus.mem_side_ports

# 3. Cache → NVMain for PCB-coalesced evictions (64B blocks)
#    Coalesced blocks go directly to persistent storage
system.metadata_cache.nvmain_port = system.nvmain.port

# Note: Cache now actively intercepts all traffic from generator
# Writes go through: TrafficGen → Cache (PCB coalescing) → NVMain (evictions)

# Create root and instantiate
root = Root(full_system=False, system=system)
m5.instantiate()

print("=" * 80)
print("Thoth Full System Demo - Secure Metadata Architecture")
print("=" * 80)
print()
print("Traffic Generator:")
print(f"  - Address Range: 0x{int(system.traffic_gen.start_addr):X} - 0x{int(system.traffic_gen.end_addr):X}")
print(f"  - Burst Size: {int(system.traffic_gen.burst_size)} requests/burst")
print(f"  - Burst Interval: {system.traffic_gen.burst_interval}")
print(f"  - Request Rate: ~{int(system.traffic_gen.burst_size) * 1000} requests/sec")
print()
print("Metadata Cache with PCB:")
print(f"  - Configuration: {int(system.metadata_cache.num_sets)} sets × {int(system.metadata_cache.num_ways)} ways")
print(f"  - Total Capacity: {int(system.metadata_cache.num_sets) * int(system.metadata_cache.num_ways) * 64 // 1024} KB")
print(f"  - Access Latency: {system.metadata_cache.access_latency}")
print(f"  - PCB: 256 entries (coalesces 8B → 64B blocks)")
print(f"  - Flush Interval: 10ms (ADR timing)")
print()
print("NVMain Backend:")
print(f"  - Technology: PCM (Phase Change Memory)")
print(f"  - Range: {system.nvmain.range}")
print(f"  - Purpose: Persistent metadata storage (coalesced 64B blocks)")
print()
print("Starting simulation for 10ms...")
print("-" * 80)

# Run simulation for 10ms (should generate 10 bursts = 2500 requests)
exit_event = m5.simulate(10_000_000_000)  # 10ms in ticks

print()
print("-" * 80)
print(f"Simulation ended: {exit_event.getCause()}")
print()
print("Results written to m5out/stats.txt")
print()
print("Key statistics to check:")
print("  Traffic Generation:")
print("    - system.traffic_gen.requestsSent")
print("    - system.traffic_gen.burstsCompleted")
print("  Metadata Cache:")
print("    - system.metadata_cache.hits / misses / evictions")
print("  PCB Coalescing:")
print("    - system.metadata_cache.pcbCoalescedBlocks (full 64B blocks)")
print("    - system.metadata_cache.pcbPartialFlushes (incomplete blocks)")
print("    - system.metadata_cache.pcbOverflows (sent to PLUB)")
print("    - system.metadata_cache.pcbTotalPartials (total 8B partials)")
print("    - system.metadata_cache.pcbCoalescingRate (efficiency)")
print("  NVMain PCM:")
print("    - system.nvmain.numWrites (persistent writes)")
print()
print("=" * 80)
print("Demo Complete!")
print("=" * 80)
