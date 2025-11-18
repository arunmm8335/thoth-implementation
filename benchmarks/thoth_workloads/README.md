# Thoth Benchmark Suite

This directory contains real workload benchmarks for evaluating the Thoth secure metadata architecture, matching the workloads used in the HPCA 2023 paper.

## Benchmarks

### 1. **Hashmap** (`hashmap.c`)
- **Description**: Hash table with chained collision resolution
- **Operations**: Insert, lookup, update with 8B metadata per entry
- **Workload Pattern**: Random access with frequent metadata updates
- **Characteristics**: Simulates database hash index operations

### 2. **B-Tree** (`btree.c`)
- **Description**: B-tree data structure (order 5)
- **Operations**: Insert and search with 8B metadata per key
- **Workload Pattern**: Sorted insertions with tree rebalancing
- **Characteristics**: Simulates database index operations

### 3. **Red-Black Tree** (`rbtree.c`)
- **Description**: Self-balancing binary search tree
- **Operations**: Insert with rotation and search, 8B metadata per node
- **Workload Pattern**: Balanced tree operations with metadata tracking
- **Characteristics**: Simulates in-memory data structure with security metadata

### 4. **Random Array Swap** (`swap.c`)
- **Description**: Exchanges elements between two contiguous arrays
- **Operations**: Random swap with metadata update for both elements
- **Workload Pattern**: Contiguous memory accesses with paired writes
- **Characteristics**: Tests worst-case scenario for coalescing (as noted in paper)

## Metadata Model

Each benchmark generates **8-byte partial writes** to simulate:
- **MAC (Message Authentication Code)**: 8B security metadata
- **Counter**: Version counter for replay protection
- **Integrity metadata**: Combined MAC/counter updates

These 8B partials are coalesced by the PCB (Partial Coalescing Buffer) into 64B cache blocks before writing to NVM.

## Compilation

```bash
cd benchmarks/thoth_workloads
make
```

This compiles all four benchmarks as static binaries.

**Requirements**: 
- GCC (for x86_64 native compilation)
- Or `riscv64-linux-gnu-gcc` for RISCV cross-compilation

## Running Individual Benchmarks

Run a specific benchmark with Thoth system:

```bash
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py hashmap
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py btree
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py rbtree
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py swap
```

## Running All Benchmarks

Automated script to run all benchmarks and generate report:

```bash
./run_benchmarks.py
```

**Output**:
- `benchmark_results/`: Directory with per-benchmark results
- `benchmark_results/all_results.json`: JSON data for all benchmarks
- `benchmark_results/BENCHMARK_REPORT.md`: Summary report with analysis

## Expected Metrics

Each benchmark reports:

| Metric | Description |
|--------|-------------|
| **Total Partial Writes** | Number of 8B metadata writes generated |
| **Coalesced Blocks** | Number of complete 64B blocks formed |
| **NVM Writes** | Actual writes to NVMain PCM backend |
| **PCB Flushes** | Number of 10ms ADR flush events |
| **Overflow to PLUB** | Partials that couldn't be coalesced |
| **Coalescing Efficiency** | (Coalesced / Total Partials) × 100% |
| **Write Amplification** | NVM Writes / Expected Writes |
| **Traffic Reduction** | Total Partials / NVM Writes |

## Comparison with Paper

### WHISPER Benchmarks
The paper uses benchmarks from the WHISPER suite [33]:
- Hashmap
- Ctree (cache-conscious tree)
- Btree
- RBtree

Our implementations are **simplified versions** that capture the essential access patterns of these workloads with 8B metadata writes.

### Transaction Size
Paper configuration: **128B transaction size**

Our benchmarks use **8B partial writes** coalesced into **64B blocks**, matching the paper's metadata granularity.

### Expected Results

From the paper (Figure 3, Section VI):
- **Coalescing Efficiency**: 95-99% across all benchmarks
- **Write Amplification**: 0.2-0.6 depending on workload
- **Traffic Reduction**: 8-50× fewer NVM writes

Our implementation should show similar trends, with:
- High efficiency for hashmap, btree, rbtree (sequential locality)
- Lower efficiency for swap (contiguous array access pattern)

## Architecture Details

### PCB (Partial Coalescing Buffer)
- **Size**: 256 entries (map-based)
- **Granularity**: 8B → 64B coalescing
- **Flush Period**: 10ms (ADR timing)
- **Full Block Action**: Immediate write to NVMain

### PLUB (Partial Log Update Buffer)
- **Purpose**: Overflow path when PCB is full
- **Behavior**: Uncoalesced writes bypass PCB
- **Size**: Configurable (107 entries per paper formula)

### NVMain PCM Backend
- **Read Latency**: 150ns
- **Write Latency**: 500ns
- **Capacity**: 4GB (8GB-12GB address range)

## Files

- `hashmap.c` - Hash table benchmark
- `btree.c` - B-tree benchmark
- `rbtree.c` - Red-black tree benchmark
- `swap.c` - Random array swap benchmark
- `Makefile` - Compilation rules
- `README.md` - This file

## Integration with Thoth System

The benchmarks integrate with:

1. **MetadataCache** (`src/mem/security/metadata_cache.{hh,cc}`)
   - Intercepts all memory writes to metadata region (8GB-12GB)
   - Performs PCB coalescing on 8B partials
   - Flushes to NVMain every 10ms

2. **NVMain** (`ext/NVMain/`)
   - PCM backend for persistent storage
   - Receives coalesced 64B blocks from cache

3. **Statistics** (`m5out/stats.txt`)
   - Tracks all PCB/PLUB/NVM metrics
   - Calculates performance formulas

## Future Enhancements

- [ ] Add Ctree benchmark (cache-conscious tree from WHISPER)
- [ ] Implement trace-driven simulation with real WHISPER traces
- [ ] Add multi-threaded versions of benchmarks
- [ ] Support 128B block size (Intel DCPMM granularity)
- [ ] Add stale metadata discard logic

## References

- **Thoth Paper**: "Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs" (HPCA 2023)
- **WHISPER Suite** [33]: Secure persistent memory benchmarks
- **gem5**: www.gem5.org
- **NVMain**: NVM simulator integrated with gem5
