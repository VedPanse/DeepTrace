"""Two-phase, two-model qualification. Same inputs/settings; model ID differs.
No response repair or favorable resampling. Network failures may retry unchanged.
"""
import json,hashlib,sys,time,random,threading,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from evidence import ROOT
OUT=ROOT/'qualification/results';RESP=OUT/'responses';RESP.mkdir(exist_ok=True);lock=threading.Lock();reserved=0.;spent=0.
for folder in [ROOT/'results/responses',ROOT/'continuation/results/responses',ROOT/'diagnosis/results/responses',RESP]:
 for p in folder.glob('*.json'):spent+=float(json.loads(p.read_text()).get('accounted_cost',0))
key=(ROOT/'.secrets/openrouter_key').read_text().strip();protocol=json.loads((OUT/'protocol.json').read_text());SETTINGS=protocol['same_request_settings_except_model']
def score(j):
 global spent,reserved
 path=RESP/(j['job_id']+'.json')
 if path.exists():return json.loads(path.read_text())
 reservation=.01 if j['model']=='openai/gpt-5' else .001;attempts=[];cost=0.;start=time.perf_counter()
 for attempt in range(2):
  with lock:
   if spent+reserved+reservation>3:return {'status':'budget_exhausted','accounted_cost':cost,'attempts':attempts}
   reserved+=reservation
  req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps({**SETTINGS,'model':j['model'],'messages':j['messages']}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Title':'DeepTrace monitor qualification'})
  try:
   with urllib.request.urlopen(req,timeout=50) as r:raw=json.load(r)
   billed=float(raw.get('usage',{}).get('cost',reservation));cost+=billed
   with lock:spent+=billed;reserved-=reservation
   content=raw.get('choices',[{}])[0].get('message',{}).get('content') or ''
   try:parsed=json.loads(content);status='ok'
   except Exception:parsed=None;status='invalid_json'
   result={'status':status,'parsed':parsed,'raw_response':raw,'accounted_cost':cost,'latency_seconds':time.perf_counter()-start,'attempts':attempts,'finish_reason':raw.get('choices',[{}])[0].get('finish_reason')};path.write_text(json.dumps(result));return result
  except Exception as e:
   with lock:spent+=reservation;reserved-=reservation
   cost+=reservation;attempts.append({'attempt':attempt+1,'error':type(e).__name__+': '+str(e),'conservative_reserved_cost':reservation})
   if isinstance(e,urllib.error.HTTPError) and e.code in [400,401,402,403,404]:break
 result={'status':'transport_error','parsed':None,'accounted_cost':cost,'latency_seconds':time.perf_counter()-start,'attempts':attempts};path.write_text(json.dumps(result));return result

def main(phase):
 path=OUT/(phase+'_jobs.jsonl');assert hashlib.sha256(path.read_bytes()).hexdigest()==protocol[phase+'_jobs_sha256']
 if phase=='qualification':
  seal=json.loads((OUT/'development_seal.json').read_text());assert seal['protocol_sha256']==hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest();assert seal['development_scores_sha256']==hashlib.sha256((OUT/'development_scores.jsonl').read_bytes()).hexdigest()
  release=OUT/'qualification_release.json'
  if not release.exists():
   jobs=list(map(json.loads,path.read_text().splitlines()));assert not any((RESP/(j['job_id']+'.json')).exists() for j in jobs)
   release.write_text(json.dumps({'released_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'criteria_and_prompt_frozen':True,'development_seal_sha256':hashlib.sha256((OUT/'development_seal.json').read_bytes()).hexdigest(),'qualification_responses_existing_before_release':0},indent=2))
 jobs=list(map(json.loads,path.read_text().splitlines()));random.Random(180304).shuffle(jobs);results={}
 print(phase,'jobs',len(jobs),flush=True)
 with ThreadPoolExecutor(max_workers=6) as pool:
  fs={pool.submit(score,j):j for j in jobs}
  for i,f in enumerate(as_completed(fs),1):
   j=fs[f];results[j['job_id']]=f.result()
   if i%20==0:print('completed',i,'/',len(jobs),'accounted total',round(spent,4),flush=True)
 rows=[{k:v for k,v in j.items() if k!='messages'}|{'response':{k:v for k,v in results[j['job_id']].items() if k!='raw_response'}} for j in jobs]
 (OUT/(phase+'_scores.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows));(OUT/'cost.json').write_text(json.dumps({'combined_accounted_usd':spent,'cap_usd':3,'qualification_accounted_usd':sum(float(json.loads(p.read_text()).get('accounted_cost',0)) for p in RESP.glob('*.json')),'transport_costs':'conservative reservation where provider billing unknown'},indent=2));print('DONE',phase,flush=True)
if __name__=='__main__':main(sys.argv[1])
