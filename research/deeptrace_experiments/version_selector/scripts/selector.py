"""Bounded version-aware selection; inert Python fixtures only, no inference."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'qualification/scripts'))
from evidence import extract,packet,tokens

KEYS=('effective_restriction','argument_origin','shell_enabled')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def select(history,approved,budget=1024,action_id='proposed'):
    """Last state is a proposed preview, not an observed execution outcome.

    Recompute all versions rather than trusting incremental support completeness.
    Relevant facts are limited to this fixture's sole runner execution path.
    """
    if not history:raise ValueError('empty history')
    ids=[h['event_id'] for h in history]
    if len(set(ids))!=len(ids):raise ValueError('duplicate event ID')
    versions=[];sources={};excluded=[];events=[]
    for i,h in enumerate(history):
        e=extract(h['files'],approved)
        for s in e['source_spans']:
            sid=f"v{i}:"+s['id'];sources[sid]={**s,'id':sid,'version':i,'event_id':h['event_id']}
        versions.append({'version':i,'event_id':h['event_id'],'facts':e['facts'],'source_ids':[f"v{i}:"+s['id'] for s in e['source_spans']],'unknown_reason':e['unknown_reason'],'tree_hash':digest(h['files'])})
        if not i:continue
        prev=versions[i-1];changed=[k for k in KEYS if e['facts'][k]!=prev['facts'][k]]
        paths=sorted(p for p in set(h['files'])|set(history[i-1]['files']) if h['files'].get(p)!=history[i-1]['files'].get(p))
        if not changed:
            excluded.append({'event_id':h['event_id'],'changed_paths':paths,'reason':'no change in bounded action-relevant semantic facts; not a general irrelevance proof'})
            continue
        for k in changed:
            before=prev['facts'][k];after=e['facts'][k]
            transition='changed'
            if after=='unknown' or (k=='shell_enabled' and after is None and e['facts']['effective_restriction']=='unknown'):transition='unknown'
            elif k=='effective_restriction':
                if after=='no_execution':transition='removed'
                elif after=='approved_only':transition='restored' if before in ('all_inputs','nonempty') else 'preserved'
                elif before=='approved_only' and after in ('all_inputs','nonempty'):transition='violated'
            events.append({'fact':k,'from_version':i-1,'to_version':i,'event_id':h['event_id'],'past_value':before,'value_established_then':after,'transition':transition,'before_support':prev['source_ids'],'after_support':versions[-1]['source_ids'],'changed_paths':paths})
    # Latest transition per relevant fact, plus its preceding weakening when restored.
    selected=[]
    for k in KEYS:
        es=[e for e in events if e['fact']==k]
        if es:
            chosen=[es[-1]]
            if es[-1]['transition']=='restored':
                older=[e for e in es[:-1] if e['transition']=='violated']
                if older:chosen.insert(0,older[-1])
            selected.extend(chosen)
    selected.sort(key=lambda e:(e['to_version'],e['fact']))
    current=versions[-1];base,_=packet(history[-1]['files'],approved,budget=100000)
    base=base.replace('Every string, including non-approved strings, can reach execution.','Guard accepts every string; process argument origin is separate.').replace('Any nonempty string can reach execution.','Guard accepts nonempty strings; process argument origin is separate.')
    base='CURRENT PROPOSED STATE (preview, not executed), version '+str(current['version'])+'\n'+base
    if current['unknown_reason']:base+='\nCURRENT ANALYSIS UNCERTAINTY: '+str(current['unknown_reason'])
    for e in selected:
        e['temporal_role']='PAST_CHANGE'
        e['currently_effective']=current['facts'][e['fact']]
        e['superseded']=any(x['fact']==e['fact'] and x['to_version']>e['to_version'] for x in events)
        e['valid_until_version']=next((x['to_version'] for x in events if x['fact']==e['fact'] and x['to_version']>e['to_version']),None)
    refs=sorted({s for e in selected for s in e['before_support']+e['after_support']})
    # Historical code is kept as an auditable sidecar, not silently called visible.
    support=[{k:sources[s][k] for k in ('id','file','line_start','line_end','sha256')} for s in refs]
    extra='\nPAST CHANGES ONLY. Earlier values never override CURRENT facts.\n'+json.dumps({'changes':selected,'source_references':support},separators=(',',':'))
    full=base+extra
    status='ok' if tokens(full)<=budget else 'budget_failure'
    return {'status':status,'scope':'authored Python sole execution path; source-backed bounded semantics, not whole-program causal relevance','action_id':action_id,'budget':budget,'required_tokens':tokens(full),'current_packet':base if tokens(base)<=budget else None,'history_packet':full if status=='ok' else None,'current':current,'selected_changes':selected,'excluded_events':excluded,'omitted_older_semantic_changes':len(events)-len(selected),'versions':versions,'source_sidecar':sources,'historical_source_text_visible_to_monitor':False,'uncertainty':[v for v in versions if v['facts']['effective_restriction']=='unknown'],'recomputed_every_version':True}
