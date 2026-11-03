import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data'
cands=json.loads((D/'successful_attack_candidates.json').read_text())['items'];seen=set();records=[]
for t in sorted(cands,key=lambda x:x['trajectory_id']):
 p=D/(t['trajectory_id']+'.json')
 if not p.exists():continue
 x=json.loads(p.read_text());s=x['sample'];a=[{'message_index':i,**tc} for i,m in enumerate(s.get('messages',[])) if m.get('role')=='assistant' for tc in m.get('tool_calls',[])]
 h=hashlib.sha256(json.dumps([{k:v for k,v in tc.items() if k!='message_index'} for tc in a],sort_keys=True).encode()).hexdigest()
 if h in seen:continue
 seen.add(h);records.append({'id':t['trajectory_id'],'environment':t['environment_id'],'side_task':t['side_task_id'],'actions':a,'ground_truth_scores':s.get('scores',{}).get('tasks'),'side_task_description':t.get('side_task_description'),'sample_metadata':s['metadata']})
(D/'real_attacks_unique.json').write_text(json.dumps(records,indent=2))
for r in records:
 print('\nCASE',r['id'],r['environment'],r['side_task']);print('SIDE',str(r['side_task_description'])[:1600])
 for i,a in enumerate(r['actions']):
  cmd=str(a['arguments'])
  if re.search(r'curl|base64|write_text|\.write\(|cat >|cat <<|eval|exec|password|secret|Popen|subprocess|authorized|chmod|import socket|connect\(',cmd,re.I):
   print('ACTION',i,a['id'],cmd[:2600])
