"""Verify locked protocol, complete paired inputs and honest invalid accounting."""
import json,hashlib,ast
from pathlib import Path
from evidence import ROOT,reference,packet,tokens
from analyze import schema,contradictions
OUT=ROOT/'qualification/results';protocol=json.loads((OUT/'protocol.json').read_text());checks={}
freeze=json.loads((OUT/'negative_pilot_freeze.json').read_text());checks['negative_pilot_files_unchanged']=all(hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in freeze['files'])
seal=json.loads((OUT/'development_seal.json').read_text());checks['protocol_unchanged_after_development_seal']=hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest()==seal['protocol_sha256'];checks['development_scores_unchanged_after_seal']=hashlib.sha256((OUT/'development_scores.jsonl').read_bytes()).hexdigest()==seal['development_scores_sha256']
checks['qualification_released_after_development_seal']=json.loads((OUT/'qualification_release.json').read_text())['qualification_responses_existing_before_release']==0
jobs=[]
for split in ['development','qualification']:
 p=OUT/(split+'_jobs.jsonl');checks[split+'_jobs_match_frozen_hash']=hashlib.sha256(p.read_bytes()).hexdigest()==protocol[split+'_jobs_sha256'];jobs += [json.loads(l) for l in p.read_text().splitlines()]
checks['development_qualification_prompt_disjoint']=not ({j['prompt_hash'] for j in jobs if j['split']=='development'}&{j['prompt_hash'] for j in jobs if j['split']=='qualification'})
checks['same_messages_for_both_models']=all(len({json.dumps(j['messages'],sort_keys=True) for j in jobs if j['case_id']==cid})==1 for cid in {j['case_id'] for j in jobs})
checks['complete_176_primary_responses']=all((OUT/'responses'/(j['job_id']+'.json')).exists() for j in jobs) and len(jobs)==176
checks['no_policy_verdict_in_evidence']=all('"policy_violation"' not in j['messages'][1]['content'] and 'combined_policy_status' not in j['messages'][1]['content'] for j in jobs)
checks['all_mandatory_evidence_fits_without_truncation']=all(j['evidence_tokens']<=1024 for j in jobs)
checks['no_labels_in_messages']=all('"expected"' not in json.dumps(j['messages']) and '"variant"' not in json.dumps(j['messages']) for j in jobs)
cs=json.loads((ROOT/'qualification/data/cases.json').read_text());checks['bounded_reference_agrees_all_known_cases']=all(reference(c['files'],c['approved'])==c['reference']['policy_violation'] for c in cs)
checks['unknown_restriction_preserves_known_argument_and_shell']=all(c['reference']['argument_origin']=='caller_string' and c['reference']['shell_enabled'] is True and c['reference']['policy_violation'] is None for c in cs if c['variant']=='unsupported')
checks['invalid_not_silently_safe']=bool(schema({})) and bool(contradictions({'effective_restriction':'approved_only','argument_origin':'caller_string','shell_enabled':True,'policy_violation':True}))
qa=json.loads((OUT/'qualification_analysis.json').read_text());checks['denominator_includes_all_cases']=all(s['n']==44 for s in qa['summaries'])
key=(ROOT/'.secrets/openrouter_key').read_bytes().strip();checks['credentials_not_in_artifacts']=all(key not in p.read_bytes() for p in (ROOT/'qualification').rglob('*') if p.is_file())
for p in (ROOT/'qualification/scripts').glob('*.py'):ast.parse(p.read_text())
(OUT/'checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2));assert all(checks.values())
