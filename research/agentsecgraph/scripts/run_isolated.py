"""macOS Seatbelt launcher; no target installation or execution, no inherited secrets."""
import os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args,log=None):
 env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','HOME':str(ROOT/'results/empty-home'),'TMPDIR':str(ROOT/'results/tmp'),'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'en_US.UTF-8'}
 cmd=['/usr/bin/sandbox-exec','-f',str(ROOT/'results/isolation.sb'),sys.executable,'-B','-I',str(ROOT/'scripts/worker.py'),*map(str,args)]
 if log:
  with Path(log).open('w') as f:return subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 return subprocess.run(cmd,env=env).returncode
if __name__=='__main__':raise SystemExit(run(sys.argv[1:]))
