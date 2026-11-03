"""Explicit source/support/version DAG and edit-driven claim rechecks.
This fuller graph was built after the frozen monitor run; NOT its scored representation.
"""
import json,hashlib,time,ast
from pathlib import Path
from controlled import summarize,sha,DATA,OUT

def build(history,approved):
 nodes={};edges=[];versions=[];previous_files={};previous_claim=None;previous_support=set();previous_status=None;summary=None;rechecks=0
 def node(id,**attrs):nodes.setdefault(id,{'id':id,**attrs});return id
 def edge(a,b,type):
  if a!=b:edges.append({'from':a,'to':b,'type':type})
 for index,h in enumerate(history):
  files=h['files'];changed={p for p in set(files)|set(previous_files) if files.get(p)!=previous_files.get(p)};event=node('event:'+str(index),kind='proposed_patch_preview' if h['edit'].startswith('proposed') else 'completed_edit',index=index,changed_paths=sorted(changed),source_event_sha256=sha(h))
  affected=summary is None or bool(changed & previous_support)
  if not affected:
   versions.append({'index':index,'claim':previous_claim,'status':previous_status,'rechecked':False,'reason':'no supporting source changed'});previous_files=files;continue
  if previous_claim:edge(previous_claim,event,'stale_after_support_edit')
  summary=summarize(files,approved);rechecks+=1
  support_spans=summary.get('source_spans',[])
  if not support_spans:
   # Unknown/removed claims still retain exact candidate sources, with uncertain scope explicit.
   support_spans=[{'file':p,'line_start':1,'line_end':max(1,len(text.splitlines())),'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'symbol':'unresolved_candidate_scope'} for p,text in files.items() if p.endswith('.py')]
  support=[]
  for sp in support_spans:
   content=files[sp['file']];sid='source:'+str(index)+':'+sp['source_sha256']+':'+sp['file'];node(sid,kind='source_version',path=sp['file'],sha256=sp['source_sha256'],first_available_index=index)
   if sp['file'] in changed:edge(event,sid,'establishes_source')
   fid='summary:'+str(index)+':'+sp['file']+':'+sp['symbol'];node(fid,kind='supporting_symbol',span=sp,verification_scope='bounded direct-call Python summary');edge(sid,fid,'supports_symbol');support.append(fid)
  status=summary['restriction_status'];transition='restored' if status=='preserved' and previous_status=='violated' else status
  claim=node('claim:'+str(index),kind='security_assumption',index=index,restriction_status=status,transition=transition,combined_policy_status=summary['combined_policy_status'],formula=summary.get('restriction_formula'),witness=summary.get('witness'),witness_checked=summary.get('witness_checked_by_independent_interpreter',False),verification=summary.get('verification'),unknown_reason=summary.get('reason'))
  for sid in support:edge(sid,claim,'supports_assumption')
  if previous_claim:edge(previous_claim,claim,'superseded_by')
  versions.append({'index':index,'claim':claim,'status':status,'transition':transition,'rechecked':True,'supporting_files':sorted({s['file'] for s in support_spans})})
  previous_claim=claim;previous_status=status;previous_support={s['file'] for s in support_spans};previous_files=files
 # Kahn check rather than assuming program call graphs themselves are DAGs.
 indeg={k:0 for k in nodes};adj={k:[] for k in nodes}
 for e in edges:indeg[e['to']]+=1;adj[e['from']].append(e['to'])
 queue=[k for k,d in indeg.items() if d==0];seen=0
 while queue:
  k=queue.pop();seen+=1
  for v in adj[k]:
   indeg[v]-=1
   if indeg[v]==0:queue.append(v)
 if seen!=len(nodes):raise ValueError('version DAG has a cycle')
 return {'nodes':list(nodes.values()),'edges':edges,'versions':versions,'rechecks':rechecks,'acyclic':True,'scope':'source/support/event DAG, not whole-program causal graph','monitor_scored':False}
if __name__=='__main__':
 cases=json.loads((DATA/'cases.json').read_text());dest=OUT/'support_dags';dest.mkdir(exist_ok=True);rows=[]
 for c in cases:
  start=time.perf_counter();g=build(c['history']+[{'edit':'proposed_counterfactual_not_observed','files':c['after']}],c['approved']);(dest/(c['case_id']+'.json')).write_text(json.dumps(g));rows.append({'case_id':c['case_id'],'nodes':len(g['nodes']),'edges':len(g['edges']),'rechecks':g['rechecks'],'versions':len(g['versions']),'seconds':time.perf_counter()-start})
 (OUT/'support_dag_validation.json').write_text(json.dumps({'histories':len(rows),'all_acyclic':True,'rows':rows,'not_monitor_scored':True,'reason':'full source/support DAG added after frozen run; needs fresh held-out evaluation before performance claims'},indent=2));print('validated DAGs',len(rows),'rechecks',sum(r['rechecks'] for r in rows),'versions',sum(r['versions'] for r in rows))
