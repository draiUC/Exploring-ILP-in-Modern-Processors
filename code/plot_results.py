from pathlib import Path
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base=Path(__file__).resolve().parent.parent
out=base/'figures'; out.mkdir(exist_ok=True)
rows=json.loads((base/'results/summary.json').read_text())
d={r['case']:r for r in rows}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors=['#35618d','#32917a','#c17c29']
names=['integer','dependent','floating','memory','branch','pointer']
fig,axs=plt.subplots(1,2,figsize=(10,3.6),gridspec_kw={'width_ratios':[4,1]})
for j,w in enumerate([1,2,4]):
    axs[0].bar(np.arange(5)+(j-1)*.24,[d[f'{n}_w{w}']['ipc'] for n in names[:5]],width=.24,label=f'{w} wide',color=colors[j])
    axs[1].bar(j,d[f'pointer_w{w}']['ipc'],color=colors[j])
axs[0].set_xticks(range(5),['Independent\ninteger','Dependent\ninteger','Floating\npoint','L1 loads','Branches'])
axs[0].set_ylabel('Committed instructions per cycle')
axs[0].legend(frameon=False,ncol=3,loc='upper left')
axs[0].set_ylim(0,4.3)
axs[1].set_xticks(range(3),['1','2','4']);axs[1].set_xlabel('Width');axs[1].set_title('Pointer chasing',fontsize=10)
axs[1].set_ylim(0,.026)
for ax in axs: ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.tight_layout();fig.savefig(out/'issue_width.png',dpi=220);plt.close(fig)

fig,ax=plt.subplots(figsize=(8.8,3.7))
pairs=['integer_floating','memory_integer','integer_integer','pointer_integer']
for j,policy in enumerate(['partitioned','dynamic']):
    vals=[d[f'smt_{p}_{policy}']['sequential_pair_speedup'] for p in pairs]
    bars=ax.bar(np.arange(4)+(j-.5)*.32,vals,width=.32,label=policy.capitalize()+' IQ and ROB',color=colors[j])
    ax.bar_label(bars,fmt='%.3f',fontsize=9,padding=3)
ax.axhline(1,color='black',lw=1,ls='--');ax.set_ylim(0,1.2)
ax.set_xticks(range(4),['Integer + FP','L1 loads + integer','Integer + integer','Pointer + integer'])
ax.set_ylabel('Sequential pair cycles / SMT cycles')
ax.legend(frameon=False,ncol=2,loc='upper center');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.tight_layout();fig.savefig(out/'smt_speedup.png',dpi=220);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(9,3.5))
for j,key in enumerate(['branch_local','branch_w1']):
    axs[0].bar(j,d[key]['ipc'],color=colors[j]);axs[1].bar(j,d[key]['branch_mpki'],color=colors[j])
for ax in axs: ax.set_xticks([0,1],['Local','Tournament']);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
axs[0].set_ylabel('Committed instructions per cycle');axs[1].set_ylabel('Mispredictions per 1000 instructions')
fig.tight_layout();fig.savefig(out/'branch_prediction.png',dpi=220);plt.close(fig)

events=list(csv.DictReader((base/'results/pipeline_events.csv').open()))
sample=[x for x in events if 400<=int(x['seq'])<414]
fig,ax=plt.subplots(figsize=(10,4.5))
stages=['fetch','decode','rename','dispatch','issue','complete','retire']
markers=['o','s','^','v','D','P','X']; cols=['#333333','#35618d','#755c9b','#b26d2e','#be453f','#32917a','#111111']
start=min(int(x['fetch'])//1000 for x in sample)
for j,stage in enumerate(stages):
    ax.scatter([int(x[stage])/1000-start for x in sample],range(len(sample)),label=stage.capitalize(),s=29,marker=markers[j],color=cols[j])
for i,row in enumerate(sample):
    ax.plot([int(row['fetch'])/1000-start,int(row['retire'])/1000-start],[i,i],color='#bbbbbb',lw=.8,zorder=0)
ax.set_yticks(range(len(sample)),[f"{x['seq']}  {x['asm']}" for x in sample],fontsize=8)
ax.invert_yaxis();ax.set_xlabel(f'Cycles after cycle {start} at 1 GHz');ax.set_xlim(-1,25)
ax.set_xticks(range(0,26,2));ax.grid(axis='x',alpha=.2)
ax.legend(frameon=False,ncol=7,fontsize=8,loc='upper center',bbox_to_anchor=(.45,1.15))
fig.tight_layout();fig.savefig(out/'pipeline_timeline.png',dpi=220);plt.close(fig)

fig,ax=plt.subplots(figsize=(9,3.6))
for n,c in [('integer',colors[0]),('dependent',colors[2])]:
    ax.plot([1,2,4],[d[f'{n}_w{w}']['mean_fetch_retire_cycles'] for w in [1,2,4]],'o-',label=n.capitalize(),color=c)
ax.set_xlabel('Front end and back end width');ax.set_ylabel('Mean fetch to retire latency in cycles')
ax.set_xticks([1,2,4]);ax.legend(frameon=False);ax.grid(alpha=.18)
fig.tight_layout();fig.savefig(out/'latency.png',dpi=220);plt.close(fig)
print('Saved five charts from measured data')
