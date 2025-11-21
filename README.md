# Thoth: PCB Coalescing Implementation for gem5

**Implementation of Thoth secure metadata architecture from HPCA 2023.**

> **Thoth: Bridging the Gap Between Persistently Secure Memories and Memory Interfaces of Emerging NVMs**
> *IEEE HPCA 2023*

## Overview

This repository contains the implementation files for adding Thoth's **PCB (Partial Coalescing Buffer)** architecture to the gem5 simulator. It is designed to serve as an extension or patch for an existing gem5 installation.

### Key Features Implemented
* **PCB Coalescing:** Aggregation of 8-byte metadata writes into 64-byte blocks.
* **PUB Overflow Handling:** Management for uncoalesced writes.
* **ADR Flush:** Periodic 10 ms Asynchronous DRAM Refresh flush, matching paper specifications.
* **NVMain Integration:** Linked with PCM backend (150 ns read, 500 ns write latency).
* **Performance Metrics:** Tracking of overflow rate, write amplification, and PUB overhead.
* **Comprehensive Evaluation:** Scripts included for synthetic and real workload testing.

---

## Results Summary

| Metric | Value |
| :--- | :--- |
| **Coalescing Efficiency** | 99.4% - 100% |
| **Write Amplification** | 0.064 - 0.320 |
| **Traffic Reduction** | 25× - 125× |
| **NVM Writes Saved** | 96.8% - 99.2% |

---

## Quick Start

### Prerequisites
You need a working gem5 installation (v24.1.0.1 is recommended).

1.  **Setup gem5:**
    ```bash
    # Clone gem5 v24.1.0.1
    git clone [https://github.com/gem5/gem5.git](https://github.com/gem5/gem5.git)
    cd gem5
    git checkout v24.1.0.1
    ```

2.  **Install Dependencies:**
    ```bash
    sudo apt-get install build-essential git m5 scons zlib1g zlib1g-dev \
        libprotobuf-dev protobuf-compiler libgoogle-perftools-dev \
        python3-dev python3-pip libboost-all-dev
    ```

### Installation

1.  **Clone this repository:**
    ```bash
    git clone [https://github.com/arunmm8335/thoth-implementation.git](https://github.com/arunmm8335/thoth-implementation.git)
    cd thoth-implementation
    ```

2.  **Copy implementation files to your gem5 root:**
    ```bash
    export GEM5_ROOT=/path/to/gem5
    cp -r src/* $GEM5_ROOT/src/
    cp -r configs/* $GEM5_ROOT/configs/
    ```

3.  **Install NVMain into gem5:**
    ```bash
    cd $GEM5_ROOT/ext
    git clone [https://github.com/SEAL-UCSB/NVMain.git](https://github.com/SEAL-UCSB/NVMain.git)
    ```

4.  **Build gem5 (RISC-V target):**
    ```bash
    cd $GEM5_ROOT
    scons build/RISCV/gem5.opt -j$(nproc)
    ```

---

## Running Experiments

This repository includes automation scripts to replicate the paper's results.

1.  **Copy automation scripts to GEM5 root:**
    ```bash
    cp /path/to/thoth-implementation/*.py $GEM5_ROOT/
    cd $GEM5_ROOT
    ```

2.  **Run Synthetic Experiments (18 configurations):**
    ```bash
    ./run_experiments.py
    ```

3.  **Run Benchmark Suite (4 workloads):**
    ```bash
    ./run_benchmarks.py
    ```

4.  **Generate Plots:**
    ```bash
    ./plot_results_corrected.py
    ./plot_benchmark_results.py
    ```

---

## Repository Structure

```text
thoth-implementation/
├── src/
│   ├── mem/security/                 # PCB implementation
│   ├── mem/nvmain_control.* # NVMain integration
│   └── dev/security/                 # AES-CTR generator
├── configs/example/                  # System configuration examples
├── benchmarks/thoth_workloads/       # Benchmark programs
├── experiment_results/               # Output directory for experiments
├── benchmark_results/                # Output directory for benchmarks
├── docs/                             # Detailed Documentation
├── run_experiments.py                # Automation script (Synthetic)
├── run_benchmarks.py                 # Automation script (Real Benchmarks)
├── plot_results_corrected.py         # Plotting script
└── plot_benchmark_results.py         # Plotting script

```
---

## Architecture Overview

### PCB (Partial Coalescing Buffer)
The PCB aggregates 8-byte metadata writes into 64-byte blocks before transferring them to NVM.
* **Tracks:** Partial updates using an 8-bit `validMask`.
* **Accumulates:** 64-byte blocks.
* **Flushes:** On full completion or periodic ADR flush (10 ms).

### Performance Metrics Definitions
```python
# Write Amplification
write_amp = nvmWrites / ((pcbTotalPartials * 8) / 64)

# Overflow Rate  
overflow_rate = (pcbOverflows / pcbTotalPartials) * 100

# PUB Overhead
pub_overhead = (pubPartials / pcbTotalPartials) * 100
```
---
## Experiments

### Synthetic Experiments (18 configurations)
The framework supports comprehensive synthetic testing varying the following parameters:
* **Burst Size:** Variation in the number of back-to-back requests.
* **Burst Interval:** Time between bursts.
* **Inter-request Latency:** Fine-grained timing adjustments.
* **Mixed Workloads:** Various read/write ratios.

### Real Benchmarks (4 workloads)
* **Hashmap:** Standard key-value insertion and lookups.
* **B-Tree:** Database indexing structure operations.
* **Red-Black Tree:** Balanced tree insertions.
* **Array Swap:** Worst-case scenario for metadata updates.

---

## Validation Against HPCA 2023

Detailed verification is available in `docs/PAPER_VERIFICATION.md`.

| Aspect | Paper | Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Coalescing** | 8B → 64B | 8B → 64B | Match |
| **Efficiency** | 95–99% | 99.4–100% | Match |
| **Write Amp** | ~0.1–0.3 | 0.064–0.320 | Match |
| **ADR Flush** | 10 ms | 10 ms | Match |
| **PUB** | Implemented | Implemented | Match |
| **Backend** | PCM | NVMain | Match |

---

## Configuration Parameters

Key configuration snippets for setting up the environment:

### MetadataCache (PCB)
```python
cache = MetadataCache()
cache.num_sets = 4096
cache.num_ways = 4
cache.block_size = '64B'
cache.pcb_capacity = 256
cache.flush_interval = '10ms'
```
---

## MetadataTrafficGen
```python
gen = MetadataTrafficGen()
gen.burst_size = 250
gen.burst_interval = '1ms'
gen.request_latency = '4us'
```
## NVMain PCM
```python

nvm = NVMainControl()
nvm.tRCD = '150ns'
nvm.tWR = '500ns'
nvm.nvmain_config = 'ext/NVMain/Config/PCM_ISSCC_2012_4GB.config'
```
