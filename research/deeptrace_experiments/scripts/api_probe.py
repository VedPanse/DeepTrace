import urllib.request,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
body={'model':'openai/gpt-5-nano','messages':[{'role':'user','content':'Return JSON only: {"score":0,"reason":"connectivity test"}'}],'max_tokens':256,'reasoning':{'effort':'minimal','exclude':True},'response_format':{'type':'json_object'},'provider':{'only':['OpenAI'],'allow_fallbacks':False,'data_collection':'deny','require_parameters':True}}
req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+(R/'.secrets/openrouter_key').read_text().strip(),'Content-Type':'application/json','X-Title':'DeepTrace capstone evaluation'})
try:
 with urllib.request.urlopen(req,timeout=90) as f:r=json.load(f)
 (R/'results/api_probe.json').write_text(json.dumps(r,indent=2));print('provider',r.get('provider'),'model',r.get('model'),'content',r['choices'][0]['message'].get('content'),'usage',r.get('usage'))
except urllib.error.HTTPError as e:print(e.code,e.read().decode()[:1000])
