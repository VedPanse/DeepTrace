"""Read-only upstream analyzer over authored snapshots, inside Seatbelt."""
import sys,json,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'agentsecgraph/upstream/src'))
from agentsecbench import analyze_repository
cases=json.loads((ROOT/'data/temporal/cases.json').read_text());out=[]
for i,c in enumerate(cases):
 entry={'case_id':c['case_id'],'versions':{}}
 for v in 'ABCD':
  dest=ROOT/'results/static'/c['case_id']/v;t=time.perf_counter();r=analyze_repository(ROOT/'data/temporal'/c['case_id']/v,dest)
  entry['versions'][v]={'graph_count':len(r.graphs),'seconds':time.perf_counter()-t,'graphs':r.graphs}
 out.append(entry)
 if i%30==0:print(i,len(cases),flush=True)
(ROOT/'results/static_graphs.json').write_text(json.dumps(out))
