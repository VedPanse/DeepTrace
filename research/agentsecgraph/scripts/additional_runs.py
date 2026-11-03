import json,csv
from run_isolated import ROOT,run
R=ROOT/'results'
for name in ['html-anything','mini-swe-agent','magentic-ui']:
 o=R/'graph-timing'/name;o.mkdir(parents=True,exist_ok=True)
 print(name,run(['graph-timing',ROOT/'targets'/name,o],o/'run.log'),flush=True)
rows=[]
for t in json.loads((R/'temporal.json').read_text()):rows.append({'sample_id':'TEMP'+t['version'],'repo':'synthetic/temporal-'+t['version'],'git_commit':t['commit'],'repository_path':str(R/'fixtures/temporal-history'),'experiment_split':'development'})
with (R/'temporal-manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
p=R/'temporal-paper';p.mkdir(exist_ok=True)
for args in [['static_scan.py','--manifest',R/'temporal-manifest.csv','--granularity','line','--output',p/'findings.jsonl','--summary',p/'scan-summary.csv'],['generate_security_adg_v2.py','--manifest',R/'temporal-manifest.csv','--findings',p/'findings.jsonl','--analysis-mode','v2_5','--split','all_corpus','--output',p/'security-adg.jsonl','--summary',p/'summary.json']]:
 print(args[0],run(['legacy',*args],p/(args[0]+'.log')),flush=True)
print('validation',run(['legacy','validate_security_adg.py','--input',R/'paper/security-adg.jsonl','--expected-split','development'],R/'paper/validation.json'))
