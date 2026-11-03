"""Whitelist only study artifacts; exclude credentials, runtimes and cloned repos."""
import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT.parents[1];HERE=ROOT/'continuation';dest=PROJECT/'output/pdf/DeepTrace_Continuation_Source_and_Results.zip';paths=[]
for p in HERE.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:paths.append(p)
for rel in ['scripts/fixture_interpreter.py','results/monitor_settings.json','results/requirements.lock.txt','results/spend.json','results/temporal_metrics.json','results/real_metrics.json','results/frozen_trajectories.json']:
 paths.append(ROOT/rel)
paths += [PROJECT/'output/pdf/deeptrace_experiment_report/main.tex',PROJECT/'output/pdf/deeptrace_experiment_report/pilot_report_2026-10-29.tex',PROJECT/'output/pdf/DeepTrace_Two_Experiment_Results.pdf']
paths=[p for p in paths if p.name not in {'artifact_manifest.json','bundle_receipt.json'}]
key=(ROOT/'.secrets/openrouter_key').read_bytes().strip();manifest=[]
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(paths):
  data=p.read_bytes()
  if key and key in data:raise ValueError('credential found, not packaging')
  rel=str(p.relative_to(PROJECT));assert not any(x in p.parts for x in ['.secrets','.venv','models'])
  z.writestr(rel,data);manifest.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
 z.writestr('artifact_manifest.json',json.dumps(manifest,indent=2))
 proposal=Path('/Users/vedpanse/Downloads/DeepTrace_Two_Experiment_Proposals.pdf');z.write(proposal,'inputs/DeepTrace_Two_Experiment_Proposals.pdf')
(HERE/'results/artifact_manifest.json').write_text(json.dumps(manifest,indent=2));receipt={'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(manifest)+2,'credentials_excluded':True,'scope':'continuation plus shared interpreter, settings, locked dependencies and original pilot metrics; cloned analyzer repos obtainable at recorded commits; cached original trajectories not redistributed here'}
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 for m in manifest:assert hashlib.sha256(z.read(m['path'])).hexdigest()==m['sha256']
(HERE/'results/bundle_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
