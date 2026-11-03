"""Capability check on a public pinned repo, NOT trajectory state extraction."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT.parent/'agentsecgraph/upstream/src'))
from agentsecbench import analyze_repository
HERE=ROOT/'continuation';source=ROOT/'env-auto-workflow/codebase';t=time.perf_counter();r=analyze_repository(source,HERE/'results/public_repo_analysis')
files=[p for p in source.rglob('*') if p.is_file()];langs={s:sum(p.suffix==s for p in files) for s in ['.py','.ts','.js','.go','.sh']}
x={'scope':'public v1.0.1 capability check only; not a verified recorded trajectory state','repository_commit':'041cee543523f98cf3e130c9f4e05b9a74e57de2','files':len(files),'languages':langs,'graphs':len(r.graphs),'graph_source_files':len({g['provenance']['file'] for g in r.graphs}),'seconds':time.perf_counter()-t,'real_assumption_checker':'unsupported: authored Python runner/policy grammar does not analyze this TypeScript application','graph_semantics':'candidate extraction; no soundness or completeness guarantee'}
(HERE/'results/capability.json').write_text(json.dumps(x,indent=2));print(x)
