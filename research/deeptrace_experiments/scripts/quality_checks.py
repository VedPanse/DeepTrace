"""Verify experiment integrity: hidden labels, budgets, DAG acyclicity, source spans and splits."""
import json,hashlib,collections,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';D=ROOT/'data'
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x]
def dag(g):
 ids={x['id'] for x in g['nodes']};assert len(ids)==len(g['nodes']);degrees=dict.fromkeys(ids,0);edges=collections.defaultdict(list)
 for e in g['edges']:assert e['from'] in ids and e['to'] in ids;degrees[e['to']]+=1;edges[e['from']].append(e['to'])
 queue=collections.deque(x for x in ids if not degrees[x]);n=0
 while queue:
  v=queue.popleft();n+=1
  for c in edges[v]:
   degrees[c]-=1
   if not degrees[c]:queue.append(c)
 assert n==len(ids)
gt=json.loads((R/'ground_truth_validation.json').read_text());assert gt['all_matches'] and gt['labels_changed']==0
jobs=read(R/'jobs_temporal.jsonl')+read(R/'jobs_real.jsonl');assert all(x['evidence_tokens']<=x['evidence_budget'] for x in jobs)
# Format ablations must serialize the identical selected fact list.
formats=collections.defaultdict(dict)
for j in jobs:
 if j['condition'] in {'temporal','prose','selected'} and j['metadata'].get('format_fact_hash'):formats[(j['experiment'],j['case_id'],j['evidence_budget'])][j['condition']]=j['metadata']['format_fact_hash']
assert all(len(set(d.values()))==1 for d in formats.values())
for p in (R/'temporal_dags').glob('*.json'):dag(json.loads(p.read_text()))
static=json.loads((R/'static_graphs.json').read_text());graph_count=0
for c in static:
 for v,record in c['versions'].items():
  for g in record['graphs']:dag(g);assert g['provenance']['evidence_hash_verified'];assert not g['provenance']['source_execution_used'];graph_count+=1
cases=json.loads((D/'temporal/cases.json').read_text());cal={x['family'] for x in cases if x['split']=='calibration'};test={x['family'] for x in cases if x['split']=='test'};assert not cal&test
real=json.loads((D/'real_replay.json').read_text());ids={x['trajectory_id'] for x in real};protocol=json.loads((R/'real_protocol.json').read_text());calids={x[0] for x in protocol['calibration_actions']};testids={x[0] for x in protocol['test_honest_actions']};assert not calids&testids
for r in real:
 for a in r['actions']:assert all(e['index']<a['index'] for e in a['prior_editor_events'])
assert not subprocess.check_output(['git','-C',str(ROOT.parent/'agentsecgraph/upstream'),'status','--porcelain'],text=True).strip()
key=(ROOT/'.secrets/openrouter_key').read_text().strip()
# Verify credentials are absent from shareable scripts, metrics, report sources and PDFs.
checked=0
for base in [ROOT/'scripts',R,ROOT.parent.parent/'output/pdf/deeptrace_experiment_report']:
 for p in base.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:
   assert key.encode() not in p.read_bytes(),str(p);checked+=1
if (R/'scores.jsonl').exists():
 scores=read(R/'scores.jsonl');expected={j['job_id'] for j in jobs};actual={s['job_id'] for s in scores};assert expected==actual,'Final score file does not correspond to frozen final jobs'
 assert all(s['monitor']['status']=='ok' for s in scores)
result={'logical_monitor_jobs':len(jobs),'temporal_cases':len(cases),'temporal_static_graphs':graph_count,'temporal_event_dags':len(list((R/'temporal_dags').glob('*.json'))),'all_checked_graphs_acyclic':True,'format_ablation_identical_facts':True,'evidence_token_budgets_satisfied':True,'disjoint_guard_family_split':True,'disjoint_real_history_split':True,'prefix_only_editor_evidence':True,'original_analyzer_unmodified':True,'no_target_execution_in_static_graphs':True,'shareable_files_checked_for_api_secret':checked,'limitation':'real code observation fragments are incomplete; no monitor can be credited with a missing harm boundary'}
(R/'quality_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
