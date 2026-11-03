# Graph construction and semantic limits

## What graph is actually emitted?

Both implementations emit one graph per candidate operation. The product builder [src/agentsecbench/graph/builder.py:58](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/builder.py#L58) starts with four nodes even when no source or guard is found: owner, operation, abstract effect and a default trust boundary. This explains why graph production can succeed without recovering a dependency. There is no complete repository graph in these outputs.

Our `all-candidate-forest.json` is explicitly a **disjoint union** of these records, with IDs prefixed by candidate ID. It invents no cross-candidate joins or edges. The catalogs preserve every candidate as its own graph. A whole-program security graph that merges entities would require additional analysis and identity rules.

## Node and edge vocabulary

| Node type | Why it exists | Evidence and caveat |
|---|---|---|
| agent_or_program_symbol | Owning or nearest source symbol | Guessed lexical owner plus optional framework evidence; not proof of externally reachable entrypoint |
| security_sensitive_operation | Candidate anchor | Regex/AST-assisted detector, category, confidence, source-line hashes and snippets |
| external_effect | Category-to-effect mapping | Deterministic static semantics, not an observed effect |
| trust_boundary | Generic input-to-effect context | Always added; its existence is not evidence a trust boundary is actually crossed |
| input_source | Recovered parameter or source API | Backward-name slice or bounded incoming-call propagation; may be incomplete or incorrect |
| guard_candidate | Visible If/Assert context | Potential constraint, not effective authorization; guard code may be outside the graph |
| program_symbol | Public cross-file call chain | Added only for recovered interprocedural sources; absent from the legacy builder |

| Edge type | Direction used by implementation | Meaning/status |
|---|---|---|
| contains | owner → operation | Structural ownership |
| may_cause | operation → effect | Category semantics |
| reaches | boundary → operation | Unconfirmed context; added even with no source |
| may_data_depend_on | source → operation | Possible dependency; the English relation name is opposite to a literal reading of its arrow |
| may_cross | source → boundary | Possible boundary crossing |
| may_guard | guard → operation | Candidate constraint; structural/lexical status does not establish effectiveness |
| flows_through | source → call-chain symbols → operation | Public bounded project-call candidate |

Edges retain their status strings. Some cross-file-promoted source edges still use the generic `local_static_candidate` status in the builder; inspect source metadata and `analysis.interprocedural` rather than assuming the edge status alone captures its provenance.

## Retained versus omitted information

Retained facts include the operation category and detector identity, matched lines and hashes, source/guard identifiers and lines, explanatory name paths, modeled framework evidence, uncertainty labels, default effect/boundary semantics and analysis limitations. The paper format includes the frozen commit; our outer manifest supplies it for public runs.

Intermediate local variables are usually path strings rather than standalone nodes. Most non-candidate functions, imports, callsites, constants, branch bodies and configuration declarations do not appear. Deployment authorization, actual secrets, runtime outcomes and complete historical versions are not inferred. The generic effect mapping does not distinguish all critical argument settings. Multiline sink snippets can omit `shell=True`, even though the parser saw the full file.

An evidence hash answers whether the source line stayed the same. It does not answer whether an imported guard's implementation still has the same security meaning. In the temporal experiment, the guard call and sink line stay fixed while the helper changes.

## Controlled observations

| Case | Expected source/guard fact from authored source | Public observation | Paper analyzer observation |
|---|---|---|---|
| Parameter replaced by constant | No original parameter flow | Parameter source retained | Original parameter flow removed |
| Intermediate local replaced by constant | No original parameter flow | Flow removed | Flow removed |
| Direct imported helper called by MCP tool | Cross-file tool parameter flow | Recovered, including program_symbol and flows_through | Local helper parameter only |
| Same call via copied local variable | Same cross-file flow | Tool provenance lost; generic helper parameter retained | Local helper parameter only |
| Early-return/raise input validation | Relevant validation context | No guard node | No guard node |
| Enclosing allowlist If | Relevant validation context | Guard candidate | Guard candidate |
| getattr(subprocess, "run") | Process operation candidate | No candidate, hence no graph | Not independently scanned by legacy scanner in this probe; source rule has no matching low-level syntax |
| Configuration getter returns getenv value | Cross-file source API path | No source path at process sink | No source path |
| Multiline JS exec(command) | Command parameter flow | Candidate found, source missing | Parameter path retained |
| Recursive function | Recursive program call edge | Emitted candidate graph remains acyclic | Local evidence only |

These are authored counterexamples and positive controls, not a statistical estimate of field accuracy. `results/challenge-cases.json` records public graphs; `results/paper-probes.json` records direct legacy dataflow results using the same source and detected lines. The actual legacy whole-pipeline temporal runs are separately saved in `results/temporal-paper/`.

## DAG question

All 509 real product graphs and every controlled product graph passed an independent topological-sort test. The builder's emitted edge types run from context/sources/guards through the operation to an effect, and cross-file chains introduce fresh nodes. This makes the tested candidate representation acyclic. The underlying program call index can contain recursive cycles; a visited-state set and depth limit prevent traversing them indefinitely. The emitted graph is not a faithful encoding of the entire recursive callgraph.

The upstream validator checks structural validity but does not assert acyclicity. Our renderer does not remove edges or compute an SCC condensation. It displays exactly the selected nodes/edges, and the machine-readable files preserve them. Consequently, no claim is made that all possible agent program dependency graphs are DAGs.

## Visual inspection guide

Open [the catalog](visualizations/index.html). Each selected `*-full.svg` contains the complete candidate graph; `*-security.svg` removes only the owner/contains context and preserves the remaining upstream relations. This is our documented display projection, not a second extraction algorithm. Because the upstream record is already centered on a sensitive operation, the difference is intentionally small.

The source and guard nodes exist only if their extraction rules recovered them. Default boundary/effect nodes exist because the builder adds them. A missing source in `html-anything-full.svg` is visible rather than replaced by a guessed executable or configuration node. Cross-file_direct explicitly shows the positive MCP call-chain case. Small-auth-app shows the lexical guard/source evidence without inventing edges to auth.ts or config.ts.

Each SVG prints its typed edge list and uncertainty status; dashed relations are possible dependencies/effects/context. Every SVG is XML-parsed and checked against its JSON; selected real and synthetic figures were rendered for visual QA. The original paper renderer's three projection views are also preserved under `results/paper/showcase/`, independently of our exports.
