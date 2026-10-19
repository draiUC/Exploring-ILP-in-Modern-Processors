import os
import m5
from m5.objects import (
    AddrRange, ArmTimingSimpleCPU, DDR3_1600_8x8, MemCtrl, Process,
    Root, SEWorkload, SrcClockDomain, System, SystemXBar, VoltageDomain,
)

binary = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello-arm64")
system = System()
system.clk_domain = SrcClockDomain(clock="1GHz", voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]
system.cpu = ArmTimingSimpleCPU()
system.membus = SystemXBar()
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports
system.cpu.createInterruptController()
system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports
system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()
root = Root(full_system=False, system=system)
m5.instantiate()
exit_event = m5.simulate()
print(f"Simulation finished: {exit_event.getCause()}; code={exit_event.getCode()}")
if exit_event.getCode() != 0:
    raise SystemExit(exit_event.getCode())
