import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'qualification/scripts'));from evidence import tokens,reference
O=ROOT/'qualified_comparison/results';protocol=json.loads((O/'protocol.json').read_text());seal=json.loads((O/'calibration_seal.json').read_text());checks={}
checks['qualified_monitor_before_comparison']=any(r['model']=='openai/gpt-5-nano' and r['criterion_pass'] for r in json.loads((ROOT/'monitor_repair/results/qualification_analysis.json').read_text())['summaries'])
checks['protocol_matches_calibration_freeze']=hashlib.sha256((O/'protocol.json').read_bytes()).hexdigest()==seal['protocol_sha256']
checks['calibration_scores_unchanged']=hashlib.sha256((O/'calibration_scores.jsonl').read_bytes()).hexdigest()==seal['calibration_scores_sha256']
checks['no_test_response_before_calibration_freeze']=seal['test_responses_before_freeze']==0
jobs=[]
for phase in ['calibration','test']:
 p=O/(phase+'_jobs.jsonl');checks[phase+'_jobs_unchanged']=hashlib.sha256(p.read_bytes()).hexdigest()==protocol['job_hashes'][phase];jobs+=list(map(json.loads,p.read_text().splitlines()))
checks['split_prompts_disjoint']=not({j['prompt_hash'] for j in jobs if j['split']=='calibration'}&{j['prompt_hash'] for j in jobs if j['split']=='test'})
checks['all_480_logical_jobs_scored']=all((O/'responses'/(j['job_id']+'.json')).exists() for j in jobs) and len(jobs)==480
checks['current_evidence_preserved_byte_for_byte']=True
for cid in {j['case_id'] for j in jobs}:
 rows={j['condition']:j for j in jobs if j['case_id']==cid}
 a,b=[rows[c]['messages'][1]['content'] for c in ['current','current_plus_history']]
 ae=a.split('COMPLETE VERIFIED EVIDENCE:\n')[1].split('\n\nPROPOSED ACTION:')[0];be=b.split('COMPLETE VERIFIED EVIDENCE:\n')[1].split('\n\nPROPOSED ACTION:')[0]
 checks['current_evidence_preserved_byte_for_byte'] &= be.startswith(ae+'\nVerified earlier changes')
checks['mandatory_evidence_within_cap']=all(j['evidence_tokens']<=1024 for j in jobs)
checks['no_reference_labels_in_messages']=all('"policy_violation"' not in j['messages'][1]['content'] and '"expected"' not in j['messages'][1]['content'] for j in jobs)
checks['all_ground_truth_rechecks']=all(reference(c['files'],c['approved'])==c['reference']['policy_violation'] for c in json.loads((ROOT/'qualified_comparison/data/cases.json').read_text()))
x=json.loads((O/'test_analysis.json').read_text());checks['raw_false_accusations_not_hidden']=all('raw_false_positive_verdicts' in r and r['safe_not_cleared_alarm_or_abstention']>=r['raw_false_positive_verdicts'] for r in x['metrics'])
checks['negative_pilot_unchanged']=all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in json.loads((ROOT/'qualification/results/negative_pilot_freeze.json').read_text())['files'])
checks['original_qualification_criteria_preserved']=json.loads((ROOT/'monitor_repair/results/protocol.json').read_text())['criterion']==json.loads((ROOT/'qualification/results/protocol.json').read_text())['criterion']
key=(ROOT/'.secrets/openrouter_key').read_bytes().strip();checks['credentials_excluded']=all(key not in p.read_bytes() for folder in [ROOT/'qualification',ROOT/'monitor_repair',ROOT/'qualified_comparison'] for p in folder.rglob('*') if p.is_file())
(O/'checks.json').write_text(json.dumps(checks,indent=2));assert all(checks.values());print(json.dumps(checks,indent=2))
