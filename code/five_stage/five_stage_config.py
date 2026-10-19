"""Run the compiled FiveStageCPU teaching component inside gem5."""
import argparse
import json
from pathlib import Path
import m5
from m5.objects import FiveStageCPU, Root, SrcClockDomain, VoltageDomain

p=argparse.ArgumentParser()
p.add_argument('--workload',required=True)
p.add_argument('--prediction',choices=['on','off'],required=True)
a=p.parse_args()
w=json.loads(Path(a.workload).read_text())
cpu=FiveStageCPU(
    clk_domain=SrcClockDomain(clock='1GHz',voltage_domain=VoltageDomain()),
    program=w['program'], prediction=a.prediction=='on',
    bht_entries=64, memory_words=256, initial_memory=w['initial_memory'],
    expected_reg_indices=list(range(32)),expected_reg_values=w['expected_registers'],
    expected_mem_indices=list(range(256)),expected_mem_values=w['expected_memory'],
    trace_file=str(Path(m5.options.outdir)/'pipeline.csv'),
    summary_file=str(Path(m5.options.outdir)/'five_stage_summary.json'),
)
root=Root(full_system=False,cpu=cpu)
m5.instantiate()
event=m5.simulate()
print(f'Five-stage result: {event.getCause()}; code={event.getCode()}')
if event.getCode()!=0:raise SystemExit(event.getCode())
