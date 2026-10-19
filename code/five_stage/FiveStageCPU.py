# SPDX-License-Identifier: BSD-3-Clause
"""A clocked teaching CPU with explicit IF/ID/EX/MEM/WB pipeline latches.

This is an independent CPU component, not an AArch64 BaseCPU subclass. It
executes the documented small RISC instruction set, with separate ideal
instruction and data memories. No external ISA decoder or OS is required.
"""
from m5.objects.ClockedObject import ClockedObject
from m5.params import *

class FiveStageCPU(ClockedObject):
    type = 'FiveStageCPU'
    cxx_header = 'cpu/five_stage/five_stage_cpu.hh'
    cxx_class = 'gem5::FiveStageCPU'
    program = VectorParam.String([], 'Decoded teaching RISC program')
    prediction = Param.Bool(True, 'Enable two-bit conditional prediction')
    bht_entries = Param.Unsigned(64, 'Direct-indexed two-bit BHT entries')
    memory_words = Param.Unsigned(256, 'Number of 64-bit data words')
    initial_memory = VectorParam.UInt64([], 'Initial data-memory contents')
    expected_reg_indices = VectorParam.Unsigned([], 'Registers to validate')
    expected_reg_values = VectorParam.UInt64([], 'Expected register values')
    expected_mem_indices = VectorParam.Unsigned([], 'Memory words to validate')
    expected_mem_values = VectorParam.UInt64([], 'Expected memory values')
    max_cycles = Param.Unsigned(100000, 'Watchdog maximum cycles')
    trace_file = Param.String('five-stage-trace.csv', 'Cycle occupancy trace')
    summary_file = Param.String('five-stage-summary.json', 'Results and checks')
