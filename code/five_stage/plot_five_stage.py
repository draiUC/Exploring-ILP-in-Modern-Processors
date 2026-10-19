from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Patch

base=Path(__file__).resolve().parents[2]
out=base/'figures';out.mkdir(exist_ok=True)
results=base/'results_five_stage'
rows=json.loads((results/'summary.json').read_text())
d={(r['workload'],r['prediction']):r for r in rows}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
stages=['IF','ID','EX','MEM','WB']
colors=['#365c83','#6989a5','#c18c35','#418c79','#815c88']

def pipeline(workload,filename,limit):
    records=list(csv.DictReader((results/f'{workload}_on/pipeline.csv').open()))
    fig,ax=plt.subplots(figsize=(9.5,3.9))
    for r in records:
        seq=int(r['seq']);cycle=int(r['cycle'])
        if seq>limit or r['detail']=='squashed':continue
        j=stages.index(r['stage'])
        ax.add_patch(Rectangle((cycle-.5,seq-.4),1,.8,facecolor=colors[j],edgecolor='white',lw=.7,
                              hatch='//' if r['detail']=='load_use_stall' else None))
        ax.text(cycle,seq,r['stage'],ha='center',va='center',fontsize=8,color='white')
    labels=[]
    for seq in range(1,limit+1):
        first=next(r for r in records if int(r['seq'])==seq)
        labels.append(f"I{seq}  {first['op']}")
    max_cycle=max(int(r['cycle']) for r in records if int(r['seq'])<=limit)
    ax.set_yticks(range(1,limit+1),labels);ax.set_ylim(limit+.7,.2)
    ax.set_xlim(.4,max_cycle+.7);ax.set_xticks(range(1,max_cycle+1));ax.set_xlabel('CPU cycle at 1 GHz')
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.tight_layout();fig.savefig(out/filename,dpi=220);plt.close(fig)
pipeline('straight','five_stage_pipeline.png',8)
pipeline('load_use','five_stage_load_use.png',6)

fig,axes=plt.subplots(1,2,figsize=(9.5,3.8))
for j,mode in enumerate(['off','on']):
    values=[d[(w,mode)] for w in ['loop','alternating']]
    b=axes[0].bar(np.arange(2)+(j-.5)*.32,[r['cycles'] for r in values],.32,label=f'Prediction {mode}',color=colors[j*2])
    axes[0].bar_label(b,padding=3,fontsize=9)
    b=axes[1].bar(np.arange(2)+(j-.5)*.32,[r['ipc'] for r in values],.32,label=f'Prediction {mode}',color=colors[j*2])
    axes[1].bar_label(b,fmt='%.3f',padding=3,fontsize=9)
for ax in axes:
    ax.set_xticks([0,1],['Counted loop','Alternating branches']);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0].set_ylabel('Cycles to complete identical work');axes[1].set_ylabel('Committed instructions per cycle')
axes[0].set_ylim(0,max(d[(w,'off')]['cycles'] for w in ['loop','alternating'])*1.2)
axes[1].set_ylim(0,1.15);axes[1].legend(frameon=False,fontsize=9)
fig.tight_layout();fig.savefig(out/'five_stage_prediction.png',dpi=220);plt.close(fig)
print('Saved three figures from the compiled five-stage CPU traces')
