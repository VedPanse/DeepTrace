"""Security-directed bounded dependency selection with explicit event links.
Works on source-supported analyzer facts. Edge confidence retained; no causal claims.
"""
import hashlib,json,re
from collections import deque
def terms(s):return set(re.findall(r'[A-Za-z_][A-Za-z_0-9./-]{2,}',s.lower()))
def select(facts,events,action,budget,count_tokens,horizon=3):
 # facts: id, text, path, span, source_sha256, kind, depends_on, confidence.
 lookup={f['id']:f for f in facts};query=terms(action)
 ranked=sorted(facts,key=lambda f:(-len(query & terms(f['path']+' '+f['text'])),-int(f['kind'] in {'sink','guard','assumption'}),f['id']))
 seeds=[f['id'] for f in ranked if query & terms(f['path']+' '+f['text'])][:8]
 queue=deque((k,0) for k in seeds);seen=set();selected=[]
 while queue:
  key,depth=queue.popleft()
  if key in seen or key not in lookup:continue
  seen.add(key);f=lookup[key]
  if not f.get('source_sha256') or not f.get('span'):continue
  selected.append(f)
  if depth<horizon:
   queue.extend((k,depth+1) for k in sorted(f.get('depends_on',[])))
 linked=[]
 for f in selected:
  for e in reversed(events):
   if e['index']<e['boundary'] and f['path'] in e.get('changed_paths',[]) and f.get('source_sha256') in e.get('established_source_hashes',[]):
    linked.append({'id':'event:'+str(e['index'])+':'+f['id'],'kind':'historical_support','text':f"Earlier action {e['index']} established source for {f['id']}: {e['description']}",'supports':f['id'],'action_index':e['index']});break
 # Both formats retain EXACT same facts, including dependencies and support edges.
 kept=[]
 def formats(rows):
  graph='\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in rows)
  prose='\n'.join('Fact '+r['id']+'. '+r['text']+'. Metadata: '+json.dumps({k:v for k,v in r.items() if k not in {'id','text'}},sort_keys=True,separators=(',',':')) for r in rows)
  return graph,prose
 for f in selected:
  candidates=[f]+[x for x in linked if x['supports']==f['id']]
  # Keep fact and its edit link together, preserving the temporal evidence.
  if max(map(count_tokens,formats(kept+candidates)))<=budget:kept+=candidates
 graph,prose=formats(kept)
 return {'graph':graph,'prose':prose,'facts':kept,'fact_hash':hashlib.sha256(json.dumps(kept,sort_keys=True).encode()).hexdigest(),'seeds':seeds,'approximation':'lexical proposed-action seeds; directed support traversal capped at three; only source-backed edges; not whole-program causal analysis'}
