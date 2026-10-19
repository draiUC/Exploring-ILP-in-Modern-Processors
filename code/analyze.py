"""Analyze real gem5 statistics and O3PipeView event timestamps."""
from pathlib import Path
import csv
import json
import statistics
import re
import gzip

base = Path(__file__).resolve().parent.parent
results = base / 'results'
rows = []
stage_rows = []
for directory in sorted(results.iterdir()):
    if not directory.is_dir() or directory.name.startswith('pilot'):
        continue
    stats = {}
    for line in (directory/'stats.txt').read_text().splitlines():
        fields=line.split()
        if len(fields)>1:
            try: stats[fields[0]]=float(fields[1])
            except ValueError: pass
    meta=json.loads((directory/'exit.json').read_text())
    if meta['events'][-1]['code'] != 0:
        raise ValueError(directory)
    args=meta['args']
    n=stats['simInsts']; cycles=stats['system.cpu.numCycles']
    latencies=[]; execute_latencies=[]; inst=None
    trace=directory/'trace.out'
    trace_gz=directory/'trace.out.gz'
    trace_stream = trace.open() if trace.exists() else gzip.open(trace_gz,'rt')
    with trace_stream as f:
        for line in f:
            if not line.startswith('O3PipeView:'): continue
            fields=line.rstrip().split(':')
            event=fields[1]
            if event=='fetch':
                inst={'seq':int(fields[5]),'pc':fields[3], 'asm':':'.join(fields[6:]).strip(),'fetch':int(fields[2])}
            elif inst is not None:
                inst[event]=int(fields[2])
                if event=='retire' and inst['retire']>0:
                    latencies.append((inst['retire']-inst['fetch'])/1000)
                    if inst.get('complete',0)>0:
                        execute_latencies.append((inst['complete']-inst['fetch'])/1000)
                    if directory.name=='integer_w1': stage_rows.append(inst.copy())
    threads=2 if args['second'] else 1
    tinst=[stats.get(f'system.cpu.commitStats{i}.numInsts',0) for i in range(threads)]
    mispred=sum(stats.get(f'system.cpu.branchPred.mispredicted_{i}::total',0) for i in range(threads))
    branches=sum(stats.get(f'system.cpu.branchPred.committed_{i}::total',0) for i in range(threads))
    row={'case':directory.name,'model':args['model'],'width':args['width'],'predictor':args['predictor'],
         'threads':threads,'instructions':int(n),'cycles':int(cycles),'ipc':n/cycles,'cpi':cycles/n,
         'trace_committed_ops':len(latencies),'mean_fetch_retire_cycles':statistics.mean(latencies) if latencies else '',
         'mean_fetch_complete_cycles':statistics.mean(execute_latencies) if execute_latencies else '',
         'latency_p95_cycles':sorted(latencies)[int(.95*(len(latencies)-1))] if latencies else '',
         'mispredictions':int(mispred),'branches':int(branches),'branch_mpki':1000*mispred/n,
         'rob_full_events':int(stats.get('system.cpu.rename.ROBFullEvents',0)),
         'iq_full_events':int(stats.get('system.cpu.iew.iqFullEvents',0)),
         'lsq_full_events':int(stats.get('system.cpu.iew.lsqFullEvents',0)),
         'fu_busy_events':int(stats.get('system.cpu.fuBusy::total',0)),
         'thread0_insts':int(tinst[0]),'thread1_insts':int(tinst[1]) if threads==2 else 0}
    if args['model']=='timing':
        row.update(predictor='none',mispredictions='',branches='',branch_mpki='')
    rows.append(row)
by_name={x['case']:x for x in rows}
for row in rows:
    row['sequential_pair_speedup']=''
    row['weighted_speedup']=''
    if row['threads']==2:
        _,a,b,policy=row['case'].split('_')
        solo1=by_name[f'{a}_w4']; solo2=by_name[f'{b}_w4']
        row['sequential_pair_speedup']=(solo1['cycles']+solo2['cycles'])/row['cycles']
        row['weighted_speedup']=(row['thread0_insts']/row['cycles'])/solo1['ipc']+(row['thread1_insts']/row['cycles'])/solo2['ipc']
with (results/'summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(results/'summary.json').write_text(json.dumps(rows,indent=2))
fields=['seq','pc','asm','fetch','decode','rename','dispatch','issue','complete','retire']
with (results/'pipeline_events.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(stage_rows)
print(json.dumps(rows,indent=2))
