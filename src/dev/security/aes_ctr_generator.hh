#ifndef __DEV_SECURITY_AES_CTR_GENERATOR_HH__
#define __DEV_SECURITY_AES_CTR_GENERATOR_HH__

#include "base/statistics.hh"
#include "base/types.hh"
#include "dev/security/aes128.hh"
#include "params/AESCTRGenerator.hh"
#include "sim/clocked_object.hh"
#include "sim/eventq.hh"

#include <memory>

namespace gem5
{

namespace security
{

class AESCTRGenerator : public ClockedObject
{
  public:
    AESCTRGenerator(const AESCTRGeneratorParams &params);

    void startup() override;

  private:
    void processNext();

    const Tick latency;
    const Tick counterLatency;
    uint64_t nextCounter;
    uint64_t keySeed;
    uint64_t remainingRequests;

    std::unique_ptr<AES128CTR> aesCtr;

    EventFunctionWrapper generateEvent;

    struct Statistics : public statistics::Group
    {
        Statistics(statistics::Group *parent);

        statistics::Scalar generatedCounters;
        statistics::Scalar generatedPartials;
        statistics::Scalar lastCounter;
        statistics::Scalar lastPartial;
    } stats;
};

} // namespace security
} // namespace gem5

#endif // __DEV_SECURITY_AES_CTR_GENERATOR_HH__
