// SPDX-License-Identifier: BSD-3-Clause
#ifndef __CPU_FIVE_STAGE_CPU_HH__
#define __CPU_FIVE_STAGE_CPU_HH__

#include <array>
#include <cstdint>
#include <fstream>
#include <string>
#include <vector>

#include "base/statistics.hh"
#include "params/FiveStageCPU.hh"
#include "sim/clocked_object.hh"
#include "sim/eventq.hh"

namespace gem5
{

class FiveStageCPU : public ClockedObject
{
  private:
    enum class Op { Nop, Addi, Add, Sub, Mul, Load, Store, Beq, Bne, Halt };
    struct Inst
    {
        Op op = Op::Nop;
        unsigned rd = 0, rs = 0, rt = 0;
        int64_t imm = 0;
        std::string name;
    };
    struct Token
    {
        bool valid = false;
        uint64_t seq = 0, pc = 0, fetchStart = 0, bits = 0;
        Inst inst;
        uint64_t lhs = 0, rhs = 0, value = 0, storeValue = 0;
        uint64_t next = 0;
    };
    struct Retirement
    {
        uint64_t seq, pc, fetchStart, retired;
        std::string op;
    };
    std::vector<uint64_t> program;
    std::array<uint64_t, 32> regs{};
    std::vector<uint64_t> memory;
    std::vector<uint8_t> counters;
    struct Target { bool valid = false; uint64_t pc = 0, target = 0; };
    std::vector<Target> targets;
    Token ifid, idex, exmem, memwb;
    std::vector<Retirement> retired;
    bool prediction, branchBlocked = false, haltBlocked = false;
    bool done = false;
    uint64_t cycle = 0, pc = 0, seq = 0, maxCycles;
    uint64_t branchCount = 0, lookups = 0, updates = 0;
    uint64_t mispredicts = 0, squashed = 0, loadStalls = 0;
    uint64_t branchStalls = 0, flushSlots = 0, forwarded = 0;
    std::vector<unsigned> regChecks, memChecks;
    std::vector<uint64_t> regValues, memValues;
    std::ofstream trace;
    const std::string summaryFile;
    EventFunctionWrapper tickEvent;
    struct Stats : public statistics::Group
    {
        statistics::Scalar numCycles, committedInsts, branches;
        statistics::Scalar predictions, mispredictions, loadUseStalls;
        statistics::Scalar branchWaitCycles, squashedInsts;
        statistics::Scalar totalResidenceCycles;
        statistics::Formula ipc, meanResidenceCycles;
        explicit Stats(statistics::Group *parent);
    } stats;

    static bool writes(const Inst &i);
    static bool isBranch(const Inst &i);
    static bool uses(const Inst &i, unsigned r);
    static Inst decode(uint64_t bits);
    static uint64_t encode(const Inst &i);
    uint64_t operand(unsigned r, uint64_t latched,
                     const Token &olderMem, const Token &olderWb);
    void record(const char *stage, const Token &token,
                const char *detail = "active");
    void tick();
    void finish();

  public:
    explicit FiveStageCPU(const FiveStageCPUParams &p);
    void startup() override;
};
} // namespace gem5
#endif
