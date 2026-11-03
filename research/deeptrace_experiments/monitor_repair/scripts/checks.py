import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'qualification/scripts'));from evidence import reference
O=ROOT/'monitor_repair/results';p=json.loads((O/'protocol.json').read_text());s=json.loads((O/'development_seal.json').read_text());checks={}
checks['criteria_unchanged_from_first_qualification']=p['criterion']==json.loads((ROOT/'qualification/results/protocol.json').read_text())['criterion']
checks['protocol_unchanged_after_development']=hashlib.sha256((O/'protocol.json').read_bytes()).hexdigest()==s['protocol_sha256']
checks['development_scores_unchanged']=hashlib.sha256((O/'development_scores.jsonl').read_bytes()).hexdigest()==s['development_scores_sha256']
jobs=[]
for phase in ['development','qualification']:
 path=O/(phase+'_jobs.jsonl');checks[phase+'_jobs_frozen']=hashlib.sha256(path.read_bytes()).hexdigest()==p[phase+'_jobs_sha256'];jobs += list(map(json.loads,path.read_text().splitlines()))
checks['same_evidence_both_models']=all(len({json.dumps(j['messages'],sort_keys=True) for j in jobs if j['case_id']==cid})==1 for cid in {j['case_id'] for j in jobs})
checks['no_cross_split_exact_duplicates']=not({j['prompt_hash'] for j in jobs if j['split']=='development'}&{j['prompt_hash'] for j in jobs if j['split']=='qualification'})
checks['all_176_primary_results_saved']=all((O/'responses'/(j['job_id']+'.json')).exists() for j in jobs)
checks['all_facts_fit_budget']=all(j['evidence_tokens']<=1024 for j in jobs)
checks['reference_verdict_not_supplied']=all('"policy_violation"' not in j['messages'][1]['content'] for j in jobs)
cs=json.loads((ROOT/'monitor_repair/data/cases.json').read_text());checks['all_references_recheck']=all(reference(c['files'],c['approved'])==c['reference']['policy_violation'] for c in cs)
checks['no_qualification_calls_before_release']=json.loads((O/'qualification_release.json').read_text())['qualification_responses_existing_before_release']==0
checks['negative_pilot_unchanged']=all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in json.loads((ROOT/'qualification/results/negative_pilot_freeze.json').read_text())['files'])
(O/'checks.json').write_text(json.dumps(checks,indent=2));assert all(checks.values());print('Monitor repair checks passed:',len(checks))
