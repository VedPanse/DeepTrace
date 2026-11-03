# DeepTrace opportunities: ranked and conditional

## Recommended research question

**Can an online index of security assumptions and their invalidating edits help a fixed safety monitor recognize a current action's dependence on earlier changes, under a fixed evidence budget?**

This targets a distinction our experiments expose: current candidate graphs can retain a guard call while omitting the changed predicate implementation and the edit that altered its meaning. It asks for more than concatenating static graphs or handing them to an LLM. It remains a hypothesis, not an established novel contribution.

## 1. Security-assumption invalidation across edits — strongest conceptual direction

**Observed limitation:** A→B changes the imported authorization predicate, but emitted sink nodes/edges remain identical; baseline policy reports the candidate as existing. C/D add argument/shell behavior without any reference to B's earlier modification. Evidence: `results/temporal-structure.json`, all four saved source trees, `results/baseline-B/policy.json`, [src/agentsecbench/graph/analysis.py:89](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/analysis.py#L89), [src/agentsecbench/graph/project.py:230](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/project.py#L230).

**Safety relevance:** an earlier approved edit may weaken a condition that a later action relies on. A current sink path alone need not explain that loss of protection. The [LinuxArena paper](https://arxiv.org/html/2604.15384v2) identifies shallow tracing among monitor failure modes; it motivates an evaluation setting rather than proving that our representation would fix those failures.

**Possible algorithm:** maintain versioned facts about input origins, guard predicates, configuration choices and security effects; link monitor decisions to the assumptions they used. For a current edit/action, find earlier changes that invalidated those assumptions, retrieve a compact explanation chain with before/after evidence, and expire superseded facts. Stable semantic identities and uncertainty are essential. This is a proposal only; no such system was implemented here.

**Small falsifiable test:** create paired trajectories with the same final tree but different ordering/authorization histories, and matched benign refactors. Compare full-snapshot code retrieval, raw diffs/history, current graph, graph-diff retrieval, and assumption-history retrieval with one fixed monitor and tokenizer. Label both historical authorization and final executable security condition separately. Evaluate attack detection at matched benign false-positive rates, evidence attribution accuracy, and retrieval cost. Final-state labels alone cannot fairly test history-sensitive authorization.

**Novelty assessment:** plausible problem-specific contribution, not established. [AgentSentry](https://arxiv.org/abs/2602.22724) already studies temporal causal diagnostics for multi-turn prompt injection, including counterfactual re-execution. [AttriGuard](https://arxiv.org/abs/2603.10749) attributes tool calls through runtime counterfactual tests. A contribution must distinguish code-edit assumption invalidation and past monitor-decision dependencies from existing temporal causal defenses. A systematic literature review remains necessary.

## 2. Monitor-aware selection of source and historical evidence — conditional on better labels

**Observed limitation:** single candidate records are small; six pooled operations exceed small context budgets. Generic packing scores differ, but we have no monitor or security-relevance outcome. The magentic-ui multiline process snippet omits shell=True; selection cannot rank evidence absent from the graph. Evidence: `selection_analysis.md`, `results/budget-results.json`, source `_null.py:54–62`.

**Safety relevance:** a monitor needs the facts that distinguish permissible behavior from a policy violation, rather than many cheap structural edges. Old guard text and a current argument change can be jointly necessary.

**Possible algorithm:** score evidence by its estimated contribution to resolving specific security assumptions for the current action, select whole explanatory chains under a token budget, and include before/after source spans with confidence. A submodular/knapsack objective might be a useful baseline, but using such an optimizer is not itself novel.

**Small test:** human-label minimal evidence sets for 20–30 benign/unsafe multi-edit pairs, hold out repositories and attack templates, compare all six current baselines plus raw text/recent-history baselines. Include oracle labels and real model-token budgets. Ablate graph structure, temporal provenance and source text separately, then run a fixed monitor. Do not train a new model initially.

**Novelty assessment:** uncertain and potentially overlapping. [LLMLingua](https://arxiv.org/abs/2310.05736) and [LLMLingua-2](https://arxiv.org/abs/2403.12968) already investigate prompt compression. The differentiator would need to be security-assumption evidence utility and causal-chain sufficiency, with measured monitor benefit. Our retention experiment alone does not justify it.

## 3. Incremental maintenance with security-aware invalidation — useful supporting work

**Observed limitation:** each public scan reloads files, rebuilds project indexes and regenerates candidate graphs; baseline classification occurs after extraction. A helper-only change can matter even when sink finding hashes do not change. Evidence: [src/agentsecbench/scanner/engine.py:250](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L250), [src/agentsecbench/graph/builder.py:190](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/builder.py#L190), `results/graph-timing/` and the temporal baseline outputs.

**Safety relevance:** a monitor operating after each edit needs timely evidence, and a changed authorization helper should invalidate dependent conclusions even when the sink is untouched.

**Possible algorithm:** cache parsed file/function summaries with content hashes, track dependencies on imported predicate/configuration summaries and invalidate affected candidate/assumption records. Distinguish changed evidence from changed security meaning; preserve historical records separately from current caches.

**Small test:** replay edits in the three pinned repositories, compare every incremental graph against a full rebuild, measure stale/missing evidence and latency/peak memory. Include helper changes, import renames, local aliasing and configuration mutations; compare simple changed-file and transitive-call invalidation before claiming a new algorithm.

**Novelty assessment:** low for incremental analysis alone. [Infer's CI workflow](https://fbinfer.com/docs/1.1.0/steps-for-ci/) already supports incremental-analysis workflows. [TaintTyper](https://arxiv.org/abs/2504.18529) studies modular taint checking/inference. A credible contribution would require a new security/monitor invalidation contract, not merely caching ASTs.

## 4. Better static security extraction — clearly useful, mostly baseline engineering

**Observed limitation:** direct cross-file propagation fails through a copied caller local; configuration getter returns are not summarized; list mutation loses the action-to-command dependency in mini-swe-agent; regex .exec is misclassified; overwritten parameters differ between paper and product. Evidence: `results/challenge-cases.json`, `results/paper-probes.json`, real source inspections in repository comparison.

**Safety relevance:** a missing/false path undermines every downstream selection or temporal method. Comparing to the weaker product implementation could overstate gains.

**Possible approach:** resolve detector-to-call anchors, use versioned SSA/def-use summaries, model return values and common mutation patterns, and add conservative guard-body dependency summaries. Preserve the original analyzer as a baseline and explicitly label stronger extraction as a separate component if later implemented.

**Small test:** expand authored controls into independently labeled suites, then manually audit matched real cross-file paths. Compare stronger existing analyzers before writing new analysis logic. Use the paper v2_5 overwrite handling as a positive baseline.

**Novelty assessment:** low for these fixes individually. [AgentFlow](https://arxiv.org/abs/2607.01640) already recovers framework-aware component, control and data dependencies. AgentSecGraph's own related-work discussion covers additional static agent analyses. Cross-file extraction cannot be claimed as DeepTrace's novel idea simply because the legacy local pipeline lacks it.

## 5. Runtime-supported dependency evidence — potentially valuable but separate

**Observed limitation:** static relation statuses are explicitly candidates; SHA256 checks verify text consistency only. Dynamic getattr dispatch produces no process candidate in the authored fixture. We did not execute it or validate any real runtime flow. Evidence: `results/challenge-cases.json`, [src/agentsecbench/graph/builder.py:45](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/builder.py#L45), [src/agentsecbench/graph/analysis.py:89](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/analysis.py#L89).

**Safety relevance:** observed effects can corroborate a relationship that static analysis guesses, while dynamic dispatch can hide relevant operations. Absence in a trace still cannot prove absence across executions.

**Possible approach:** add isolated execution observations carrying code-version and action IDs, mark each fact as structural/inferred/observed and compare observations with the static graph. Treat traces as partial coverage, not semantic truth.

**Small test:** first use only authored harmless stubs in a disposable sandbox, label known dynamic flows, and compare static versus observed paths. Assess observation overhead and missed-trigger behavior before testing real repositories.

**Novelty assessment:** weak for combining static and dynamic tracing in general; causal tool-call attribution already exists in AttriGuard and AgentSentry. A novel link might concern code-version/assumption provenance and monitor decisions, but requires stronger prior-work comparison.

## Capability comparison

| Capability | AgentSecGraph | DeepTrace opportunity | Evidence |
|---|---|---|---|
| Static dependency extraction | Local Python AST and lexical JS/TS; public product adds bounded direct-call propagation | Reuse as baseline; improve extraction only where necessary | architecture source trace; overwrite/local controls |
| Security-sensitive path identification | Candidate anchoring plus source, guard, boundary and effect context; no exploitability verdict | Retrieve evidence for a specific current action and its security assumptions | graph_analysis; typed graph JSONL |
| Cross-file dependencies | Public direct MCP parameter case succeeds; caller local copy and config return fail; legacy pipeline is local | Predicate/configuration summaries and versioned invalidation | cross_file_direct, cross_file_local_alias, config_return |
| Temporal dependency tracking | Frozen commit provenance in research pipeline and finding baselines in product; no causal edit-history graph in executed paths | Track when assumptions change and which later actions rely on them | A–D graph outputs and baseline B/D |
| Incremental updates | Full scan/index/graph rebuild per public invocation; finding comparison is separate | Correct dependency/assumption invalidation with measured equivalence | scanner engine; graph-stage timings |
| Context-budgeted selection | Executed extraction outputs graphs; report has projections; no monitor-budget optimizer in these paths | Budget source/history evidence based on security decisions, if labels support it | budget experiment; per-candidate saturation at 1,024 |
| Integration with safety monitors | Static outputs and CI policy exist; no online sabotage-monitor loop exercised here | Evaluate a fixed monitor using retrieved assumption history | CLI/policy source inspection; no monitor evaluation |
| Evaluation against multi-step sabotage | Paper examines static security context; our static temporal sequence tests representation only | Matched benign/unsafe trajectory evaluation with monitor outcomes | temporal_analysis; LinuxArena motivation |

## Decision for the capstone

Treat AgentSecGraph as a useful static evidence baseline and avoid presenting extraction plus LLM monitoring as novel. Before building DeepTrace, conduct a small labeled evidence-sufficiency study on real multi-edit sabotage trajectories and benign controls. Ask whether the missing information is static source semantics, history, or a monitor's use of already available evidence. If full-snapshot source retrieval solves the examples as well as a temporal representation, the proposed temporal contribution needs revision. If histories expose decision-critical invalidated assumptions under matched budgets, that is the most defensible next hypothesis.
