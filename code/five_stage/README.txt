FiveStageCPU teaching component for gem5

This is a compiled gem5 ClockedObject that models a scalar CPU. It has its
own register file, instruction memory, data memory, four interstage latches,
and five actual pipeline stages: IF, ID, EX, MEM and WB. It is not a BaseCPU
subclass, does not decode AArch64 ELFs and does not use an operating system.
The separate original O3/Minor/SMT experiments still execute AArch64 programs.

Installation into the pinned gem5 source tree
  mkdir -p ~/src/gem5/src/cpu/five_stage
  cp SConscript FiveStageCPU.py five_stage_cpu.cc five_stage_cpu.hh \
    ~/src/gem5/src/cpu/five_stage/
  cd ~/src/gem5
  scons build/ARM/gem5.opt -j8 CC=gcc-13 CXX=g++-13

Run all checks and controlled comparisons
  cd ~/assignment4/code/five_stage
  python3 run_five_stage.py

Supported teaching ISA
  ADDI rd rs immediate     rd = rs + signed immediate
  ADD  rd rs rt            rd = rs + rt
  SUB  rd rs rt            rd = rs - rt
  MUL  rd rs rt            rd = rs * rt
  LD   rd rs offset        rd = memory[rs + signed offset]
  ST   rt rs offset        memory[rs + signed offset] = rt
  BEQ  rs rt target        branch to instruction index if rs == rt
  BNE  rs rt target        branch to instruction index if rs != rt
  NOP
  HALT

There are 32 unsigned 64-bit registers. Register zero is immutable. ADD,
SUB, MUL and ADDI wrap modulo 2^64. Data addresses are word indices, not
byte addresses. Conditional targets are absolute instruction indices.
The Python assembler accepts labels and resolves them before execution.

Timing contract
  IF: fetch one raw 64-bit instruction word from ideal instruction memory.
  ID: decode its opcode, register fields and immediate; read registers and
      detect a load-use dependency.
  EX: perform one-cycle ALU work, compute an address or resolve a branch.
  MEM: perform one-cycle ideal data-memory access (or pass an ALU result).
  WB: write the architectural register file and retire in program order.

Every instruction, including branches and HALT, visits all five stages.
Separate ideal instruction and data memories avoid structural IF/MEM hazards.
There are no caches, variable memory delays, exceptions or interrupts.
MUL is deliberately one cycle. This is a timing teaching model, not a
performance model of a specific commercial processor.

EX/MEM and MEM/WB forwarding cover ALU operands, branch operands and store
data. A load-use hazard freezes PC and IF/ID and inserts one EX bubble.
Stores update data memory only in MEM. Branches resolve in EX, so a
wrong-path store in ID is discarded before it can touch memory.

Prediction ON: a 64-entry direct-indexed two-bit BHT starts weakly not-taken.
A same-sized tagged target buffer learns branches and direct targets in EX.
Its entries start invalid. IF consults the learned target metadata without
decoding instructions; a cold target miss falls through. Counters train
at EX. An incorrect predicted next PC flushes younger ID
work and suppresses IF in that cycle, creating the standard two-slot
EX-resolution penalty. No indirect branches are modeled.

Prediction OFF: ID recognizes a branch and blocks the next fetch until EX
provides its actual next PC. The C++ class and all five stages stay the same.
There are no BHT
lookups, counter updates or guesses. With no data interlock, each branch
uses two blocked IF slots. It is not an always-not-taken predictor.

Only the prediction boolean and output file paths differ between each pair
of gem5 CPU parameter sets. All other model parameters and the workload are
checked to be identical. Both modes must retire the oracle's exact PC
sequence and match all 32 registers and all 256 data words.

Trace and latency convention
pipeline.csv records per-cycle stage occupancy from the actual C++ model.
ID may repeat when stalled. A squashed ID entry is marked squashed.
Cycle 1 is the first IF cycle. Fetch-start time is cycle 0; WB ends at cycle
5 for an unstalled instruction. Thus its IF-start to WB-end latency is
five cycles. The steady stream takes N+4 cycles from an empty pipeline.
This endpoint convention is stated explicitly; the old O3 trace metric
uses the difference between two gem5 event timestamps instead.

The model writes built-in gem5 statistics plus a detailed JSON result.
The seven programs test straight-line overlap, bypass paths, two load-use
interlocks, a counted loop, alternating branches, wrong-path stores and
wrong-path HALT recovery. Results are under results_five_stage/.
