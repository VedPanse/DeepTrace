"""Content-addressed /app capture from real paused Docker containers."""
import gzip,hashlib,json,subprocess,tarfile,tempfile,time
from pathlib import Path

def command(*args):return subprocess.check_output(args,text=True).strip()
def capture(primary,containers,dest,cas):
    start=time.perf_counter();paused=[];entries=[];cas=Path(cas);cas.mkdir(parents=True,exist_ok=True)
    receipts=[]
    try:
        for c in containers:
            state=json.loads(command('docker','inspect',c))[0]['State']
            if state.get('Paused'):raise RuntimeError('container unexpectedly paused')
            command('docker','pause',c);paused.append(c);receipts.append({'container':c,'paused_at_ns':time.time_ns()})
        with tempfile.TemporaryFile() as errors:
            proc=subprocess.Popen(['docker','cp',primary+':/app','-'],stdout=subprocess.PIPE,stderr=errors)
            try:
                with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
                    for m in tar:
                        parts=Path(m.name).parts
                        if '..' in parts or not parts or parts[0]!='app':raise ValueError('unexpected tar path')
                        e={'path':'/'+m.name.rstrip('/'),'mode':m.mode,'uid':m.uid,'gid':m.gid,'mtime':m.mtime}
                        if m.isfile():
                            h=hashlib.sha256()
                            with tempfile.TemporaryFile() as spool:
                                f=tar.extractfile(m)
                                while chunk:=f.read(1024*1024):h.update(chunk);spool.write(chunk)
                                key=h.hexdigest();p=cas/key
                                if not p.exists():
                                    spool.seek(0)
                                    with p.open('xb') as out:
                                        while chunk:=spool.read(1024*1024):out.write(chunk)
                            e.update(kind='file',sha256=key,bytes=m.size)
                        elif m.isdir():e['kind']='directory'
                        elif m.issym() or m.islnk():e.update(kind='symlink' if m.issym() else 'hardlink',target=m.linkname)
                        else:raise ValueError('unsupported special entry: '+m.name)
                        entries.append(e)
                if proc.wait()!=0:
                    errors.seek(0);raise RuntimeError(errors.read().decode())
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
        entries.sort(key=lambda e:e['path']);content=[{k:v for k,v in e.items() if k!='mtime'} for e in entries]
        result={'scope':'/app including dependencies and runtime files; database/broker/memory/outside filesystem not captured','entries':entries,'content_tree_sha256':hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'pause_receipts':receipts,'copy_started_after_all_pauses':True,'pauses_sequential_not_globally_atomic':True,'silent_exclusions':False,'duration_seconds':time.perf_counter()-start}
        with gzip.open(dest,'wt') as f:json.dump(result,f,separators=(',',':'))
        return result
    finally:
        for c in reversed(paused):command('docker','unpause',c)

def differences(a,b):
    aa={x['path']:{k:v for k,v in x.items() if k!='mtime'} for x in a['entries']};bb={x['path']:{k:v for k,v in x.items() if k!='mtime'} for x in b['entries']}
    return [p for p in sorted(set(aa)|set(bb)) if aa.get(p)!=bb.get(p)]
