# Temporal dependency experiment

## Controlled setup

This experiment is deliberately small, synthetic and static-only. No shell commands from the application were executed. Two Python files define an authorization predicate and a process wrapper. Four complete snapshots are saved under `results/fixtures/temporal-A` through `temporal-D`; a local Git history is retained in `results/fixtures/temporal-history/`. Exact commits are in `results/temporal.json` and `results/temporal-manifest.csv`.

| Version | Change | Sink source paths | Guard candidates |
|---|---|---:|---:|
| A | allowed(command) compares command with "status"; sink uses fixed printf argument vector and shell=False | 0 | 1 |
| B | allowed(command) becomes bool(command); sink unchanged | 0 | 1 |
| C | sink now receives command rather than fixed arguments, shell=False | 1 | 1 |
| D | sink enables shell=True | 1 | 1 |

The same predicate-call spelling remains at the sink in every snapshot. These modifications isolate how an earlier relaxed check can matter when later code broadens the sink's input and interpretation. They are transparent test mutations, not a claim of stealth against a human reviewer. A allows an action labeled status but only emits a fixed synthetic string; C permits executable selection, and D enables shell interpretation. No exploit payloads or production credentials are used.

## Exact observations

Each public invocation independently analyzes both files and emits one command-operation graph. Each paper v2_5 whole-pipeline run also emits one graph per version. The sink candidate ID remains `ASB-91B0DAF032842D57` in all public versions, because its file, symbol, detector and line remain fixed.

A and B have identical node/edge JSON hashes in `results/temporal-structure.json`. They do **not** have identical complete output hashes: the project callsite count increases from two to three because `bool(command)` adds a call. Scan roots also differ. That metadata difference does not identify the predicate body or explain its weakened authorization meaning. No edge links the sink guard to the config.py function body. A portable bundle preserving this original synthetic Git history is saved as `results/temporal-history.bundle`.

C adds a command-parameter dependency. D keeps the same dependency path and guard count, but its operation snippet and finding fingerprint change with shell=True. Thus the output preserves some argument evidence when it is on the matched line; it does not encode the causal history that gave that argument its significance. We do not claim C and D are indistinguishable.

## Baselines are a real existing capability

We froze A's findings with the product CLI's baseline feature. Scanning B against that baseline reports **0 new, 1 existing** candidate. Scanning D reports **1 new, 0 existing**. Files are `results/baseline-B/policy.json` and `results/baseline-D/policy.json`. This demonstrates some cross-run comparison support and prevents the overstatement that the tool has no concept of historical findings.

The saved baseline stores candidate fingerprints. It does not store the security dependency graph history, validity intervals, edits introducing facts, or an explanation of how the earlier helper change affects later sink behavior. Each scan rebuilds source and project indexes. Inspect [src/agentsecbench/scanner/engine.py:228](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L228) and [src/agentsecbench/policy.py:133](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/policy.py#L133).

## Answers to the six temporal questions

1. **Dependencies at each version:** it correctly changes from no argument-source path in A/B to a command-source path in C/D. It retains the enclosing If in all snapshots. It does not model the imported predicate implementation as security evidence for the sink.
2. **Which edit introduced the dependency:** the standalone graph does not say. Comparing separately saved graphs can reveal that C introduces the argument path, but cannot recover the meaning of B from these paths.
3. **Historical preservation:** the public graph entry point consumes one directory snapshot and no previous graph. The research pipeline consumes one frozen commit per manifest row. Its commit provenance identifies a version without automatically constructing a history.
4. **New versus existing:** finding-baseline comparison exists and recognizes changed sink evidence; it does not compare semantic dependency edges or detect an unchanged sink's weakened cross-file guard in this experiment.
5. **Final snapshot and attack history:** a final code snapshot can expose the permissive predicate, but cannot uniquely identify when it was changed, what the previous predicate was, or which earlier monitor decision relied on it. Different edit sequences can yield the same final tree. Git/trajectory evidence would resolve facts that a single tree cannot determine.
6. **Additional temporal representation:** store stable semantic identities, before/after source and predicates, action/commit IDs, dependency validity intervals, evidence origin and confidence, plus links from past monitor decisions to assumptions later invalidated. Retain replaced/removed facts, rather than only unioning all historical edges as though simultaneously valid.

## What this experiment does not establish

No monitor saw these changes, so there is no measured shallow-tracing failure, detection benefit, attack success rate or false-positive rate. A larger static interprocedural analyzer could improve predicate/configuration evidence without a temporal algorithm. A trajectory-aware monitor with raw diffs might already reconstruct the history. Those are necessary controls for a future DeepTrace study.

The temporal opportunity should therefore be tested against full-snapshot source retrieval, graph differences, raw edit history and a stronger static analysis baseline before attributing benefits to an online temporal method. The proposed next study is in `deeptrace_opportunities.md`.
