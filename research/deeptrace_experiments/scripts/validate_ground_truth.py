import json,hashlib
from pathlib import Path
from fixture_interpreter import run
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/temporal';cases=json.loads((D/'cases.json').read_text());rows=[];changed=0
for c in cases:
 traces=[]
 for x in c['known_domain']:
  effects=run(c['after'],x)
  violates=any(e['shell'] and isinstance(e['args'],str) and e['args']!='status' for e in effects)
  traces.append({'input':x,'recorded_process_effects':effects,'violates_declared_property':violates})
 actual=any(t['violates_declared_property'] for t in traces);changed+=actual!=bool(c['label'])
 rows.append({'case_id':c['case_id'],'computed_label':int(actual),'frozen_label':c['label'],'matches':actual==bool(c['label']),'traces':traces})
(ROOT/'results/concrete_ground_truth.json').write_text(json.dumps(rows,indent=2));(ROOT/'results/ground_truth_validation.json').write_text(json.dumps({'cases':len(cases),'concrete_runs':sum(len(x['traces']) for x in rows),'labels_changed':changed,'all_matches':changed==0,'interpreter':'full source files, resolved direct imports, whitelisted Python AST, process calls recorded instead of executed','label_access':'concrete interpreter does not read case variant names or frozen labels while evaluating source'},indent=2));assert changed==0
print('Full-source concrete execution checks',sum(len(x['traces']) for x in rows),'all labels unchanged')
