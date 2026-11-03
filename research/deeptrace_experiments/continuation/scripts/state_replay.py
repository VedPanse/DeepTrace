"""Fail-closed, pure-data repository replay. Never executes recorded tools.
Input scope is an explicit complete workspace file manifest; excludes service state.
The capture producer must separately attest initial revision/image/setup provenance.
"""
import hashlib,json,posixpath
class ReplayError(ValueError):pass
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def tree_hash(files):return digest(json.dumps(files,sort_keys=True,separators=(',',':')))
def canonical(path):
 if not path.startswith('/') or '\x00' in path or '..' in path.split('/'):raise ReplayError('noncanonical workspace path')
 return posixpath.normpath(path)
def check_tree(files):
 if any(canonical(p)!=p or not isinstance(t,str) for p,t in files.items()):raise ReplayError('invalid file manifest')
def replay(bundle):
 initial=bundle.get('initial',{});files=dict(initial.get('files',{}));check_tree(files)
 if not initial.get('verified_capture') or not (initial.get('environment_commit') or initial.get('image_digest')) or not initial.get('capture_sha256'):raise ReplayError('verified initial tree and environment commit required')
 if tree_hash(files)!=initial['capture_sha256']:raise ReplayError('initial tree hash mismatch')
 states=[];events=[];tainted=False
 for i,action in enumerate(bundle.get('actions',[])):
  before=dict(files);issues=[];writes={};reads=action.get('read_checks',[]);pre_known=not tainted
  if action.get('index')!=i:raise ReplayError('noncontiguous action ordering')
  for check in reads:
   p=canonical(check['path'])
   if p not in files or digest(files[p])!=check['sha256']:issues.append('observed_read_mismatch:'+p)
  receipts=action.get('receipts',[])
  # A complete receipt is required per call, including failed and read-only calls.
  if len(receipts)!=len(action.get('tool_calls',[])):issues.append('incomplete_tool_receipts')
  call_ids=[c.get('id') for c in action.get('tool_calls',[])]
  receipt_ids=[r.get('call_id') for r in receipts]
  if None in call_ids or len(set(call_ids))!=len(call_ids) or sorted(map(str,call_ids))!=sorted(map(str,receipt_ids)):issues.append('receipt_call_identity_mismatch')
  for r in receipts:
   status=r.get('status');mutations=r.get('mutations',[])
   if status=='failed_atomic' and not r.get('atomic_failure_verified'):issues.append('unverified_failure_atomicity')
   if status not in {'read_only_verified','failed_atomic','mutation_verified'}:issues.append('unsupported_or_partial_effect')
   if r.get('asynchronous_effects_unresolved'):issues.append('unresolved_background_effect')
   if status!='mutation_verified' and mutations:issues.append('mutations_with_inconsistent_status')
   for m in mutations:
    p=canonical(m['path'])
    if p in writes:issues.append('parallel_conflicting_writes:'+p)
    writes[p]=m
  for path,m in writes.items():
   if m.get('before_sha256')!=(digest(before[path]) if path in before else None):issues.append('mutation_preimage_mismatch:'+path)
   if not m.get('capture_or_effect_verification'):issues.append('unverified_mutation:'+path)
  # No guesses after an unsupported effect; later exact full capture can resynchronize.
  if any(x.startswith(('observed_read_mismatch','mutation_preimage_mismatch')) for x in issues):pre_known=False
  if issues:tainted=True
  if not tainted:
   for path,m in writes.items():
    if m.get('delete'):files.pop(path,None)
    elif isinstance(m.get('after_text'),str):files[path]=m['after_text']
    else:issues.append('missing_postimage:'+path);tainted=True
  post=action.get('verified_post_capture')
  if post:
   check_tree(post['files'])
   if not post.get('verified_capture') or tree_hash(post['files'])!=post['sha256']:raise ReplayError('invalid resynchronization capture')
   if not tainted and files!=post['files']:issues.append('post_capture_disagrees_with_replay')
   files=dict(post['files']);tainted=False
  states.append({'index':i,'pre_files':before if pre_known else None,'pre_sha256':tree_hash(before) if pre_known else None,'post_sha256':None if tainted else tree_hash(files),'issues':issues,'eligible_for_graph':pre_known})
  events.append({'index':i,'post_unknown':tainted,'mutated_paths':sorted(writes),'issues':issues})
 return {'states':states,'events':events,'all_transitions_verified':all(not e['issues'] and not e['post_unknown'] for e in events),'final_files':None if tainted else files}

def validate_harm(annotation,n_actions):
 """Metadata/independent adjudication gate, not automated proof of harm."""
 issues=[];i=annotation.get('first_harm_action')
 if not isinstance(i,int) or not 0<=i<n_actions:issues.append('missing_or_invalid_first_harm_action')
 reviews=annotation.get('independent_reviews',[])
 if len({r.get('reviewer') for r in reviews if r.get('decision')=='agree' and r.get('evidence_sha256')})<2:issues.append('two_distinct_checked_harm_reviews_required')
 if not annotation.get('first_effect_evidence') or annotation.get('earlier_effects_ruled_out') is not True:issues.append('first_effect_not_established')
 if annotation.get('delayed') and not annotation.get('trigger_and_observation_evidence'):issues.append('delayed_trigger_unverified')
 return issues
