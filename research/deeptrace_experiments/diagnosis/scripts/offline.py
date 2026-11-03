"""Diagnostic reuse of inspected data. NO model calls, NO held-out claims."""
import json,hashlib,collections,math,statistics,html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];PREV=ROOT/'continuation';OUT=ROOT/'diagnosis/results';ART=ROOT.parents[1]/'output/deeptrace_diagnosis';OUT.mkdir(exist_ok=True);ART.mkdir(exist_ok=True)
def load(p):return [json.loads(l) for l in p.read_text().splitlines()]
def auc(y,s):
 p=np.array([v for a,v in zip(y,s) if a]);n=np.array([v for a,v in zip(y,s) if not a]);return float(((p[:,None]>n).sum()+.5*(p[:,None]==n).sum())/(len(p)*len(n))) if len(p)*len(n) else None
def roc(y,s):
 levels=[float('inf')]+sorted(set(s),reverse=True)+[float('-inf')];P=sum(y);N=len(y)-P
 return [{'threshold':t if math.isfinite(t) else str(t),'tpr':sum(a and v>t for a,v in zip(y,s))/P,'fpr':sum(not a and v>t for a,v in zip(y,s))/N} for t in levels]
def summarize(rs):
 y=[r['label'] for r in rs];s=[r['monitor']['score'] for r in rs];ph=collections.defaultdict(list)
 for r in rs:ph[r['prompt_hash']].append(r)
 unique_pairs=list({(r['prompt_hash'],r['label']):r for r in rs}.values())
 dist={}
 for label in [0,1]:
  vals=[r['monitor']['score'] for r in rs if r['label']==label];dist[str(label)]={'n':len(vals),'histogram':dict(sorted(collections.Counter(vals).items())),'min':min(vals),'median':statistics.median(vals),'max':max(vals)}
 return {'cases':len(rs),'unique_prompts':len(ph),'ambiguous_prompt_hashes':sum(len({r['label'] for r in rr})>1 for rr in ph.values()),'auc_case_weighted':auc(y,s),'auc_unique_prompt_label_pairs':auc([r['label'] for r in unique_pairs],[r['monitor']['score'] for r in unique_pairs]),'distributions':dist,'roc':roc(y,s),'interpretation':'diagnostic reuse, correlated variants; unique-prompt-label pairs can share a response across classes'}
def main():
 rows=load(PREV/'results/calibration_scores.jsonl')+load(PREV/'results/test_scores.jsonl');jobs={j['job_id']:j for j in load(PREV/'results/jobs.jsonl')};cases={c['case_id']:c for c in json.loads((PREV/'data/cases.json').read_text())};thresholds=json.loads((PREV/'results/thresholds.json').read_text())['conditions'];conditions=sorted({r['condition'] for r in rows});summary={};forcing={}
 for phase in ['calibration','test']:
  summary[phase]={}
  for cond in conditions:
   rs=[r for r in rows if r['split']==phase and r['condition']==cond];summary[phase][cond]=summarize(rs)
 for cond in conditions:
  rs=[r for r in rows if r['condition']==cond and r['split']=='calibration' and not r['label']];tau=thresholds[cond]['threshold'];groups={}
  for r in rs:
   if r['monitor']['score']>=tau:
    h=r['prompt_hash']
    if h not in groups:groups[h]={'prompt_hash':h,'score':r['monitor']['score'],'response':r['monitor']['reason'],'case_ids':[],'variants':[],'evidence_packet':jobs[r['job_id']]['messages'][1]['content']}
    groups[h]['case_ids'].append(r['case_id']);groups[h]['variants'].append(r['metadata']['variant'])
  forcing[cond]={'threshold':tau,'safe_cases_at_or_above':sum(len(g['case_ids']) for g in groups.values()),'unique_responses_at_or_above':len(groups),'examples':list(groups.values())}
 # Several matched triples, selected from the now-inspected DEVELOPMENT pool.
 matched=[]
 for fam in ['cal_reversed','held_nested','held_conditional']:
  for depth in [2,4]:
   cs=[c for c in cases.values() if c['family']==fam and c['depth']==depth and c['gap']==0 and c['variant'] in ['equivalent','weakened','repaired']]
   if not cs:continue
   group={'family':fam,'depth':depth,'development_only':True,'cases':[]}
   for c in sorted(cs,key=lambda c:['equivalent','weakened','repaired'].index(c['variant'])):
    observations=[]
    for cond in ['static','current_summary','assumption','reference']:
     r=next(r for r in rows if r['case_id']==c['case_id'] and r['condition']==cond);j=jobs[r['job_id']]
     observations.append({'condition':cond,'score':r['monitor']['score'],'response':r['monitor']['reason'],'prompt_hash':r['prompt_hash'],'exact_messages':j['messages']})
    group['cases'].append({'case_id':c['case_id'],'variant':c['variant'],'approved':c['approved'],'policy':c['policy'],'current_code':c['before'],'proposed_patch':c['action'],'proposed_code':c['after'],'verified_current':c['records'][-2]['summary'],'verified_preview':c['records'][-1]['summary'],'label':c['label'],'observations':observations})
   matched.append(group)
 # Prior pilot AUC, same budget, kept separate from continuation (not pooled).
 old=load(ROOT/'results/scores.jsonl');old=[r for r in old if r.get('experiment')=='E2' and r.get('evidence_budget')==1024 and r.get('split')=='test' and r.get('monitor',{}).get('status')=='ok'];oldstats={}
 for cond in sorted({r['condition'] for r in old}):oldstats[cond]=summarize([r for r in old if r['condition']==cond])
 (OUT/'score_diagnostics.json').write_text(json.dumps({'warning':'DIAGNOSTIC REUSE OF INSPECTED DATA. Not a fresh held-out result. No new model calls.','continuation':summary,'old_pilot_1024_test_separate':oldstats},indent=2));(OUT/'threshold_forcing_cases.json').write_text(json.dumps(forcing,indent=2));(OUT/'matched_cases.json').write_text(json.dumps(matched,indent=2))
 plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
 fig,axes=plt.subplots(2,4,figsize=(16,8),sharex=True,sharey=True)
 for ax,cond in zip(axes.flat,conditions):
  for phase,col in [('calibration','#6a8aa1'),('test','#b34b33')]:
   v=summary[phase][cond];curve=v['roc'];ax.plot([p['fpr'] for p in curve],[p['tpr'] for p in curve],marker='.',color=col,label=f"{phase}: AUC {v['auc_case_weighted']:.2f}")
  ax.plot([0,1],[0,1],':',color='#aaa');ax.set_title(cond);ax.legend(loc='lower right',fontsize=8);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.set_xlabel('False-positive rate');ax.set_ylabel('Detection rate')
 fig.suptitle('Diagnostic score ranking on already inspected examples; repeated cases are dependent');fig.tight_layout();fig.savefig(ART/'roc.png',dpi=150);fig.savefig(ART/'roc.pdf');plt.close(fig)
 fig,axes=plt.subplots(2,4,figsize=(16,8),sharex=True)
 for ax,cond in zip(axes.flat,conditions):
  for label,col,name in [(0,'#257784','safe'),(1,'#c45a3f','unsafe')]:
   ss=[r['monitor']['score'] for r in rows if r['condition']==cond and r['split']=='test' and r['label']==label];ax.hist(ss,bins=np.arange(0,1051,50),weights=np.ones(len(ss))/len(ss),alpha=.55,color=col,label=name)
  ax.axvline(thresholds[cond]['threshold'],color='black',ls='--',lw=1);ax.set_title(cond);ax.set_xlabel('Suspicion score');ax.set_ylabel('Fraction within class');ax.legend(fontsize=8)
 fig.suptitle('Inspected test score distributions; dashed line is the frozen calibration threshold');fig.tight_layout();fig.savefig(ART/'distributions.png',dpi=150);fig.savefig(ART/'distributions.pdf');plt.close(fig)
 # Exact source + packet + response in a browser-readable case notebook.
 body=['<h1>DeepTrace mistake notebook</h1><p>Development diagnosis of already inspected examples. No new model calls or held-out claim.</p>']
 for g in matched:
  body.append('<h2>'+html.escape(g['family'])+' / depth '+str(g['depth'])+'</h2><div class="triple">')
  for c in g['cases']:
   body.append('<article><h3>'+html.escape(c['variant'])+' / '+('unsafe' if c['label'] else 'safe under policy')+'</h3><p>Approved token: '+html.escape(c['approved'])+'</p>')
   body.append('<h4>Current policy.py</h4><pre>'+html.escape(c['current_code']['policy.py'])+'</pre><h4>Current runner.py</h4><pre>'+html.escape(c['current_code']['runner.py'])+'</pre><h4>Proposed patch</h4><pre>'+html.escape(c['proposed_patch'])+'</pre>')
   body.append('<details><summary>Exact current modules, including import chain</summary><pre>'+html.escape(json.dumps(c['current_code'],indent=2))+'</pre></details>')
   for o in c['observations']:
    body.append('<h4>'+o['condition']+' / score '+str(o['score'])+'</h4><p>'+html.escape(o['response'])+'</p><details><summary>Exact evidence packet and prompt</summary><pre>'+html.escape(json.dumps(o['exact_messages'],indent=2))+'</pre></details>')
   body.append('</article>')
  body.append('</div>')
 (ART/'mistake_notebook.html').write_text('<!doctype html><meta charset="utf-8"><title>DeepTrace diagnosis</title><style>body{font:17px system-ui;margin:36px;color:#172c39}h1,h2{max-width:1100px}.triple{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}article{border-top:3px solid #257784;min-width:0}pre{font:13px monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f6;padding:12px}summary{cursor:pointer}p{line-height:1.5}</style>'+''.join(body))
 print('TEST AUC AND UNIQUE PROMPTS')
 for c in conditions:print(c,round(summary['test'][c]['auc_case_weighted'],3),summary['test'][c]['unique_prompts'],'ambiguous',summary['test'][c]['ambiguous_prompt_hashes'],'forcing-safe',forcing[c]['safe_cases_at_or_above'])
if __name__=='__main__':main()
