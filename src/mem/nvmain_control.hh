#ifndef __MEM_NVMAIN_CONTROL_HH__
#define __MEM_NVMAIN_CONTROL_HH__

#include <memory>
#include <string>

#include "mem/abstract_mem.hh"
#include "mem/port.hh"
#include "params/NVMainControl.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace memory  
{

class NVMainControl : public AbstractMemory
{
  private:
    class MemoryPort : public ResponsePort
    {
      private:
        NVMainControl &owner;

      public:
        MemoryPort(const std::string &name, NVMainControl &mem);

      protected:
        AddrRangeList getAddrRanges() const override;
        Tick recvAtomic(PacketPtr pkt) override;
        Tick recvAtomicBackdoor(PacketPtr pkt,
                                MemBackdoorPtr &backdoor) override;
        void recvFunctional(PacketPtr pkt) override;
        void recvMemBackdoorReq(const MemBackdoorReq &req,
                                MemBackdoorPtr &backdoor) override;
        bool recvTimingReq(PacketPtr pkt) override;
        void recvRespRetry() override;
    };

    std::string nvmainConfigPath;
    Tick tRCD;
    Tick tCL;
    Tick tWR;

    MemoryPort port;
    EventFunctionWrapper responseEvent;
    PacketPtr pendingRequest;
    PacketPtr retryRespPkt;
    std::unique_ptr<Packet> pendingDelete;
    bool retryReq;

    Tick packetLatency(const PacketPtr pkt) const;
    void recordStats(const PacketPtr pkt, Tick latency);
    void sendResponse();
    void trySendRetry();
    bool trySendTimingResp(PacketPtr pkt);

  public:
    typedef NVMainControlParams Params;
    NVMainControl(const Params &p);
    ~NVMainControl() override;

    void init() override;
    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;

    Tick recvAtomic(PacketPtr pkt);
    Tick recvAtomicBackdoor(PacketPtr pkt, MemBackdoorPtr &backdoor);
    void recvFunctional(PacketPtr pkt);
    void recvMemBackdoorReq(const MemBackdoorReq &req,
                            MemBackdoorPtr &backdoor);
    bool recvTimingReq(PacketPtr pkt);
    void recvRespRetry();

    struct NVMainControlStats : public statistics::Group {
        NVMainControlStats(statistics::Group *parent);
        
        statistics::Scalar numReads;
        statistics::Scalar numWrites;
        statistics::Scalar bytesRead;
        statistics::Scalar bytesWritten;
        statistics::Histogram readLatency;
        statistics::Histogram writeLatency;
    } stats;
};

} // namespace memory
} // namespace gem5

#endif
