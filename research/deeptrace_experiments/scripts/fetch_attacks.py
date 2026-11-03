from fetch_data import get,D
import json
from concurrent.futures import ThreadPoolExecutor
items=sorted(json.loads((D/'successful_attack_candidates.json').read_text())['items'],key=lambda x:x['trajectory_id'])[:8]
(D/'attack_selection_v2.json').write_text(json.dumps({'selection':'lexicographically first eight among latest thirty recorded successful attacks; take six unique accessible action histories','candidates':items},indent=2))
def fetch(x):
 tid=x['trajectory_id']
 try:
  r=get('https://data.linuxarena.ai/api/trajectories/'+tid,D/(tid+'.json'));print(tid,'messages',len(r.get('sample',{}).get('messages',[])),flush=True)
 except Exception as e:print(tid,str(e),flush=True)
with ThreadPoolExecutor(max_workers=4) as p:list(p.map(fetch,items))
