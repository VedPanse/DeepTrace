"""Bounded source-derived assumptions and SMT checks, independent of fixture labels."""
import ast,json,hashlib,time
from dataclasses import dataclass
import z3
class Unsupported(Exception):pass

def translate(node,env,files,module,support,depth=0):
 if depth>12:raise Unsupported('call depth exceeds 12')
 if isinstance(node,ast.Constant):
  v=node.value
  if isinstance(v,bool):return z3.BoolVal(v)
  if isinstance(v,str):return z3.StringVal(v)
  if isinstance(v,int):return z3.IntVal(v)
  raise Unsupported('constant')
 if isinstance(node,ast.Name):
  if node.id not in env:raise Unsupported('unresolved symbol '+node.id)
  return env[node.id]
 if isinstance(node,(ast.Set,ast.List,ast.Tuple)):return [translate(x,env,files,module,support,depth) for x in node.elts]
 if isinstance(node,ast.Compare):
  left=translate(node.left,env,files,module,support,depth);out=[]
  for op,r in zip(node.ops,node.comparators):
   right=translate(r,env,files,module,support,depth)
   if isinstance(op,ast.Eq):out.append(left==right)
   elif isinstance(op,ast.NotEq):out.append(left!=right)
   elif isinstance(op,ast.In):out.append(z3.Or(*[left==v for v in right]))
   elif isinstance(op,ast.NotIn):out.append(z3.And(*[left!=v for v in right]))
   else:raise Unsupported('comparison')
   left=right
  return z3.And(*out)
 if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return z3.Not(translate(node.operand,env,files,module,support,depth))
 if isinstance(node,ast.BoolOp):return (z3.And if isinstance(node.op,ast.And) else z3.Or)(*[translate(x,env,files,module,support,depth) for x in node.values])
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
  args=[translate(a,env,files,module,support,depth) for a in node.args]
  if node.func.id=='bool' and len(args)==1:
   if z3.is_string(args[0]):return args[0]!=z3.StringVal('')
   if z3.is_bool(args[0]):return args[0]
  if node.func.id=='len' and len(args)==1:return z3.Length(args[0])
  return summarize(files,module,node.func.id,args,support,depth+1)
 raise Unsupported(type(node).__name__)

def summarize(files,module,symbol,args,support,depth=0):
 filename=module+'.py'
 if filename not in files:raise Unsupported('missing module '+filename)
 tree=ast.parse(files[filename]);imports={}
 for n in tree.body:
  if isinstance(n,ast.ImportFrom):
   for x in n.names:imports[x.asname or x.name]=(n.module,x.name)
 f=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==symbol),None)
 if f is None:
  if symbol in imports:return summarize(files,*imports[symbol],args,support,depth+1)
  raise Unsupported('unresolved function '+symbol)
 support.add(filename+':'+symbol)
 env={n.arg:v for n,v in zip(f.args.args,args)}
 def expr(node):
  # Resolve imported call aliases through this module's summary lookup.
  return translate(node,env,files,module,support,depth)
 def block(nodes):
  if not nodes:raise Unsupported('implicit return')
  n,*tail=nodes
  if isinstance(n,ast.Return):return expr(n.value)
  if isinstance(n,ast.If):return z3.If(expr(n.test),block(n.body+tail),block(n.orelse+tail))
  raise Unsupported('unsupported statement '+type(n).__name__)
 return z3.simplify(block(f.body))

def extract(files, approved="status"):
 x=z3.String('command');support=set()
 try:
  tree=ast.parse(files['runner.py']);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');support.add('runner.py:run')
  
  if len(f.body)==1 and isinstance(f.body[0],ast.Return) and isinstance(f.body[0].value,ast.Constant):return {'restriction_status':'removed','unknown':False,'removed':True,'support':['runner.py:run'],'reason':'authored wrapper has only a literal return and no operation'}
  branch=next(n for n in f.body if isinstance(n,ast.If))
  guard=translate(branch.test,{'command':x},files,'runner',support)
  calls=[n for n in ast.walk(branch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run']
  if len(calls)!=1:raise Unsupported('ambiguous process sink')
  call=calls[0];arg=call.args[0];variable=isinstance(arg,ast.Name) and arg.id=='command'
  fixed=isinstance(arg,(ast.List,ast.Tuple)) and all(isinstance(n,ast.Constant) for n in arg.elts)
  if not(variable or fixed):raise Unsupported('argument expression')
  shell=next((k.value.value for k in call.keywords if k.arg=='shell' and isinstance(k.value,ast.Constant)),None)
  if not isinstance(shell,bool):raise Unsupported('nonconstant shell mode')
  solver=z3.Solver();solver.set(timeout=1000);solver.add(guard,x!=z3.StringVal(approved));status=solver.check()
  restriction='preserved' if status==z3.unsat else 'violated' if status==z3.sat else 'unknown'
  witness=solver.model().eval(x,model_completion=True).as_string() if status==z3.sat else None
  spans=[]
  for qualified in sorted(support):
   file,name=qualified.rsplit(':',1);fn=next(n for n in ast.parse(files[file]).body if isinstance(n,ast.FunctionDef) and n.name==name);spans.append({'file':file,'symbol':name,'line_start':fn.lineno,'line_end':fn.end_lineno,'source_sha256':hashlib.sha256(files[file].encode()).hexdigest()})
  return {'source_spans':spans,'restriction_status':restriction,'restriction_formula':str(z3.simplify(guard)),'witness':witness,'input_independent':fixed,'shell':shell,'support':sorted(support),'verification':'bounded direct-call symbolic model over all strings; SMT timeout 1s','unknown':restriction=='unknown'}
 except (Unsupported,SyntaxError,KeyError,StopIteration,z3.Z3Exception) as ex:return {'restriction_status':'unknown','unknown':True,'reason':str(ex),'support':sorted(support)}

def history_records(history,after):
 records=[];last=None
 for t,snapshot in enumerate([*history,{'edit':'proposed','files':after}]):
  summary=extract(snapshot['files'])
  # Invalidation records depend on source summaries, never case labels.
  if last is None or any(summary.get(k)!=last.get(k) for k in ['restriction_formula','restriction_status','input_independent','shell','unknown']):
   changed=[k for k in ['restriction_formula','restriction_status','input_independent','shell','unknown'] if last is not None and summary.get(k)!=last.get(k)]
   records.append({'event_index':t,'edit':snapshot['edit'],'changed_fields':changed,'before':last,'after':summary})
  last=summary
 return records
