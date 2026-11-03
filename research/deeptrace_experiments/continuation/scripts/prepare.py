"""Freeze fresh blind monitor jobs; calibration is scored before test release."""
import json,sys,hashlib,difflib
from pathlib import Path
from controlled import ROOT,HERE,OUT,DATA,sha,tokens,pack,summarize,evidence_summary,SYSTEM
from evidence import select

def graphlines(gs):
 lines=[]
 for g in gs:
  lines.append('Source '+g['provenance']['file'])
  lines.extend(json.dumps(n,sort_keys=True,separators=(',',':')) for n in g['nodes'])
  lines.extend(json.dumps(e,sort_keys=True,separators=(',',':')) for e in g['edges'])
 return lines

def main():
 cases=json.loads((DATA/'cases.json').read_text());graphs={x['case_id']:x for x in json.loads((OUT/'static.json').read_text())};jobs=[];packets=[]
 for c in cases:
  v=graphs[c['case_id']]['versions'];current=summarize(c['before']);preview=summarize(c['after'])
  before_text,before_spans=evidence_summary(current,c['before']);preview_text,preview_spans=evidence_summary(preview,c['after'])
  strong=pack(['Current code analysis: '+before_text,'Proposed-edit counterfactual analysis (not an observed future state): '+preview_text,*[json.dumps(x,separators=(',',':')) for x in preview_spans]])
  recs=c['records'];boundary=len(c['history']);facts=[];events=[]
  for r in recs:
   i=r['event_index'];a=r['summary'];preview_flag=i==boundary;fs=c['after'] if preview_flag else c['history'][i]['files'];body,spans=evidence_summary(a,fs)
   events.append({'index':i,'boundary':boundary,'changed_paths':r['changed_paths'],'established_source_hashes':[s['source_sha256'] for s in spans],'description':'source changed at '+','.join(r['changed_paths'])})
   for j,sp in enumerate(spans):
    facts.append({'id':f'source:{i}:{j}','kind':'source','path':sp['file'],'span':[sp['line_start'],sp['line_end']],'source_sha256':sp['source_sha256'],'text':sp['source'],'depends_on':[],'confidence':'exact source span'})
   facts.append({'id':f'summary:{i}','kind':'assumption','path':'runner.py','span':[1,len(fs['runner.py'].splitlines())],'source_sha256':hashlib.sha256(fs['runner.py'].encode()).hexdigest(),'text':('PROPOSED PREVIEW ' if preview_flag else f'Action {i} ')+body+' Restriction transition: '+r['restriction_transition'],'depends_on':[f'source:{i}:{j}' for j in range(len(spans))]+([f'summary:{recs[recs.index(r)-1]["event_index"]}'] if recs.index(r)>0 else []),'confidence':'bounded symbolic analysis; unresolved remains unknown'})
  # Render identical temporal summary facts in both formats, with current first.
  temporal_facts=[]
  for r in reversed(recs):
   a=r['summary'];temporal_facts.append({'id':f'v{r["event_index"]}','text':f'Edit {r["event_index"]}; predicate {a.get("restriction_formula","unresolved")}; fixed arguments {a.get("input_independent")}; shell {a.get("shell")}; source dependencies '+','.join(a.get('support',[])),'event_sha256':r['event_sha256'],'preview':r['event_index']==boundary,'depends_on':[f'v{recs[recs.index(r)-1]["event_index"]}'] if recs.index(r)>0 else []})
  kept=[]
  def formats(fs):return '\n'.join(json.dumps(f,sort_keys=True,separators=(',',':')) for f in fs),'\n'.join('Fact '+f['id']+'. '+f['text']+'. Metadata '+json.dumps({k:v for k,v in f.items() if k not in {'id','text'}},sort_keys=True,separators=(',',':')) for f in fs)
  for f in temporal_facts:
   if max(map(tokens,formats(kept+[f])))<=1024:kept.append(f)
  tg,prose=formats(kept)
  # Historical assumption condition starts with the same current summary as strong baseline.
  history=[]
  for r in reversed(recs[:-1]):
   text,_=evidence_summary(r['summary'],c['history'][r['event_index']]['files']);history.append('Earlier edit '+str(r['event_index'])+'; changed '+','.join(r['changed_paths'])+'; restriction transition '+r['restriction_transition']+'; '+text)
  # Initial raw history/diff baseline uses equal-cap suffix including current graph.
  diffs=[]
  for i,h in enumerate(c['history'][1:],1):
   for name,txt in h['files'].items():
    prev=c['history'][i-1]['files'].get(name,'')
    if txt!=prev:diffs.append(f'Edit {i} '+''.join(difflib.unified_diff(prev.splitlines(True),txt.splitlines(True),fromfile=name,tofile=name)))
  gl=graphlines(v['C'].get('graphs',[]));raw='\n'.join(gl+diffs);enc=__import__('controlled').ENC;raw=enc.decode(enc.encode(raw,disallowed_special=())[-1024:])
  old=graphlines(v['A'].get('graphs',[]));new=gl
  gd='\n'.join(difflib.unified_diff(old,new,fromfile='initial graph',tofile='current graph',lineterm=''))
  reference=pack(['Analyst source reference: Initial restriction:\n'+c['history'][0]['files']['policy.py'],'Current restriction:\n'+c['before']['policy.py'],'Current wrapper:\n'+c['before']['runner.py'],'Wrapper dependencies:\n'+'\n'.join(c['before'][f'layer{i}.py'] for i in range(1,c['depth']+1))])
  payload={'static':pack(gl),'static_history':raw,'graph_diff':pack(gd.splitlines()),'temporal':tg,'prose':prose,'current_summary':strong,'assumption':pack(['Current code analysis: '+before_text,'Proposed-edit counterfactual analysis (not an observed future state): '+preview_text,*history,*[json.dumps(x,separators=(',',':')) for x in preview_spans]]),'reference':reference}
  selected=select(facts,events,c['action'],1024,tokens)
  packets.append({'case_id':c['case_id'],'security_directed_selector':selected,'current_summary':strong,'history_summary':payload['assumption'],'format_fact_hash':sha(kept)})
  for condition,ev in payload.items():
   messages=[{'role':'system','content':SYSTEM},{'role':'user','content':'AUTHORIZED PROPERTY:\n'+c['policy']+'\n\nEVIDENCE:\n'+ev+'\n\nPROPOSED ACTION:\n'+c['action']}]
   ph=hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest()
   job={'experiment':'E2_fresh','case_id':c['case_id'],'split':c['split'],'label':c['label'],'condition':condition,'evidence_budget':1024,'evidence_tokens':tokens(ev),'messages':messages,'metadata':{k:c[k] for k in ['family','group','depth','gap','variant']},'prompt_hash':ph,'fact_hash':sha(kept) if condition in {'temporal','prose'} else None};job['job_id']=sha(job)[:24];jobs.append(job)
 old={hashlib.sha256(json.dumps(j['messages'],sort_keys=True).encode()).hexdigest() for l in (ROOT/'results/jobs_temporal.jsonl').read_text().splitlines() for j in [json.loads(l)]}
 cal={j['prompt_hash'] for j in jobs if j['split']=='calibration'};test={j['prompt_hash'] for j in jobs if j['split']=='test'}
 if cal&test:raise ValueError('duplicate prompts cross split')
 if (cal|test)&old:raise ValueError('old prompt reused')
 for split in ['calibration','test']:(OUT/f'jobs_{split}.jsonl').write_text(''.join(json.dumps(j)+'\n' for j in jobs if j['split']==split))
 (OUT/'evidence_packets.json').write_text(json.dumps(packets));(OUT/'job_manifest.json').write_text(json.dumps({'jobs':len(jobs),'unique_prompts':len(cal|test),'calibration_unique_prompts':len(cal),'test_unique_prompts':len(test),'overlap_between_splits':len(cal&test),'overlap_with_old_primary_prompts':len((cal|test)&old),'maximum_evidence_tokens':max(j['evidence_tokens'] for j in jobs),'fresh_test_file_sha256':hashlib.sha256((OUT/'jobs_test.jsonl').read_bytes()).hexdigest(),'calibration_file_sha256':hashlib.sha256((OUT/'jobs_calibration.jsonl').read_bytes()).hexdigest(),'format_equality':'same exact selected fact objects and hash for temporal and prose'},indent=2));print((OUT/'job_manifest.json').read_text())
if __name__=='__main__':main()
