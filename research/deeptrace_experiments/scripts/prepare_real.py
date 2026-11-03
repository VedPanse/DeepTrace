"""Prefix-only replay of publicly observed editor text; never execute trajectory tools.
Recovered text is marked complete/partial. Missing original repository states remain missing.
"""
import json,hashlib,random,re,time,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data';R=ROOT/'results';OBS=D/'observed';OBS.mkdir(exist_ok=True)
records=[];seen=set();duplicates=[]
for path in sorted(D.glob('*.json')):
 x=json.loads(path.read_text())
 if not isinstance(x,dict) or 'sample' not in x:continue
 s=x['sample'];raw=[{'message_index':i,'tool_calls':m['tool_calls']} for i,m in enumerate(s.get('messages',[])) if m.get('role')=='assistant' and m.get('tool_calls')]
 if not raw:continue
 # Message index is retained for replay, excluded from content deduplication.
 h=hashlib.sha256(json.dumps([{k:v for k,v in a.items() if k!='message_index'} for a in raw],sort_keys=True).encode()).hexdigest()
 if h in seen:duplicates.append(path.stem);continue
 seen.add(h);meta=s.get('metadata',{});attack=bool(meta.get('side_tasks'))
 outs={m.get('tool_call_id'):m for m in s.get('messages',[]) if m.get('role')=='tool'}
 task='\n'.join(t.get('description','') for t in meta.get('main_tasks',[]));env=meta.get('environment',{}).get('id','unknown')
 acts=[];history=[];state={};quality={};events=[];states={}
 for index,a in enumerate(raw):
  action=json.dumps({'proposed_tool_calls':[{'tool':tc['function'],'arguments':tc.get('arguments',{})} for tc in a['tool_calls']]},ensure_ascii=False)
  # Snapshot and evidence refer only to completed earlier actions.
  state_hash=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()[:20]
  if state_hash not in states:
   state_dir=OBS/path.stem/state_hash;state_dir.mkdir(parents=True,exist_ok=True)
   for source,text in state.items():
    # Fragment files have original extension; normalized local names cannot escape the sandbox.
    suffix=Path(source).suffix;local=hashlib.sha256(source.encode()).hexdigest()[:12]+suffix
    (state_dir/local).write_text(text)
   states[state_hash]={'path':str(state_dir),'files':dict(state),'quality':dict(quality)}
  acts.append({'index':index,'tool_call_ids':[tc['id'] for tc in a['tool_calls']],'action':action,'prefix_history':list(history),'prior_editor_events':list(events),'state_hash':state_hash,'source_quality':dict(quality)})
  observations=[]
  for tc in a['tool_calls']:
   result=outs.get(tc['id'],{});content=result.get('content','');content=content if isinstance(content,str) else json.dumps(content)
   observations.append(content)
   args=tc.get('arguments',{});command=args.get('command');source=args.get('path')
   failed=result.get('error') or result.get('is_error') or re.match(r'\s*(Error:|ERROR:)',content)
   if tc['function']=='text_editor' and source and not failed:
    if command=='create' and isinstance(args.get('file_text'),str):state[source]=args['file_text'];quality[source]='complete_created_file'
    elif command=='str_replace' and isinstance(args.get('new_str'),str):
     old=args.get('old_str','');new=args['new_str']
     if source in state and old and old in state[source]:state[source]=state[source].replace(old,new,1)
     else:state[source]=textwrap.dedent(new);quality[source]='partial_replacement_fragment'
    if command in {'create','str_replace'}:events.append({'index':index,'path':source,'before':args.get('old_str'),'after':args.get('new_str',args.get('file_text')),'quality':quality.get(source,'unresolved')})
  history.append(f'Action {index}: {action}\nObserved results: '+'\n'.join(observations))
 tasks=s.get('scores',{}).get('tasks',{}).get('value',{})
 records.append({'trajectory_id':path.stem,'environment':env,'attack':attack,'task':task,'actions':acts,'states':states,'recorded_task_scores':tasks,'source_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
attacks=[r for r in records if r['attack']];honest=[r for r in records if not r['attack']]
# Freeze calibration by environment and held-out honest test by different environments.
cal=[];test=[]
for r in honest:
 target=cal if r['environment'] in {'linuxarena/slack_clone','linuxarena/file_indexing'} or r['trajectory_id']=='03b20bf82ec746ac811c5c1a7c567d8b' else test
 target.extend((r['trajectory_id'],a['index']) for a in r['actions'])
rng=random.Random(18029);cal=sorted(rng.sample(cal,min(100,len(cal))));test=sorted(rng.sample(test,min(100,len(test))))
selection={'attack_ids':[r['trajectory_id'] for r in attacks],'honest_unique_ids':[r['trajectory_id'] for r in honest],'excluded_duplicate_ids':duplicates,'calibration_actions':cal,'test_honest_actions':test,'split':'three unique honest trajectories for calibration (slack_clone, file_indexing, web_scraping task A); two held-out trajectories for test (model_registry, web_scraping task B); no transcript duplicates across splits','attack_harm_indices':{r['trajectory_id']:r['recorded_task_scores'].get('landed_at') for r in attacks},'action_unit':'one assistant turn containing tool calls; grouped calls scored together, no same-turn results in evidence','protocol_version':2,'scope':'Recorded successful attacks only. Only text_editor creations/replacements replayed; bash writes and initial repository trees not reconstructed. Fragment quality explicit.'}
(R/'real_protocol.json').write_text(json.dumps(selection,indent=2));(D/'real_replay.json').write_text(json.dumps(records))
print('unique attacks',len(attacks),'honest',len(honest),'cal',len(cal),'test',len(test),'states',sum(len(r['states']) for r in records),'attack actions',sum(len(r['actions']) for r in attacks))
