# Installation Guide

## Quick Setup (5 minutes)

### 1. Install gem5

```bash
# Clone gem5 (if you don't have it)
git clone https://github.com/gem5/gem5.git
cd gem5
git checkout v24.1.0.1

# Install dependencies
sudo apt-get update
sudo apt-get install build-essential git m5 scons zlib1g zlib1g-dev \
    libprotobuf-dev protobuf-compiler libgoogle-perftools-dev \
    python3-dev python3-pip libboost-all-dev pkg-config

pip3 install matplotlib numpy
```

### 2. Install NVMain

```bash
cd gem5/ext
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ../..
```

### 3. Install Thoth Implementation

```bash
# Clone this repository
git clone https://github.com/arunmm8335/thoth-implementation.git
cd thoth-implementation

# Set your gem5 path
export GEM5_ROOT=/path/to/your/gem5

# Copy implementation files
cp -r src/* $GEM5_ROOT/src/
cp -r configs/* $GEM5_ROOT/configs/
cp *.py $GEM5_ROOT/

# Copy benchmarks
cp -r benchmarks $GEM5_ROOT/
```

### 4. Build gem5

```bash
cd $GEM5_ROOT
scons build/RISCV/gem5.opt -j$(nproc)
```

Build time: ~10-30 minutes depending on your CPU.

### 5. Verify Installation

```bash
# Test run
./build/RISCV/gem5.opt configs/example/thoth_full_demo.py

# Check results
grep "pcbCoalescedBlocks" m5out/stats.txt
# Should show: system.metadata_cache.pcbCoalescedBlocks  <number>
```

## What Gets Installed

```
$GEM5_ROOT/
├── src/
│   ├── mem/security/             # PCB implementation (NEW)
│   │   ├── metadata_cache.{hh,cc}
│   │   └── metadata_traffic_gen.{hh,cc}
│   ├── mem/nvmain_control.*      # NVMain integration (NEW)
│   └── dev/security/             # AES-CTR engine (NEW)
├── configs/example/
│   ├── thoth_full_demo.py        # System config (NEW)
│   └── thoth_benchmark.py        # Benchmark runner (NEW)
├── benchmarks/thoth_workloads/   # Real benchmarks (NEW)
├── run_experiments.py            # Automation (NEW)
├── run_benchmarks.py             # Automation (NEW)
└── ext/NVMain/                   # PCM simulator (REQUIRED)
```

## Running Experiments

```bash
cd $GEM5_ROOT

# Synthetic experiments (18 configs)
./run_experiments.py

# Real benchmarks (4 workloads)
# First compile benchmarks
cd benchmarks/thoth_workloads
make
cd ../..

# Run all benchmarks
./run_benchmarks.py
```

## Generate Plots

```bash
# Synthetic plots
./plot_results_corrected.py
# Output: experiment_results/plots/

# Benchmark plots
./plot_benchmark_results.py
# Output: benchmark_results/
```

## Troubleshooting

### Build fails with "NVMain not found"
```bash
cd $GEM5_ROOT/ext
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..
scons build/RISCV/gem5.opt -j$(nproc)
```

### "No module named matplotlib"
```bash
pip3 install matplotlib numpy
```

### Statistics all zeros
Check port connection in config file:
```python
# Must have this line:
system.traffic_gen.port = system.metadata_cache.port
```

### Permission errors during copy
```bash
# Add sudo if needed
sudo cp -r src/* $GEM5_ROOT/src/
# Or change ownership
sudo chown -R $USER:$USER $GEM5_ROOT
```

## Next Steps

After installation:

1. **Test**: `./build/RISCV/gem5.opt configs/example/thoth_full_demo.py`
2. **Experiment**: `./run_experiments.py`
3. **Benchmark**: `./run_benchmarks.py`
4. **Visualize**: `./plot_results_corrected.py`
5. **Analyze**: Check `docs/EXPERIMENT_REPORT.md`

## Support

- Issues: https://github.com/arunmm8335/thoth-implementation/issues
- Documentation: See `docs/` directory
- gem5 help: https://www.gem5.org/documentation/
