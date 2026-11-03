"""Run reviewed upstream code under the external OS sandbox; never import targets."""
import sys, json, time, resource, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'upstream/src'))
sys.path.insert(0,str(ROOT/'upstream/scripts'))
from agentsecbench import analyze_repository
from agentsecbench.scanner import ScanOptions
mode=sys.argv[1]
if mode=='scan':
 target,output=map(Path,sys.argv[2:4]); t=time.perf_counter()
 result=analyze_repository(target,output,options=ScanOptions())
 (output/'measurement.json').write_text(json.dumps({'wall_seconds':time.perf_counter()-t,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'rss_platform':'macOS bytes','summary':result.summary.to_dict()},indent=2))
elif mode=='legacy':
 import runpy
 script=sys.argv[2]; sys.argv=sys.argv[2:];runpy.run_path(str(ROOT/'upstream/scripts'/script),run_name='__main__')
elif mode=='cli':
 from agentsecbench.cli import main
 raise SystemExit(main(sys.argv[2:]))
elif mode=='test':
 import unittest
 suite=unittest.defaultTestLoader.discover(str(ROOT/'upstream/tests'),pattern=sys.argv[2] if len(sys.argv)>2 else 'test_product*.py')
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
elif mode=='isolation':
 import socket
 checks={}
 try: Path('/Users/vedpanse/.ssh').iterdir().__next__();checks['private_directory']='UNEXPECTED_ACCESS'
 except (PermissionError,FileNotFoundError):checks['private_directory']='denied_or_absent'
 try: socket.socket().connect(('1.1.1.1',443));checks['network']='UNEXPECTED_ACCESS'
 except PermissionError:checks['network']='denied'
 print(json.dumps(checks))
elif mode=='paper-probes':
 import dataclasses
 from security_adg_dataflow import analyze
 from agentsecbench.scanner.engine import _scan_text
 rows=[]
 for folder in sorted((ROOT/'results/fixtures').iterdir()):
  if folder.name=='temporal-history':continue
  for p in sorted(folder.glob('*')):
   if p.suffix not in {'.py','.ts'}:continue
   text=p.read_text()
   for record in _scan_text(p.name,text,'line'):
    if record.category not in {'command_execution','network_access'}:continue
    result=analyze(text,p.name,list(record.evidence_lines),symbol=record.symbol,prefer_parameter_sources=True,respect_parameter_overwrites=True,include_intrinsic_source_operation=False)
    rows.append({'case':folder.name,'file':p.name,'category':record.category,'analysis':dataclasses.asdict(result)})
 (ROOT/'results/paper-probes.json').write_text(json.dumps(rows,indent=2))
elif mode=='indexes':
 from agentsecbench.graph.project import build_python_project_index
 from agentsecbench.graph.project_typescript import build_typescript_project_index
 from agentsecbench.frameworks import BUILTIN_ADAPTERS
 from agentsecbench.scanner.engine import _iter_source_files
 results={}
 for target in (ROOT/'targets').iterdir():
  files,_,_=_iter_source_files(target,ROOT/'results',ScanOptions());texts={name:p.read_text(errors='replace') for name,p in files}
  py=build_python_project_index(texts,BUILTIN_ADAPTERS);ts=build_typescript_project_index(texts,BUILTIN_ADAPTERS)
  results[target.name]={'python_functions':len(py.functions),'typescript_functions':len(ts.functions),'python_calls':py.callsite_count,'typescript_calls':ts.callsite_count,'parse_failures':list(py.parse_failures)}
 (ROOT/'results/indexes.json').write_text(json.dumps(results,indent=2))
elif mode=='graph-timing':
 import agentsecbench.scanner.engine as engine
 from agentsecbench.graph import builder
 measurements={}
 original=engine.build_graphs
 def timed(*args,**kwargs):
  start=time.perf_counter();result=original(*args,**kwargs)
  measurements['graph_construction_seconds']=time.perf_counter()-start
  measurements['peak_rss_after_graph_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  return result
 engine.build_graphs=timed
 target,output=map(Path,sys.argv[2:4]);start=time.perf_counter()
 result=engine.analyze_repository(target,output)
 measurements.update({'total_seconds':time.perf_counter()-start,'candidates':len(result.graphs),'instrumentation':'one wrapper around build_graphs, including project indexes; no algorithm changes','memory_scope':'process peak RSS through graph stage, includes scanning/imports, not isolated graph allocation'})
 (output/'graph-timing.json').write_text(json.dumps(measurements,indent=2))
