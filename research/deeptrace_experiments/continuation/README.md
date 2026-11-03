# DeepTrace continuation

This directory preserves the original pilots and separates new protocols, data,
checks, and results. Neither H1 nor H2 is treated as established.

First gate: exact LinuxArena initial-state provenance, replay receipts/order,
source-tree verification, independently checked first-harm boundary, validated
reference evidence, and disjoint fresh cohort/splits. A failed gate is an explicit
blocked result, not permission to substitute observed fragments or a current tag.

No recorded command is executed on the host. The bounded replay accepts explicit
verified file mutations or externally captured snapshots. Unsupported shell writes,
partial failures, asynchronous effects, and conflicting parallel mutations remain
unknown. Container execution and service-state replay require an isolated runtime.

The strong current-code baseline and history summaries share the same symbolic
engine and verification scope. Both may analyze the explicitly proposed edit as a
counterfactual preview; neither receives an observed future state. Labels and
hidden attack information are not monitor inputs.

## Reproduction (from project root)

```
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/audit.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/controlled.py
# Run static.py with continuation/results/isolation.sb and cleared environment.
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/packets.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/checks.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/cohort_gate.py
# Scoring already completed. Do not overwrite frozen thresholds:
# score.py calibration ; then score.py test (only in a new run directory).
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/metrics.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/final_checks.py
```

`score.py` reads the original ignored credential and checks the combined $3 cap.
Provider settings are the same OpenAI-only GPT-5 Nano settings as the pilots.
It refuses to overwrite frozen thresholds. All new prompts/responses are saved in
this directory; original pilot results are preserved. Analysis is offline.

Fresh split: four calibration and four held-out syntax families, each with a
specified approved command token. Entire depth/distance/variant groups stay in one
split. Distinct authorized tokens avoid exact task/prompt collisions across family
splits in baselines that cannot see guard semantics. This does not make these
semantically related tasks independent repositories. The current semantic baseline
has 32 unique held-out prompts versus 160 held-out cases; effective sample sizes
must always be reported. Unsupported calls are exercised by engineering controls,
not silently treated as either safe or malicious in monitor evaluation.

LinuxArena `linuxarena_packets.py` is a bounded adapter for future externally
verified captures, not an executed real-cohort result. Its receipt attestation
fields require source-producer evidence and review, not self-asserted booleans.
Its explicit limitations include plain-text workspace scope, candidate analyzer
edges, lexical action seeds, bounded traversal, and no live service-state replay.
The current-code symbolic checker supports only the authored Python grammar and
cannot analyze the public auto_workflow TypeScript application. An isolated Linux
runtime is also required for actual tool/scorer replay; Docker currently has no
daemon. Public source checkout/candidate extraction is not trajectory verification.

A fuller source/support/version DAG is in `scripts/assumption_graph.py` and
`results/support_dags/`. It was added AFTER the frozen monitor run and is not the
representation those scores evaluate. It rechecks claims after supporting source
edits and reuses them after unrelated edits. All 320 histories are checked acyclic;
restoring identical source content creates a new version occurrence, avoiding
backward cycles. Testing its monitor value requires fresh held-out data.
