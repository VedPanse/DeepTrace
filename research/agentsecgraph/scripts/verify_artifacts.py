"""Validate every recorded graph and export; never executes target code."""
import json,hashlib,collections,re,xml.etree.ElementTree as ET,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';V=ROOT/'visualizations'
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x]
def check(g):
 ids={n['id'] for n in g['nodes']};assert len(ids)==len(g['nodes'])
 assert g['provenance']['evidence_hash_verified'];assert not g['provenance']['source_execution_used'];assert not g['provenance']['label_inputs_used']
 children=collections.defaultdict(list);indeg=dict.fromkeys(ids,0)
 for e in g['edges']:assert e['from'] in ids and e['to'] in ids;children[e['from']].append(e['to']);indeg[e['to']]+=1
 q=collections.deque(n for n in ids if not indeg[n]);seen=0
 while q:
  n=q.popleft();seen+=1
  for c in children[n]:
   indeg[c]-=1
   if not indeg[c]:q.append(c)
 assert seen==len(ids),'cycle found; update report rather than removing edges'
 return len(ids),len(g['edges'])
product=[];summary=[]
paper=read(R/'paper/security-adg.jsonl')
for folder in (R/'product').iterdir():
 gs=read(folder/'security-adg.jsonl');findings=read(folder/'findings.jsonl')
 assert len(gs)==len(findings);assert json.loads((folder/'validation.json').read_text())['valid']
 pkeys={(g['provenance']['file'],g['provenance']['line_start'],next(n['category'] for n in g['nodes'] if n['type']=='security_sensitive_operation')) for g in gs}
 legacy=[g for g in paper if g['provenance']['repo'].split('/')[-1]==folder.name]
 lkeys={(g['provenance']['file'],min(next(n['evidence_lines'] for n in g['nodes'] if n['type']=='security_sensitive_operation')),next(n['category'] for n in g['nodes'] if n['type']=='security_sensitive_operation')) for g in legacy}
 assert pkeys==lkeys
 for g in gs:
  check(g);doc=ET.parse(V/folder.name/(g['candidate_id']+'.svg'));nodes={x.attrib['data-node'] for x in doc.iter() if 'data-node' in x.attrib};assert nodes=={n['id'] for n in g['nodes']}
  paths=[x for x in doc.iter() if 'marker-end' in x.attrib];assert len(paths)==len(g['edges'])
 product.extend(gs)
for g in paper:check(g)
controlled=0
for folder in (R/'experiments').iterdir():
 for g in read(folder/'security-adg.jsonl'):check(g);controlled+=1
for g in read(R/'temporal-paper/security-adg.jsonl'):check(g)
for path in V.rglob('*.svg'):ET.parse(path)
for item in json.loads((R/'visualization-manifest.json').read_text()):
 g=json.loads((V/(item['label']+'-candidate.json')).read_text());expected={n['id'] for n in g['nodes'] if item['view']=='full' or n['type']!='agent_or_program_symbol'}
 got={x.attrib['data-node'] for x in ET.parse(V/item['file']).iter() if 'data-node' in x.attrib};assert got==expected
for x in json.loads((R/'budget-results.json').read_text()):assert x['estimated_tokens']<=x['budget']
for x in json.loads((R/'relevance-results.json').read_text()):
 if x['method']!='text_summary':assert x['preserved_reference_facts']==x['extractable_reference_facts']
pins=json.loads((R/'repositories.json').read_text())
for x in [pins['analyzer'],*pins['targets']]:assert subprocess.check_output(['git','-C',str(ROOT/x['path']),'rev-parse','HEAD'],text=True).strip()==x['commit']
assert not subprocess.check_output(['git','-C',str(ROOT/'upstream'),'status','--porcelain'],text=True).strip()
# Verify immutable source citations resolve to actual line numbers in this checkout.
for md in ROOT.glob('*.md'):
 for file,line in re.findall(r'https://github.com/A1LinLin1/AgentSecBench/blob/[0-9a-f]+/([^\s)#]+)#L(\d+)',md.read_text()):assert 0<int(line)<=len((ROOT/'upstream'/file).read_text().splitlines())
# Check relative local Markdown links, skipping protocol URLs and anchors.
for md in ROOT.glob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',md.read_text()):
  if '://' not in target and not target.startswith('#'):assert (md.parent/target.split('#')[0]).exists(),(md,target)
status={'product_graphs':len(product),'paper_graphs':len(paper),'controlled_product_graphs':controlled,'temporal_paper_graphs':len(read(R/'temporal-paper/security-adg.jsonl')),'product_svg_files':len(list(V.rglob('*.svg'))),'candidate_keys_match_paper_and_product':True,'all_checked_graphs_acyclic':True,'source_checkout_unmodified':True,'all_graphs_source_execution_used':False,'svg_node_and_edge_preservation':True,'budget_constraints_satisfied':True,'relative_report_links_valid':True,'source_reference_line_numbers_valid':True,'visual_manual_QA':'selected full real-repository figures and cross_file_direct rendered and inspected; full SVG catalog parsed and compared to JSON'}
(R/'verification.json').write_text(json.dumps(status,indent=2))
manifest={}
for base in [R,V,ROOT/'scripts']:
 for f in sorted(base.rglob('*')):
  if not f.is_file() or any(x in f.parts for x in ['.git','__pycache__','tmp']) or f.name=='artifact-sha256.json':continue
  manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
for f in ROOT.glob('*.md'):manifest[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
(R/'artifact-sha256.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(status,indent=2));print('Hashed artifacts:',len(manifest))
