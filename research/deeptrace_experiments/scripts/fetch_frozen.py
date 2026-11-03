"""Restore only the ten frozen public trajectory samples. Never execute their tools."""
import json,urllib.request,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data';D.mkdir(exist_ok=True)
for row in json.loads((ROOT/'results/frozen_trajectories.json').read_text()):
 p=D/(row['trajectory_id']+'.json')
 if not p.exists():
  with urllib.request.urlopen('https://data.linuxarena.ai/api/trajectories/'+row['trajectory_id'],timeout=60) as f:raw=f.read()
  p.write_bytes(raw)
 x=json.loads(p.read_text());digest=hashlib.sha256(json.dumps(x['sample'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if digest!=row['sample_canonical_sha256']:raise RuntimeError('Frozen sample changed: '+row['trajectory_id'])
 print(row['trajectory_id'],'verified')
