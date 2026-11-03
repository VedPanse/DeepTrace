import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'agentsecgraph/upstream/src'))
from agentsecbench import analyze_repository
records=json.loads((ROOT/'data/real_replay.json').read_text());out={}
for r in records:
 output={}
 for sid,state in r['states'].items():
  start=time.perf_counter();dest=ROOT/'results/real_static'/r['trajectory_id']/sid
  try:
   result=analyze_repository(Path(state['path']),dest)
   output[sid]={'graphs':result.graphs,'seconds':time.perf_counter()-start,'files_scanned':result.summary.files_scanned,'quality':state['quality'],'status':'ok'}
  except Exception as e:output[sid]={'status':'failure','message':str(e),'graphs':[]}
 out[r['trajectory_id']]=output;print(r['trajectory_id'],len(output),flush=True)
(ROOT/'results/real_static_graphs.json').write_text(json.dumps(out))
