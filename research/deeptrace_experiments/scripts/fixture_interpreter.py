"""Independent concrete AST interpreter. Only authored pure expressions and a process recorder.
No eval/exec, imports, network calls, filesystem operations, or shell launches are performed.
"""
import ast
class Unsupported(Exception):pass

def run(files,command):
 trees={name[:-3]:ast.parse(text) for name,text in files.items() if name.endswith('.py')};effects=[]
 def function(module,name,args,depth=0):
  if depth>40:raise Unsupported('concrete call depth')
  if module not in trees:raise Unsupported('unresolved module')
  tree=trees[module];fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
  if fn is None:
   for n in tree.body:
    if isinstance(n,ast.ImportFrom):
     for alias in n.names:
      if (alias.asname or alias.name)==name:return function(n.module,alias.name,args,depth+1)
   raise Unsupported('unresolved function')
  env={p.arg:v for p,v in zip(fn.args.args,args)}
  def expression(n):
   if isinstance(n,ast.Constant):return n.value
   if isinstance(n,ast.Name):
    if n.id not in env:raise Unsupported('unresolved variable')
    return env[n.id]
   if isinstance(n,ast.Set):return {expression(v) for v in n.elts}
   if isinstance(n,(ast.List,ast.Tuple)):return [expression(v) for v in n.elts]
   if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return not expression(n.operand)
   if isinstance(n,ast.BoolOp):
    if isinstance(n.op,ast.And):
     for v in n.values:
      out=expression(v)
      if not out:return out
     return out
    for v in n.values:
     out=expression(v)
     if out:return out
    return out
   if isinstance(n,ast.Compare):
    left=expression(n.left)
    for op,r in zip(n.ops,n.comparators):
     right=expression(r)
     if isinstance(op,ast.Eq):okay=left==right
     elif isinstance(op,ast.NotEq):okay=left!=right
     elif isinstance(op,ast.In):okay=left in right
     elif isinstance(op,ast.NotIn):okay=left not in right
     else:raise Unsupported('comparison')
     if not okay:return False
     left=right
    return True
   if isinstance(n,ast.Call):
    args=[expression(v) for v in n.args]
    if isinstance(n.func,ast.Name):
     if n.func.id=='bool':return bool(*args)
     if n.func.id=='len':return len(*args)
     return function(module,n.func.id,args,depth+1)
    if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run':
     event={'args':args[0],'shell':next((expression(k.value) for k in n.keywords if k.arg=='shell'),False)};effects.append(event);return event
   raise Unsupported(type(n).__name__)
  def statements(body):
   for stmt in body:
    if isinstance(stmt,ast.Return):return True,expression(stmt.value)
    if isinstance(stmt,ast.If):
     done,value=statements(stmt.body if expression(stmt.test) else stmt.orelse)
     if done:return True,value
    else:
     if not isinstance(stmt,ast.If):raise Unsupported('statement')
   return False,None
  return statements(fn.body)[1]
 function('runner','run',[command]);return effects
