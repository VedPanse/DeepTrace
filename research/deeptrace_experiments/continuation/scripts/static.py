import sys,json,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'continuation';sys.path.insert(0,str(ROOT.parent/'agentsecgraph/upstream/src'))
from agentsecbench import analyze_repository
out=[]
for i,c in enumerate(json.loads((HERE/'data/cases.json').read_text())):
 row={'case_id':c['case_id'],'versions':{}}
 for v in ['A','C','D']:
  start=time.perf_counter()
  try:
   source=HERE/'data/controlled'/c['case_id']/v
   result=analyze_repository(source,HERE/'results/static'/c['case_id']/v)
   row['versions'][v]={'status':'ok','source_files':len(list(source.glob('*.py'))),'graphs':result.graphs,'seconds':time.perf_counter()-start}
  except Exception as e:row['versions'][v]={'status':'failed','error':type(e).__name__+': '+str(e),'seconds':time.perf_counter()-start}
 out.append(row)
 if i%80==0:print('extracted',i,flush=True)
(HERE/'results/static.json').write_text(json.dumps(out));print('done',len(out),flush=True)
