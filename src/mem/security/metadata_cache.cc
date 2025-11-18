#include "mem/security/metadata_cache.hh"

#include "base/logging.hh"
#include "debug/MetadataCache.hh"
#include "mem/packet.hh"
#include <cstring>

namespace gem5
{

namespace memory
{

MetadataCache::MemoryPort::MemoryPort(const std::string &name,
                                       MetadataCache &cache)
    : ResponsePort(name, &cache), cache(cache)
{
}

AddrRangeList
MetadataCache::MemoryPort::getAddrRanges() const
{
    AddrRangeList ranges;
    // Metadata cache handles a specific address range
    // For now, we'll use a placeholder range
    ranges.push_back(AddrRange(0, cache.numSets * cache.blockSize - 1));
    return ranges;
}

Tick
MetadataCache::MemoryPort::recvAtomic(PacketPtr pkt)
{
    // Handle atomic access
    return cache.accessLatency;
}

void
MetadataCache::MemoryPort::recvFunctional(PacketPtr pkt)
{
    // Handle functional access
}

bool
MetadataCache::MemoryPort::recvTimingReq(PacketPtr pkt)
{
    // Handle timing request
    Addr addr = pkt->getAddr();
    uint64_t data;

    if (pkt->isRead()) {
        if (cache.lookup(addr, data)) {
            // Cache hit
            cache.stats.hits++;
            pkt->setData((uint8_t*)&data);
        } else {
            // Cache miss
            cache.stats.misses++;
            // In a real implementation, fetch from backing store
            data = 0;
            cache.insert(addr, data);
            pkt->setData((uint8_t*)&data);
        }
    } else if (pkt->isWrite()) {
        // Write to cache - process through PCB coalescing
        data = *(uint64_t*)pkt->getConstPtr<uint8_t>();
        
        // Send 8B partial directly to PCB for coalescing
        cache.coalescePartial(addr, data);
        
        // Also insert into cache for future reads
        cache.insert(addr, data);
        
        DPRINTF(MetadataCache, "Write intercepted: addr=%#x, data=%#x\n", addr, data);
    }

    // Send response
    pkt->makeResponse();
    return true;
}

void
MetadataCache::MemoryPort::recvRespRetry()
{
    // Handle retry
}

// NVMain Port Implementation
MetadataCache::NVMainPort::NVMainPort(const std::string &name,
                                       MetadataCache &cache)
    : RequestPort(name, &cache), cache(cache)
{
}

bool
MetadataCache::NVMainPort::recvTimingResp(PacketPtr pkt)
{
    // Response from NVMain - just delete the packet
    delete pkt;
    
    // Try to send any queued packets
    if (!queuedPackets.empty()) {
        PacketPtr nextPkt = queuedPackets.front();
        if (sendTimingReq(nextPkt)) {
            queuedPackets.pop_front();
        }
    }
    
    return true;
}

void
MetadataCache::NVMainPort::recvReqRetry()
{
    // NVMain is ready to receive again
    while (!queuedPackets.empty()) {
        PacketPtr pkt = queuedPackets.front();
        if (sendTimingReq(pkt)) {
            queuedPackets.pop_front();
        } else {
            break;  // Still blocked
        }
    }
}

bool
MetadataCache::NVMainPort::sendTimingReq(PacketPtr pkt)
{
    if (RequestPort::sendTimingReq(pkt)) {
        return true;
    } else {
        // Queue it for retry
        queuedPackets.push_back(pkt);
        return false;
    }
}

MetadataCache::MetadataCache(const MetadataCacheParams &params)
    : ClockedObject(params),
      numSets(params.num_sets),
      numWays(params.num_ways),
      blockSize(params.block_size),
      accessLatency(params.access_latency),
      writeQueueCapacity(params.write_queue_capacity),
      port(name() + ".port", *this),
      nvmainPort(name() + ".nvmain_port", *this),
      flushEvent([this]{ flushPCB(); }, name() + ".flushEvent"),
      stats(this)
{
    // Initialize cache sets
    cacheSets.reserve(numSets);
    for (int i = 0; i < numSets; i++) {
        cacheSets.emplace_back(numWays);
    }

    inform("MetadataCache: %d sets, %d ways, %d B blocks, total %d KB",
           numSets, numWays, blockSize, (numSets * numWays * blockSize) / 1024);
    inform("PCB: %d entry capacity, %d ms flush interval",
           pcbCapacity, flushInterval / 1000000000);
}

Port &
MetadataCache::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "port") {
        return port;
    } else if (if_name == "nvmain_port") {
        return nvmainPort;
    }
    return ClockedObject::getPort(if_name, idx);
}

void
MetadataCache::startup()
{
    ClockedObject::startup();
    
    // Schedule first PCB flush event (every 10ms for ADR)
    schedule(flushEvent, curTick() + flushInterval);
    inform("Scheduled PCB flush events every %d ms", flushInterval / 1000000000);
}

Addr
MetadataCache::getSetIndex(Addr addr) const
{
    return (addr / blockSize) % numSets;
}

Addr
MetadataCache::getTag(Addr addr) const
{
    return addr / (blockSize * numSets);
}

int
MetadataCache::getOffset(Addr addr) const
{
    return (addr % blockSize) / 8;  // 8-byte entries
}

bool
MetadataCache::lookup(Addr addr, uint64_t &data)
{
    int setIdx = getSetIndex(addr);
    Addr tag = getTag(addr);
    int offset = getOffset(addr);

    CacheSet &set = cacheSets[setIdx];
    for (int i = 0; i < numWays; i++) {
        if (set.ways[i].valid && set.ways[i].tag == tag) {
            // Hit!
            set.ways[i].lastAccess = curTick();
            data = set.ways[i].data[offset];
            DPRINTF(MetadataCache, "Cache hit: addr=%#x, data=%#x\n",
                    addr, data);
            return true;
        }
    }

    DPRINTF(MetadataCache, "Cache miss: addr=%#x\n", addr);
    return false;
}

void
MetadataCache::insert(Addr addr, uint64_t data)
{
    int setIdx = getSetIndex(addr);
    Addr tag = getTag(addr);
    int offset = getOffset(addr);

    CacheSet &set = cacheSets[setIdx];

    // Check if already present (update)
    for (int i = 0; i < numWays; i++) {
        if (set.ways[i].valid && set.ways[i].tag == tag) {
            set.ways[i].data[offset] = data;
            set.ways[i].dirty = true;
            set.ways[i].lastAccess = curTick();
            DPRINTF(MetadataCache, "Cache update: addr=%#x, data=%#x\n",
                    addr, data);
            return;
        }
    }

    // Find invalid way first
    for (int i = 0; i < numWays; i++) {
        if (!set.ways[i].valid) {
            set.ways[i].valid = true;
            set.ways[i].tag = tag;
            set.ways[i].data[offset] = data;
            set.ways[i].dirty = true;
            set.ways[i].lastAccess = curTick();
            DPRINTF(MetadataCache, "Cache insert: addr=%#x, way=%d\n",
                    addr, i);
            return;
        }
    }

    // All ways valid, need to evict
    int victimWay = findVictim(setIdx);
    evict(setIdx, victimWay);

    set.ways[victimWay].valid = true;
    set.ways[victimWay].tag = tag;
    set.ways[victimWay].data[offset] = data;
    set.ways[victimWay].dirty = true;
    set.ways[victimWay].lastAccess = curTick();

    DPRINTF(MetadataCache, "Cache insert with eviction: addr=%#x, victim=%d\n",
            addr, victimWay);
}

int
MetadataCache::findVictim(int setIdx)
{
    // CLRU (Clock-based LRU) replacement
    CacheSet &set = cacheSets[setIdx];
    Tick oldestTime = MaxTick;
    int victim = 0;

    // Simple LRU for now (can enhance to Clock algorithm)
    for (int i = 0; i < numWays; i++) {
        if (set.ways[i].lastAccess < oldestTime) {
            oldestTime = set.ways[i].lastAccess;
            victim = i;
        }
    }

    return victim;
}

void
MetadataCache::evict(int setIdx, int wayIdx)
{
    CacheSet &set = cacheSets[setIdx];
    CacheLine &line = set.ways[wayIdx];

    if (line.dirty) {
        // Evict all 8 entries in the line through PCB coalescing
        Addr evictAddr = (line.tag * numSets + setIdx) * blockSize;
        
        for (int i = 0; i < 8; i++) {
            // Send each 8B partial to PCB for coalescing
            coalescePartial(evictAddr + i * 8, line.data[i]);
        }
        
        stats.evictions++;
        DPRINTF(MetadataCache, "Evicted line to PCB: set=%d, way=%d, tag=%#x\n",
                setIdx, wayIdx, line.tag);
    }

    line.valid = false;
}

void
MetadataCache::coalescePartial(Addr addr, uint64_t data)
{
    Addr baseAddr = PCBEntry::getBase(addr);
    int offset = (addr - baseAddr) / 8;  // Which 8B partial (0-7)
    
    stats.pcbTotalPartials++;

    // Check if PCB has space
    if (pcbMap.size() >= (size_t)pcbCapacity && 
        pcbMap.find(baseAddr) == pcbMap.end()) {
        // PCB full and this is a new address - send to PLUB (overflow)
        sendToPLUB(addr, data);
        stats.pcbOverflows++;
        DPRINTF(MetadataCache, "PCB overflow: addr=%#x sent to PLUB\n", addr);
        return;
    }

    // Get or create PCB entry
    PCBEntry &entry = pcbMap[baseAddr];
    if (entry.baseAddr == 0) {
        entry.baseAddr = baseAddr;
        entry.lastUpdate = curTick();
    }

    // Merge partial into 64B block
    memcpy(&entry.data[offset * 8], &data, 8);
    entry.validMask |= (1 << offset);  // Mark this partial as valid
    entry.dirty = true;
    entry.lastUpdate = curTick();

    DPRINTF(MetadataCache, "PCB coalesce: addr=%#x, offset=%d, mask=%#x, "
            "numPartials=%d\n", addr, offset, entry.validMask, entry.numPartials());

    // If block is full (all 8 partials present), send to NVMain immediately
    if (entry.isFull()) {
        sendToNVMain(entry);
        pcbMap.erase(baseAddr);
        stats.pcbCoalescedBlocks++;
        DPRINTF(MetadataCache, "PCB full block: baseAddr=%#x sent to NVMain\n",
                baseAddr);
    }
}

void
MetadataCache::flushPCB()
{
    DPRINTF(MetadataCache, "PCB flush: %lu entries in buffer\n", pcbMap.size());

    // Flush all PCB entries to NVMain (periodic ADR flush)
    for (auto &pair : pcbMap) {
        const PCBEntry &entry = pair.second;
        if (entry.dirty && entry.numPartials() > 0) {
            sendToNVMain(entry);
            if (entry.isFull()) {
                stats.pcbCoalescedBlocks++;
            } else {
                stats.pcbPartialFlushes++;
            }
            DPRINTF(MetadataCache, "PCB flush: baseAddr=%#x, partials=%d\n",
                    entry.baseAddr, entry.numPartials());
        }
    }
    
    pcbMap.clear();

    // Schedule next flush
    schedule(flushEvent, curTick() + flushInterval);
}

void
MetadataCache::sendToNVMain(const PCBEntry &entry)
{
    // NVMain port might not be connected or packets might have wrong address range
    // For now, just use write queue for evictions
    // TODO: Proper NVMain integration requires correct address translation
    
    if (writeQueue.size() < (size_t)writeQueueCapacity) {
        for (int i = 0; i < 8; i++) {
            if (entry.validMask & (1 << i)) {
                uint64_t partial;
                memcpy(&partial, &entry.data[i * 8], 8);
                writeQueue.push({entry.baseAddr + i * 8, partial});
            }
        }
        
        // Track NVM writes and bytes
        stats.nvmWrites++;
        stats.nvmBytesWritten += 64;  // 64B block written
        
        DPRINTF(MetadataCache, "Sent coalesced block to write queue: baseAddr=%#x, mask=%#x\n",
                entry.baseAddr, entry.validMask);
    } else {
        stats.writeQueueFull++;
    }
}

void
MetadataCache::sendToPLUB(Addr addr, uint64_t data)
{
    // PLUB (Partial Log Update Buffer) - overflow path for uncoalesced partials
    // In full implementation, this would send directly to NVMain bypassing coalescing
    if (writeQueue.size() < (size_t)writeQueueCapacity) {
        writeQueue.push({addr, data});
        stats.plubPartials++;  // Track PLUB usage
        DPRINTF(MetadataCache, "Sent to PLUB: addr=%#x\n", addr);
    } else {
        stats.writeQueueFull++;
    }
}

MetadataCache::MetadataCacheStats::MetadataCacheStats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(hits, statistics::units::Count::get(),
               "Number of cache hits"),
      ADD_STAT(misses, statistics::units::Count::get(),
               "Number of cache misses"),
      ADD_STAT(evictions, statistics::units::Count::get(),
               "Number of cache line evictions"),
      ADD_STAT(writeQueueFull, statistics::units::Count::get(),
               "Number of times write queue was full"),
      ADD_STAT(hitRate, statistics::units::Ratio::get(),
               "Cache hit rate"),
      ADD_STAT(pcbCoalescedBlocks, statistics::units::Count::get(),
               "Number of full 64B blocks coalesced in PCB"),
      ADD_STAT(pcbPartialFlushes, statistics::units::Count::get(),
               "Number of incomplete blocks flushed from PCB"),
      ADD_STAT(pcbOverflows, statistics::units::Count::get(),
               "Number of partials sent to PLUB due to PCB overflow"),
      ADD_STAT(pcbTotalPartials, statistics::units::Count::get(),
               "Total 8B partials processed by PCB"),
      ADD_STAT(pcbCoalescingRate, statistics::units::Ratio::get(),
               "PCB coalescing efficiency (coalesced / total)"),
      // PLUB & NVM statistics (from handwritten notes IMG_20251022_143634.jpg)
      ADD_STAT(plubPartials, statistics::units::Count::get(),
               "Number of partials sent to PLUB (overflow path)"),
      ADD_STAT(nvmWrites, statistics::units::Count::get(),
               "Total write operations to NVM"),
      ADD_STAT(nvmBytesWritten, statistics::units::Byte::get(),
               "Total bytes written to NVM"),
      ADD_STAT(staleBlocksDiscarded, statistics::units::Count::get(),
               "Blocks discarded due to stale threshold"),
      ADD_STAT(overflowRate, statistics::units::Ratio::get(),
               "Overflow Rate = (Overflows / Total Partials) × 100"),
      ADD_STAT(writeAmplification, statistics::units::Ratio::get(),
               "Write Amplification = NVM writes / (Partial Bytes/64B)"),
      ADD_STAT(plubOverhead, statistics::units::Ratio::get(),
               "PLUB Overhead = (PLUB Partials / Total Partials) × 100")
{
    hitRate = hits / (hits + misses);
    pcbCoalescingRate = pcbCoalescedBlocks * 8 / pcbTotalPartials;
    
    // Formulas from handwritten notes
    overflowRate = (pcbOverflows / pcbTotalPartials) * 100;
    writeAmplification = nvmWrites / ((pcbTotalPartials * 8) / 64);
    plubOverhead = (plubPartials / pcbTotalPartials) * 100;
}

} // namespace memory
} // namespace gem5
