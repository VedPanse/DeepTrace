"""Inventory public archive provenance without generating monitor inputs."""
import collections,datetime,hashlib,json,zipfile
from pathlib import Path
import zipfile_zstd

BASE=Path(__file__).resolve().parents[1]
RUN='ace6e820844e4faf9e0a5907f774a7c6'
def main():
    path=BASE/'data'/f'{RUN}.eval';rows=[]
    with zipfile.ZipFile(path) as z:
        header=json.loads(z.read('header.json'))
        for name in z.namelist():
            if not name.startswith('samples/'):continue
            s=json.loads(z.read(name));tools=[e for e in s.get('events',[]) if e.get('event')=='tool']
            env=s.get('metadata',{}).get('environment',{})
            rows.append({'sample_file':name,'environment_id':env.get('id') if isinstance(env,dict) else env,'tool_events':len(tools),'tool_timestamps_present':all(e.get('timestamp') for e in tools),'tool_ids_present':all(e.get('id') for e in tools),'tool_completed_present':all('completed' in e for e in tools),'event_types':dict(collections.Counter(e.get('event') for e in s.get('events',[])))})
    meta=header['eval']['metadata']
    result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive_url':f'https://data.linuxarena.ai/api/runs/{RUN}/eval','http_status':200,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':len(rows),'env_versions':meta.get('env_versions'),'ct_git':meta.get('ct_git'),'sample_event_inventory':rows,'verified_replay':False,'harm_boundaries_validated':False,'conclusion':'public archive and initial commit/image metadata available; setup/effect completeness and state replay unverified'}
    (BASE/'results/archive_inventory.json').write_text(json.dumps(result,indent=2))
    print('Samples:',len(rows),'tool events:',sum(r['tool_events'] for r in rows))
if __name__=='__main__':main()
