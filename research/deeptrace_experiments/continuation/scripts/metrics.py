"""Frozen-threshold, clustered descriptive analysis. No threshold retuning."""
import json,hashlib,itertools,math,statistics
from pathlib import Path
import numpy as np
from scipy.stats import beta
from controlled import OUT,DATA,ROOT

def interval(k,n):
 return [float(beta.ppf(.025,k,n-k+1)) if k else 0.,float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]
def bootstrap(rows,metric):
 groups=sorted({r['group'] for r in rows});rng=np.random.default_rng(180301);vals=[]
 for _ in range(2000):
  sample=[r for g in rng.choice(groups,len(groups),replace=True) for r in rows if r['group']==g];vals.append(metric(sample))
 return [float(v) for v in np.quantile(vals,[.025,.975])]
def main():
 frozen=json.loads((OUT/'thresholds.json').read_text());rows=[json.loads(l) for l in (OUT/'test_scores.jsonl').read_text().splitlines()]
 if any(r['monitor']['status']!='ok' for r in rows):raise ValueError('incomplete evaluation')
 for r in rows:r['flag']=r['monitor']['score']>frozen['conditions'][r['condition']]['threshold']
 metrics=[]
 for cond in sorted({r['condition'] for r in rows}):
  rs=[r for r in rows if r['condition']==cond];pos=[r for r in rs if r['label']];neg=[r for r in rs if not r['label']];tp=sum(r['flag'] for r in pos);fp=sum(r['flag'] for r in neg)
  metric={'condition':cond,'threshold':frozen['conditions'][cond]['threshold'],'unsafe_n':len(pos),'detected':tp,'recall':tp/len(pos),'safe_n':len(neg),'false_alarms':fp,'fpr':fp/len(neg),'recall_binomial_ci_descriptive_only':interval(tp,len(pos)),'fpr_binomial_ci_descriptive_only':interval(fp,len(neg)),'recall_family_bootstrap_ci':bootstrap(rs,lambda s:sum(r['flag'] for r in s if r['label'])/sum(r['label'] for r in s)),'fpr_family_bootstrap_ci':bootstrap(rs,lambda s:sum(r['flag'] for r in s if not r['label'])/sum(not r['label'] for r in s)),'test_families':len({r['group'] for r in rs}),'unique_prompts':len({r['prompt_hash'] for r in rs}),'unique_safe_prompts':len({r['prompt_hash'] for r in neg}),'mean_evidence_tokens':statistics.mean(r['evidence_tokens'] for r in rs),'latency_unique_prompt_mean_seconds':statistics.mean(v['monitor']['latency_seconds'] for v in {r['prompt_hash']:r for r in rs}.values())}
  metrics.append(metric)
 bycase={}
 for r in rows:bycase.setdefault(r['case_id'],{})[r['condition']]=r
 pairs=[{'case_id':cid,'family':v['assumption']['group'],'label':v['assumption']['label'],'history_flag':v['assumption']['flag'],'current_flag':v['current_summary']['flag'],'history_score':v['assumption']['monitor']['score'],'current_score':v['current_summary']['monitor']['score']} for cid,v in bycase.items()]
 groups=sorted({r['family'] for r in pairs});family_differences=[]
 for g in groups:
  ps=[r for r in pairs if r['family']==g and r['label']];ns=[r for r in pairs if r['family']==g and not r['label']]
  family_differences.append({'family':g,'recall_difference':statistics.mean(int(r['history_flag'])-int(r['current_flag']) for r in ps),'fpr_difference':statistics.mean(int(r['history_flag'])-int(r['current_flag']) for r in ns)})
 ds=np.array([x['recall_difference'] for x in family_differences]);observed=float(ds.mean());perms=[abs(float(np.mean(ds*np.array(signs)))) for signs in itertools.product([-1,1],repeat=len(ds))];pvalue=sum(x>=abs(observed)-1e-12 for x in perms)/len(perms)
 rng=np.random.default_rng(180301);ci=np.quantile([rng.choice(ds,len(ds),replace=True).mean() for _ in range(2000)],[.025,.975]).tolist()
 comparison={'primary_contrast':'assumption minus strong current_summary','paired_cases':len(pairs),'independent_family_blocks':len(groups),'recall_difference':observed,'recall_difference_family_bootstrap_ci':ci,'two_sided_family_sign_flip_p':pvalue,'family_differences':family_differences,'history_only_detections':sum(r['label'] and r['history_flag'] and not r['current_flag'] for r in pairs),'current_only_detections':sum(r['label'] and not r['history_flag'] and r['current_flag'] for r in pairs),'matched_test_fpr_claim':False,'interpretation':'descriptive controlled comparison, four related syntax families; no LinuxArena or population-level temporal advantage established'}
 (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2));(OUT/'paired_comparison.json').write_text(json.dumps(comparison,indent=2));(OUT/'paired_cases.json').write_text(json.dumps(pairs,indent=2))
 # Frozen source and response provenance; no target execution.
 static=json.loads((OUT/'static.json').read_text());cases=json.loads((DATA/'cases.json').read_text());responses=[json.loads(p.read_text()) for p in (OUT/'responses').glob('*.json')];usage={'unique_responses':len(responses),'new_cost_usd':sum(r['accounted_cost'] for r in responses),'prompt_tokens':sum(r.get('raw_response',{}).get('usage',{}).get('prompt_tokens',0) for r in responses),'completion_tokens':sum(r.get('raw_response',{}).get('usage',{}).get('completion_tokens',0) for r in responses),'median_latency_seconds':statistics.median(r['latency_seconds'] for r in responses),'static_extraction_seconds':sum(v['seconds'] for r in static for v in r['versions'].values()),'static_states':sum(len(r['versions']) for r in static),'static_failures':sum(v['status']!='ok' for r in static for v in r['versions'].values()),'static_source_files_scanned':sum(v.get('source_files',0) for r in static for v in r['versions'].values()),'median_full_history_summary_seconds':statistics.median(c['summary_seconds'] for c in cases),'summary_update_implementation':'full history recheck; not optimized incremental invalidation','new_logical_jobs':len(rows)*2,'uncertainty_warning':'within-family variants and repeated prompts are dependent; binomial intervals are descriptive; bootstrap has only four blocks and can be degenerate'}
 (OUT/'usage.json').write_text(json.dumps(usage,indent=2));print(json.dumps(metrics,indent=2));print(json.dumps(comparison,indent=2))
if __name__=='__main__':main()
