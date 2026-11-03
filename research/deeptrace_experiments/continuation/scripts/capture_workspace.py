"""Capture inert workspace bytes without following links or executing code.
Content integrity is not boundary provenance: use only with a paused isolated
producer and separately attest revision/image/setup/action boundary. Binary files
and links remain explicit; this does not pretend they fit the text replay adapter.
"""
import os,stat,json,hashlib,base64,argparse
from pathlib import Path

def capture(root,mount,boundary,max_bytes=256*1024*1024):
 root=Path(root).resolve();entries=[];total=0
 if not root.is_dir():raise ValueError('root must be an existing directory')
 for directory,dirs,files in os.walk(root,followlinks=False):
  dirs.sort();files.sort()
  links=[d for d in dirs if (Path(directory)/d).is_symlink()]
  dirs[:]=[d for d in dirs if d not in links]
  for name in sorted(files+links):
   p=Path(directory)/name;before=p.lstat();rel=p.relative_to(root).as_posix();entry={'path':mount.rstrip('/')+'/'+rel,'mode':stat.S_IMODE(before.st_mode)}
   if stat.S_ISLNK(before.st_mode):entry.update({'kind':'symlink','target':os.readlink(p),'text_replay_supported':False})
   elif stat.S_ISREG(before.st_mode):
    total+=before.st_size
    if total>max_bytes:raise ValueError('capture byte cap exceeded; no partial manifest emitted')
    data=p.read_bytes();after=p.lstat()
    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('file changed during capture: '+rel)
    entry.update({'kind':'file','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    try:entry['text']=data.decode('utf-8');entry['text_replay_supported']=True
    except UnicodeDecodeError:entry['base64']=base64.b64encode(data).decode();entry['text_replay_supported']=False
   else:raise ValueError('unsupported special file: '+rel)
   entries.append(entry)
 payload=json.dumps(entries,sort_keys=True,separators=(',',':')).encode()
 return {'boundary_claim':boundary,'workspace_mount':mount,'entries':entries,'manifest_sha256':hashlib.sha256(payload).hexdigest(),'content_bytes':total,'attestation_status':'unverified producer; require external paused-boundary and initial revision/image/setup provenance','global_atomicity_proven':False,'silent_exclusions':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--mount',required=True);p.add_argument('--boundary',required=True);p.add_argument('--out',required=True);a=p.parse_args();result=capture(a.root,a.mount,a.boundary)
 with open(a.out,'x') as f:json.dump(result,f,indent=2)
