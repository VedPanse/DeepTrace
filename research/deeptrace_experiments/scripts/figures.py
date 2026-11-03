import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';OUT=ROOT.parent.parent/'output/pdf/deeptrace_experiment_report/images';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight','pdf.fonttype':42})
metrics=json.loads((R/'temporal_metrics.json').read_text());order=['static','static_history','graph_diff','temporal','assumption','oracle','prose'];labels=['Static','Static +\nhistory','Graph\ndiff','Temporal','Assumption','Reference\nsource','Same facts\nin prose'];colors=['#8395a7']*4+['#2476a8','#7aa889','#a5a0b9']
fig,axs=plt.subplots(2,2,figsize=(11,6.0),sharex='col')
for col,budget in enumerate([512,1024]):
 xs={m['condition']:m for m in metrics if m['budget']==budget};rec=[100*xs[c]['recall'] for c in order];fpr=[100*xs[c]['test_fpr'] for c in order]
 axs[0,col].bar(range(len(order)),rec,color=colors);axs[0,col].set_ylim(0,100);axs[0,col].set_title(f'{budget}-token evidence budget');axs[0,col].set_ylabel('Held-out regression recall (%)');axs[0,col].grid(axis='y',alpha=.2)
 for i,c in enumerate(order):axs[0,col].text(i,rec[i]+2,f"{xs[c]['true_positives']}/{xs[c]['test_positive_n']}",ha='center',fontsize=8)
 axs[1,col].bar(range(len(order)),fpr,color=colors);axs[1,col].axhline(1,color='#b84e4e',linestyle='--',linewidth=1,label='Calibration target cap');axs[1,col].set_ylim(0,max(5,max(fpr)+1));axs[1,col].set_ylabel('Held-out benign FPR (%)');axs[1,col].set_xticks(range(len(order)),labels,rotation=30,ha='right',fontsize=8);axs[1,col].grid(axis='y',alpha=.2)
fig.suptitle('Condition-specific calibration at a 1% FPR cap does not ensure matched held-out FPR',fontsize=12)
fig.tight_layout();fig.savefig(OUT/'temporal_monitor.pdf');fig.savefig(OUT/'temporal_monitor.png',dpi=160);plt.close(fig)
coverage=json.loads((R/'real_coverage.json').read_text());protocol=json.loads((R/'real_protocol.json').read_text());n=len(coverage);no=sum(not x['graph_count'] for x in coverage)
fig,axs=plt.subplots(1,2,figsize=(9.5,3))
axs[0].barh(['Nonempty observed-code graph','Empty observed-code graph'],[n-no,no],color=['#2476a8','#b7c1cb']);axs[0].set_xlabel('Evaluated pre-action boundaries');axs[0].set_xlim(0,n);axs[0].set_title('Original repository snapshots unavailable')
for i,v in enumerate([n-no,no]):axs[0].text(v+2,i,str(v),va='center')
known=sum(v is not None for v in protocol['attack_harm_indices'].values());axs[1].barh(['Recorded landing boundary','No landing boundary'],[known,len(protocol['attack_ids'])-known],color=['#2476a8','#b7c1cb']);axs[1].set_xlabel('Unique recorded-success attack histories');axs[1].set_xlim(0,5.5);axs[1].set_xticks(range(6));axs[1].set_title('Timely detection has an inadequate denominator')
for i,v in enumerate([known,5-known]):axs[1].text(v+.08,i,str(v),va='center')
fig.tight_layout();fig.savefig(OUT/'real_coverage.pdf');fig.savefig(OUT/'real_coverage.png',dpi=160);plt.close(fig)
strata=json.loads((R/'temporal_strata.json').read_text());fig,ax=plt.subplots(figsize=(8,3))
for condition,color in [('static_history','#8395a7'),('temporal','#8e71a6'),('assumption','#2476a8'),('oracle','#7aa889')]:
 ys=[next(x['tp']/x['positive_n']*100 for x in strata if x['budget']==512 and x['condition']==condition and x['dimension']=='gap' and x['value']==v) for v in [0,8,24]]
 ax.plot([0,8,24],ys,marker='o',label=condition.replace('_',' '),color=color)
ax.set_ylim(-3,103);ax.set_xticks([0,8,24]);ax.set_xlabel('Unrelated edits between guard and argument changes');ax.set_ylabel('Held-out regression recall (%)');ax.legend(ncol=2,fontsize=9);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'edit_distance.pdf');plt.close(fig)
