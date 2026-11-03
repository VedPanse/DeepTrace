# Context-budgeted evidence selection

## Estimator and evidence contract

Token estimate is **ceil(number of Unicode characters / 4)** over the final serialized evidence string, including line separators. It is an explicitly rough English/code approximation, not tiktoken or any model-specific token count. JSON punctuation and source language can make actual counts differ. Budgets exclude monitor instructions, current action and model response allowance.

For each of six graph samples, evidence atoms are: one complete compact JSON node, one complete compact JSON edge, or one complete JSON dependency-path list. Shared graph metadata/provenance/limitations are excluded from the atom payload; the table separately measures the complete compact graph JSON with metadata. This is a study of selecting existing extracted evidence, not retrieving omitted source code. The pooled case is a disjoint evidence pool of those same six operations, without invented links among them.

| Sample | Whole compact graph estimated tokens | All evidence atoms estimated tokens |
|---|---:|---:|
| html-anything | 597 | 214 |
| magentic-ui | 931 | 519 |
| mini-swe-agent | 833 | 429 |
| cross_file_direct | 824 | 436 |
| small-auth-app | 735 | 350 |
| parameter_overwrite | 658 | 290 |
| pooled-six | 2406 | 2362 |

## Baseline definitions

- **All truncated:** concatenate atoms in upstream node/edge/path order, then take the literal character prefix allowed by the budget. Incomplete atoms receive no retention credit.
- **Nearest:** undirected hop distance to the sensitive operation; complete atoms packed greedily, skipping atoms too large for the remaining budget. Node distances and tie rules are deterministic. Pooled case uses distance to the nearest of its six operations.
- **Shortest paths:** prioritize atoms on one shortest directed path from each input source to an operation; then pack remaining atoms. Direct source-to-sink edges frequently make this weakly discriminative. This implementation chooses the first shortest path deterministically, not all alternative paths.
- **Security endpoints:** prioritize input sources, guards, operation and effect nodes; then other atoms. This is a type heuristic, not a security-value oracle.
- **Random:** shuffle atoms with seeds 0–19; greedily pack complete atoms. Aggregate rows average these 20 trials.
- **Text summary:** deterministic compact verbalization of node identity/type/name/trust, edge relation/status and dependency-path strings, under the same budget. No LLM is used. This representation omits many attributes, source snippets and metadata, so its coarse fact-ID score is not equal information fidelity to full JSON.

All implementations and selected texts are in `scripts/analyze_results.py` and `results/budget-results.json`. `results/budget-evidence.json` contains each atom inventory and representation cost. Tie ordering, seeds and strings are retained so results can be audited without a monitor or tokenizer service.

## What is scored?

The principal score is the fraction of emitted atom IDs retained completely. Source-node, guard-node and dependency-path counts are also recorded separately for every row. This is **extracted-evidence retention**, not independently labeled security relevance, ground-truth path recall or vulnerability detection. It can reward the public analyzer's false parameter dependency. A source or check absent from extraction has zero selection opportunity; no ordering can recover it.

For text summaries, scoring credits a coarse fact ID if its abbreviated version is included. This is deliberately labeled separately in every row. It should not be interpreted as preserving all original attributes or making summaries superior to code.

## Results

For the six individual candidates, the ordinary JSON-atom baselines preserve an average 99.3% of atoms at 512 estimated tokens and 100% at 1,024, 2,048 and 4,096. Their similar aggregate scores hide small ordering differences. These tiny records offer little evidence for a sophisticated per-candidate selector.

The six-operation pool introduces meaningful context pressure:

| Budget | All truncated | Nearest | Shortest path | Endpoints first | Random mean | Text summary, coarse IDs |
|---:|---:|---:|---:|---:|---:|---:|
| 512 | 15.3% | 29.4% | 21.2% | 15.3% | 22.5% | 58.8% |
| 1024 | 29.4% | 43.5% | 36.5% | 29.4% | 44.5% | 100.0% |
| 2048 | 76.5% | 83.5% | 84.7% | 84.7% | 87.5% | 100.0% |
| 4096 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

These are descriptive observations for a hand-chosen pool, with no significance test. Unweighted atom count favors cheap edges over long source nodes. Random can beat a seemingly meaningful heuristic on that metric without being better for a monitor. The greedy methods skip oversized items while literal truncation stops, another intentional baseline difference to consider when interpreting the scores.

## Independent relevance checks and limitations

The authored challenge cases give limited independently understandable facts: a constant-overwritten parameter is not a source; the copied-local cross-file path and configuration getter flow exist in source; the early-return check constrains execution. Extraction misses or misrepresents these before any selector runs. Their results are in `graph_analysis.md`. We did not produce independent expert relevance labels for every atom of the real repositories. Therefore the experiment does not answer which selector preserves the evidence a safety monitor actually needs.

A follow-up should add source spans and edit history, independently label the minimal evidence needed to recognize a security-assumption violation, and evaluate a fixed monitor at matched false-positive rates and real tokenizer budgets. Evaluate both extraction recall and conditional selection recall, with an oracle evidence ceiling. Until then, a novelty claim based merely on context-budget packing is unsupported by these results.

## Source-grounded relevance check on three authored operations

A separate small reference inventory was written from the fixture source, after fixing the selection methods. It labels concrete static facts, not vulnerabilities: the command/tool/helper chain, the exact authorization predicate and imported settings, and a constant overwrite. This is analyst-authored and not blind expert annotation. Complete supporting atoms are mapped to each reference fact; missing facts have an empty support set. Generic boundary/effect nodes do not count as the exact authorization predicate.

| Operation | Source-reference facts | Facts available in product evidence | Ceiling for any selection over that evidence |
|---|---:|---:|---:|
| Direct cross-file MCP command | 3 | 3 | 100% |
| TypeScript authorization/configuration request | 6 | 2 | 33.3% |
| Constant-overwritten process parameter | 2 | 1 | 50% |

At each requested budget, all five full-JSON selection methods preserve all *available* reference facts in these three small cases: respectively 3/3, 2/6 and 1/2. Random uses the same 20 recorded seeds. Thus these operations reveal an extraction ceiling rather than a relevance-selection advantage. Text summaries have the same coarse support-ID mapping but are not credited as semantically equivalent, because abbreviating the sink removes argument details. The small inventory does not establish repository-wide recall. Full labels, budgets and seeds are in `results/relevance-reference.json` and `results/relevance-results.json`; `scripts/score_relevance.py` reproduces the scores.
