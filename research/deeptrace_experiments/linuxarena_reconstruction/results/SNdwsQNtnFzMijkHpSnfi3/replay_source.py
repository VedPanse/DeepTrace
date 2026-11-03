"""Re-execute recorded public tools in a pinned live container, with captures."""
import asyncio,hashlib,json,sys,time,re,shlex,gzip
from pathlib import Path
from capture import capture,command,differences
from control_tower.live.session import get,attached
from control_tower.tools.bash_tools import bash_with_timeout
from control_tower.tools.diff_display_text_editor import diff_display_text_editor

BASE=Path(__file__).resolve().parents[1]
def source_expectation(call,before,cas):
    if call['function']!='text_editor':return None
    args=call['arguments'];path=args['path'];entry=next((e for e in before['entries'] if e['path']==path and e['kind']=='file'),None)
    if args.get('command')=='create':
        if not path.startswith('/app/'):return {'status':'outside_captured_workspace','path':path}
        parent=Path(path).parent.as_posix();exists=any(e['path']==parent and e['kind']=='directory' for e in before['entries'])
        failed=entry is not None or not exists
        return {'path':path,'operation':'create','expected_atomic_failure':failed,'parent_exists':exists,'expected_after_sha256':entry['sha256'] if entry else None if failed else hashlib.sha256(args['file_text'].encode()).hexdigest()}
    if args.get('command')!='str_replace':return {'path':path,'status':'unsupported_editor_operation'}
    if not entry:return {'status':'missing_preimage','path':path}
    try:text=(cas/entry['sha256']).read_text().expandtabs()
    except UnicodeDecodeError:return {'status':'unsupported_binary','path':path}
    old=args['old_str'].expandtabs();n=text.count(old)
    return {'path':path,'matches_in_preimage':n,'expected_after_sha256':hashlib.sha256(text.replace(old,(args.get('new_str') or '').expandtabs(),1).encode()).hexdigest() if n==1 else entry['sha256'],'expected_atomic_failure':n!=1}

async def main(uuid,session_id,attempt='attempt_1'):
    row=json.loads((BASE/'data'/f'{uuid}.json').read_text());out=BASE/'results'/uuid
    if attempt!='attempt_1':out=out/attempt
    out.mkdir(parents=True,exist_ok=True);cas=BASE/'data/blobs';cas.mkdir(exist_ok=True)
    if (out/'complete.json').exists():raise RuntimeError('already replayed')
    (out/'replay_source.py').write_bytes(Path(__file__).read_bytes())
    (out/'capture_source.py').write_bytes((Path(__file__).parent/'capture.py').read_bytes())
    sess=get(session_id);allcontainers=[json.loads(x) for x in command('docker','ps','--format','json').splitlines()]
    containers=[c['Names'] for c in allcontainers if c['Names'].startswith('inspect-live-'+session_id[:7]+'-')];primary=next(c for c in containers if c.endswith('-default-1'))
    inspection=json.loads(command('docker','inspect',*containers));(out/'containers.json').write_text(json.dumps([{'name':x['Name'],'image':x['Config']['Image'],'image_id':x['Image'],'mounts':x['Mounts'],'health':x['State'].get('Health',{}).get('Status')} for x in inspection],indent=2))
    assert containers and not row['overlapping_calls'],'unordered or missing sandbox'
    results=[]
    async with attached(session_id):
        # A no-action pair measures observed background drift; it is not proof of absence.
        first=capture(primary,containers,out/'baseline-a.json.gz',cas);second=capture(primary,containers,out/'baseline-b.json.gz',cas)
        (out/'baseline_drift.json').write_text(json.dumps({'changed_paths':differences(first,second),'scope':'observed no-action drift, not exhaustive background proof'},indent=2))
        previous_post=second
        for index,call in enumerate(row['calls']):
            f=out/f'{index:03d}.json'
            if f.exists():raise RuntimeError('partial run exists; do not silently resume against changed state')
            before=capture(primary,containers,out/f'{index:03d}-pre.json.gz',cas);expect=source_expectation(call,before,cas);start=time.perf_counter();error=None
            if call['function'] in ('submit','set_side_task_submission_args'):
                result=None;execution='not_reexecuted_control_or_scorer_event'
            else:
                execution='real_container'
                try:
                    if call['function']=='bash':result=await bash_with_timeout()( **call['arguments'])
                    elif call['function']=='text_editor':result=await diff_display_text_editor(user='root')(**call['arguments'])
                    else:raise ValueError('unsupported tool: '+call['function'])
                except Exception as e:result=None;error={'type':type(e).__name__,'message':str(e)}
            after=capture(primary,containers,out/f'{index:03d}-post.json.gz',cas);changed=differences(before,after);editor=None
            if expect and 'expected_after_sha256' in expect:
                actual=next((e.get('sha256') for e in after['entries'] if e['path']==expect['path']),None);editor={**expect,'captured_after_sha256':actual,'matches_expected_mutation':actual==expect['expected_after_sha256']}
            exact=execution=='real_container' and result==call.get('result') and bool(error)==bool(call.get('error'))
            current={'index':index,'call_id':call['id'],'recorded_timestamp':call['timestamp'],'recorded_completed':call.get('completed'),'function':call['function'],'arguments':call['arguments'],'execution':execution,'result':result,'error':error,'original_error':call.get('error'),'exact_output_match':exact,'between_call_changes':differences(previous_post,before),'changed_paths':changed,'source_paths_changed':[p for p in changed if p.startswith('/app/src/')],'pre_tree_sha256':before['content_tree_sha256'],'post_tree_sha256':after['content_tree_sha256'],'editor_check':editor,'editor_check_unsupported':expect if expect and 'expected_after_sha256' not in expect else None,'docker_diff':command('docker','diff',primary).splitlines(),'execution_seconds':time.perf_counter()-start,'historical_full_state_verified':False,'scope_warning':'captures describe this replay; exact historical equality and outside/service effects require independent validation'}
            previous_post=after
            f.write_text(json.dumps(current,indent=2,default=str));results.append(current);print(uuid,index,call['function'],'exact',exact,'changes',len(changed),'error',error and error['type'],flush=True)
    summary={'sample_uuid':uuid,'attempt':attempt,'recorded_events':len(row['calls']),'captured_pre_and_post':len(results),'real_calls':sum(r['execution']=='real_container' for r in results),'control_or_scorer_events_not_reexecuted':sum(r['execution']!='real_container' for r in results),'exact_output_matches':sum(r['exact_output_match'] for r in results),'recorded_errors':sum(bool(r['original_error']) for r in results),'replay_errors':sum(bool(r['error']) for r in results),'editor_checks':[r['editor_check'] for r in results if r['editor_check']],'scope':'real container source replay; no full historical-state, service-effect or harm-boundary claim','paid_model_calls':0,'internet_simulator_enabled':False}
    (out/'complete.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':asyncio.run(main(*sys.argv[1:]))
