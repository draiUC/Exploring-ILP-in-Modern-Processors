"""Controlled AArch64 ILP experiments on gem5 25.1.

Low-level wiring is intentional: the experiment needs explicit O3 widths,
predictor composition, and multiple SE processes on one SMT core.
"""
import argparse
import json
import os
import m5
from m5.objects import *

p = argparse.ArgumentParser()
p.add_argument('--binary', required=True)
p.add_argument('--second')
p.add_argument('--model', choices=['o3', 'minor', 'timing'], default='o3')
p.add_argument('--width', type=int, choices=[1, 2, 4], default=1)
p.add_argument('--predictor', choices=['local', 'tournament'], default='tournament')
p.add_argument('--smt-policy', choices=['Partitioned', 'Dynamic'], default='Partitioned')
a = p.parse_args()
threads = 2 if a.second else 1
if threads > 1 and a.model != 'o3':
    raise ValueError('SMT experiment requires O3')
s = System()
s.multi_thread = threads > 1
s.clk_domain = SrcClockDomain(clock='1GHz', voltage_domain=VoltageDomain())
s.mem_mode = 'timing'
s.mem_ranges = [AddrRange('512MiB')]
s.cache_line_size = 64
if a.model == 'o3':
    s.cpu = ArmO3CPU(numThreads=threads)
    for field in ['fetchWidth', 'decodeWidth', 'renameWidth', 'dispatchWidth',
                  'issueWidth', 'wbWidth', 'commitWidth', 'squashWidth']:
        setattr(s.cpu, field, a.width)
    s.cpu.numROBEntries = 128
    s.cpu.instQueues = [IQUnit(numEntries=64, smtIQPolicy=a.smt_policy)]
    s.cpu.LQEntries = 32
    s.cpu.SQEntries = 32
    s.cpu.numPhysIntRegs = 256
    s.cpu.numPhysFloatRegs = 256
    s.cpu.numPhysVecRegs = 256
    s.cpu.numPhysVecPredRegs = 128
    s.cpu.numPhysMatRegs = 8
    s.cpu.smtFetchPolicy = 'RoundRobin'
    s.cpu.smtNumFetchingThreads = 1
    s.cpu.smtROBPolicy = a.smt_policy
    # Dynamic LSQ sharing triggers an upstream assertion on the pointer test
    # at the pinned revision. Keep LSQ partitioning fixed across comparisons.
    s.cpu.smtLSQPolicy = 'Partitioned'
elif a.model == 'minor':
    s.cpu = ArmMinorCPU()
    s.cpu.decodeInputWidth = 1
    s.cpu.executeInputWidth = 1
    s.cpu.executeIssueLimit = 1
    s.cpu.executeCommitLimit = 1
else:
    s.cpu = ArmTimingSimpleCPU()
if a.model != 'timing':
    cond = LocalBP(numThreads=threads) if a.predictor == 'local' else TournamentBP(numThreads=threads)
    s.cpu.branchPred = BranchPredictor(numThreads=threads, conditionalBranchPred=cond, instShiftAmt=2)

class L1(Cache):
    assoc = 2
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 8
    tgts_per_mshr = 8

s.cpu.icache = L1(size='32KiB')
s.cpu.dcache = L1(size='32KiB')
s.membus = SystemXBar()
s.cpu.icache_port = s.cpu.icache.cpu_side
s.cpu.dcache_port = s.cpu.dcache.cpu_side
s.cpu.icache.mem_side = s.membus.cpu_side_ports
s.cpu.dcache.mem_side = s.membus.cpu_side_ports
s.cpu.createInterruptController()
s.system_port = s.membus.cpu_side_ports
s.mem_ctrl = MemCtrl()
s.mem_ctrl.dram = DDR3_1600_8x8(device_size='32MiB')
s.mem_ctrl.dram.range = s.mem_ranges[0]
s.mem_ctrl.port = s.membus.mem_side_ports
s.workload = SEWorkload.init_compatible(os.path.abspath(a.binary))
processes = []
for i, binary in enumerate([a.binary] + ([a.second] if a.second else [])):
    proc = Process(pid=100 + i)
    proc.cmd = [os.path.abspath(binary)]
    processes.append(proc)
s.cpu.workload = processes
s.cpu.createThreads()
root = Root(full_system=False, system=s)
m5.instantiate()
events = []
while True:
    event = m5.simulate(1000000000000)
    cause, code = event.getCause(), event.getCode()
    events.append({'tick': int(m5.curTick()), 'cause': cause, 'code': int(code)})
    if 'last active thread' in cause or 'all threads' in cause:
        break
    if 'exiting' in cause and code == 0:
        continue
    raise RuntimeError(f'Unexpected simulation termination: {cause}, {code}')
with open(os.path.join(m5.options.outdir, 'exit.json'), 'w') as f:
    json.dump({'args': vars(a), 'events': events}, f, indent=2)
print(f'ILP experiment complete: {cause}; code={code}; tick={m5.curTick()}')
if code:
    raise SystemExit(code)
