"""Artifact integrity, evidence parity, reference and leakage checks; no inference."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'selector_evaluation/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=json.loads((OUT/'protocol.json').read_text());m=json.loads((OUT/'manifest.json').read_text());checks={}
    checks['frozen_implementation_unchanged']=all(sha(ROOT/k)==h for k,h in p['implementation_hashes'].items())
    checks['protocol_hash']=sha(OUT/'protocol.json')==m['protocol_sha256']
    checks['cases_hash']=sha(ROOT/'selector_evaluation/data/cases.json')==m['cases_sha256']
    jobs={s:[json.loads(x) for x in (OUT/(s+'_jobs.jsonl')).read_text().splitlines()] for s in ['calibration','test']}
    checks['jobs_hashes']=all(sha(OUT/(s+'_jobs.jsonl'))==m['job_hashes'][s] for s in jobs)
    checks['no_split_prompt_overlap']=not ({j['prompt_hash'] for j in jobs['calibration']}&{j['prompt_hash'] for j in jobs['test']})
    checks['no_split_family_overlap']=not ({j['family'] for j in jobs['calibration']}&{j['family'] for j in jobs['test']})
    checks['budget_all']=all(j['evidence_tokens']<=p['budget'] for js in jobs.values() for j in js)
    groups={}
    for js in jobs.values():
        for j in js:groups.setdefault(j['case_id'],{})[j['condition']]=j
    checks['paired_actions_and_current_facts']=True
    for g in groups.values():
        c=g['current']['messages'][-1]['content'];base=c.split('EVIDENCE:\n',1)[1].split('\nPROPOSED ACTION:',1)[0]
        checks['paired_actions_and_current_facts'] &= all(base in g[k]['messages'][-1]['content'] for k in ['unselected','selected']) and len({json.dumps(j['expected'],sort_keys=True) for j in g.values()})==1
    checks['no_serialized_reference_label']=all('policy_violation"' not in j['messages'][-1]['content'] for js in jobs.values() for j in js)
    freeze=json.loads((ROOT/'history_diagnosis/results/negative_comparison_freeze.json').read_text())
    checks['prior_negative_comparison_unchanged']=all(sha(ROOT/k)==h for k,h in freeze['sha256'].items())
    for s in jobs:
        f=OUT/(s+'_scores.jsonl')
        if f.exists():checks[s+'_all_scores_saved']=len(f.read_text().splitlines())==len(jobs[s])
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2));assert all(checks.values()),checks
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
