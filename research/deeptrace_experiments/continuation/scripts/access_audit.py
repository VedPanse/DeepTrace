"""Recheck documented public routes. Never accepts or logs authentication tokens."""
import json,urllib.request,hashlib,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'results'
urls=['https://data.linuxarena.ai/api/trajectories/21c5fa535dd54a46bfb1ae8958dd7f27','https://data.linuxarena.ai/api/trajectories/21c5fa535dd54a46bfb1ae8958dd7f27/eval','https://data.linuxarena.ai/api/runs/ace6e820844e4faf9e0a5907f774a7c6/eval','https://ct-linuxarena-public-eval-logs.s3.amazonaws.com/ace6e820844e4faf9e0a5907f774a7c6.eval']
rows=[]
for url in urls:
 try:
  with urllib.request.urlopen(url,timeout=20) as r:
   b=r.read(8_000_000);row={'url':url,'status':r.status,'prefix_bytes':len(b),'prefix_sha256':hashlib.sha256(b).hexdigest()}
 except Exception as e:row={'url':url,'error':str(e)}
 rows.append(row)
(OUT/'access_recheck.json').write_text(json.dumps({'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requests':rows},indent=2));print(rows)
