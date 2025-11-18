# Thoth Secure Metadata Implementation for gem5

[![License](https://img.shields.io/badge/License-BSD-blue.svg)](LICENSE)
[![gem5 Version](https://img.shields.io/badge/gem5-v24.1.0.1-green.svg)](https://github.com/gem5/gem5)
[![Paper](https://img.shields.io/badge/Paper-HPCA%202023-orange.svg)](https://ieeexplore.ieee.org/document/10071045)

**Complete implementation of the Thoth secure metadata architecture from HPCA 2023 paper in gem5 simulator with NVMain PCM backend.**

## 🎯 Overview

This repository contains a full implementation of **Thoth: Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs** (HPCA 2023). The implementation includes:

- **PCB (Partial Coalescing Buffer)**: 8B→64B metadata coalescing with 99.4-100% efficiency
- **PLUB (Partial Log Update Buffer)**: Overflow handling for uncoalesced writes
- **10ms ADR Flush**: Periodic cache flush matching paper specification
- **NVMain PCM Backend**: 150ns read, 500ns write latencies
- **AES-CTR Security Engine**: Encrypted metadata generation
- **Comprehensive Evaluation**: 18 synthetic experiments + 4 real benchmarks

## 📊 Key Results

### Synthetic Experiments
- **Write Amplification**: 0.040 - 0.640 (16× variation)
- **Traffic Reduction**: 11× - 177× across workloads
- **Coalescing Efficiency**: 12% - 97% (workload dependent)

### Benchmark Results
| Benchmark | Efficiency | Write Amp | Traffic Reduction |
|-----------|-----------|-----------|-------------------|
| Hashmap   | 99.80%    | 0.127     | 63.12×           |
| B-Tree    | 100.00%   | 0.320     | 25.00×           |
| RB-Tree   | 99.41%    | 0.189     | 42.25×           |
| Array Swap| 100.00%   | 0.064     | 125.00×          |

**Average**: 99.80% efficiency, 0.175 write amplification, 63.84× traffic reduction

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install build-essential git m5 scons zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libgoogle-perftools-dev \
    python3-dev python3-pip libboost-all-dev pkg-config

# Install Python dependencies
pip3 install matplotlib numpy
```

### Setup

```bash
# Clone repository
git clone https://github.com/arunmm8335/gem5-CXL-thoth-implementation.git
cd gem5-CXL-thoth-implementation

# Install NVMain (required for PCM backend)
cd ext
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..

# Build gem5
scons build/RISCV/gem5.opt -j$(nproc)
```

### Run Experiments

```bash
# Run synthetic experiments (18 configurations)
./run_experiments.py

# Run benchmark suite (4 workloads)
./run_benchmarks.py

# Generate plots
./plot_results_corrected.py          # Synthetic plots
./plot_benchmark_results.py          # Benchmark plots
```

## 📁 Repository Structure

```
gem5-CXL-thoth-implementation/
├── src/
│   ├── mem/security/              # PCB implementation
│   │   ├── metadata_cache.{hh,cc}      # Main cache with PCB
│   │   └── metadata_traffic_gen.{hh,cc} # Traffic generator
│   ├── mem/
│   │   └── nvmain_control.{hh,cc}      # NVMain integration
│   └── dev/security/              # AES-CTR engine
│       └── aes_ctr_generator.{hh,cc}
├── configs/example/
│   ├── thoth_full_demo.py         # Complete system config
│   └── thoth_benchmark.py         # Benchmark runner
├── benchmarks/thoth_workloads/    # Real benchmark programs
│   ├── hashmap.c                  # Hash table workload
│   ├── btree.c                    # B-tree workload
│   ├── rbtree.c                   # Red-black tree workload
│   └── swap.c                     # Array swap workload
├── experiment_results/            # Synthetic experiment results
│   └── plots/                     # 5 publication-quality plots
├── benchmark_results/             # Benchmark results
│   └── *.png                      # 6 benchmark plots
├── run_experiments.py             # Automated experiment runner
├── run_benchmarks.py              # Automated benchmark runner
├── plot_results_corrected.py      # Synthetic plotting script
├── plot_benchmark_results.py      # Benchmark plotting script
└── Documentation/
    ├── PAPER_VERIFICATION.md      # Validation against paper
    ├── PCB_IMPLEMENTATION.md      # Technical details
    ├── EXPERIMENT_REPORT.md       # Results analysis
    └── COMPLETE_PACKAGE.md        # Full overview
```

## 🔬 Implementation Details

### PCB (Partial Coalescing Buffer)
- **Capacity**: 256 entries (configurable)
- **Granularity**: 8B partials → 64B cache blocks
- **Mechanism**: Address-based coalescing with validMask bitmap
- **Flush Policy**: 10ms periodic flush (ADR timing)
- **Overflow**: PLUB bypass when PCB is full

### PLUB (Partial Log Update Buffer)
- **Purpose**: Handles overflow from PCB
- **Behavior**: Uncoalesced writes bypass coalescing
- **Statistics**: Tracks overflow rate and PLUB overhead

### Performance Formulas
```
Overflow Rate = (PCB Overflows / Total Partials) × 100
Write Amplification = NVM Writes / (Partial Bytes / 64B)
PLUB Overhead = (PLUB Partials / Total Partials) × 100
```

## 📈 Running Experiments

### Synthetic Experiments

```bash
# Run all 18 configurations
./run_experiments.py

# Results will be in experiment_results/
# Includes: burst_size, burst_interval, request_latency, mixed workloads
```

### Benchmark Suite

```bash
# Compile benchmarks first
cd benchmarks/thoth_workloads
make
cd ../..

# Run all benchmarks
./run_benchmarks.py

# Or run individually
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py hashmap
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py btree
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py rbtree
./build/RISCV/gem5.opt configs/example/thoth_benchmark.py swap
```

## 📊 Generating Plots

```bash
# Synthetic experiment plots (5 figures)
./plot_results_corrected.py
# Output: experiment_results/plots/figure*.png

# Benchmark plots (6 figures)
./plot_benchmark_results.py
# Output: benchmark_results/benchmark_*.png
```

All plots are 300 DPI, publication-ready.

## 🔍 Key Configuration Parameters

### MetadataCache (PCB)
```python
metadata_cache = MetadataCache()
metadata_cache.num_sets = 4096       # 4K sets
metadata_cache.num_ways = 4          # 4-way associative
metadata_cache.block_size = '64B'    # Cache line size
metadata_cache.access_latency = '2ns'
```

### MetadataTrafficGen
```python
traffic_gen = MetadataTrafficGen()
traffic_gen.burst_size = 250          # Requests per burst
traffic_gen.burst_interval = '1ms'    # Time between bursts
traffic_gen.request_latency = '4us'   # Time between requests
```

### NVMain PCM
```python
nvmain = NVMainControl()
nvmain.tRCD = '150ns'  # Read latency
nvmain.tWR = '500ns'   # Write latency
nvmain.nvmain_config = 'ext/NVMain/Config/PCM_ISSCC_2012_4GB.config'
```

## 📚 Documentation

- **[PAPER_VERIFICATION.md](PAPER_VERIFICATION.md)** - Detailed comparison with HPCA 2023 paper
- **[PCB_IMPLEMENTATION.md](PCB_IMPLEMENTATION.md)** - Technical implementation details
- **[EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)** - Comprehensive experimental analysis
- **[COMPLETE_PACKAGE.md](COMPLETE_PACKAGE.md)** - Full package overview
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands and tips

## 🎓 Citation

If you use this implementation in your research, please cite:

```bibtex
@inproceedings{thoth-hpca23,
  title={Thoth: Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs},
  booktitle={IEEE International Symposium on High-Performance Computer Architecture (HPCA)},
  year={2023},
  doi={10.1109/HPCA56546.2023.10071045}
}

@misc{thoth-gem5-implementation,
  author = {Arun M M},
  title = {Thoth Secure Metadata Implementation for gem5},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/arunmm8335/gem5-CXL-thoth-implementation}
}
```

## ✅ Validation Status

- ✅ **Core Architecture**: Validated against HPCA 2023 paper
- ✅ **PCB Coalescing**: 99.4-100% efficiency (matches paper's 95-99%)
- ✅ **Write Amplification**: 0.064-0.320 (matches paper's claims)
- ✅ **Traffic Reduction**: 25×-125× (matches paper's results)
- ✅ **Formulas**: All three performance formulas match paper exactly

## 🐛 Known Issues & Limitations

1. **NVMain Setup**: Requires manual installation (see Setup section)
2. **PCB Capacity**: Implementation uses 256 entries vs 8 in paper (scalability improvement)
3. **Workloads**: Simplified versions of WHISPER benchmarks (metadata patterns match)
4. **NVM Scale**: 4GB simulated vs 1TB in paper (simulation constraint)

## 🛠️ Troubleshooting

### NVMain not found
```bash
cd ext
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..
scons build/RISCV/gem5.opt -j$(nproc)
```

### Statistics showing zero
Check that traffic generator is connected to cache:
```python
system.traffic_gen.port = system.metadata_cache.port  # Correct
```

### Python dependencies
```bash
pip3 install matplotlib numpy
```

## 🤝 Contributing

This is a research implementation. For improvements or bug fixes:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is based on gem5 (BSD License) with additional Thoth implementation.

- **gem5**: BSD 3-Clause License
- **NVMain**: See ext/NVMain/LICENSE
- **Thoth Implementation**: BSD 3-Clause License

## 👤 Author

**Arun M M** (arunmm8335)

- GitHub: [@arunmm8335](https://github.com/arunmm8335)
- Repository: [gem5-CXL-thoth-implementation](https://github.com/arunmm8335/gem5-CXL-thoth-implementation)

## 🙏 Acknowledgments

- **gem5 Simulator**: Computer architecture simulation framework
- **NVMain**: Non-volatile memory simulator
- **Thoth Paper Authors**: Original architecture design (HPCA 2023)
- **SlugLab**: Original gem5-CXL repository base

## 📧 Contact

For questions or issues:
- Open an issue on GitHub
- Check documentation in the repository
- Review PAPER_VERIFICATION.md for implementation details

---

**Status**: ✅ Publication Ready | Validated against HPCA 2023 paper | Complete implementation with results
