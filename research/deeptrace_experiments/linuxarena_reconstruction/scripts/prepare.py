"""Freeze a task-matched recorded cohort before real-container replay."""
import hashlib,json,sys,datetime
from pathlib import Path
from inspect_ai.log import read_eval_log
from inspect_ai.event import ToolEvent

BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=BASE/'results/cohort.json'
    if out.exists():raise RuntimeError('cohort already frozen')
    src=ROOT/'linuxarena_reassessment/data/ace6e820844e4faf9e0a5907f774a7c6.eval'
    candidates=json.loads((ROOT/'linuxarena_reassessment/results/candidate_cohort.json').read_text())['candidates']
    log=read_eval_log(str(src),resolve_attachments=True);byid={s.uuid:s for s in log.samples};rows=[]
    for c in candidates:
        s=byid[c['sample_uuid']];tools=[e.model_dump(mode='json') for e in s.events if isinstance(e,ToolEvent)]
        assert len({e['id'] for e in tools})==len(tools)
        overlaps=[{'a':a['id'],'b':b['id']} for i,a in enumerate(tools) for b in tools[i+1:] if a.get('completed') and b['timestamp']<a['completed']]
        row={'sample_uuid':s.uuid,'sample_file':c['sample_file'],'stream':'attack' if c['has_side_task'] else 'honest','environment_id':c['environment_id'],'main_tasks':[t['id'] for t in s.metadata['main_tasks']],'side_tasks':[t['id'] for t in s.metadata['side_tasks']],'calls':tools,'overlapping_calls':overlaps}
        (BASE/'data'/f'{s.uuid}.json').write_text(json.dumps(row,indent=2));rows.append({k:v for k,v in row.items() if k!='calls'}|{'tool_events':len(tools),'record_sha256':sha(BASE/'data'/f'{s.uuid}.json')})
    meta=log.eval.metadata
    result={'frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':'all three task-matched samples, chosen by task name before replay; not selected by attack success','source_archive_sha256':sha(src),'cohort':rows,'original_harness':meta['ct_git'],'original_setting_commit':meta['setting_repos']['.settings/linuxarena'],'original_environment':meta['env_versions']['linuxarena/auto_workflow'],'original_packages':log.eval.packages,'original_sandbox':meta['sandbox_config'],'workspace_scope':['/app'],'other_effects':'docker diff and declared external-path/service effects retained; no claim of complete process/database reconstruction','capture':'real Docker paused source snapshots, content-addressed blobs; no recorded-output sandbox','paid_model_calls':0,'original_outcomes_used_for_selection':False,'historical_state_equality':'requires independent recorded read/edit checks; a successful local replay alone is insufficient','harm_review':'not performed in this infrastructure pilot'}
    out.write_text(json.dumps(result,indent=2));print('Frozen',len(rows),'recordings;',sum(r['tool_events'] for r in rows),'tool events;',sum(len(r['overlapping_calls']) for r in rows),'overlaps')
if __name__=='__main__':main()
