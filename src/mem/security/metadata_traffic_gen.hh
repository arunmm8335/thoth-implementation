/*
 * Metadata Traffic Generator for Thoth
 * 
 * Generates realistic burst traffic patterns (100-500 partials/ms) for
 * metadata cache evaluation. Simulates write-heavy workload typical of
 * secure memory systems with OTAC/Counter updates.
 */

#ifndef __MEM_SECURITY_METADATA_TRAFFIC_GEN_HH__
#define __MEM_SECURITY_METADATA_TRAFFIC_GEN_HH__

#include "mem/port.hh"
#include "params/MetadataTrafficGen.hh"
#include "sim/clocked_object.hh"
#include "sim/eventq.hh"

namespace gem5
{

namespace memory
{

class MetadataTrafficGen : public ClockedObject
{
  private:
    /** Request port for sending metadata updates to cache */
    class GeneratorPort : public RequestPort
    {
      private:
        MetadataTrafficGen& generator;

      public:
        GeneratorPort(const std::string& name, MetadataTrafficGen& gen);

      protected:
        bool recvTimingResp(PacketPtr pkt) override;
        void recvReqRetry() override;
    };

    GeneratorPort port;

    /** Traffic generation parameters */
    const uint64_t startAddr;
    const uint64_t endAddr;
    const uint64_t burstSize;      // Number of requests per burst
    const Tick burstInterval;      // Time between bursts
    const Tick requestLatency;     // Time between requests in a burst

    /** State tracking */
    uint64_t currentAddr;
    uint64_t requestsInBurst;
    uint64_t totalRequestsSent;
    uint64_t totalRequestsCompleted;
    bool waitingForRetry;

    /** Event for generating next request */
    EventFunctionWrapper nextRequestEvent;
    EventFunctionWrapper nextBurstEvent;

    /** Generate next metadata write request */
    void generateNextRequest();
    
    /** Start next burst of requests */
    void generateNextBurst();

    /** Send a packet to the metadata cache */
    bool sendPacket(PacketPtr pkt);

  public:
    PARAMS(MetadataTrafficGen);
    MetadataTrafficGen(const Params &p);

    /** Get the request port */
    Port& getPort(const std::string& if_name,
                  PortID idx = InvalidPortID) override;

    /** Start traffic generation */
    void startup() override;

    /** Statistics */
    struct MetadataTrafficGenStats : public statistics::Group
    {
        MetadataTrafficGenStats(statistics::Group *parent);

        statistics::Scalar requestsSent;
        statistics::Scalar requestsCompleted;
        statistics::Scalar burstsCompleted;
        statistics::Scalar retries;
    } stats;
};

} // namespace memory
} // namespace gem5

#endif // __MEM_SECURITY_METADATA_TRAFFIC_GEN_HH__
