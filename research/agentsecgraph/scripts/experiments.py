"""Authored static-only temporal and dependency challenge cases. No payload runs."""
import json,subprocess,hashlib
from pathlib import Path
from run_isolated import run,ROOT
R=ROOT/'results'; F=R/'fixtures';F.mkdir(exist_ok=True)
def write(name,files):
 p=F/name;p.mkdir(exist_ok=True)
 for file,text in files.items():
  out=p/file;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
 return p
def scan(name,files):
 p=write(name,files);o=R/'experiments'/name;o.mkdir(parents=True,exist_ok=True)
 code=run(['scan',p,o],o/'run.log')
 if code:raise RuntimeError((name,code))
 return [json.loads(x) for x in (o/'security-adg.jsonl').read_text().splitlines()]
base='''from config import allowed
import subprocess

def run(command):
    if allowed(command):
        return subprocess.run(["printf", "synthetic"], shell=False)
'''
auth='def allowed(command):\n    return command == "status"\n'
weak='def allowed(command):\n    return bool(command)\n'
versions={'A':{'agent.py':base,'config.py':auth},'B':{'agent.py':base,'config.py':weak},'C':{'agent.py':base.replace('["printf", "synthetic"]','command'),'config.py':weak},'D':{'agent.py':base.replace('["printf", "synthetic"]','command').replace('shell=False','shell=True'),'config.py':weak}}
# Version-controlled snapshots make the experiment independently inspectable.
p=F/'temporal-history';p.mkdir(exist_ok=True)
def git(*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
if not (p/'.git').exists():
 git('init');git('config','user.name','DeepTrace synthetic experiment');git('config','user.email','synthetic@example.invalid')
temporal=[]
for v,files in versions.items():
 gs=scan('temporal-'+v,files)
 for file,text in files.items():(p/file).write_text(text)
 git('add','.');subprocess.run(['git','-C',str(p),'commit','--allow-empty','-m',f'Authored version {v}'],check=True,capture_output=True)
 commit=git('rev-parse','HEAD')
 canonical=json.loads(json.dumps(gs))
 for g in canonical:g['provenance'].pop('scan_root',None)
 digest=hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()
 sink=next(g for g in gs if any(n.get('category')=='command_execution' for n in g['nodes']))
 temporal.append({'version':v,'commit':commit,'canonical_graph_sha256':digest,'candidate_id':sink['candidate_id'],'source_count':sink['views']['security_adg']['source_candidates'],'guard_count':sink['views']['security_adg']['guard_candidates'],'dependency_paths':sink['analysis']['dependency_paths']})
(R/'temporal.json').write_text(json.dumps(temporal,indent=2))
fixtures={
 'parameter_overwrite':{'case.py':'import subprocess\n\ndef run(command):\n    command = "printf synthetic"\n    return subprocess.run(command)\n'},
 'local_overwrite':{'case.py':'import subprocess\n\ndef run(command):\n    value = command\n    value = "printf synthetic"\n    return subprocess.run(value)\n'},
 'cross_file_direct':{'helper.py':'import subprocess\n\ndef execute(value):\n    return subprocess.run(value)\n','agent.py':'from mcp.server.fastmcp import FastMCP\nfrom helper import execute\nmcp = FastMCP("synthetic")\n\n@mcp.tool()\ndef run(command):\n    return execute(command)\n'},
 'cross_file_local_alias':{'helper.py':'import subprocess\n\ndef execute(value):\n    return subprocess.run(value)\n','agent.py':'from mcp.server.fastmcp import FastMCP\nfrom helper import execute\nmcp = FastMCP("synthetic")\n\n@mcp.tool()\ndef run(command):\n    copied = command\n    return execute(copied)\n'},
 'early_return_guard':{'case.py':'import subprocess\n\ndef run(command):\n    if command != "status":\n        raise ValueError("not allowed")\n    return subprocess.run(command)\n'},
 'enclosing_guard':{'case.py':'import subprocess\n\ndef run(command):\n    if command == "status":\n        return subprocess.run(command)\n'},
 'dynamic_dispatch':{'case.py':'import subprocess\n\ndef run(command):\n    execute = getattr(subprocess, "run")\n    return execute(command)\n'},
 'config_return':{'case.py':'from config import get_command\nimport subprocess\n\ndef run():\n    command = get_command()\n    return subprocess.run(command)\n','config.py':'import os\n\ndef get_command():\n    return os.getenv("SYNTHETIC_COMMAND")\n'},
 'js_multiline':{'case.ts':'export function run(command: string) {\n  return exec(\n    command\n  );\n}\n'},
 'js_singleline':{'case.ts':'export function run(command: string) {\n  return exec(command);\n}\n'},
 'recursion':{'case.py':'import subprocess\n\ndef run(command):\n    if command:\n        run(command)\n        return subprocess.run(command)\n'},
 'small-auth-app':{'config.ts':'export const settings = { requireAuth: true, endpoint: "https://example.invalid/audit" };\n','auth.ts':'export function authorized(token: string) {\n  return token === "synthetic-token";\n}\n','app.ts':'import { settings } from "./config";\nimport { authorized } from "./auth";\nexport function audit(token: string, payload: string) {\n  if (settings.requireAuth && !authorized(token)) throw new Error("denied");\n  const endpoint = settings.endpoint;\n  return fetch(endpoint, { method: "POST", body: payload });\n}\nexport function secret() {\n  const token = process.env.SYNTHETIC_TOKEN;\n  return token;\n}\n'}
}
rows=[]
for name,files in fixtures.items():
 gs=scan(name,files)
 rows.append({'case':name,'fixture_files':list(files),'graph_count':len(gs),'command_graphs':[{'id':g['candidate_id'],'operation':next(n['name'] for n in g['nodes'] if n['type']=='security_sensitive_operation'),'sources':[n for n in g['nodes'] if n['type']=='input_source'],'guards':[n for n in g['nodes'] if n['type']=='guard_candidate'],'analysis':g['analysis']} for g in gs if any(n.get('category')=='command_execution' for n in g['nodes'])]})
(R/'challenge-cases.json').write_text(json.dumps(rows,indent=2))
# Compare the actual paper dataflow implementation on the same authored snippets.
# This import occurs only in sandbox worker mode below, not in this launcher.
print('Completed',len(fixtures),'challenge fixtures and 4 temporal snapshots')
