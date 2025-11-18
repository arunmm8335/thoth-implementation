# NVMain Setup Guide for Thoth Implementation

## ⚠️ Important: NVMain Required

This repository **requires NVMain** to be installed in the `ext/` directory. NVMain is a cycle-accurate non-volatile memory simulator that provides the PCM backend for the Thoth implementation.

## Why NVMain is Not Included

NVMain is a separate project maintained by SEAL-UCSB and is **not included** in this fork for the following reasons:

1. **License Compatibility**: NVMain has its own license
2. **Repository Size**: Keeps this repo lightweight
3. **Version Control**: Allows users to choose NVMain version
4. **Upstream Updates**: Users can pull latest NVMain updates independently

## 🚀 Quick Installation

```bash
cd ext/
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..
```

**That's it!** gem5 will automatically detect and integrate NVMain.

## 📋 Step-by-Step Installation

### 1. Navigate to ext directory

```bash
cd /path/to/gem5-CXL-thoth-implementation
cd ext/
```

### 2. Clone NVMain

```bash
git clone https://github.com/SEAL-UCSB/NVMain.git
```

### 3. Verify installation

```bash
ls ext/NVMain/
# Should show: Config/ DataEncoders/ Decoders/ Endurance/ MemControl/ NVM/ nvmain.cpp nvmain.h ...
```

### 4. Rebuild gem5

```bash
cd ..
scons build/RISCV/gem5.opt -j$(nproc)
```

## ✅ Verification

### Check that NVMain is integrated

```bash
# Build should complete without errors
scons build/RISCV/gem5.opt -j$(nproc)

# Run a test simulation
./build/RISCV/gem5.opt configs/example/thoth_full_demo.py

# Check for NVMain in output
grep -i "nvmain" m5out/config.ini
```

Expected output:
```
type=NVMainControl
nvmain_config=ext/NVMain/Config/PCM_ISSCC_2012_4GB.config
```

## 🔧 Configuration Files Used

This implementation uses the following NVMain configurations:

- **PCM Config**: `ext/NVMain/Config/PCM_ISSCC_2012_4GB.config`
  - **Read Latency (tRCD)**: 150ns
  - **Write Latency (tWR)**: 500ns
  - **Capacity**: 4GB (simulated)
  - **Address Range**: 8GB-12GB in system memory map

## 🐛 Troubleshooting

### Error: "NVMain not found"

```bash
# Symptom
scons: *** [build/RISCV/mem/nvmain_control.o] Error 1

# Solution
cd ext/
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..
scons build/RISCV/gem5.opt -j$(nproc)
```

### Error: "nvmain_config file not found"

```bash
# Symptom
fatal: Unable to open config file: ext/NVMain/Config/PCM_ISSCC_2012_4GB.config

# Solution - Verify NVMain installation
ls ext/NVMain/Config/PCM_ISSCC_2012_4GB.config

# If missing, re-clone NVMain
rm -rf ext/NVMain
cd ext/
git clone https://github.com/SEAL-UCSB/NVMain.git
cd ..
```

### Error: Build fails with linker errors

```bash
# Symptom
undefined reference to `NVM::NVMainRequest`

# Solution - Clean and rebuild
scons --clean
scons build/RISCV/gem5.opt -j$(nproc)
```

## 📝 What Files Depend on NVMain

The following files in this repository integrate with NVMain:

1. **src/mem/nvmain_control.hh**
   - Header for NVMain integration
   - Defines NVMainControl SimObject

2. **src/mem/nvmain_control.cc**
   - Implementation of NVMain controller
   - Handles memory requests to PCM
   - Implements timing models (150ns read, 500ns write)

3. **src/mem/SConscript**
   - Build script that includes NVMain
   - Links NVMain library during compilation

4. **configs/example/thoth_full_demo.py**
   - System configuration that instantiates NVMainControl
   - Sets config file path: `nvmain_config='ext/NVMain/Config/PCM_ISSCC_2012_4GB.config'`

## 🔍 Checking Integration Status

### Verify NVMain in gem5 build

```bash
# Check if NVMain objects are built
ls build/RISCV/ext/NVMain/

# Check gem5 binary includes NVMain
nm build/RISCV/gem5.opt | grep -i nvmain | head -5
```

### Test simulation with NVMain

```bash
# Run quick test
./build/RISCV/gem5.opt configs/example/thoth_full_demo.py

# Check statistics show NVMain activity
grep "nvmWrites" m5out/stats.txt
# Should show: system.metadata_cache.nvmWrites    XXX
```

## 🌐 NVMain Resources

- **GitHub**: https://github.com/SEAL-UCSB/NVMain
- **Documentation**: See ext/NVMain/README after cloning
- **Paper**: "NVMain: An Architectural-Level Main Memory Simulator for Emerging Non-volatile Memories" (ISCA 2012)

## ⚙️ Alternative: Using Different NVMain Versions

If you need a specific NVMain version:

```bash
cd ext/
git clone https://github.com/SEAL-UCSB/NVMain.git
cd NVMain
git checkout <specific-commit-or-tag>
cd ../..
scons build/RISCV/gem5.opt -j$(nproc)
```

## 📦 What's Included in This Repository

✅ **Included**:
- Thoth PCB implementation (`src/mem/security/`)
- NVMain integration code (`src/mem/nvmain_control.*`)
- System configurations (`configs/example/thoth_*.py`)
- Benchmarks (`benchmarks/thoth_workloads/`)
- Experiment automation (`run_*.py`)
- Documentation

❌ **Not Included** (requires manual setup):
- NVMain source code (`ext/NVMain/`)

## 🔄 Keeping NVMain Updated

To update NVMain to latest version:

```bash
cd ext/NVMain
git pull origin master
cd ../..
scons --clean
scons build/RISCV/gem5.opt -j$(nproc)
```

## 📧 Support

If you encounter issues with NVMain setup:

1. **Check this guide first**
2. **Verify NVMain installation**: `ls ext/NVMain/`
3. **Check NVMain documentation**: `ext/NVMain/README`
4. **Open an issue**: Include error messages and `ls ext/` output

## ✅ Quick Checklist

Before running simulations, verify:

- [ ] NVMain cloned to `ext/NVMain/`
- [ ] Config file exists: `ext/NVMain/Config/PCM_ISSCC_2012_4GB.config`
- [ ] gem5 builds without errors
- [ ] Test simulation runs successfully
- [ ] Statistics show NVMain activity (`grep nvmWrites m5out/stats.txt`)

---

**Status**: Once NVMain is installed, all experiments will run successfully! ✅
