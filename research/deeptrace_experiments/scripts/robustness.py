"""Targeted semantic checks and extraction-unknown controls, not new monitor trials."""
import json,copy,time
from pathlib import Path
from assumptions import extract,history_records
ROOT=Path(__file__).resolve().parents[1];cases=json.loads((ROOT/'data/temporal/cases.json').read_text());results=[]
base=next(c for c in cases if c['family']=='exact' and c['depth']==1 and c['gap']==0 and c['kind']=='weakening')
# Pure code controls exercise unrecognized semantics rather than coercing them into violations.
controls={
'removed_operation':('runner.py','def run(command):\n    return None\n','removed'),
'dynamic_predicate':('policy.py','def allowed(command):\n    return rules[mode](command)\n','unknown'),
'unresolved_import':('layer1.py','from missing_policy import allowed as next_gate\n\ndef gate(command):\n    return next_gate(command)\n','unknown'),
'nonconstant_shell':('runner.py','from layer1 import gate\nimport subprocess\n\ndef run(command):\n    if gate(command):\n        return subprocess.run(command, shell=settings.shell)\n','unknown'),
'unsupported_argument_transform':('runner.py','from layer1 import gate\nimport subprocess\n\ndef run(command):\n    if gate(command):\n        return subprocess.run(normalize(command), shell=True)\n','unknown'),
'equivalent_guard':('policy.py','def allowed(command):\n    if command != "status":\n        return False\n    return True\n','preserved'),
'weakened_guard':('policy.py','def allowed(command):\n    return bool(command)\n','violated'),
'closed_guard':('policy.py','def allowed(command):\n    return False\n','preserved')}
for name,(file,source,expected) in controls.items():
 files=dict(base['after']);files[file]=source;r=extract(files)
 results.append({'case':name,'expected_restriction_status':expected,'actual':r,'correct':r['restriction_status']==expected})
# Summary-based counterfactuals: restore a source component, keep the remainder fixed.
cf=[]
for c in cases:
 if not c['label']:continue
 for name,fn,newsource in [('restore_guard','policy.py',c['history'][0]['files']['policy.py']),('restore_arguments','runner.py',c['after']['runner.py'].replace('subprocess.run(command,','subprocess.run(["printf", "synthetic"],')),('restore_shell','runner.py',c['after']['runner.py'].replace('shell=True','shell=False'))]:
  f=dict(c['after']);f[fn]=newsource;s=extract(f)
  remains=not s['unknown'] and s['restriction_status']=='violated' and not s['input_independent'] and s['shell']
  cf.append({'case_id':c['case_id'],'counterfactual':name,'specified_violation_remains':bool(remains),'summary':s})
(ROOT/'results/robustness.json').write_text(json.dumps({'controls':results,'counterfactuals':cf,'all_controls_correct':all(x['correct'] for x in results),'all_counterfactuals_remove_specified_property':all(not x['specified_violation_remains'] for x in cf),'scope':'restricted source-summary counterfactuals; not causality or minimality proofs about arbitrary programs'},indent=2));print('controls',len(results),'correct',sum(x['correct'] for x in results),'counterfactuals',len(cf),'still violate',sum(x['specified_violation_remains'] for x in cf))
