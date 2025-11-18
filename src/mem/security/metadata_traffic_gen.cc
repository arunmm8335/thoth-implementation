/*
 * Metadata Traffic Generator for Thoth
 */

#include "mem/security/metadata_traffic_gen.hh"

#include "base/random.hh"
#include "base/trace.hh"
#include "debug/MetadataTrafficGen.hh"
#include "mem/packet.hh"
#include "mem/request.hh"

namespace gem5
{

namespace memory
{

MetadataTrafficGen::GeneratorPort::GeneratorPort(
    const std::string& name, MetadataTrafficGen& gen)
    : RequestPort(name, &gen), generator(gen)
{
}

bool
MetadataTrafficGen::GeneratorPort::recvTimingResp(PacketPtr pkt)
{
    generator.totalRequestsCompleted++;
    generator.stats.requestsCompleted++;
    
    DPRINTF(MetadataTrafficGen, "Received response for addr %#x\n",
            pkt->getAddr());
    
    delete pkt;
    return true;
}

void
MetadataTrafficGen::GeneratorPort::recvReqRetry()
{
    DPRINTF(MetadataTrafficGen, "Received retry signal\n");
    generator.stats.retries++;
    generator.waitingForRetry = false;
    generator.generateNextRequest();
}

MetadataTrafficGen::MetadataTrafficGen(const Params &p)
    : ClockedObject(p),
      port("port", *this),
      startAddr(p.start_addr),
      endAddr(p.end_addr),
      burstSize(p.burst_size),
      burstInterval(p.burst_interval),
      requestLatency(p.request_latency),
      currentAddr(p.start_addr),
      requestsInBurst(0),
      totalRequestsSent(0),
      totalRequestsCompleted(0),
      waitingForRetry(false),
      nextRequestEvent([this]{ generateNextRequest(); }, name()),
      nextBurstEvent([this]{ generateNextBurst(); }, name()),
      stats(this)
{
    DPRINTF(MetadataTrafficGen,
            "Created MetadataTrafficGen: addr range [%#x, %#x), "
            "burst size %d, burst interval %llu ticks\n",
            startAddr, endAddr, burstSize, burstInterval);
}

Port&
MetadataTrafficGen::getPort(const std::string& if_name, PortID idx)
{
    if (if_name == "port") {
        return port;
    } else {
        return ClockedObject::getPort(if_name, idx);
    }
}

void
MetadataTrafficGen::startup()
{
    // Schedule first burst
    schedule(nextBurstEvent, curTick() + clockPeriod());
}

void
MetadataTrafficGen::generateNextBurst()
{
    DPRINTF(MetadataTrafficGen, "Starting new burst of %d requests\n",
            burstSize);
    
    requestsInBurst = 0;
    stats.burstsCompleted++;
    
    // Start generating requests in this burst
    generateNextRequest();
}

void
MetadataTrafficGen::generateNextRequest()
{
    if (waitingForRetry) {
        return; // Will be called again on retry
    }

    if (requestsInBurst >= burstSize) {
        // Burst complete, schedule next burst
        schedule(nextBurstEvent, curTick() + burstInterval);
        return;
    }

    // Create metadata write request (8-byte partial)
    RequestPtr req = std::make_shared<Request>(
        currentAddr, 8, Request::UNCACHEABLE, Request::funcRequestorId);
    
    PacketPtr pkt = new Packet(req, MemCmd::WriteReq);
    pkt->allocate();
    
    // Fill with dummy metadata (counter or OTAC partial)
    uint64_t metadata = (totalRequestsSent << 32) | currentAddr;
    pkt->setData((uint8_t*)&metadata);

    DPRINTF(MetadataTrafficGen,
            "Generating request %d in burst: addr %#x, data %#x\n",
            requestsInBurst, currentAddr, metadata);

    if (sendPacket(pkt)) {
        // Packet sent successfully
        totalRequestsSent++;
        stats.requestsSent++;
        requestsInBurst++;
        
        // Move to next address (wrap around if needed)
        currentAddr += 8;
        if (currentAddr >= endAddr) {
            currentAddr = startAddr;
        }
        
        // Schedule next request in burst
        if (requestsInBurst < burstSize) {
            schedule(nextRequestEvent, curTick() + requestLatency);
        } else {
            // Burst complete, schedule next burst
            schedule(nextBurstEvent, curTick() + burstInterval);
        }
    } else {
        // Packet blocked, wait for retry
        waitingForRetry = true;
    }
}

bool
MetadataTrafficGen::sendPacket(PacketPtr pkt)
{
    if (!port.sendTimingReq(pkt)) {
        DPRINTF(MetadataTrafficGen, "Request blocked, waiting for retry\n");
        return false;
    }
    return true;
}

MetadataTrafficGen::MetadataTrafficGenStats::MetadataTrafficGenStats(
    statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(requestsSent, statistics::units::Count::get(),
               "Number of metadata requests sent"),
      ADD_STAT(requestsCompleted, statistics::units::Count::get(),
               "Number of metadata requests completed"),
      ADD_STAT(burstsCompleted, statistics::units::Count::get(),
               "Number of bursts completed"),
      ADD_STAT(retries, statistics::units::Count::get(),
               "Number of retry events")
{
}

} // namespace memory
} // namespace gem5
