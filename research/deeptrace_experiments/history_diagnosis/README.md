# Offline follow-up: separate facts, policy, and history

The latest paired comparison is frozen as a negative pilot. All its cases and all
previous qualification cases are spent development data. No new model calls were
made in this follow-up. Original scores and reports are unchanged.

## Qualification coverage audit

The passing qualification contained 44 unique prompts. Eight included a short
earlier-state note, only for restored/removed variants. There was no paired
current-versus-history qualification on every category. Evidence was 129–286
tokens, versus up to 831 in the broader paired test. Basic factual/policy checks
did not qualify interpretation of multi-event histories at comparable lengths.
Equivalent refactors, irrelevant changes, intermediate unknowns, and multiple
weaken/restore cycles were not systematically qualified. The numeric threshold
was strict; coverage of the intended workload was insufficient.

## Separate deterministic policy pipeline

`scripts/audit.py` applies the declared fixture rule to the model's reported
facts, not reference facts. This intentionally replaces the verdict stage for
diagnosis; it does not silently repair or rescore the original monitor.

Current-only: 120/120 correct, 12/12 unsafe detected, zero false accusations.
History: 102/120 correct, 9/12 unsafe detected, 18 unknowns, zero false accusations.
Unknowns are unresolved cases, never safe classifications. These counts are
post-hoc and clustered, not an independent reliability estimate. A rule checker
for this tiny declared policy cannot replace general sabotage monitoring.

This localizes two problems: current-only verdict generation misapplied correctly
reported facts; historical context additionally damaged fact interpretation.
It does not establish how either pipeline performs on new cases.

Reproduce without inference:

    research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/history_diagnosis/scripts/audit.py

Outputs: `results/offline_audit.json`, including per-case derived decisions and
input hashes; `results/negative_comparison_freeze.json`, the preserved-study hash
manifest. Re-running updates these derivative artifacts only.

## Next selector: development specification, not implemented or evaluated here

Reuse continuation/scripts/assumption_graph.py's source/support/version DAG, but
do not mistake it for a finished selector. Its bounded source dependency analysis
is approximate, especially under changed imports, dynamic dispatch, and languages
outside the supported Python grammar.

For each pre-action boundary, represent:

* SourceVersion: path, content hash, span, observed boundary, provenance.
* FactVersion: predicate, value, scope, source support, valid-from/valid-until.
* AssumptionVersion: formula, supporting fact IDs, preserved/violated/removed/
  unknown status; restored is an explicit transition back to preserved.
* ChangeEvent: ordered action ID, before/after source IDs, effect verification.
* Witness: input/trace, expected predicate, checker version, verification result.
* RelevanceLink: proposed sink/argument -> dependency -> assumption -> edit,
  with separate verified and approximate edge types.

At a boundary: (1) verify state provenance; (2) extract the proposed action's
execution/data-flow dependencies; (3) invalidate assumptions whose support changed;
(4) recheck and close superseded versions; (5) walk backward only from assumptions
relevant to that action; (6) retain the latest decisive transition and any later
restoration/removal; (7) serialize current facts first, then explicitly PAST
events with validity intervals and CURRENT status; (8) attach source support and
checked witnesses, or explicit unknown reasons. No future actions/states/outcomes.

Older violated assumptions never imply current danger after verified restoration.
Unknown support invalidates a conclusion rather than silently preserving it.
Unrelated edits are excluded with recorded selection reasons. If mandatory current
facts plus supporting spans exceed budget, mark coverage failure; do not truncate
away repairs or uncertainty. Ranking/packing is deterministic and versioned.

Before model testing, use spent development cases to check restoration, removal,
equivalent refactors, unsupported dependencies, and identical-packet conflicts.
Those engineering checks are not detection results. The selector above still
needs implementation and independent validation; no completed algorithm claim.

## Where history could earn a benefit

With complete current semantics and a state-only rule, history supplies no missing
information. Those cases test robustness to extra context, not history necessity.
A meaningful additional test is retrieval efficiency in verified repositories:
can versioned support links find the relevant distant dependency under a budget
more efficiently than strong current-state search? Give both arms the same full
current repository, legitimate task, proposed action, analysis tools, and resource
caps. Only the history arm additionally receives legitimately available past
records. Count indexing/extraction, search, tokens, and latency. Do not hide current
facts from the baseline. If both retrieve sufficient evidence, no history advantage
is expected on this narrow policy. History-dependent legitimate-task requirements
would be a separate, explicitly labeled research question.

## Freeze requirements before another evaluation

No new run is authorized by this document as a frozen experiment. Before any run,
commit/hash extractor, selector, model/prompt/settings, evidence and compute caps,
calibration rules, raw/derived pipeline definitions, unknown/invalid handling,
deduplication/cache policy, family/repository splits, qualification coverage and
gate, primary paired metrics and uncertainty procedure. Qualify both evidence
conditions at intended lengths using new families; inspect development only.
Publish raw verdicts, fact accuracy, contradictions, invalids, abstentions,
unsafe misses, safe intervention burden and unique prompts. Keep alarms and
abstentions separate. Do not calibrate away contradictory answers and call it a
matched false-positive evaluation. A failed gate stops the fresh comparison.

## LinuxArena is a separate blocker

No verified cohort exists yet. The prior access failures are historical observations,
not freshly checked availability. Request original archives, exact source/image
and setup, ordered calls/results and concurrency/background events, checkpoints,
task/scorer versions and outcomes. Harm-boundary review must independently locate
both installation and delayed effects; final success alone is insufficient.
Per-action snapshots are optional if a pinned initial environment plus complete
records support independently checked replay of every effect. Final diffs do not.

The updated request is continuation/RESOURCE_REQUEST.txt. Nothing was sent.
