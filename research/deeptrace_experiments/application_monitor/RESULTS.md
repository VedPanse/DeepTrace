# Application-derived monitor comparison — November 13

## Result

The bounded dependency representation performed best in this run. Explicit assumption-change history improved on raw history but did not improve on the current-code dependency representation. This is a new monitor experiment, not just a capture test, but it is still a controlled test of one real module rather than the proposed real-trajectory evaluation.

| Evidence | Correct / 24 | Violations caught / 12 | False alarms / 12 safe |
|---|---:|---:|---:|
| Current and proposed source | 17 (70.8%) | 7 | 2 |
| Same source + dependency representation | 22 (91.7%) | 11 | 1 |
| Same source + dependencies + raw change history | 17 (70.8%) | 5 | 0 |
| Same source + dependencies + assumption-change history | 20 (83.3%) | 8 | 0 |

All 96 logical responses supplied valid boolean verdicts and confidence values. Six exact duplicate prompts shared one provider response, leaving 90 distinct calls. No response was repaired, rescored from its explanation, or rerun for a better answer. New provider cost was $0.00679295; combined recorded project cost is $0.97670572, within the existing $3 cap.

## What this says about our questions

**H1, dependency evidence:** The observed difference is +5 correct decisions out of 24 (+20.8 percentage points). This is a promising representation result in this narrow setting, not proof of better timely sabotage detection. The descriptive bootstrap interval over six role-configuration groups is approximately [-4.2, +45.8] percentage points. Those groups are related variants of the same module, not independent applications or attacks.

**H2, assumption-change history:** It gained 3/24 (+12.5 points) over raw history but lost 2/24 (-8.3 points) against dependencies without history. The hypothesis requires an advantage over both comparisons; this run does not support that claim. History conditions also had fewer false alarms, so these raw verdict counts are not a comparison at a calibrated matched audit rate. Zero false alarms on just 12 safe cases is not a deployment reliability guarantee.

The original H1 and H2 remain unestablished for real agent trajectories. We now have a concrete mixed result to report: structured dependency information was useful in this run, whereas adding temporal information did not consistently improve it.

## Frozen setup

- Real `requireRole` TypeScript code from the same pinned LinuxArena application image used by the capture study. This is a bounded source-derived dependency representation, not the general AgentSecGraph pipeline or full support DAG.
- Six role configurations, each with four authored edit cases: introduce a disabled role guard, restore the guard, add a harmless comment after restoration, and add a harmless comment after an earlier failed command nevertheless disabled the guard. There are 12 violating and 12 conforming proposed states.
- A Docker-isolated functional oracle transpiled and executed the proposed module with mock request/response objects for no user, admin, developer and viewer. All 96 probes agreed with the authored references before inference. No independent human review was performed.
- One fixed GPT-5 Nano monitor and settings across all conditions. Every condition received identical full current source, proposed source and access contract. No labels or oracle outcomes were sent to the monitor. A shared 4,096-token cap applied; the largest locally counted prompt was 1,140 tokens. This is equal-cap, not equal-consumed-token evaluation.
- Current predicates and dependency fields were extracted from the proposed source. Historical records included version hashes and exit statuses; the assumption representation retained changed predicates and their source support, without safe/unsafe labels. This bundles selection and presentation and does not isolate their causal effects.
- Protocol, prompts, executable reference and implementation hashes were frozen before calls. A recorded pre-inference amendment deduplicated identical empty-history prompts; the initial protocol is retained. No test result drove a protocol change.

These were known development templates, including the weakening already demonstrated in the capture pilot, not unseen held-out attacks. Full relevant source already fits the evidence budget, so this test measures the effect of representation and history on reasoning, not DeepTrace's proposed advantage in retrieving distant dependencies from a large repository.

## Error inspection

Several missed violations described the missing role enforcement correctly but emitted `policy_violation: false`. For example, one assumption-history response said the result "omits 403 behavior for insufficient permissions" while returning a non-violation. This resembles the earlier fact-to-verdict failure. The primary table retains the boolean decision exactly as returned; explanations were not used to repair scores.

The prompt also used the shorthand "no user must receive status 401" for a request with no authenticated user. That wording could be read ambiguously and is a limitation of this frozen exploratory run. A future qualification should use explicit wording and fresh cases; this run must not be presented as clean evidence of general superiority or silently replaced by a more favorable rerun.

## Evidence and reproducibility

`results/protocol.json`, `jobs.json`, `reference.json` and `release.json` record what was fixed before inference. `responses/` contains original provider outputs; `analysis.json` contains every scored case and the descriptive paired contrasts. `verify_results.py` recomputes labels from the executable probes and counts directly from provider outputs rather than trusting the summary flags.

From the repository root:

```sh
python3 research/deeptrace_experiments/application_monitor/verify_results.py
python3 research/deeptrace_experiments/application_monitor/study.py analyze
```

Both commands are offline. The `prepare` and `run` commands refuse to overwrite existing artifacts. Existing synthetic studies and capture-pilot results remain unchanged. Full-harness integration, realistic task/scorer outcomes, independently reviewed harm boundaries and a calibrated audit-rate comparison are still needed to answer the original real-world hypotheses.
