#ifndef __MEM_SECURITY_METADATA_CACHE_HH__
#define __MEM_SECURITY_METADATA_CACHE_HH__

#include "base/statistics.hh"
#include "base/types.hh"
#include "mem/port.hh"
#include "params/MetadataCache.hh"
#include "sim/clocked_object.hh"

#include <deque>
#include <map>
#include <queue>
#include <vector>

namespace gem5
{

namespace memory
{

/**
 * Secure Metadata Cache for holding partials (OTAC/Counter values).
 * 
 * Architecture:
 * - 256KB SRAM cache (4KB cache lines of 64B each)
 * - 4-way set-associative
 * - Granularity: 8B entries (8 entries per 64B line)
 * - Eviction: CLRU (Clock-based LRU) policy
 * - Outputs evicted partials to Write Queue on full
 */
class MetadataCache : public ClockedObject
{
  public:
    MetadataCache(const MetadataCacheParams &params);

    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;

    void startup() override;

  private:
    /** Cache line structure (64 bytes) */
    struct CacheLine {
        bool valid;
        Addr tag;
        uint64_t data[8];  // 8 x 8-byte entries
        Tick lastAccess;
        bool dirty;

        CacheLine()
            : valid(false), tag(0), lastAccess(0), dirty(false)
        {
            for (int i = 0; i < 8; i++) data[i] = 0;
        }
    };

    /** Cache set (4-way associative) */
    struct CacheSet {
        std::vector<CacheLine> ways;
        int clockHand;  // For CLRU replacement

        explicit CacheSet(int numWays)
            : ways(numWays), clockHand(0)
        {}
    };

    // Cache parameters
    const int numSets;
    const int numWays;
    const Addr blockSize;
    const Tick accessLatency;
    const int writeQueueCapacity;

    // Cache storage
    std::vector<CacheSet> cacheSets;

    // Write queue for evicted partials
    std::queue<std::pair<Addr, uint64_t>> writeQueue;

    /** PCB (Partial Coalescing Buffer) for merging 8B partials into 64B blocks */
    struct PCBEntry {
        Addr baseAddr;           // Base address (64B aligned)
        uint8_t data[64];        // 64-byte coalesced block
        uint8_t validMask;       // Bitmap: which 8B partials are valid (8 bits for 8 partials)
        Tick lastUpdate;         // For flush timing
        bool dirty;

        PCBEntry() : baseAddr(0), validMask(0), lastUpdate(0), dirty(false)
        {
            memset(data, 0, 64);
        }

        bool isFull() const { return validMask == 0xFF; }  // All 8 partials present
        int numPartials() const { return __builtin_popcount(validMask); }
        
        // Get 64B-aligned base address from any address in the block
        static Addr getBase(Addr addr) { return (addr / 64) * 64; }
    };

    // PCB storage: map from 64B-aligned base address to coalescing entry
    std::map<Addr, PCBEntry> pcbMap;
    const int pcbCapacity = 256;  // Max 256 entries in PCB (16KB buffer)
    const Tick flushInterval = 10000000000;  // 10ms in picoseconds (ADR flush)
    EventFunctionWrapper flushEvent;

    // Helper functions for PCB
    void coalescePartial(Addr addr, uint64_t data);
    void flushPCB();
    void sendToNVMain(const PCBEntry &entry);
    void sendToPLUB(Addr addr, uint64_t data);  // Overflow path
    bool trySendPacket(PacketPtr pkt);  // Try to send packet to NVMain

    // Helper functions
    Addr getSetIndex(Addr addr) const;
    Addr getTag(Addr addr) const;
    int getOffset(Addr addr) const;
    int findVictim(int setIdx);
    bool lookup(Addr addr, uint64_t &data);
    void insert(Addr addr, uint64_t data);
    void evict(int setIdx, int wayIdx);

    // Port for communication
    class MemoryPort : public ResponsePort
    {
      private:
        MetadataCache &cache;

      public:
        MemoryPort(const std::string &name, MetadataCache &cache);

        Tick recvAtomic(PacketPtr pkt) override;
        void recvFunctional(PacketPtr pkt) override;
        bool recvTimingReq(PacketPtr pkt) override;
        void recvRespRetry() override;
        AddrRangeList getAddrRanges() const override;
    };

    // Port for sending evictions to NVMain
    class NVMainPort : public RequestPort
    {
      private:
        MetadataCache &cache;
        std::deque<PacketPtr> queuedPackets;

      public:
        NVMainPort(const std::string &name, MetadataCache &cache);

        bool recvTimingResp(PacketPtr pkt) override;
        void recvReqRetry() override;
        
        bool sendTimingReq(PacketPtr pkt);
        bool hasQueuedPackets() const { return !queuedPackets.empty(); }
    };

    MemoryPort port;
    NVMainPort nvmainPort;

    // Statistics
    struct MetadataCacheStats : public statistics::Group
    {
        MetadataCacheStats(statistics::Group *parent);

        statistics::Scalar hits;
        statistics::Scalar misses;
        statistics::Scalar evictions;
        statistics::Scalar writeQueueFull;
        statistics::Formula hitRate;
        
        // PCB statistics
        statistics::Scalar pcbCoalescedBlocks;   // Full 64B blocks created
        statistics::Scalar pcbPartialFlushes;    // Incomplete blocks flushed
        statistics::Scalar pcbOverflows;         // Partials sent to PLUB due to overflow
        statistics::Scalar pcbTotalPartials;     // Total 8B partials processed
        statistics::Formula pcbCoalescingRate;   // (coalesced / total)
        
        // PLUB & NVM statistics (from handwritten notes)
        statistics::Scalar plubPartials;         // Partials sent to PLUB
        statistics::Scalar nvmWrites;            // Total writes to NVM
        statistics::Scalar nvmBytesWritten;      // Total bytes written to NVM
        statistics::Scalar staleBlocksDiscarded; // Blocks discarded (>STALE_THRESHOLD)
        statistics::Formula overflowRate;        // (Overflows / Total) × 100
        statistics::Formula writeAmplification;  // NVM writes / (Partial Bytes/64B)
        statistics::Formula plubOverhead;        // (PLUB Partials / Total) × 100
    } stats;
};

} // namespace memory
} // namespace gem5

#endif // __MEM_SECURITY_METADATA_CACHE_HH__
