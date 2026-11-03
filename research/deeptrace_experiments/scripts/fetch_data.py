import json,urllib.request,hashlib,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data'
def get(url,path):
 if path.exists():return json.loads(path.read_text())
 req=urllib.request.Request(url,headers={'User-Agent':'DeepTrace capstone research (evaluation only)'})
 with urllib.request.urlopen(req,timeout=60) as f:b=f.read()
 path.write_bytes(b);return json.loads(b)
la=json.loads((D/'lastraj.json').read_text());ids=sorted(la['item_ids'])[:6]
h=get('https://data.linuxarena.ai/api/trajectories?stream=honest&limit=30',D/'honest_candidates.json')['items']
# Match public Python-rich environments where possible, then deterministic identifier order.
h=sorted(h,key=lambda x:x['trajectory_id'])[:12]
pins={'base_url':'https://data.linuxarena.ai','dataset':'LaStraj','dataset_version':la['version'],'selection':'six lexicographically first LaStraj IDs; twelve lexicographically first IDs from latest thirty honest records','attack_ids':ids,'honest_ids':[x['trajectory_id'] for x in h]}
(D/'selection.json').write_text(json.dumps(pins,indent=2))
def fetch(tid):
 
 try:x=get('https://data.linuxarena.ai/api/trajectories/'+tid,D/(tid+'.json'))
 except Exception as e:
  print(tid,'UNAVAILABLE',type(e).__name__,str(e),flush=True);return
 sample=x.get('sample',{});print(tid,'keys',list(x),'messages',len(sample.get('messages',[])),'bytes',(D/(tid+'.json')).stat().st_size,flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,ids+pins['honest_ids']))
