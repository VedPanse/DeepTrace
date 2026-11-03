"""Restore exact read-only research checkouts; never install or execute targets."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
pins=json.loads((ROOT/'results/repositories.json').read_text())
for pin in [pins['analyzer'],*pins['targets']]:
 path=ROOT/pin['path'];path.parent.mkdir(exist_ok=True,parents=True)
 if not path.exists():
  subprocess.run(['git','init',str(path)],check=True)
  subprocess.run(['git','-C',str(path),'remote','add','origin',pin['url']],check=True)
  subprocess.run(['git','-C',str(path),'fetch','--depth','1','origin',pin['commit']],check=True)
  subprocess.run(['git','-C',str(path),'checkout','--detach',pin['commit']],check=True)
 actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
 if actual!=pin['commit']:raise RuntimeError(f'Existing checkout mismatch: {path}; preserve local work and fix manually')
# Sandbox is macOS-specific and absolute paths must follow the restored workspace.
p=ROOT/'results/isolation.sb';text=p.read_text();import re
old=re.search(r'\(subpath "([^"]+)/results"\)',text).group(1)
p.write_text(text.replace(old,str(ROOT)))
