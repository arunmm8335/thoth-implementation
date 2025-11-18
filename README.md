# Thoth: PCB Coalescing Implementation for gem5

[![gem5](https://img.shields.io/badge/gem5-v24.1.0.1-green.svg)](https://github.com/gem5/gem5)
[![Paper](https://img.shields.io/badge/Paper-HPCA%202023-orange.svg)](https://ieeexplore.ieee.org/document/10071045)
[![License](https://img.shields.io/badge/License-BSD-blue.svg)](LICENSE)

**Implementation of Thoth secure metadata architecture from HPCA 2023 paper.**

> *"Thoth: Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs"*  
> IEEE HPCA 2023

## 🎯 What is This?

This repository contains **only the implementation files** for adding Thoth's PCB (Partial Coalescing Buffer) architecture to gem5 simulator. It's designed to be a **patch/addon** to an existing gem5 installation.

### Key Features Implemented

✅ **PCB Coalescing**: 8B → 64B metadata block coalescing (99.4-100% efficiency)  
✅ **PLUB Overflow**: Handles uncoalesced writes when PCB is full  
✅ **10ms ADR Flush**: Periodic cache flush matching paper specification  
✅ **NVMain Integration**: PCM backend with 150ns/500ns read/write latencies  
✅ **Performance Formulas**: Overflow rate, write amplification, PLUB overhead  
✅ **Comprehensive Evaluation**: 18 synthetic + 4 real benchmark experiments  

## 📊 Results

| Metric | Value |
|--------|-------|
| **Coalescing Efficiency** | 99.4% - 100% |
| **Write Amplification** | 0.064 - 0.320 |
| **Traffic Reduction** | 25× - 125× |
| **NVM Writes Saved** | 96.8% - 99.2% |

## 🚀 Quick Start

### Prerequisites

You need an existing gem5 installation. If you don't have one:

```bash
# Clone gem5 v24.1.0.1
git clone https://github.com/gem5/gem5.git
cd gem5
git checkout v24.1.0.1

# Install dependencies
sudo apt-get install build-essential git m5 scons zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libgoogle-perftools-dev \
    python3-dev python3-pip libboost-all-dev
```

### Installation

```bash
# 1. Clone this repository
git clone https://github.com/arunmm8335/thoth-implementation.git
cd thoth-implementation

# 2. Copy files to your gem5 installation
export GEM5_ROOT=/path/to/your/gem5
cp -r src/* $GEM5_ROOT/src/
cp -r configs/* $GEM5_ROOT/configs/

# 3. Install NVMain in gem5 (required for PCM backend)
cd $GEM5_ROOT/ext
git clone https://github.com/SEAL-UCSB/NVMain.git
cd $GEM5_ROOT

# 4. Build gem5 with RISCV target
scons build/RISCV/gem5.opt -j$(nproc)
```

### Run Experiments

```bash
# Copy automation scripts
cp /path/to/thoth-implementation/*.py $GEM5_ROOT/

# Run synthetic experiments (18 configurations)
cd $GEM5_ROOT
./run_experiments.py

# Run benchmark suite (4 workloads)
./run_benchmarks.py

# Generate plots
./plot_results_corrected.py
./plot_benchmark_results.py
```

## 📁 What's Included

```
thoth-implementation/
├── src/
│   ├── mem/security/                   # PCB Implementation
│   │   ├── metadata_cache.hh           # Cache with PCB coalescing
│   │   ├── metadata_cache.cc
│   │   ├── metadata_traffic_gen.hh     # Traffic generator
│   │   └── metadata_traffic_gen.cc
│   ├── mem/
│   │   ├── nvmain_control.hh           # NVMain PCM integration
│   │   └── nvmain_control.cc
│   └── dev/security/
│       ├── aes_ctr_generator.hh        # AES-CTR encryption
│       └── aes_ctr_generator.cc
├── configs/example/
│   ├── thoth_full_demo.py              # Complete system config
│   └── thoth_benchmark.py              # Benchmark runner
├── benchmarks/thoth_workloads/         # Real benchmark programs
│   ├── hashmap.c                       # Hash table workload
│   ├── btree.c                         # B-tree workload
│   ├── rbtree.c                        # Red-black tree
│   ├── swap.c                          # Array swap (worst case)
│   └── Makefile
├── run_experiments.py                  # Automation script
├── run_benchmarks.py                   # Benchmark automation
├── plot_results_corrected.py           # Synthetic plots
├── plot_benchmark_results.py           # Benchmark plots
├── experiment_results/                 # Pre-run results
│   └── plots/                          # 5 publication plots
├── benchmark_results/                  # Pre-run benchmarks
│   └── *.png                           # 6 benchmark plots
└── docs/                               # Documentation
    ├── PAPER_VERIFICATION.md
    ├── PCB_IMPLEMENTATION.md
    ├── EXPERIMENT_REPORT.md
    └── ...
```

## 🔧 Architecture Overview

### PCB (Partial Coalescing Buffer)

The PCB coalesces 8-byte metadata writes into 64-byte cache blocks before writing to NVM:

```
Incoming Partials (8B each) ──→ PCB (256 entries) ──→ Coalesced Blocks (64B) ──→ NVMain PCM
                                      │
                                      ├─ validMask: Tracks which 8B slots are filled
                                      ├─ data[64B]: Accumulates partial writes
                                      └─ Flushes every 10ms (ADR timing)
```

**Key Mechanisms:**
- **Address-based coalescing**: Partials with same base address (aligned to 64B) merge into same PCB entry
- **validMask bitmap**: 8-bit mask tracks which of 8 slots (8B each) are filled
- **Full block detection**: When validMask == 0xFF, block is complete and written to NVM
- **10ms periodic flush**: Timer-based flush for ADR persistence guarantee

### Performance Formulas

```python
# Write Amplification
write_amp = nvmWrites / ((pcbTotalPartials × 8) / 64)

# Overflow Rate  
overflow_rate = (pcbOverflows / pcbTotalPartials) × 100

# PLUB Overhead
plub_overhead = (plubPartials / pcbTotalPartials) × 100
```

## 📈 Experiments Included

### Synthetic Experiments (18 configs)

1. **Burst Size Variation**: Small (25) to Huge (400 requests/burst)
2. **Burst Interval**: Fast (500µs) to Lazy (10ms between bursts)
3. **Request Latency**: Dense (1µs) to Very Sparse (50µs between requests)
4. **Mixed Workloads**: Low/Medium/High/Bursty load patterns

### Real Benchmarks (4 workloads)

1. **Hashmap**: 100K operations, random access, high update rate
2. **B-Tree**: 50K insertions, sequential with moderate locality
3. **RB-Tree**: 50K operations with tree rebalancing
4. **Array Swap**: 25K swaps, contiguous access (worst case per paper)

## 🔍 Validation Against Paper

| Aspect | Paper (HPCA 2023) | This Implementation | Status |
|--------|-------------------|---------------------|--------|
| Coalescing | 8B → 64B | 8B → 64B | ✅ Match |
| Efficiency | 95-99% | 99.4-100% | ✅ Match |
| Write Amp | ~0.1-0.3 | 0.064-0.320 | ✅ Match |
| ADR Flush | 10ms | 10ms | ✅ Match |
| PLUB | Overflow path | Implemented | ✅ Match |
| PCM Backend | NVMain | NVMain | ✅ Match |

See `docs/PAPER_VERIFICATION.md` for detailed comparison.

## 🛠️ Configuration Parameters

### MetadataCache (PCB)
```python
cache = MetadataCache()
cache.num_sets = 4096           # 4K sets
cache.num_ways = 4              # 4-way associative
cache.block_size = '64B'        # Cache line size
cache.pcb_capacity = 256        # Max PCB entries
cache.flush_interval = '10ms'   # ADR flush timing
```

### MetadataTrafficGen
```python
gen = MetadataTrafficGen()
gen.burst_size = 250            # Requests per burst
gen.burst_interval = '1ms'      # Time between bursts
gen.request_latency = '4us'     # Inter-request time
```

### NVMain PCM
```python
nvm = NVMainControl()
nvm.tRCD = '150ns'             # Read latency
nvm.tWR = '500ns'              # Write latency
nvm.nvmain_config = 'ext/NVMain/Config/PCM_ISSCC_2012_4GB.config'
```

## 📚 Documentation

- **[PAPER_VERIFICATION.md](docs/PAPER_VERIFICATION.md)** - Validation against HPCA 2023 paper
- **[PCB_IMPLEMENTATION.md](docs/PCB_IMPLEMENTATION.md)** - Technical implementation details
- **[EXPERIMENT_REPORT.md](docs/EXPERIMENT_REPORT.md)** - Comprehensive results analysis
- **[COMPLETE_PACKAGE.md](docs/COMPLETE_PACKAGE.md)** - Full package overview
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Quick commands and tips

## 🔗 Integration with gem5

This implementation integrates with gem5's memory system:

1. **Traffic Generator** → Creates metadata write traffic
2. **MetadataCache** → Intercepts writes, performs PCB coalescing
3. **NVMain** → Receives coalesced 64B blocks for PCM write
4. **AES-CTR** → Provides encrypted metadata (optional)

Connection example in config:
```python
system.traffic_gen.port = system.metadata_cache.port
system.metadata_cache.nvm_port = system.nvmain.port
```

## 🎓 Citation

If you use this implementation, please cite:

```bibtex
@inproceedings{thoth-hpca23,
  title={Thoth: Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs},
  booktitle={IEEE HPCA},
  year={2023},
  doi={10.1109/HPCA56546.2023.10071045}
}

@misc{thoth-gem5-implementation,
  author = {Arun M M},
  title = {Thoth PCB Coalescing Implementation for gem5},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/arunmm8335/thoth-implementation}
}
```

## ⚠️ Requirements

- **gem5**: v24.0.0.0 or newer (tested on v24.1.0.1)
- **NVMain**: Must be installed in `$GEM5_ROOT/ext/NVMain/`
- **Target**: RISCV (can be adapted to X86/ARM)
- **Python**: 3.8+ with matplotlib, numpy

## 🐛 Troubleshooting

### "NVMain not found" during build
```bash
cd $GEM5_ROOT/ext
git clone https://github.com/SEAL-UCSB/NVMain.git
```

### Statistics showing zero
Verify port connection in config:
```python
system.traffic_gen.port = system.metadata_cache.port  # Must be connected
```

### Python module errors
```bash
pip3 install matplotlib numpy
```

## 📝 License

This implementation is released under the BSD 3-Clause License, matching gem5's license.

## 👤 Author

**Arun M M**  
GitHub: [@arunmm8335](https://github.com/arunmm8335)

## 🙏 Acknowledgments

- **gem5 Simulator** - Computer architecture simulation framework
- **NVMain** - Non-volatile memory simulator
- **Thoth Paper Authors** - Original architecture design (HPCA 2023)

## 📧 Contact

For questions or issues:
- Open an issue on GitHub
- Check documentation in `docs/` directory
- Review `PAPER_VERIFICATION.md` for implementation details

---

**Status**: ✅ Validated against HPCA 2023 paper | Complete implementation with results
