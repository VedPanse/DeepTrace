"""Literal typed version-event DAG and equivalent graph/prose fact serialization."""
import json

def build(events):
 nodes=[];edges=[];facts=[];previous=None
 for event in events:
  t=event['event_index'];a=event['after'];eid=f'edit{t}';sid=f'summary{t}'
  nodes.append({'id':eid,'type':'edit_event','time':t})
  attrs={'predicate':a.get('restriction_formula','unresolved'),'input_independent':a.get('input_independent'),'shell':a.get('shell'),'unknown':a.get('unknown')}
  nodes.append({'id':sid,'type':'security_summary','time':t,'attributes':attrs,'supporting_symbols':a.get('support',[])})
  edges.append({'from':eid,'to':sid,'type':'establishes','status':'source_derived_summary'})
  facts.append({'from':eid,'to':sid,'type':'establishes','attributes':attrs})
  if previous:
   edges.append({'from':previous,'to':sid,'type':'superseded_by','status':'version_order'})
   facts.append({'from':previous,'to':sid,'type':'superseded_by','attributes':{}})
  for j,source in enumerate(a.get('support',[])):
   fid=f'source{t}_{j}';nodes.append({'id':fid,'type':'versioned_program_symbol','name':source,'time':t});edges.append({'from':fid,'to':sid,'type':'supports','status':'resolved_direct_call_chain'})
  previous=sid
 return {'nodes':nodes,'edges':edges,'selection_facts':facts,'claim_boundary':'DAG of versioned events and summaries; not all program dependencies are acyclic'}

def render(facts,style):
 if style=='graph':return '\n'.join(f'{f["from"]} --{f["type"]}--> {f["to"]} '+json.dumps(f['attributes'],separators=(',',':')) for f in facts)
 return ' '.join(f'{f["from"]} {f["type"].replace("_"," ")} {f["to"]}. Attributes: '+json.dumps(f['attributes'],separators=(',',':'))+'.' for f in facts)
