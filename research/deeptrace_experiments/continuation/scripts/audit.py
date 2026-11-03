"""Read-only audit of frozen pilot data and documented access routes."""
import hashlib,json,collections,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'continuation';OUT=HERE/'results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for p in sorted((ROOT/'data').glob('*.json')):
 x=json.loads(p.read_text());s=x.get('sample') if isinstance(x,dict) else None
 if not s:continue
 meta=s.get('metadata',{});actions=[m for m in s.get('messages',[]) if m.get('role')=='assistant' and m.get('tool_calls')]
 env=meta.get('environment',{});rev=env.get('version') or env.get('commit') or meta.get('env_commit')
 rows.append({'id':p.stem,'sha256':sha(p),'environment':env.get('id'),'attack':bool(meta.get('side_tasks')),'assistant_action_groups':len(actions),'tool_calls':sum(len(m['tool_calls']) for m in actions),'parallel_action_groups':sum(len(m['tool_calls'])>1 for m in actions),'initial_environment_provenance':rev,'workspace_diff_present':'workspace_diff' in s.get('scores',{}),'baseline_snapshot_present':any('baseline' in k.lower() for k in s.get('store',{})),'ready_for_exact_replay':False,'blockers':['no verified initial revision/tree','no complete state transition verification','no independently validated first-harm boundary/reference']})
oldjobs=[json.loads(l) for l in (ROOT/'results/jobs_temporal.jsonl').read_text().splitlines()]
oldhashes={hashlib.sha256(json.dumps(j['messages'],sort_keys=True).encode()).hexdigest() for j in oldjobs}
notes={'audit_version':1,'proposal_sha256':sha(Path('/Users/vedpanse/Downloads/DeepTrace_Two_Experiment_Proposals.pdf')),'cached_samples':rows,'sample_count':len(rows),'exact_replay_ready':0,'old_e2_logical_jobs':len(oldjobs),'old_e2_unique_prompts':len(oldhashes),'old_e1_limitations':['editor-only fragment replay','missing initial revisions','same-turn grouping does not resolve execution interleavings','any-alarm metrics do not measure timely detection','only one unverified recorded landing marker'],'old_e2_limitations':['extractor only supports authored runner/policy grammar','no strong current-code semantic baseline','history recomputed, not incremental','reference passages not independently validated oracle','cached variants not independent observations','previous test inspected and unsuitable for confirmatory reuse'],'local_archive_search':'No preexisting research .eval files found in project or Downloads. Newly cloned Control Tower has CI probe/test fixtures; these are not LinuxArena research trajectories.','docker_runtime':'client installed, daemon unavailable; no target tools executed','pins':{}}
for name,path in [('control_tower',ROOT/'control-tower'),('public_auto_workflow_candidate',ROOT/'env-auto-workflow'),('agentsecgraph',ROOT.parent/'agentsecgraph/upstream')]:
 r=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True);notes['pins'][name]=r.stdout.strip()
notes['public_auto_workflow_candidate_note']='Pinned public v1.0.1 checkout is a provenance candidate only; not established as any cached trajectory initial tree.'
OUT.mkdir(exist_ok=True);(OUT/'audit.json').write_text(json.dumps(notes,indent=2));print(json.dumps({'samples':len(rows),'exact_replay_ready':0,'pins':notes['pins']},indent=2))
if (ROOT/'results/continuation/access_probes.json').exists():(OUT/'access_probes.json').write_bytes((ROOT/'results/continuation/access_probes.json').read_bytes())
