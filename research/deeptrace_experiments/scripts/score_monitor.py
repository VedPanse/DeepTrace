"""Fixed OpenRouter monitor, one draw per unique prompt, no training or tools.
Budget reserves a conservative upper bound before dispatch; credentials never logged.
"""
import json,urllib.request,urllib.error,hashlib,time,random,threading,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';RESP=R/'responses';RESP.mkdir(exist_ok=True)
API='https://openrouter.ai/api/v1/chat/completions'
SETTINGS={'model':'openai/gpt-5-nano','max_tokens':256,'reasoning':{'effort':'minimal','exclude':True},'response_format':{'type':'json_object'},'provider':{'only':['OpenAI'],'allow_fallbacks':False,'data_collection':'deny','require_parameters':True}}
(R/'monitor_settings.json').write_text(json.dumps({'request':SETTINGS,'endpoint':API,'spend_cap_usd':3.0,'workers':8,'draws_per_unique_prompt':1,'same_prompt_reuse':'exact message hash; shared across conditions and budgets if text identical','privacy':'training/data collection disallowed; per-request ZDR attempted but endpoint unavailable, so no ZDR guarantee'},indent=2))
key=(ROOT/'.secrets/openrouter_key').read_text().strip();lock=threading.Lock();spent=sum(float(json.loads(p.read_text()).get('accounted_cost',0)) for p in RESP.glob('*.json'));reserved=0.0

def score(ph,messages):
 global spent,reserved
 p=RESP/(ph+'.json')
 if p.exists():return json.loads(p.read_text())
 # Every request here is <= 10k input tokens. Reserve covers 10k*5e-8 + 512*4e-7.
 reserve=.001
 for attempt in range(3):
  with lock:
   if spent+reserved+reserve>3.0:return {'status':'budget_exhausted','prompt_hash':ph}
   reserved+=reserve
  body={**SETTINGS,'messages':messages}
  if attempt:body['max_tokens']=512
  request=urllib.request.Request(API,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Title':'DeepTrace capstone evaluation'})
  start=time.perf_counter();result={'prompt_hash':ph,'attempt':attempt+1}
  try:
   with urllib.request.urlopen(request,timeout=120) as f:raw=json.load(f)
   cost=raw.get('usage',{}).get('cost');accounted=float(cost) if cost is not None else reserve
   with lock:spent+=accounted;reserved-=reserve
   message=raw['choices'][0]['message'];content=message.get('content') or '';parsed=json.loads(content)
   value=parsed['score']
   if not isinstance(value,(int,float)) or not 0<=value<=1000:raise ValueError('score outside [0,1000]')
   result.update({'status':'ok','score':float(value),'reason':str(parsed.get('reason','')),'latency_seconds':time.perf_counter()-start,'accounted_cost':accounted,'raw_response':raw})
   p.write_text(json.dumps(result));return result
  except urllib.error.HTTPError as ex:
   with lock:reserved-=reserve
   result.update({'status':'http_error','http_status':ex.code,'message':ex.read().decode()[:1500],'accounted_cost':0,'latency_seconds':time.perf_counter()-start})
  except Exception as ex:
   with lock:
    # If response arrived, usage has already been accounted above.
    if 'raw' not in locals():reserved-=reserve
   result.update({'status':'parse_or_network_error','message':type(ex).__name__+': '+str(ex),'accounted_cost':locals().get('accounted',0),'latency_seconds':time.perf_counter()-start})
  with lock:
   with (R/'monitor_errors.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
  if result.get('http_status') in {401,402,403,404}:break
  time.sleep(1.5*(attempt+1))
 p.write_text(json.dumps(result));return result

def main(paths):
 jobs=[]
 for f in paths:jobs.extend(json.loads(x) for x in Path(f).read_text().splitlines())
 prompts={}
 for j in jobs:
  ph=hashlib.sha256(json.dumps(j['messages'],sort_keys=True).encode()).hexdigest();j['prompt_hash']=ph;prompts[ph]=j['messages']
 ordered=list(prompts);random.Random(18029).shuffle(ordered)
 cached={ph for ph in ordered if (RESP/(ph+'.json')).exists()}
 print('jobs',len(jobs),'unique_prompts',len(prompts),'cached',len(cached),'accounted_spend',spent,flush=True)
 results={ph:json.loads((RESP/(ph+'.json')).read_text()) for ph in cached}
 with ThreadPoolExecutor(max_workers=8) as pool:
  futures={pool.submit(score,ph,prompts[ph]):ph for ph in ordered if ph not in cached}
  for i,f in enumerate(as_completed(futures),1):
   ph=futures[f];results[ph]=f.result()
   if i%25==0:print('completed',i,'/',len(futures),'spend',round(spent,4),'errors',sum(x.get('status')!='ok' for x in results.values()),flush=True)
 out=R/'scores.jsonl'
 with out.open('w') as f:
  for j in jobs:
   response=results.get(j['prompt_hash'],{'status':'missing'});f.write(json.dumps({k:v for k,v in j.items() if k!='messages'}|{'monitor':{k:v for k,v in response.items() if k!='raw_response'}})+'\n')
 (R/'spend.json').write_text(json.dumps({'accounted_usd':spent,'cap_usd':3,'raw_responses':len(results),'jobs':len(jobs)},indent=2));print('DONE',spent,flush=True)
if __name__=='__main__':main(sys.argv[1:])
