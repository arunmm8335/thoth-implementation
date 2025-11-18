#include "mem/nvmain_control.hh"

#include "base/logging.hh"
#include "base/trace.hh"
#include "debug/NVMain.hh"

namespace gem5
{
namespace memory
{

NVMainControl::MemoryPort::MemoryPort(const std::string &name, NVMainControl &mem)
    : ResponsePort(name), owner(mem)
{
}

AddrRangeList
NVMainControl::MemoryPort::getAddrRanges() const
{
    AddrRangeList ranges;
    ranges.push_back(owner.getAddrRange());
    return ranges;
}

Tick
NVMainControl::MemoryPort::recvAtomic(PacketPtr pkt)
{
    return owner.recvAtomic(pkt);
}

Tick
NVMainControl::MemoryPort::recvAtomicBackdoor(
        PacketPtr pkt, MemBackdoorPtr &backdoor)
{
    return owner.recvAtomicBackdoor(pkt, backdoor);
}

void
NVMainControl::MemoryPort::recvFunctional(PacketPtr pkt)
{
    owner.recvFunctional(pkt);
}

void
NVMainControl::MemoryPort::recvMemBackdoorReq(
        const MemBackdoorReq &req, MemBackdoorPtr &backdoor)
{
    owner.recvMemBackdoorReq(req, backdoor);
}

bool
NVMainControl::MemoryPort::recvTimingReq(PacketPtr pkt)
{
    return owner.recvTimingReq(pkt);
}

void
NVMainControl::MemoryPort::recvRespRetry()
{
    owner.recvRespRetry();
}

NVMainControl::NVMainControl(const Params &p)
    : AbstractMemory(p),
      nvmainConfigPath(p.nvmain_config),
      tRCD(p.tRCD),
      tCL(p.tCL),
      tWR(p.tWR),
      port(name() + ".port", *this),
      responseEvent([this]{ sendResponse(); }, name()),
      pendingRequest(nullptr),
      retryRespPkt(nullptr),
      retryReq(false),
      stats(this)
{
    inform("NVMainControl: Config=%s, Read=%d ticks, Write=%d ticks",
           nvmainConfigPath, tRCD + tCL, tWR);
}

NVMainControl::~NVMainControl() = default;

void
NVMainControl::init()
{
    AbstractMemory::init();
    if (port.isConnected()) {
        port.sendRangeChange();
    }
}

Port &
NVMainControl::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "port") {
        return port;
    }
    return AbstractMemory::getPort(if_name, idx);
}

Tick
NVMainControl::recvAtomic(PacketPtr pkt)
{
    panic_if(pkt->cacheResponding(),
             "Should not see packets where cache is responding");
    access(pkt);
    Tick latency = packetLatency(pkt);
    recordStats(pkt, latency);
    return latency;
}

Tick
NVMainControl::recvAtomicBackdoor(PacketPtr pkt, MemBackdoorPtr &backdoor)
{
    Tick latency = recvAtomic(pkt);
    getBackdoor(backdoor);
    return latency;
}

void
NVMainControl::recvFunctional(PacketPtr pkt)
{
    pkt->pushLabel(name());
    functionalAccess(pkt);
    pkt->popLabel();
}

void
NVMainControl::recvMemBackdoorReq(const MemBackdoorReq &req,
                                    MemBackdoorPtr &backdoor)
{
    (void)req;
    getBackdoor(backdoor);
}

bool
NVMainControl::recvTimingReq(PacketPtr pkt)
{
    panic_if(pkt->cacheResponding(),
             "Should not see packets where cache is responding");
    panic_if(!(pkt->isRead() || pkt->isWrite()),
             "NVMainControl expects read/write, saw %s to %#llx",
             pkt->cmdString(), pkt->getAddr());

    if (pendingRequest || retryRespPkt) {
        retryReq = true;
        return false;
    }

    // account for any transfer delay that has already been modelled upstream
    Tick receive_delay = pkt->headerDelay + pkt->payloadDelay;
    pkt->headerDelay = pkt->payloadDelay = 0;

    pendingRequest = pkt;

    Tick latency = receive_delay + packetLatency(pkt);
    recordStats(pkt, latency);

    panic_if(responseEvent.scheduled(),
             "NVMainControl response event already scheduled");
    schedule(responseEvent, curTick() + latency);

    return true;
}

void
NVMainControl::sendResponse()
{
    assert(pendingRequest);
    PacketPtr pkt = pendingRequest;
    pendingRequest = nullptr;

    access(pkt);

    if (pkt->needsResponse()) {
        pkt->makeTimingResponse();
        if (!trySendTimingResp(pkt)) {
            retryRespPkt = pkt;
            return;
        }
    } else {
        pendingDelete.reset(pkt);
    }

    trySendRetry();
}

bool
NVMainControl::trySendTimingResp(PacketPtr pkt)
{
    if (!port.sendTimingResp(pkt)) {
        return false;
    }
    return true;
}

void
NVMainControl::trySendRetry()
{
    if (retryReq && !pendingRequest && !retryRespPkt) {
        retryReq = false;
        port.sendRetryReq();
    }
}

void
NVMainControl::recvRespRetry()
{
    if (!retryRespPkt) {
        return;
    }

    if (trySendTimingResp(retryRespPkt)) {
        retryRespPkt = nullptr;
        trySendRetry();
    }
}

Tick
NVMainControl::packetLatency(const PacketPtr pkt) const
{
    if (pkt->isRead()) {
        return tRCD + tCL;
    } else if (pkt->isWrite()) {
        return tWR;
    }
    return 0;
}

void
NVMainControl::recordStats(const PacketPtr pkt, Tick latency)
{
    if (pkt->isRead()) {
        stats.numReads++;
        stats.bytesRead += pkt->getSize();
        stats.readLatency.sample(latency);
    } else if (pkt->isWrite()) {
        stats.numWrites++;
        stats.bytesWritten += pkt->getSize();
        stats.writeLatency.sample(latency);
    }
}

NVMainControl::NVMainControlStats::NVMainControlStats(
    statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numReads, statistics::units::Count::get(), "Number of reads"),
      ADD_STAT(numWrites, statistics::units::Count::get(), "Number of writes"),
      ADD_STAT(bytesRead, statistics::units::Byte::get(), "Bytes read"),
      ADD_STAT(bytesWritten, statistics::units::Byte::get(), "Bytes written"),
      ADD_STAT(readLatency, statistics::units::Tick::get(), "Read latency"),
      ADD_STAT(writeLatency, statistics::units::Tick::get(), "Write latency")
{
    readLatency.init(20);
    writeLatency.init(20);
}

} // namespace memory
} // namespace gem5

