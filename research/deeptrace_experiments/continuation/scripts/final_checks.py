"""Read-only validity checks of final frozen evaluation and scope boundaries."""
import json,hashlib,sys,collections,ast
from controlled import OUT,DATA,ROOT,tokens
jobs=[json.loads(l) for l in (OUT/'jobs.jsonl').read_text().splitlines()];cases=json.loads((DATA/'cases.json').read_text());packets=json.loads((OUT/'packets.json').read_text());cal=[json.loads(l) for l in (OUT/'calibration_scores.jsonl').read_text().splitlines()];test=[json.loads(l) for l in (OUT/'test_scores.jsonl').read_text().splitlines()];frozen=json.loads((OUT/'thresholds.json').read_text());checks={}
checks['all_2560_jobs_scored']=len(cal)+len(test)==len(jobs)==2560 and all(r['monitor']['status']=='ok' for r in cal+test)
checks['no_exact_prompt_overlap_across_splits']=not ({j['prompt_hash'] for j in jobs if j['split']=='calibration'}&{j['prompt_hash'] for j in jobs if j['split']=='test'})
checks['calibration_unchanged_after_freeze']=hashlib.sha256((OUT/'calibration_scores.jsonl').read_bytes()).hexdigest()==frozen['calibration_scores_sha256']
checks['test_jobs_unchanged_after_freeze']=hashlib.sha256((OUT/'test_jobs.jsonl').read_bytes()).hexdigest()==frozen['test_jobs_sha256']
checks['actual_whole_action_retained']=all(j['messages'][1]['content'].endswith(next(c['action'] for c in cases if c['case_id']==j['case_id'])) for j in jobs)
checks['evidence_budgets']=all(j['evidence_tokens']<=1024 for j in jobs)
checks['family_groups_disjoint']=not({c['group'] for c in cases if c['split']=='calibration'}&{c['group'] for c in cases if c['split']=='test'})
checks['same_fact_hash_both_formats']=all(len({j['metadata']['fact_hash'] for j in jobs if j['case_id']==c['case_id'] and j['condition'] in ['temporal','prose']})==1 for c in cases)
checks['source_spans_match']=all(span['source_sha256']==hashlib.sha256(next(c['after'][span['file']] for c in cases if c['case_id']==p['case_id']).encode()).hexdigest() for p in packets for span in p['current_summary_spans'])
checks['linuxarena_not_mislabeled_complete']=json.loads((OUT/'linuxarena_cohort.json').read_text())['eligibility'] is False
checks['upstream_unchanged']=__import__('subprocess').run(['git','-C',str(ROOT.parent/'agentsecgraph/upstream'),'diff','--exit-code'],capture_output=True).returncode==0
keyfile=ROOT/'.secrets/openrouter_key';key=keyfile.read_text().strip() if keyfile.exists() else None
checks['no_credentials_in_deliverable_inputs']=all((not key or key not in p.read_text(errors='ignore')) for folder in [ROOT/'continuation/scripts',OUT] for p in folder.rglob('*') if p.is_file())
# Claim metadata never enters model messages, which contain only task, code evidence, action.
checks['hidden_conditions_and_labels']=all('"label"' not in ''.join(m['content'] for m in j['messages']) and '"variant"' not in ''.join(m['content'] for m in j['messages']) and j['metadata']['family'] not in ''.join(m['content'] for m in j['messages']) for j in jobs)
(OUT/'final_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
if not all(checks.values()):raise SystemExit('failed final check')
