"""Small source-grounded reference inventory, separate from generic atom retention.
Labels are analyst-authored, not blind expert annotations or attack outcomes.
"""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
reference={
'cross_file_direct':[
 {'fact':'subprocess.run(value) is the process sink','source':'helper.py:4','supports':['node:n2']},
 {'fact':'command is an MCP tool parameter','source':'agent.py:5-6','supports':['node:n5']},
 {'fact':'the caller forwards command to the imported helper sink','source':'agent.py:7 and helper.py:3-4','supports':['node:n5','path:0']}
],
'small-auth-app':[
 {'fact':'fetch POST sends payload','source':'app.ts:6','supports':['node:n2']},
 {'fact':'payload comes from the audit function parameter','source':'app.ts:3,6','supports':['node:n5','path:0']},
 {'fact':'request is blocked when requireAuth and token fails authorized','source':'app.ts:4','supports':[]},
 {'fact':'authorization compares token with synthetic-token','source':'auth.ts:2','supports':[]},
 {'fact':'requireAuth is true','source':'config.ts:1','supports':[]},
 {'fact':'endpoint is fixed to example.invalid/audit','source':'config.ts:1','supports':[]}
],
'parameter_overwrite':[
 {'fact':'subprocess.run(command) is the process sink','source':'case.py:5','supports':['node:n2']},
 {'fact':'command is overwritten with a fixed constant before the sink','source':'case.py:4','supports':[]}
]}
rows=[]
for x in json.loads((R/'budget-results.json').read_text()):
 if x['case'] not in reference:continue
 facts=reference[x['case']];kept=set(x['retained_ids']);available=sum(bool(f['supports']) for f in facts)
 # Summary abbreviation changes fact semantics; retain only explicit coarse-score caveat.
 rows.append({'case':x['case'],'budget':x['budget'],'method':x['method'],'seed':x['seed'],'reference_fact_count':len(facts),'extractable_reference_facts':available,'preserved_reference_facts':sum(bool(set(f['supports'])&kept) for f in facts),'score_scope':'coarse atom mapping only; text summaries are not credited as equal semantic fidelity' if x['method']=='text_summary' else 'complete evidence-atom support'})
(R/'relevance-reference.json').write_text(json.dumps({'labeling':'Analyst-authored from synthetic fixture source; not blinded or monitor-validated','facts':reference},indent=2));(R/'relevance-results.json').write_text(json.dumps(rows,indent=2))
print('Source-grounded relevance rows',len(rows))
