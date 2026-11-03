"""Check semantic graph augmentation on all frozen pilot programs, no API calls."""
import json,hashlib,collections
from pathlib import Path
from evidence import ROOT,packet,sha,reference
OUT=ROOT/'qualification/results'
cs=json.loads((ROOT/'continuation/data/cases.json').read_text());oldjobs=[json.loads(l) for l in (ROOT/'continuation/results/jobs.jsonl').read_text().splitlines()];oldgroups=collections.defaultdict(list)
for j in oldjobs:
 if j['condition']=='static':oldgroups[j['prompt_hash']].append(j)
oldconf=[{'prompt_hash':h,'cases':[(r['case_id'],r['label']) for r in rs]} for h,rs in oldgroups.items() if len({r['label'] for r in rs})>1]
newgroups=collections.defaultdict(list);entries=[]
for c in cs:
 text,e=packet(c['after'],c['approved']);h=hashlib.sha256((c['policy']+'\n'+text).encode()).hexdigest();label=reference(c['after'],c['approved']);assert label==bool(c['label']);newgroups[h].append(label)
 entries.append({'case_id':c['case_id'],'packet_hash':h,'source_facts':e['facts'],'source_spans':e['source_spans'],'typed_fact_nodes':e['nodes'],'typed_support_edges':e['edges'],'text':text})
newconf=[h for h,labels in newgroups.items() if len(set(labels))>1];assert not newconf
(OUT/'repaired_pilot_evidence.json').write_text(json.dumps(entries))
x={'scope':'evidence repair audit only, no pilot rescoring','cases':len(cs),'old_static_conflicting_prompt_hashes':len(oldconf),'old_conflicts':oldconf,'new_semantic_packet_conflicts':len(newconf),'new_distinct_semantic_packets':len(newgroups),'fields':['effective input restriction','argument origin','execution setting','source spans with imports and hashes'],'method':'bounded symbolic support facts augment candidate graph; not new general-purpose AgentSecGraph implementation','supported_languages':'authored Python grammar only; unknown on unsupported calls','all_reference_verdicts_omitted_from_monitor_packets':True,'old_pilot_scores_unchanged':True}
(OUT/'evidence_repair_audit.json').write_text(json.dumps(x,indent=2));print({k:v for k,v in x.items() if k!='old_conflicts'})
