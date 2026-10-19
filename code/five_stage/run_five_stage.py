"""Functional oracle, pipeline invariants and predictor-on/off experiments.

The oracle executes instructions sequentially. It contains no pipeline,
forwarding, speculation or prediction logic, so its result is independent
of the timing implementation in C++.
"""
from pathlib import Path
import hashlib
import json
import csv
import configparser
import subprocess
import sys

here=Path(__file__).resolve().parent
out=here.parents[1]/'results_five_stage'
out.mkdir(exist_ok=True)
gem5=Path.home()/'src/gem5/build/ARM/gem5.opt'

def assemble(source):
    instructions=[];labels={}
    for line in source.strip().splitlines():
        line=line.split('#',1)[0].strip()
        if not line:continue
        if line.endswith(':'):labels[line[:-1]]=len(instructions)
        else:instructions.append(line)
    final=[]
    for line in instructions:
        parts=line.split()
        if parts[0] in ['BEQ','BNE']:
            parts[-1]=str(labels[parts[-1]])
        final.append(' '.join(parts))
    return final

def oracle(program,initial):
    r=[0]*32;mem=(initial+[0]*256)[:256];pc=0;pcs=[]
    for _ in range(10000):
        fields=program[pc].split();op=fields[0];v=list(map(int,fields[1:]));pcs.append(pc)
        nxt=pc+1
        if op=='HALT':return r,mem,pcs
        if op=='ADDI':r[v[0]]=(r[v[1]]+v[2])&((1<<64)-1)
        elif op in ['ADD','SUB','MUL']:
            lhs,rhs=r[v[1]],r[v[2]]
            result=lhs+rhs if op=='ADD' else lhs-rhs if op=='SUB' else lhs*rhs
            r[v[0]]=result&((1<<64)-1)
        elif op=='LD':r[v[0]]=mem[r[v[1]]+v[2]]
        elif op=='ST':mem[r[v[1]]+v[2]]=r[v[0]]
        elif op in ['BEQ','BNE']:
            take=(r[v[0]]==r[v[1]]) if op=='BEQ' else (r[v[0]]!=r[v[1]])
            if take:nxt=v[2]
        elif op!='NOP':raise ValueError(op)
        r[0]=0;pc=nxt
    raise RuntimeError('Oracle watchdog')

programs={
 'straight':('\n'.join(f'ADDI {i} 0 {i}' for i in range(1,13))+'\nHALT',[]),
 'forwarding':('''ADDI 1 0 2
ADDI 2 1 3
ADD 3 1 2
MUL 4 3 2
SUB 5 4 3
ADDI 0 0 99
ADD 6 0 5
HALT''',[]),
 'load_use':('''LD 1 0 0
ADD 2 1 1
ST 2 0 1
LD 3 0 1
ADDI 4 3 1
HALT''',[7,11]),
 'loop':('''ADDI 10 0 64
ADDI 2 0 0
ADDI 3 0 0
ADDI 4 0 0
ADDI 5 0 0
again:
ADDI 2 2 1
ADDI 3 3 1
ADDI 4 4 1
ADDI 5 5 1
ADDI 10 10 -1
BNE 10 0 again
HALT''',[]),
 'alternating':('''ADDI 10 0 64
ADDI 1 0 0
ADDI 2 0 1
ADDI 3 0 0
again:
SUB 1 2 1
BEQ 1 0 skip
ADDI 3 3 1
skip:
ADDI 10 10 -1
BNE 10 0 again
HALT''',[]),
 'wrong_path_store':('''ADDI 1 0 1
BNE 1 0 target
ST 1 0 0
ADDI 2 0 999
target:
ADDI 2 0 42
HALT''',[123]),
 'wrong_path_halt':('''LD 1 0 0
BNE 1 0 target
HALT
target:
ADDI 2 0 42
HALT''',[1]),
}

rows=[]
for name,(source,initial) in programs.items():
    program=assemble(source);r,mem,pcs=oracle(program,initial)
    workload={'name':name,'source':source,'program':program,'initial_memory':initial,
              'expected_registers':r,'expected_memory':mem,'expected_retired_pcs':pcs}
    workload_file=out/f'{name}.json';workload_file.write_text(json.dumps(workload,indent=2))
    pair=[]
    for mode in ['off','on']:
        directory=out/f'{name}_{mode}';directory.mkdir(exist_ok=True)
        cmd=[str(gem5),f'--outdir={directory}',str(here/'five_stage_config.py'),
             '--workload',str(workload_file),'--prediction',mode]
        print('RUN',name,mode,flush=True)
        with (directory/'console.log').open('w') as f:
            subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
        result=json.loads((directory/'five_stage_summary.json').read_text())
        assert result['passed'] and result['registers']==r and result['memory']==mem
        assert [x['pc'] for x in result['retired']]==pcs
        assert result['committed']==len(pcs)
        numeric={}
        for line in (directory/'stats.txt').read_text().splitlines():
            fields=line.split()
            if len(fields)>1:
                try:numeric[fields[0]]=float(fields[1])
                except ValueError:pass
        assert numeric['cpu.numCycles']==result['cycles']
        assert numeric['cpu.committedInsts']==result['committed']
        assert abs(numeric['cpu.ipc']-result['ipc'])<1e-5
        assert abs(numeric['cpu.meanResidenceCycles']-result['mean_latency'])<1e-5
        if mode=='off':assert result['predictions']==result['predictor_updates']==result['mispredictions']==0
        occupancy=list(csv.DictReader((directory/'pipeline.csv').open()))
        for inst in result['retired']:
            stage_cycles={s:[] for s in ['IF','ID','EX','MEM','WB']}
            for row in occupancy:
                if int(row['seq'])==inst['seq'] and row['detail']!='squashed':
                    stage_cycles[row['stage']].append(int(row['cycle']))
            assert all(stage_cycles.values()),inst
            assert len(stage_cycles['IF'])==len(stage_cycles['EX'])==len(stage_cycles['MEM'])==len(stage_cycles['WB'])==1
            assert max(stage_cycles['ID'])<stage_cycles['EX'][0]
            assert stage_cycles['MEM'][0]==stage_cycles['EX'][0]+1
            assert stage_cycles['WB'][0]==stage_cycles['MEM'][0]+1
        if name=='straight':
            assert result['cycles']==len(pcs)+4
            assert all(x['wb_end']-x['fetch_start']==5 for x in result['retired'])
        if name=='load_use':assert result['load_use_stalls']==2 and result['cycles']==12
        config=configparser.ConfigParser(strict=False);config.read(directory/'config.ini')
        cfg=dict(config['cpu'])
        for key in ['prediction','trace_file','summary_file']:cfg.pop(key)
        pair.append((result,cfg))
        keep=['cycles','committed','ipc','mean_latency','branches','predictions','predictor_updates',
              'mispredictions','squashed','load_use_stalls','branch_wait_cycles','redirect_bubbles','forwarded_operands']
        rows.append({'workload':name,'prediction':mode,**{k:result[k] for k in keep}})
        print('PASS',name,mode,result['cycles'],'cycles',flush=True)
    assert pair[0][1]==pair[1][1],f'Uncontrolled parameter change in {name}'
    if name=='loop':
        off,on=pair[0][0],pair[1][0]
        assert off['branches']==on['branches']==64
        assert off['branch_wait_cycles']==128
        assert on['mispredictions']==2
        assert off['cycles']==len(pcs)+4+128
        assert on['cycles']==len(pcs)+4+4

(out/'summary.json').write_text(json.dumps(rows,indent=2))
with (out/'summary.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

# Negative control: the compiled CPU must fail when an expected architectural
# value is deliberately wrong. This is validation, not a performance case.
negative=json.loads((out/'straight.json').read_text())
negative['expected_registers'][1]=999
bad_file=out/'negative_expected_state.json';bad_file.write_text(json.dumps(negative,indent=2))
bad_dir=out/'negative_control';bad_dir.mkdir(exist_ok=True)
with (bad_dir/'console.log').open('w') as f:
    failed=subprocess.run([str(gem5),f'--outdir={bad_dir}',str(here/'five_stage_config.py'),
                           '--workload',str(bad_file),'--prediction','off'],stdout=f,stderr=subprocess.STDOUT)
assert failed.returncode==1
assert json.loads((bad_dir/'five_stage_summary.json').read_text())['passed'] is False
manifest={'cases':len(rows),'all_checks_passed':True,
          'negative_control_failed_as_expected':True,
          'binary_sha256':hashlib.sha256(gem5.read_bytes()).hexdigest(),
          'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in here.iterdir() if p.is_file()},
          'invariants':['all architectural state matches a sequential oracle','same retired PC sequence',
                        'only prediction and output paths differ in paired CPU parameters',
                        'all retired instructions visit IF ID EX MEM WB in order',
                        'prediction-off executes zero BHT lookups and updates',
                        'straight program takes N+4 cycles with latency 5',
                        'load-use test takes 12 cycles with two interlocks',
                        'loop control penalties match branch counts and mispredictions']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('ALL FIVE-STAGE CHECKS PASSED',flush=True)
