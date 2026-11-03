"""Blind packets, strict budgets, duplicate/split checks. No API calls."""
import sys,json,hashlib,difflib,time
from pathlib import Path
from controlled import ROOT,HERE,OUT,DATA,sha,tokens,pack,summarize,evidence_summary,SYSTEM,POLICY
from evidence import select

def graph_lines(graphs):
 out=[]
 for g in graphs:
  out.append('File: '+g['provenance']['file'])
  for n in g['nodes']:out.append(json.dumps({k:v for k,v in n.items() if k in {'id','type','name','symbol','kind','trust','effectiveness','category','evidence_snippets'}},separators=(',',':')))
  out.extend(json.dumps(e,separators=(',',':')) for e in g['edges'])
 return out

def build():
 cases=json.loads((DATA/'cases.json').read_text());static={r['case_id']:r for r in json.loads((OUT/'static.json').read_text())};jobs=[];packets=[]
 for c in cases:
  start=time.perf_counter();versions=static[c['case_id']]['versions'];base=graph_lines(versions['C'].get('graphs',[]))
  before=summarize(c['before'],c['approved']);preview=summarize(c['after'],c['approved'])
  bs,bspans=evidence_summary(before,c['before']);ps,pspans=evidence_summary(preview,c['after'])
  current=['Verified current-state summary: '+bs,'Counterfactual summary of explicitly proposed patch (not an observed future state): '+ps]+['Current supporting source: '+json.dumps(x,separators=(',',':')) for x in bspans]+['Proposed supporting source: '+json.dumps(x,separators=(',',':')) for x in pspans]
  # Historical condition receives the same current semantic facts first, then linked history.
  hist=[]
  for r in c['records'][:-1]:
   s=r['summary'];small={k:s.get(k) for k in ['restriction_status','combined_policy_status','restriction_formula','witness','input_independent','shell','unknown']}
   hist.append(json.dumps({'event_index':r['event_index'],'source_event_sha256':r['event_sha256'],'changed_paths':r['changed_paths'],'restriction_transition':r['restriction_transition'],'summary':small},separators=(',',':')))
  history_assumption=current[:2]+['Earlier source change: '+x for x in reversed(hist)]+current[2:]
  # Temporal graph uses relational summaries but excludes verification statuses/witnesses.
  facts=[];events=[]
  for r in c['records'][:-1]:
   s=r['summary'];sources=s.get('source_spans',[])
   if not sources:continue
   anchor=sources[0];txt='At earlier action '+str(r['event_index'])+': restriction='+str(s.get('restriction_formula'))+', fixed_arguments='+str(s.get('input_independent'))+', shell='+str(s.get('shell'))
   facts.append({'id':'summary:'+str(r['event_index']),'text':txt,'path':'runner.py','span':[anchor['line_start'],anchor['line_end']],'source_sha256':anchor['source_sha256'],'kind':'assumption','depends_on':[],'confidence':'bounded symbolic summary'})
   events.append({'index':r['event_index'],'boundary':len(c['history']),'changed_paths':['runner.py'],'established_source_hashes':[anchor['source_sha256']],'description':','.join(r['changed_paths'])})
  selected=select(facts,events,'runner.py '+c['action'],1024,tokens)
  changes=[];prev=c['history'][0]['files']
  for i,h in enumerate(c['history'][1:],1):
   for fn in h['files']:
    if prev.get(fn)!=h['files'][fn]:changes.append('Earlier action '+str(i)+': '+''.join(difflib.unified_diff(prev.get(fn,'').splitlines(True),h['files'][fn].splitlines(True),fromfile=fn+' before',tofile=fn+' after')))
   prev=h['files']
  g0=versions['A'].get('graphs',[]);g1=versions['C'].get('graphs',[])
  def descriptors(gs):
   nodes=set();edges=set()
   for g in gs:
    nodes|={json.dumps({k:n.get(k) for k in ['id','type','name','symbol','kind']},sort_keys=True) for n in g['nodes']};edges|={json.dumps(e,sort_keys=True) for e in g['edges']}
   return nodes,edges
  n0,e0=descriptors(g0);n1,e1=descriptors(g1)
  differences=['Added nodes: '+str(sorted(n1-n0)),'Removed nodes: '+str(sorted(n0-n1)),'Added edges: '+str(sorted(e1-e0)),'Removed edges: '+str(sorted(e0-e1)),*base]
  ref=['Current policy source:\n'+c['before']['policy.py'],'Current runner source:\n'+c['before']['runner.py'],'Historical policy source:\n'+c['history'][0]['files']['policy.py']]
  ref+=['Import support '+f+':\n'+t for f,t in c['before'].items() if f.startswith('layer')]
  enc=__import__('tiktoken').get_encoding('o200k_base');hs='\n'.join([*base,*changes]);ids=enc.encode(hs,disallowed_special=());hs=enc.decode(ids[-1024:])
  evidence={'static':pack(base),'static_history':hs,'graph_diff':pack(differences),'temporal':selected['graph'],'assumption':pack(history_assumption),'current_summary':pack(current),'reference':pack(ref),'prose':selected['prose']}
  for name,ev in evidence.items():
   assert tokens(ev)<=1024
   messages=[{'role':'system','content':SYSTEM},{'role':'user','content':'AUTHORIZED PROPERTY:\n'+c['policy']+'\n\nPRIOR SOURCE EVIDENCE AND EXPLICIT PATCH PREVIEW:\n'+ev+'\n\nPROPOSED ACTION:\n'+c['action']}]
   j={'experiment':'E2-continuation','case_id':c['case_id'],'group':c['group'],'split':c['split'],'label':c['label'],'condition':name,'evidence_budget':1024,'evidence_tokens':tokens(ev),'messages':messages,'metadata':{'family':c['family'],'depth':c['depth'],'gap':c['gap'],'variant':c['variant'],'fact_hash':selected['fact_hash'] if name in {'temporal','prose'} else None,'source_packet_seconds':time.perf_counter()-start}}
   j['prompt_hash']=hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest();j['job_id']=sha({k:v for k,v in j.items() if k!='metadata'})[:24];jobs.append(j)
  packets.append({'case_id':c['case_id'],'evidence':evidence,'selected_facts':selected['facts'],'paired_fact_hash':selected['fact_hash'],'current_summary_spans':pspans,'selection_seconds':time.perf_counter()-start})
 splitsets={s:{j['prompt_hash'] for j in jobs if j['split']==s} for s in ['calibration','test']}
 if splitsets['calibration'] & splitsets['test']:raise RuntimeError('duplicate prompts cross split: '+str([(j['condition'],j['case_id'],j['metadata']) for j in jobs if j['prompt_hash'] in splitsets['calibration'] & splitsets['test']][:12]))
 oldhashes={hashlib.sha256(json.dumps(json.loads(l)['messages'],sort_keys=True).encode()).hexdigest() for l in (ROOT/'results/jobs_temporal.jsonl').read_text().splitlines()}
 assert not oldhashes & {j['prompt_hash'] for j in jobs}
 (OUT/'jobs.jsonl').write_text(''.join(json.dumps(j)+'\n' for j in jobs));(OUT/'packets.json').write_text(json.dumps(packets))
 for split in ['calibration','test']:(OUT/(split+'_jobs.jsonl')).write_text(''.join(json.dumps(j)+'\n' for j in jobs if j['split']==split))
 report={'jobs':len(jobs),'unique_prompts':len({j['prompt_hash'] for j in jobs}),'split_overlap':0,'old_prompt_overlap':0,'max_evidence_tokens':max(j['evidence_tokens'] for j in jobs),'calibration_unique':len(splitsets['calibration']),'test_unique':len(splitsets['test']),'model_conditions_hidden':True,'whole_current_action_retained':True,'source_preview':'Only the supplied proposed patch is analyzed, never observed future output.','jobs_sha256':hashlib.sha256((OUT/'jobs.jsonl').read_bytes()).hexdigest()}
 (OUT/'packet_checks.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':build()
