import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent.parent;R=ROOT/'results';PAPER=WORKSPACE/'output/pdf/deeptrace_experiment_report'
manifest={}
paths=[]
for p in (ROOT/'scripts').glob('*.py'):paths.append(p)
paths.extend([ROOT/'REPRODUCTION.txt',ROOT/'data/temporal/cases.json'])
for p in R.glob('*.json'):
 if p.name!='artifact_sha256.json':paths.append(p)
for name in ['scores.jsonl','jobs_temporal.jsonl','jobs_real.jsonl','requirements.lock.txt']:paths.append(R/name)
paths.extend((R/'responses').glob('*.json'));paths.extend((R/'temporal_dags').glob('*.json'))
paths.append(PAPER/'main.tex');paths.extend((PAPER/'images').glob('*.pdf'))
paths.append(WORKSPACE/'output/pdf/DeepTrace_Two_Experiment_Results.pdf')
key=(ROOT/'.secrets/openrouter_key').read_bytes().strip()
for p in paths:
 assert p.exists(),p
 assert '.secrets' not in p.parts
 data=p.read_bytes();assert key not in data,p
 manifest[str(p.relative_to(WORKSPACE))]=hashlib.sha256(data).hexdigest()
(R/'artifact_sha256.json').write_text(json.dumps(manifest,indent=2));paths.append(R/'artifact_sha256.json')
archive=WORKSPACE/'output/pdf/DeepTrace_Experiment_Source_and_Results.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(paths)):
  # Deliver one report PDF separately; source archive contains LaTeX, plots and analysis evidence.
  if p.name=='DeepTrace_Two_Experiment_Results.pdf':continue
  z.write(p,str(p.relative_to(WORKSPACE)))
with zipfile.ZipFile(archive) as z:
 assert not any('/.secrets/' in n or '/.venv/' in n or '/models/' in n for n in z.namelist())
 assert all(key not in z.read(n) for n in z.namelist())
print('Source/result archive',archive,'bytes',archive.stat().st_size,'entries',len(z.namelist()))
print('Report SHA256',manifest['output/pdf/DeepTrace_Two_Experiment_Results.pdf'])
