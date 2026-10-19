// SPDX-License-Identifier: BSD-3-Clause
#include "cpu/five_stage/five_stage_cpu.hh"

#include <algorithm>
#include <iomanip>
#include <sstream>

#include "base/logging.hh"
#include "sim/sim_exit.hh"

namespace gem5
{

FiveStageCPU::Stats::Stats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numCycles, statistics::units::Cycle::get(), "CPU cycles"),
      ADD_STAT(committedInsts, statistics::units::Count::get(),
               "Architectural instructions retired including HALT"),
      ADD_STAT(branches, statistics::units::Count::get(),
               "Conditional branches resolved in EX"),
      ADD_STAT(predictions, statistics::units::Count::get(),
               "BHT lookups on tagged target hits; zero when disabled"),
      ADD_STAT(mispredictions, statistics::units::Count::get(),
               "Predicted next PCs corrected in EX"),
      ADD_STAT(loadUseStalls, statistics::units::Count::get(),
               "One-cycle load-use interlocks"),
      ADD_STAT(branchWaitCycles, statistics::units::Count::get(),
               "IF slots waiting for an unpredicted branch to resolve"),
      ADD_STAT(squashedInsts, statistics::units::Count::get(),
               "Younger ID instructions squashed by EX redirect"),
      ADD_STAT(totalResidenceCycles, statistics::units::Cycle::get(),
               "Sum of IF-start to WB-end latency of retired instructions"),
      ADD_STAT(ipc, statistics::units::Rate<statistics::units::Count,
               statistics::units::Cycle>::get(), "Retired instructions/cycle",
               committedInsts / numCycles),
      ADD_STAT(meanResidenceCycles, statistics::units::Cycle::get(),
               "Mean instruction latency in cycles",
               totalResidenceCycles / committedInsts)
{
}

FiveStageCPU::FiveStageCPU(const FiveStageCPUParams &p)
    : ClockedObject(p), memory(p.memory_words, 0),
      counters(p.bht_entries, 1), targets(p.bht_entries),
      prediction(p.prediction),
      maxCycles(p.max_cycles), regChecks(p.expected_reg_indices),
      memChecks(p.expected_mem_indices), regValues(p.expected_reg_values),
      memValues(p.expected_mem_values), trace(p.trace_file),
      summaryFile(p.summary_file),
      tickEvent([this] { tick(); }, name()), stats(this)
{
    fatal_if(!trace.is_open(), "Cannot create five-stage trace");
    fatal_if(counters.empty(), "BHT must contain at least one entry");
    fatal_if(p.initial_memory.size() > memory.size(), "Initial memory too big");
    fatal_if(regChecks.size() != regValues.size() ||
             memChecks.size() != memValues.size(), "Mismatched check vectors");
    std::copy(p.initial_memory.begin(), p.initial_memory.end(), memory.begin());
    for (const auto &text : p.program) {
        Inst i;
        std::istringstream line(text);
        line >> i.name;
        if (i.name == "ADDI") {
            i.op = Op::Addi;
            line >> i.rd >> i.rs >> i.imm;
        } else if (i.name == "ADD" || i.name == "SUB" || i.name == "MUL") {
            i.op = i.name == "ADD" ? Op::Add :
                (i.name == "SUB" ? Op::Sub : Op::Mul);
            line >> i.rd >> i.rs >> i.rt;
        } else if (i.name == "LD") {
            i.op = Op::Load;
            line >> i.rd >> i.rs >> i.imm;
        } else if (i.name == "ST") {
            i.op = Op::Store;
            line >> i.rt >> i.rs >> i.imm;
        } else if (i.name == "BEQ" || i.name == "BNE") {
            i.op = i.name == "BEQ" ? Op::Beq : Op::Bne;
            line >> i.rs >> i.rt >> i.imm;
        } else if (i.name == "HALT") {
            i.op = Op::Halt;
        } else if (i.name == "NOP") {
            i.op = Op::Nop;
        } else {
            fatal("Unsupported five-stage instruction: %s", text);
        }
        fatal_if(line.fail() || i.rd >= 32 || i.rs >= 32 || i.rt >= 32,
                 "Invalid five-stage instruction: %s", text);
        std::string extra;
        fatal_if(bool(line >> extra), "Extra operands: %s", text);
        program.push_back(encode(i));
    }
    fatal_if(program.empty(), "Empty program");
    trace << "cycle,stage,seq,pc,op,detail\n";
}

uint64_t
FiveStageCPU::encode(const Inst &i)
{
    return uint64_t(i.op) | (uint64_t(i.rd) << 4) |
        (uint64_t(i.rs) << 9) | (uint64_t(i.rt) << 14) |
        (uint64_t(uint32_t(i.imm)) << 19);
}

FiveStageCPU::Inst
FiveStageCPU::decode(uint64_t bits)
{
    static const char *names[] = {
        "NOP", "ADDI", "ADD", "SUB", "MUL", "LD", "ST", "BEQ", "BNE", "HALT"
    };
    Inst i;
    const unsigned code = bits & 15;
    fatal_if(code > unsigned(Op::Halt), "Invalid teaching opcode");
    i.op = Op(code);
    i.name = names[code];
    i.rd = (bits >> 4) & 31;
    i.rs = (bits >> 9) & 31;
    i.rt = (bits >> 14) & 31;
    i.imm = int32_t((bits >> 19) & 0xffffffff);
    return i;
}

bool
FiveStageCPU::writes(const Inst &i)
{
    return i.op == Op::Addi || i.op == Op::Add || i.op == Op::Sub ||
        i.op == Op::Mul || i.op == Op::Load;
}

bool
FiveStageCPU::isBranch(const Inst &i)
{
    return i.op == Op::Beq || i.op == Op::Bne;
}

bool
FiveStageCPU::uses(const Inst &i, unsigned r)
{
    if (r == 0 || i.op == Op::Nop || i.op == Op::Halt)
        return false;
    if (i.rs == r)
        return true;
    return (i.op == Op::Add || i.op == Op::Sub || i.op == Op::Mul ||
            i.op == Op::Store || isBranch(i)) && i.rt == r;
}

uint64_t
FiveStageCPU::operand(unsigned r, uint64_t latched,
                      const Token &olderMem, const Token &olderWb)
{
    if (r == 0)
        return 0;
    if (olderMem.valid && writes(olderMem.inst) &&
        olderMem.inst.rd == r && olderMem.inst.op != Op::Load) {
        ++forwarded;
        return olderMem.value;
    }
    if (olderWb.valid && writes(olderWb.inst) && olderWb.inst.rd == r) {
        ++forwarded;
        return olderWb.value;
    }
    return latched;
}

void
FiveStageCPU::record(const char *stage, const Token &token, const char *detail)
{
    if (token.valid)
        trace << cycle << ',' << stage << ',' << token.seq << ',' <<
            token.pc << ',' << token.inst.name << ',' << detail << '\n';
}

void
FiveStageCPU::startup()
{
    ClockedObject::startup();
    schedule(tickEvent, clockEdge(Cycles(1)));
}

void
FiveStageCPU::tick()
{
    ++cycle;
    ++stats.numCycles;
    fatal_if(cycle > maxCycles, "Five-stage watchdog expired");

    // All right-hand sides below refer to the OLD interstage latches.
    // Stage results replace the four latches together at the end of this tick.
    Token nextWb, nextMem, nextEx, nextId;
    bool redirect = false;
    bool resolveWithoutPrediction = false;

    record("WB", memwb);
    if (memwb.valid) {
        if (writes(memwb.inst) && memwb.inst.rd != 0)
            regs[memwb.inst.rd] = memwb.value;
        ++stats.committedInsts;
        stats.totalResidenceCycles += cycle - memwb.fetchStart;
        retired.push_back({memwb.seq, memwb.pc, memwb.fetchStart,
                           cycle, memwb.inst.name});
        if (memwb.inst.op == Op::Halt) {
            finish();
            return;
        }
    }

    record("MEM", exmem);
    if (exmem.valid) {
        nextWb = exmem;
        if (exmem.inst.op == Op::Load || exmem.inst.op == Op::Store) {
            fatal_if(exmem.value >= memory.size(),
                     "Teaching CPU data address outside memory");
            if (exmem.inst.op == Op::Load)
                nextWb.value = memory[exmem.value];
            else
                memory[exmem.value] = exmem.storeValue;
        }
    }

    record("EX", idex);
    if (idex.valid) {
        nextMem = idex;
        const auto &i = idex.inst;
        const uint64_t lhs = operand(i.rs, idex.lhs, exmem, memwb);
        const uint64_t rhs = operand(i.rt, idex.rhs, exmem, memwb);
        switch (i.op) {
          case Op::Addi: nextMem.value = lhs + uint64_t(i.imm); break;
          case Op::Add: nextMem.value = lhs + rhs; break;
          case Op::Sub: nextMem.value = lhs - rhs; break;
          case Op::Mul: nextMem.value = lhs * rhs; break;
          case Op::Load: nextMem.value = lhs + uint64_t(i.imm); break;
          case Op::Store:
            nextMem.value = lhs + uint64_t(i.imm);
            nextMem.storeValue = rhs;
            break;
          case Op::Beq:
          case Op::Bne: {
            ++branchCount;
            ++stats.branches;
            const bool taken = i.op == Op::Beq ? lhs == rhs : lhs != rhs;
            const uint64_t actual = taken ? uint64_t(i.imm) : idex.pc + 1;
            if (prediction) {
                auto &counter = counters[idex.pc % counters.size()];
                counter = taken ? std::min(3, int(counter) + 1) :
                    std::max(0, int(counter) - 1);
                ++updates;
                auto &target = targets[idex.pc % targets.size()];
                target = {true, idex.pc, uint64_t(i.imm)};
                if (actual != idex.next) {
                    ++mispredicts;
                    ++stats.mispredictions;
                    redirect = true;
                    pc = actual;
                    haltBlocked = false;
                }
            } else {
                // The only branch-off behavior: no BHT call or update, and
                // IF waits until EX produces the real next PC.
                branchBlocked = false;
                resolveWithoutPrediction = true;
                pc = actual;
            }
            break;
          }
          case Op::Nop:
          case Op::Halt: break;
        }
    }

    // IF stores only the raw instruction word. Actual opcode, register and
    // immediate decoding occurs here, in ID, before its hazard/read logic.
    Token decoded = ifid;
    if (decoded.valid)
        decoded.inst = decode(decoded.bits);
    const bool loadUse = decoded.valid && idex.valid &&
        idex.inst.op == Op::Load && uses(decoded.inst, idex.inst.rd);
    if (!redirect && decoded.valid) {
        if (!prediction && isBranch(decoded.inst))
            branchBlocked = true;
        if (decoded.inst.op == Op::Halt)
            haltBlocked = true;
    }
    if (redirect) {
        record("ID", decoded, "squashed");
        if (ifid.valid) {
            ++squashed;
            ++stats.squashedInsts;
        }
        ++flushSlots;
        // Younger ID is discarded, EX/MEM keeps the resolving branch.
    } else if (loadUse) {
        record("ID", decoded, "load_use_stall");
        nextId = ifid;
        ++loadStalls;
        ++stats.loadUseStalls;
        // Bubble in ID/EX, freeze IF/ID and PC for one cycle.
    } else {
        record("ID", decoded);
        if (ifid.valid) {
            nextEx = decoded;
            nextEx.lhs = regs[decoded.inst.rs];
            nextEx.rhs = regs[decoded.inst.rt];
        }
    }

    const bool waiting = branchBlocked || resolveWithoutPrediction;
    if (waiting) {
        ++branchStalls;
        ++stats.branchWaitCycles;
    }
    if (!redirect && !loadUse && !waiting && !haltBlocked) {
        fatal_if(pc >= program.size(), "PC outside program before HALT");
        nextId.valid = true;
        nextId.seq = ++seq;
        nextId.pc = pc;
        nextId.bits = program[pc];
        nextId.fetchStart = cycle - 1;
        nextId.next = pc + 1;
        // A learned tagged target buffer identifies branches in IF. IF does
        // not decode the instruction to obtain a type or a direct target.
        if (prediction) {
            const auto &target = targets[pc % targets.size()];
            if (target.valid && target.pc == pc) {
                ++lookups;
                ++stats.predictions;
                if (counters[pc % counters.size()] >= 2)
                    nextId.next = target.target;
            }
        }
        // A mnemonic is attached solely for trace display. No operands or
        // control decisions are decoded in IF.
        static const char *names[] = {
            "NOP", "ADDI", "ADD", "SUB", "MUL", "LD", "ST", "BEQ", "BNE", "HALT"
        };
        nextId.inst.name = names[nextId.bits & 15];
        record("IF", nextId);
        pc = nextId.next;
    }
    ifid = nextId;
    idex = nextEx;
    exmem = nextMem;
    memwb = nextWb;
    regs[0] = 0;
    schedule(tickEvent, clockEdge(Cycles(1)));
}

void
FiveStageCPU::finish()
{
    done = true;
    trace.flush();
    bool passed = true;
    for (size_t n = 0; n < regChecks.size(); ++n) {
        fatal_if(regChecks[n] >= regs.size(), "Invalid expected register");
        passed &= regs[regChecks[n]] == regValues[n];
    }
    for (size_t n = 0; n < memChecks.size(); ++n) {
        fatal_if(memChecks[n] >= memory.size(), "Invalid expected address");
        passed &= memory[memChecks[n]] == memValues[n];
    }
    uint64_t latency = 0;
    for (const auto &r : retired)
        latency += r.retired - r.fetchStart;
    std::ofstream out(summaryFile);
    fatal_if(!out.is_open(), "Cannot create five-stage summary");
    out << std::setprecision(14)
        << "{\n\"passed\":" << (passed ? "true" : "false")
        << ",\n\"prediction\":" << (prediction ? "true" : "false")
        << ",\n\"cycles\":" << cycle
        << ",\n\"committed\":" << retired.size()
        << ",\n\"ipc\":" << double(retired.size()) / cycle
        << ",\n\"mean_latency\":" << double(latency) / retired.size()
        << ",\n\"branches\":" << branchCount
        << ",\n\"predictions\":" << lookups
        << ",\n\"predictor_updates\":" << updates
        << ",\n\"mispredictions\":" << mispredicts
        << ",\n\"squashed\":" << squashed
        << ",\n\"load_use_stalls\":" << loadStalls
        << ",\n\"branch_wait_cycles\":" << branchStalls
        << ",\n\"redirect_bubbles\":" << flushSlots
        << ",\n\"forwarded_operands\":" << forwarded;
    out << ",\n\"registers\":[";
    for (size_t n = 0; n < regs.size(); ++n)
        out << (n ? "," : "") << regs[n];
    out << "],\n\"memory\":[";
    for (size_t n = 0; n < memory.size(); ++n)
        out << (n ? "," : "") << memory[n];
    out << "],\n\"retired\":[\n";
    for (size_t n = 0; n < retired.size(); ++n) {
        const auto &r = retired[n];
        out << (n ? ",\n" : "") << "{\"seq\":" << r.seq
            << ",\"pc\":" << r.pc << ",\"op\":\"" << r.op
            << "\",\"fetch_start\":" << r.fetchStart
            << ",\"wb_end\":" << r.retired << "}";
    }
    out << "\n]}\n";
    out.close();
    inform("FiveStageCPU: %llu cycles, %llu retired, checks %s",
           cycle, uint64_t(retired.size()), passed ? "PASS" : "FAIL");
    exitSimLoop(passed ? "five stage checks passed" :
                "five stage checks failed", passed ? 0 : 1);
}
} // namespace gem5
