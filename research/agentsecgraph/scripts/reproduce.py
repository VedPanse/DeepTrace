"""Run both unmodified public and paper pipelines on commit-pinned targets."""
import csv,json,subprocess,sys,platform,time
from pathlib import Path
from run_isolated import run,ROOT
R=ROOT/'results'
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
repos=[('html-anything','nexu-io/html-anything'),('mini-swe-agent','SWE-agent/mini-swe-agent'),('magentic-ui','microsoft/magentic-ui')]
manifest=[]
pins=json.loads((R/'repositories.json').read_text())
for pin in [pins['analyzer'],*pins['targets']]:
 actual=git(ROOT/pin['path'],'rev-parse','HEAD')
 if actual!=pin['commit']:raise RuntimeError(f'Commit mismatch: {pin["path"]}')
for i,(name,slug) in enumerate(repos,1):
 p=ROOT/'targets'/name
 row={'sample_id':f'DT{i:04}','repo':slug,'git_commit':git(p,'rev-parse','HEAD'),'repository_path':str(p),'experiment_split':'development'}
 manifest.append(row)
print('pins',json.dumps(manifest),flush=True)
(R/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'analyzer_commit':git(ROOT/'upstream','rev-parse','HEAD'),'url':'https://github.com/A1LinLin1/AgentSecBench','target_manifest':manifest},indent=2))
with (R/'manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
for name,_ in repos:
 output=R/'product'/name;output.mkdir(parents=True,exist_ok=True)
 print('scan',name,flush=True);code=run(['scan',ROOT/'targets'/name,output],output/'run.log');print('exit',code,flush=True)
legacy=R/'paper';legacy.mkdir(exist_ok=True)
steps=[['static_scan.py','--manifest',R/'manifest.csv','--granularity','line','--output',legacy/'findings.jsonl','--summary',legacy/'scan-summary.csv'],['generate_security_adg_v2.py','--manifest',R/'manifest.csv','--findings',legacy/'findings.jsonl','--split','all_corpus','--analysis-mode','v2_5','--output',legacy/'security-adg.jsonl','--summary',legacy/'summary.json','--showcase-dir',legacy/'showcase','--showcase-max-graphs','6']]
for args in steps:
 print('legacy',args[0],flush=True);code=run(['legacy',*args],legacy/(args[0]+'.log'));print('exit',code,flush=True)
print('product tests',run(['test'],R/'upstream-tests-rerun.log'),flush=True)
