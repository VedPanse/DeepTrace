"""Non-invasive metrics, evidence budget baselines and literal graph SVG exports."""
import json,math,re,random,collections,hashlib,html,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';V=ROOT/'visualizations';V.mkdir(exist_ok=True)
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x]
def dump(p,x):p.write_text(json.dumps(x,indent=2))
def acyclic(g):
 ids={n['id'] for n in g['nodes']};incoming={x:0 for x in ids};out=collections.defaultdict(list)
 for e in g['edges']:incoming[e['to']]+=1;out[e['from']].append(e['to'])
 q=collections.deque(x for x in ids if not incoming[x]);count=0
 while q:
  x=q.popleft();count+=1
  for y in out[x]:
   incoming[y]-=1
   if not incoming[y]:q.append(y)
 return count==len(ids)
rows=[];selected=[]
for folder in sorted((R/'product').iterdir()):
 gs=read(folder/'security-adg.jsonl');s=json.loads((folder/'measurement.json').read_text());summary=s['summary']
 paper=[g for g in read(R/'paper/security-adg.jsonl') if g['provenance']['repo'].split('/')[-1]==folder.name]
 represented={g['provenance']['file'] for g in gs}
 rows.append({'repository':folder.name,'files_scanned':summary['files_scanned'],'candidate_files':len(represented),'file_coverage_fraction':len(represented)/summary['files_scanned'],'product_candidates':len(gs),'paper_candidates':len(paper),'product_nodes':sum(len(g['nodes']) for g in gs),'product_edges':sum(len(g['edges']) for g in gs),'paper_nodes':sum(len(g['nodes']) for g in paper),'paper_edges':sum(len(g['edges']) for g in paper),'product_dependency_graphs':summary['graphs_with_dependency_path'],'paper_dependency_graphs':sum(bool(g['analysis']['dependency_paths']) for g in paper),'product_guard_graphs':summary['graphs_with_guard_candidate'],'paper_guard_graphs':sum(g['views']['security_adg']['guard_candidates']>0 for g in paper),'interprocedural_source_graphs':summary['graphs_with_interprocedural_source'],'wall_seconds':s['wall_seconds'],'peak_rss_bytes':s['peak_rss_bytes'],'acyclic_graphs':sum(acyclic(g) for g in gs),'node_types':dict(collections.Counter(n['type'] for g in gs for n in g['nodes'])),'edge_types':dict(collections.Counter(e['type'] for g in gs for e in g['edges'])),'operation_categories':summary['category_counts']})
 # Choose one effectful process candidate, retaining limitations even when no sources.
 commands=[g for g in gs if any(n.get('category')=='command_execution' for n in g['nodes'])]
 if folder.name=='html-anything':choice=next(g for g in commands if g['provenance']['file']=='cli/src/agents-invoke.ts')
 else:choice=max(commands,key=lambda g:len(g['nodes']))
 selected.append((folder.name,choice))
 # Full disjoint union preserves candidate-local identities; no invented joins.
 forest={'meaning':'Disjoint union of ALL candidate-centered graphs; no cross-candidate edges inferred','nodes':[],'edges':[]}
 for g in gs:
  prefix=g['candidate_id']+':'
  forest['nodes'].extend({**n,'id':prefix+n['id'],'candidate_id':g['candidate_id']} for n in g['nodes'])
  forest['edges'].extend({**e,'from':prefix+e['from'],'to':prefix+e['to']} for e in g['edges'])
 dump(folder/'all-candidate-forest.json',forest)
dump(R/'comparison.json',rows)
for name in ['cross_file_direct','small-auth-app','parameter_overwrite']:
 gs=read(R/'experiments'/name/'security-adg.jsonl');choice=max(gs,key=lambda g:len(g['nodes']));selected.append((name,choice))
# Full and security dependency views. The latter removes only the owner/contains context.
colors={'input_source':'#dfecff','guard_candidate':'#e6f2df','security_sensitive_operation':'#ffe3dc','trust_boundary':'#fff0cc','external_effect':'#e8e8ed','program_symbol':'#e8def4','agent_or_program_symbol':'#def0ed'}
def svg(g,label,security=False):
 nodes=[n for n in g['nodes'] if not security or n['type']!='agent_or_program_symbol'];ids={n['id'] for n in nodes};edges=[e for e in g['edges'] if e['from'] in ids and e['to'] in ids]
 positions={};cols=collections.defaultdict(list)
 for n in nodes:
  col={'input_source':0,'agent_or_program_symbol':0,'guard_candidate':1,'trust_boundary':1,'program_symbol':1,'security_sensitive_operation':2,'external_effect':3}[n['type']];cols[col].append(n)
 height=max(1400,150+len(nodes)*120+len(edges)*18);out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="{height}" viewBox="0 0 1400 {height}"><rect width="100%" height="100%" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#263443}} .small{{font-size:12px}} .label{{font-size:14px}}</style>',f'<title>{html.escape(label)}</title>',f'<text x="24" y="32" font-size="20">{html.escape(label)}</text>',f'<text x="24" y="56" class="small">{html.escape(g["provenance"]["file"])}:{g["provenance"]["line_start"]} — all relations retain upstream uncertainty</text>','<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>']
 for i,n in enumerate(nodes):positions[n['id']]=(24,95+i*120)
 for ei,e in enumerate(edges):
  x,y=positions[e['from']];a,b=positions[e['to']];arc=780+ei*45;out.append(f'<path d="M{x+650},{y+40} C{arc},{y+40} {arc},{b+40} {a+650},{b+40}" stroke="#64748b" fill="none" stroke-width="1.5" marker-end="url(#arrow)"'+(' stroke-dasharray="5 4"' if e['type'].startswith('may') or e['type']=='reaches' else '')+f'><title>{html.escape(e["type"]+" / "+e["status"])}</title></path>')
 for n in nodes:
  x,y=positions[n['id']];labeltext=str(n.get('symbol',n.get('name',n.get('kind',n.get('target_class',n.get('boundary',''))))))
  out.append(f'<g data-node="{n["id"]}"><title>{html.escape(json.dumps(n))}</title><rect x="{x}" y="{y}" width="650" height="94" rx="8" fill="{colors[n["type"]]}" stroke="#a8b5c4"/><text x="{x+10}" y="{y+20}" class="small">{n["id"]}: {n["type"]}</text>')
  for j in range(0,min(len(labeltext),160),76):out.append(f'<text x="{x+10}" y="{y+43+(j//76)*18}" class="label">{html.escape(labeltext[j:j+76])}</text>')
  out.append('</g>')
 y=120+len(nodes)*120
 for i,e in enumerate(edges):out.append(f'<text x="24" y="{y+i*18}" class="small">{e["from"]} → {e["to"]}: {e["type"]} [{e["status"]}]</text>')
 out.append('</svg>');text=''.join(out);ET.fromstring(text);return text
catalog=[]
for name,g in selected:
 dump(V/(name+'-candidate.json'),g)
 for suffix,security in [('full',False),('security',True)]:
  p=V/f'{name}-{suffix}.svg';p.write_text(svg(g,name+' / '+g['candidate_id']+' / '+suffix,security));catalog.append({'file':p.name,'candidate':g['candidate_id'],'label':name,'view':suffix})
# Repository-wide contact sheets use every candidate graph without merging nodes.
for folder in sorted((R/'product').iterdir()):
 gs=read(folder/'security-adg.jsonl');dest=V/folder.name;dest.mkdir(exist_ok=True)
 links=[]
 for g in gs:
  filename=g['candidate_id']+'.svg';(dest/filename).write_text(svg(g,folder.name+' / '+g['candidate_id']));links.append(f'<li><a href="{folder.name}/{filename}">{g["candidate_id"]}</a> — {html.escape(g["provenance"]["file"])}:{g["provenance"]["line_start"]}</li>')
 (V/(folder.name+'-all.html')).write_text('<!doctype html><meta charset="utf-8"><title>All candidate graphs</title><h1>'+folder.name+'</h1><p>Complete candidate catalog; one full typed SVG per candidate. These are separate graphs, not a whole-program call graph.</p><ul>'+''.join(links)+'</ul>')
(V/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>AgentSecGraph graph catalog</title><h1>Verified candidate graphs</h1><p>Dashed edges are candidate relations. Hover nodes for full metadata.</p>'+''.join(f'<h2>{c["label"]} / {c["view"]}</h2><object width="100%" data="{c["file"]}" type="image/svg+xml"></object>' for c in catalog)+''.join(f'<p><a href="{x["repository"]}-all.html">All {x["product_candidates"]} graphs: {x["repository"]}</a></p>' for x in rows))
dump(R/'visualization-manifest.json',catalog)
# Evidence atoms and token-budget baselines. Approximation is explicitly chars/4.
def cost(s):return math.ceil(len(s)/4)
def atoms(g):
 a=[]
 for n in g['nodes']:a.append({'id':'node:'+n['id'],'kind':n['type'],'text':json.dumps(n,sort_keys=True,separators=(',',':')),'nodes':[n['id']]})
 for i,e in enumerate(g['edges']):a.append({'id':f'edge:{i}','kind':e['type'],'text':json.dumps(e,sort_keys=True,separators=(',',':')),'nodes':[e['from'],e['to']]})
 for i,p in enumerate(g['analysis']['dependency_paths']):a.append({'id':f'path:{i}','kind':'dependency_path','text':json.dumps(p,separators=(',',':')),'nodes':[]})
 return a
budget_rows=[];evidence=[]
pool={'candidate_id':'POOLED-SIX-OPERATIONS','nodes':[],'edges':[],'analysis':{'dependency_paths':[]},'provenance':{'file':'six independent candidate records; no connecting edges'}}
for pi,(pname,pg) in enumerate(selected):
 prefix=f'p{pi}:'
 pool['nodes'].extend({**n,'id':prefix+n['id']} for n in pg['nodes'])
 pool['edges'].extend({**e,'from':prefix+e['from'],'to':prefix+e['to']} for e in pg['edges'])
 pool['analysis']['dependency_paths'].extend([[pname,*path] for path in pg['analysis']['dependency_paths']])
for name,g in [*selected,('pooled-six',pool)]:
 aa=atoms(g);ops={n['id'] for n in g['nodes'] if n['type']=='security_sensitive_operation'};dist={op:0 for op in ops};q=collections.deque(sorted(ops));adj=collections.defaultdict(set);rev=collections.defaultdict(set)
 for e in g['edges']:adj[e['from']].add(e['to']);adj[e['to']].add(e['from']);rev[e['to']].add(e['from'])
 while q:
  x=q.popleft()
  for y in adj[x]:
   if y not in dist:dist[y]=dist[x]+1;q.append(y)
 # All emitted facts form an extraction-retention inventory, not an independent security gold standard.
 evidence.append({'case':name,'candidate_id':g['candidate_id'],'atoms':aa,'compact_atom_tokens':cost('\n'.join(a['text'] for a in aa)),'whole_graph_json_tokens':cost(json.dumps(g,sort_keys=True,separators=(',',':'))),'token_estimator':'ceil(unicode character count / 4), applied to complete selected evidence string'})
 for budget in [512,1024,2048,4096]:
  for method in ['all_truncated','nearest','shortest_paths','security_endpoints','random','text_summary']:
   for seed in (range(20) if method=='random' else [0]):
    ordered=list(aa)
    if method=='nearest':ordered.sort(key=lambda a:(min([dist.get(n,999) for n in a['nodes']] or [999]),a['id']))
    if method=='shortest_paths':
     # Prioritize nodes/edges on shortest source-to-operation paths, then other evidence.
     path_ids=set();path_edges=set()
     for n in g['nodes']:
      if n['type']!='input_source':continue
      paths=collections.deque([(n['id'],[n['id']])]);seen=set()
      while paths:
       u,path=paths.popleft()
       if u in ops:
        path_ids.update(path);path_edges.update(zip(path,path[1:]));break
       if u in seen:continue
       seen.add(u)
       for e in g['edges']:
        if e['from']==u:paths.append((e['to'],path+[e['to']]))
     ordered.sort(key=lambda a:(0 if (a['id'].startswith('node:') and a['nodes'][0] in path_ids) or (len(a['nodes'])==2 and tuple(a['nodes']) in path_edges) else 1,a['id']))
    if method=='security_endpoints':ordered.sort(key=lambda a:(0 if a['kind'] in {'security_sensitive_operation','input_source','guard_candidate','external_effect'} else 1,a['id']))
    if method=='random':random.Random(seed).shuffle(ordered)
    if method=='text_summary':
     for a in ordered:
      a=dict(a);a['text']=a['kind']+' '+a['text'] # replaced below with faithful compact attribute summaries
     ordered=[]
     for a in aa:
      b=dict(a)
      if a['id'].startswith('node:'):
       n=next(n for n in g['nodes'] if n['id']==a['nodes'][0]);b['text']=n['id']+' '+n['type']+' '+str(n.get('symbol',n.get('name',n.get('kind',n.get('target_class','')))))+' '+str(n.get('trust',n.get('effectiveness','')))
      elif a['id'].startswith('edge:'):
       e=g['edges'][int(a['id'].split(':')[1])];b['text']=f"{e['from']} {e['type']} {e['to']} {e['status']}"
      else:b['text']='path '+' → '.join(g['analysis']['dependency_paths'][int(a['id'].split(':')[1])])
      ordered.append(b)
    texts=[];kept=[];partial=False
    for a in ordered:
     proposed='\n'.join([*texts,a['text']])
     if cost(proposed)<=budget:texts.append(a['text']);kept.append(a['id'])
     elif method=='all_truncated':
      # Literal character-prefix truncation; partial atom gets no fact credit.
      remaining=budget*4-len('\n'.join(texts))-(1 if texts else 0)
      if remaining>0:texts.append(a['text'][:remaining]);partial=True
      break
    wanted_source=[a['id'] for a in aa if a['kind']=='input_source'];wanted_guard=[a['id'] for a in aa if a['kind']=='guard_candidate'];wanted_path=[a['id'] for a in aa if a['kind']=='dependency_path']
    budget_rows.append({'case':name,'budget':budget,'method':method,'seed':seed,'estimated_tokens':cost('\n'.join(texts)),'retained_ids':kept,'total_atoms':len(aa),'retained_atoms':len(kept),'atom_fraction':len(kept)/len(aa),'source_retained':sum(a in kept for a in wanted_source),'source_total':len(wanted_source),'guard_retained':sum(a in kept for a in wanted_guard),'guard_total':len(wanted_guard),'path_retained':sum(a in kept for a in wanted_path),'path_total':len(wanted_path),'partial_atom':partial,'summary_credit_scope':'coarse fact ID only; attribute fidelity not scored' if method=='text_summary' else 'complete JSON atom','text':'\n'.join(texts)})
dump(R/'budget-evidence.json',evidence);dump(R/'budget-results.json',budget_rows)
# Structural comparison avoids mistaking scan-root or whole-project counters for semantic evidence.
structure=[]
for v in 'ABCD':
 g=read(R/'experiments'/('temporal-'+v)/'security-adg.jsonl')[0]
 structure.append({'version':v,'nodes_edges_sha256':hashlib.sha256(json.dumps({'nodes':g['nodes'],'edges':g['edges']},sort_keys=True).encode()).hexdigest(),'dependency_paths':g['analysis']['dependency_paths']})
dump(R/'temporal-structure.json',structure)
print(json.dumps(rows,indent=2));print('Budget rows',len(budget_rows),'SVG catalog',len(list(V.rglob('*.svg'))))
