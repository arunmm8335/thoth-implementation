#include "dev/security/aes_ctr_generator.hh"

#include "base/logging.hh"
#include "debug/AesCtrGen.hh"
#include "params/AESCTRGenerator.hh"

namespace gem5
{

namespace security
{

AESCTRGenerator::AESCTRGenerator(const AESCTRGeneratorParams &params)
    : ClockedObject(params),
      latency(params.latency),
      counterLatency(params.counter_latency),
      nextCounter(params.start_counter),
      keySeed(params.key_seed),
      remainingRequests(params.test_requests),
      generateEvent([this] { processNext(); }, name()),
      stats(this)
{
    fatal_if(latency <= 0, "AESCTRGenerator latency must be positive.");
    fatal_if(counterLatency < 0, "counter_latency cannot be negative.");

    // Initialize AES-CTR with the key derived from keySeed
    uint8_t key[16];
    for (int i = 0; i < 16; i++) {
        key[i] = (keySeed >> (8 * (i % 8))) & 0xff;
    }
    aesCtr = std::make_unique<AES128CTR>(key);
}

void
AESCTRGenerator::startup()
{
    ClockedObject::startup();
    if (remainingRequests > 0 && !generateEvent.scheduled()) {
        DPRINTF(AesCtrGen,
                "Scheduling first self-test partial generation (%llu requests pending)\n",
                remainingRequests);
        schedule(generateEvent, clockEdge(Cycles(1)));
    }
}

void
AESCTRGenerator::processNext()
{
    const Tick genLatency = latency + counterLatency;

    // Use real AES-CTR to generate the partial from the counter
    uint64_t partial = aesCtr->generatePartial(nextCounter);

    // Mask to 53 bits to fit in statistics::Scalar (stored as double)
    partial &= ((1ULL << 53) - 1);

    DPRINTF(AesCtrGen, "Generated counter=%#llx partial=%#llx latency=%llu\n",
            (unsigned long long)nextCounter, (unsigned long long)partial,
            genLatency);

    stats.generatedCounters++;
    stats.generatedPartials++;
    stats.lastCounter = nextCounter;
    stats.lastPartial = partial;

    nextCounter++;

    if (remainingRequests > 0) {
        remainingRequests--;
    }

    if (remainingRequests > 0) {
        schedule(generateEvent, curTick() + genLatency);
    }
}AESCTRGenerator::Statistics::Statistics(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(generatedCounters, statistics::units::Count::get(),
               "Number of counters produced"),
      ADD_STAT(generatedPartials, statistics::units::Count::get(),
               "Number of partials produced"),
      ADD_STAT(lastCounter, statistics::units::Count::get(),
               "Most recent counter value"),
      ADD_STAT(lastPartial, statistics::units::Count::get(),
               "Most recent partial value")
{
}

} // namespace security
} // namespace gem5
