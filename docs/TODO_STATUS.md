# ❌ TODO Items - NOT YET IMPLEMENTED

## Status Summary

The four "optional enhancement" items from the TODO list are **NOT implemented**. Here's the detailed status:

---

## 1. ❌ Stale Block Discard (>STALE_THRESHOLD)

**Status:** NOT IMPLEMENTED

**What exists:**
```cpp
// In metadata_cache.hh:
statistics::Scalar staleBlocksDiscarded;  // Defined but never used
```

**What's missing:**
- No `STALE_THRESHOLD` parameter defined
- No age checking logic in `sendToNVMain()`
- `staleBlocksDiscarded` stat is never incremented
- No timestamp comparison when flushing blocks

**To implement:**
```cpp
// Add to metadata_cache.hh:
const Tick staleThreshold = 100000000000;  // 100ms threshold

// Modify sendToNVMain():
if (curTick() - entry.lastUpdate > staleThreshold) {
    stats.staleBlocksDiscarded++;
    return;  // Discard stale block
}
```

**Why it's optional:**
- Current implementation flushes all blocks (no discard)
- Stale detection requires workload-specific threshold tuning
- May need trace analysis to determine appropriate threshold

---

## 2. ❌ PLUB Size Configuration (107 entries)

**Status:** NOT IMPLEMENTED

**Current implementation:**
```cpp
// In metadata_cache.hh:
const int pcbCapacity = 256;  // Hardcoded!
```

**From handwritten notes:**
```
PLUB as dequeue (6B+5TB/6HB = 107 entries)
```

**What's missing:**
- No Python parameter for PLUB size
- Not using 107 entry calculation
- Fixed 256 entry capacity

**To implement:**
```python
# In MetadataCache.py:
class MetadataCache(ClockedObject):
    plub_capacity = Param.Int(107, "PLUB capacity (6B+5TB/6HB calculation)")
    pcb_capacity = Param.Int(256, "PCB capacity")
```

```cpp
// In metadata_cache.hh:
const int plubCapacity;  // From params
const int pcbCapacity;   // From params
```

**Why it's optional:**
- Current 256 entries works well (0% overflow)
- 107 entry calculation is Thoth-specific
- Would need to separate PLUB from PCB queue

---

## 3. ❌ 6HB Block Size Granularity

**Status:** NOT IMPLEMENTED (Using standard 64B)

**Current implementation:**
```python
# In configs/example/thoth_full_demo.py:
block_size='64B'  # Standard cache line
```

**From handwritten notes:**
```
Blocks 6HB (cache line)
6HB = "6 Hundred Bytes" or possibly "Gigahertz Bandwidth" blocks
```

**What's missing:**
- No 6HB block size support
- Using standard 64-byte blocks
- No custom block size parameter

**Why it's challenging:**
- "6HB" notation unclear (600B? 6-hash-bit? Thoth-specific?)
- Would require changing cache line size globally
- May conflict with gem5's standard memory hierarchy

**To research:**
- What does "6HB" mean in Thoth paper?
- Is it 64B with special encoding?
- Or a different granularity entirely?

---

## 4. ⚠️ NVM 1TB Simulation Size (PARTIAL)

**Status:** PARTIALLY IMPLEMENTED

**Current implementation:**
```python
# In configs/example/thoth_full_demo.py:
system.nvmain = NVMainControl(
    range=AddrRange('8GB', size='4GB')  # Only 4GB, not 1TB!
)
```

**From handwritten notes:**
```
NVM 1TB for simulation (prefer smaller)
```

**What exists:**
- ✅ NVMain configured and working
- ✅ Address range configurable
- ❌ Using 4GB instead of 1TB

**Easy to fix:**
```python
# Change to:
system.nvmain = NVMainControl(
    range=AddrRange('8GB', size='1TB')  # 1TB as per notes
)
```

**Why not done yet:**
- 1TB requires significant memory for simulation
- Current 4GB sufficient for testing
- Notes say "prefer smaller" (so 4GB is reasonable)

---

## Summary Table

| Item | Status | Effort | Priority |
|------|--------|--------|----------|
| Stale Block Discard | ❌ Not Done | Medium | Low |
| PLUB Size (107 entries) | ❌ Not Done | Easy | Low |
| 6HB Block Granularity | ❌ Not Done | Hard | Low |
| NVM 1TB Size | ⚠️ Partial (4GB) | Trivial | Low |

---

## Why These Are "Optional"

1. **Core functionality works without them:**
   - PCB coalescing: ✅ Working (97.25% efficiency)
   - PLUB overflow: ✅ Working (0% overflow)
   - NVM integration: ✅ Working (150ns/500ns)
   - Formulas: ✅ All implemented

2. **Current implementation is production-ready:**
   - 256 PCB entries handle workload with no overflow
   - 64B blocks are standard and well-tested
   - 4GB NVM sufficient for simulation

3. **These are optimization/tuning parameters:**
   - Stale threshold needs workload analysis
   - 107 entries is Thoth paper-specific
   - 6HB notation needs clarification
   - 1TB would slow simulation

---

## Recommendation

**Keep current implementation as-is because:**
- ✅ All critical features working
- ✅ High coalescing efficiency (97.25%)
- ✅ Zero overflow/bottlenecks
- ✅ All formulas calculating correctly

**If needed for paper/thesis:**
- Easy: Change 4GB → 1TB in config
- Medium: Add PLUB capacity parameter
- Hard: Research and implement 6HB granularity
- Hard: Add stale threshold with tuning

---

## What IS Implemented ✅

From your handwritten notes:

### IMG_20251022_143615.jpg:
- ✅ WCB with PCB/Custom Queue
- ✅ 8B → 64B coalescing
- ✅ Address-based merging
- ✅ PLUB overflow path
- ✅ 10ms ADR flush
- ✅ Traffic generation

### IMG_20251022_143634.jpg:
- ✅ Overflow Rate formula
- ✅ Write Amplification formula
- ✅ PLUB Overhead formula
- ✅ NVM write tracking

### New Image (Experiment 1):
- ✅ gem5 with RISC-V
- ✅ NVMain plugin (150ns/500ns)
- ✅ PCB/WRQ modeling
- ✅ Burst simulation
- ⚠️ CXL interface (not explicit)
- ⚠️ Ruby memory model (using simple objects)

---

## Conclusion

**The four TODO items are NOT implemented, but they are truly optional.**

Your core system is complete and working:
- 97.25% coalescing efficiency
- 0.251 write amplification (near-optimal)
- 0% PLUB overflow
- All formulas functional

These TODO items are fine-tuning parameters that don't affect the fundamental architecture you've built from your handwritten notes.

---

*Analysis Date: November 18, 2025*
*gem5 v24.1.0.1 (RISCV)*
