"""Capture /app from a paused readiness session, not a live action hook."""
import datetime,gzip,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parent
sys.path.insert(0,str(ROOT/'continuation/scripts'))
from capture_workspace import capture

def main():
    readiness=json.loads((BASE/'results/local_readiness.json').read_text())
    names=[x['name'].lstrip('/') for x in readiness['containers']]
    primary=next(n for n in names if n.endswith('-default-1'));paused=[];times=[]
    def run(*args):return subprocess.check_output(list(args),text=True).strip()
    try:
        for n in names:
            state=json.loads(run('docker','inspect',n))[0]['State']
            if state.get('Paused'):raise RuntimeError('unexpected already-paused container')
            run('docker','pause',n);paused.append(n);times.append({'container':n,'paused_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        with tempfile.TemporaryDirectory(prefix='deeptrace-readiness-') as td:
            path=Path(td)/'app';path.mkdir();run('docker','cp',primary+':/app/.',str(path))
            result=capture(path,'/app','post-setup readiness only; no agent actions')
            result['capture_provenance']={'all_listed_containers_paused_before_copy':True,'pause_receipts':times,'session':readiness['session'],'scope':'/app contents and file modes only; excludes database/broker contents, external filesystem and process memory; not a complete machine snapshot','global_atomicity':'pauses sequential; services may act between pauses; copy begins only after all pauses','no_action_hook':True}
            dest=BASE/'data/readiness_app.json.gz'
            if dest.exists():raise RuntimeError('capture already exists')
            with gzip.open(dest,'wt') as f:json.dump(result,f,separators=(',',':'))
            receipt={'capture':str(dest.relative_to(BASE)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'tree_manifest_sha256':result['manifest_sha256'],'entries':len(result['entries']),'content_bytes':result['content_bytes'],'boundary':'postsetup readiness only','scope':result['capture_provenance']['scope'],'no_silent_exclusions':True}
            (BASE/'results/capture_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
    finally:
        for n in reversed(paused):run('docker','unpause',n)

if __name__=='__main__':main()
