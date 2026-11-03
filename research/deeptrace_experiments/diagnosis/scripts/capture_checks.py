import sys,tempfile,json,hashlib,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'continuation/scripts'));from capture_workspace import capture
checks={}
with tempfile.TemporaryDirectory() as d:
 root=Path(d)/'workspace';root.mkdir();(root/'code.py').write_text('print("inert")\n');(root/'binary').write_bytes(b'\xff\x00\x01');(root/'external-link').symlink_to('/etc/passwd')
 x=capture(root,'/app','fixture-only');by={r['path']:r for r in x['entries']}
 checks['external_symlink_not_followed']=by['/app/external-link']['kind']=='symlink' and 'text' not in by['/app/external-link']
 checks['binary_bytes_retained_not_silently_dropped']=base64.b64decode(by['/app/binary']['base64'])==b'\xff\x00\x01'
 checks['capture_does_not_assert_verified_provenance']=x['global_atomicity_proven'] is False and 'unverified' in x['attestation_status']
 try:capture(root,'/app','fixture-only',max_bytes=1);ok=False
 except ValueError:ok=True
 checks['size_limit_fails_whole_capture']=ok
 checks['manifest_content_hash_checkable']=hashlib.sha256(json.dumps(x['entries'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==x['manifest_sha256']
(ROOT/'diagnosis/results/capture_checks.json').write_text(json.dumps(checks,indent=2));assert all(checks.values());print(checks)
