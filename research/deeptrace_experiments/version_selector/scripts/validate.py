"""Explicitly reviewed development expectations; no held-out/model evaluation."""
import json,hashlib
from pathlib import Path
from selector import select,ROOT
OUT=ROOT/'version_selector/results'
def files(body,removed=False):
    return {'policy.py':'def allowed(command):\n    '+body+'\n','runner.py':'from policy import allowed\nimport subprocess\ndef run(command):\n'+('    return None\n' if removed else '    if allowed(command):\n        return subprocess.run(command, shell=True)\n'),'notes.txt':'notes\n'}
strict=files('return command == "status"');weak=files('return True');unknown=files('return external_check(command)');removed=files('return True',True)
equivalent=files('return command in {"status"}')
def run():
    reviewed=[('weakened',[strict,weak],'all_inputs',['violated']),('restored',[strict,weak,strict],'approved_only',['violated','restored']),('irrelevant',[strict,{**strict,'notes.txt':'changed notes\n'}],'approved_only',[]),('equivalent',[strict,equivalent],'approved_only',[]),('unknown',[strict,unknown],'unknown',['unknown']),('removed',[weak,removed],'no_execution',['removed']),('unknown_repaired',[strict,unknown,strict],'approved_only',['preserved']),('cycles',[strict,weak,strict,weak,strict],'approved_only',['violated','restored'])]
    results=[]
    for name,states,current,transitions in reviewed:
        history=[{'event_id':str(i),'files':fs} for i,fs in enumerate(states)]
        r=select(history,'status',budget=1024)
        assert r['status']=='ok', (name,r['required_tokens'])
        assert r['current']['facts']['effective_restriction']==current
        observed=[e['transition'] for e in r['selected_changes'] if e['fact']=='effective_restriction']
        assert observed==transitions,(name,observed)
        for e in r['selected_changes']:
            assert e['temporal_role']=='PAST_CHANGE'
            assert e['currently_effective']==r['current']['facts'][e['fact']]
            assert e['to_version']<=r['current']['version']
            for sid in e['before_support']+e['after_support']:
                s=r['source_sidecar'][sid];text=states[s['version']][s['file']]
                assert hashlib.sha256(text.encode()).hexdigest()==s['sha256']
        assert r['history_packet'].startswith(r['current_packet'])
        assert select(history,'status',budget=1)['status']=='budget_failure'
        (OUT/(name+'.json')).write_text(json.dumps(r,indent=2))
        results.append({'history':name,'current':current,'selected_restriction_transitions':observed,'tokens':r['required_tokens'],'checks_passed':True})
    # A changed import must be reanalyzed, not treated as unrelated.
    broken={**strict,'runner.py':strict['runner.py'].replace('from policy import allowed','from absent import allowed')}
    assert select([{'event_id':'a','files':strict},{'event_id':'b','files':broken}],'status',4096)['current']['facts']['effective_restriction']=='unknown'
    summary={'scope':'development engineering validation, not independently human-validated or a detection evaluation','histories':results,'changed_import_unknown':True,'budget_failure_checked':True,'new_model_calls':0}
    (OUT/'validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
