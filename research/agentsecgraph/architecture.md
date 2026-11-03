# Architecture and implementation trace

## Identity and version boundary

Official identity is established by the paper's artifact link and the repository's reciprocal citation, not by a name search. Commit `e27f83d631c91b80fb55a2f1d9e4112f1a080ceb` is fixed in every source link below. The latest commit only adds citation metadata; public code and paper scripts coexist in that same tree. Their dates alone do not establish algorithm equivalence.

The experiments distinguish **paper pipeline v2_5** from **public product 0.2.0**. Neither was patched. `results/paper/` and `results/product/` are separate. In particular, do not extrapolate a product regression to the paper's claimed behavior.

## Public analyzer: entry point to outputs

| Step | Source and function | Behavior verified in source |
|---|---|---|
| CLI dispatch | [src/agentsecbench/cli.py:250](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/cli.py#L250) | main; analyze builds ScanOptions then calls analyze_repository |
| Configuration | [src/agentsecbench/config.py:42](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/config.py#L42) | load_project_config; TOML options and adapter declarations |
| Repository traversal | [src/agentsecbench/scanner/engine.py:112](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L112) | _iter_source_files; sorted traversal, exclusions, symlink rejection |
| Candidate matching | [src/agentsecbench/scanner/engine.py:152](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L152) | _scan_text; lexical rules plus Python dynamic-call AST filter |
| Operation rules | [src/agentsecbench/scanner/rules.py:37](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/rules.py#L37) | RULES; predefined categories and operation/framework patterns |
| Finding identity | [src/agentsecbench/scanner/engine.py:215](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L215) | _finding_id and _finding_fingerprint; location identity vs evidence baseline |
| Analysis orchestration | [src/agentsecbench/scanner/engine.py:250](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/scanner/engine.py#L250) | analyze_repository; read files, findings, graph build, validation and exports |
| Python slice | [src/agentsecbench/graph/analysis.py:89](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/analysis.py#L89) | analyze_python; AST call/scope, latest assignments, name backtrace and guards |
| TS/JS slice | [src/agentsecbench/graph/analysis.py:250](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/analysis.py#L250) | analyze_typescript; bounded lexical function and definition recovery |
| Framework normalization | [src/agentsecbench/frameworks.py:104](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/frameworks.py#L104) | detect_python_frameworks; TypeScript counterpart at 144 |
| Python project index | [src/agentsecbench/graph/project.py:125](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/project.py#L125) | build_python_project_index; direct imports and reverse callsites |
| Python propagation | [src/agentsecbench/graph/project.py:230](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/project.py#L230) | expand_interprocedural_sources; bounded incoming argument propagation |
| TS project index | [src/agentsecbench/graph/project_typescript.py:171](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/project_typescript.py#L171) | build_typescript_project_index; lexical ES/CommonJS resolution |
| TS propagation | [src/agentsecbench/graph/project_typescript.py:244](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/project_typescript.py#L244) | expand_typescript_sources; bounded incoming named-function propagation |
| Graph construction | [src/agentsecbench/graph/builder.py:58](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/builder.py#L58) | build_graph; typed records, provenance, default boundary/effect, views |
| Project graph orchestration | [src/agentsecbench/graph/builder.py:190](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/builder.py#L190) | build_graphs; indexes once per run then candidate builders |
| Structural validation | [src/agentsecbench/graph/validation.py:15](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/validation.py#L15) | validate_graphs; one-to-one IDs, evidence hashes, endpoints and views |
| HTML export | [src/agentsecbench/report/renderer.py:65](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/report/renderer.py#L65) | build_report; compact graph report and manifest |
| Baseline policy | [src/agentsecbench/policy.py:133](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/policy.py#L133) | evaluate_policy; current fingerprints compared with saved findings |

The repository directory is the input. Include/exclude patterns restrict files; the CLI does not require a build or dependency install. Supported candidate-scanning extensions are `.c .cc .cpp .cs .go .java .js .jsx .kt .kts .mjs .php .py .rb .rs .scala .sh .swift .ts .tsx`. These are not equally supported semantic languages. Dependency extraction dispatches to Python AST or JS/JSX/TS/TSX lexical code; other extensions get an unsupported-language evidence record. `.mjs` is included by the scanner and TS project index but omitted from `analyze_source`'s local-analysis dispatch, an inconsistency verified in [src/agentsecbench/graph/analysis.py:322](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/src/agentsecbench/graph/analysis.py#L322).

Default file-size ceiling is 2,000,000 bytes. Matching ignores source lines longer than 2,000 characters and lines beginning with common comment/docstring prefixes. Python eval/exec/compile additionally must correspond to an AST call on that line. Ordinary operation regexes can still match strings, imports, framework references and unrelated methods. JS `.exec` regex operations in `html-anything/cli/src/skills-loader.ts:63` illustrate this: a regex match is labeled a process-execution candidate. Candidates are not verified effects.

The default candidate granularity is a category/symbol/source-line record. Optional symbol granularity merges occurrences, persists at most 50 evidence lines, and can blur separate operations. Symbol names are guessed by scanning the preceding 30 lines. IDs include path, category, guessed symbol, line and detectors; baseline fingerprints replace line position with hashes of evidence lines. Neither identity is a stable semantic identity for a whole function or security assumption.

## Python dependency algorithm

`analyze_python` parses the entire candidate file, selects a call starting on an evidence line, and chooses an enclosing function by source range. The call selector sorts by span length and column; this is not a resolution of the matched detector to a particular AST call. Decorator candidates have special handling to locate a parameter-consuming call in the function.

It records parameter names and the latest preceding Assign/AnnAssign for each name, gathers names loaded by call arguments and attribute receivers, and recursively follows those definitions. Recognized source APIs include getenv/get/read/fetch-like names. Paths are lists of operation and variable names. They are explanatory candidates rather than a full dataflow IR. The visited-name set prevents infinite recursion and can collapse multiple paths through a shared name.

In the public version, the recursive trace checks whether a name is a parameter **before consulting an overwrite**. The authored parameter-overwrite case therefore retains a false dependency. Reassigning an intermediate local to a constant does terminate its dependency. `results/challenge-cases.json` and `results/paper-probes.json` show the difference with the legacy analyzer.

Guards are enclosing AST If nodes and preceding related Assert nodes. An ancestor If is labeled structurally without checking whether the operation is in its true or false branch, whether the predicate authorizes anything, or whether the predicate's implementation is effective. Early-return/raise validation outside the sink's ancestor chain is omitted in our fixture. There is no CFG dominance computation or solver proof in this implementation.

## JavaScript/TypeScript dependency algorithm

The local engine uses regular expressions, not a TypeScript compiler or AST parser. It searches backward up to 160 lines for a function-like signature; without one it starts at most 120 lines before the candidate. It collects assignments before the operation, parses arguments from the candidate's single source line, then follows identifier definitions. Preceding related `if` lines within 20 lines are potential guards, without control-flow dominance verification. Uppercase identifiers are excluded by the identifier helper, which can omit configuration constants. Our multiline exec fixture loses the command source in the product; the legacy implementation's bounded multiline call collection preserves it.

This implementation is syntax-sensitive: arrow callbacks, methods, registration wrappers, lexical nesting, module alias resolution and object properties are not a complete JS semantic model. These limitations make a missing path inconclusive about runtime reachability.

## Cross-file propagation

The public builder creates Python and TS project indexes once per scan, using the same source-text cache. Python indexes module-level functions and class methods, top-level imports, argument loaded-name sets and reverse call edges. TS uses lexical named-function and direct import resolution. Propagation starts at a sink function parameter and walks incoming calls up to depth six, stopping on repeated (function, parameter) states.

A source is promoted to an agent-tool parameter when an upstream caller has recognized framework evidence. Only argument names that are directly present among the caller's parameters propagate. There is no recursive slice of the caller's local assignment for that step: `execute(command)` works, `copied = command; execute(copied)` does not in our fixture. Generic callgraphs alone do not imply that all cross-file dependencies will be emitted. Return-value summaries, cross-file guard implementation dependencies, heap state, deployment configuration and dynamic dispatch are not recovered by this propagation routine.

We observed zero promoted interprocedural sources in the three real scans, despite the authored positive case succeeding. This is compatible with strict framework-recognition requirements; it is not evidence that the repositories have no cross-file security dependencies.

## Paper research pipeline

[scripts/run_security_adg_pipeline.py:20](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/scripts/run_security_adg_pipeline.py#L20) orchestrates scanner, generator, validator, showcase and corpus reports. We invoked its stages explicitly to preserve line-level granularity. The wrapper's scanner command otherwise defaults to symbol aggregation, whereas upstream comments recommend line-level matching before dataflow analysis.

[scripts/static_scan.py:240](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/scripts/static_scan.py#L240) reads source blobs from a Git archive at each manifest commit; it never imports targets. [scripts/generate_security_adg_v2.py:79](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/scripts/generate_security_adg_v2.py#L79) loads relevant frozen blobs, calls `make_graph`, runs legacy dependency analysis and replaces heuristic source/guard nodes using `replace_heuristics` at line 24. In `v2_5`, parameter precedence, overwrite handling, intrinsic-source-operation exclusion and framework normalization are enabled. [scripts/security_adg_dataflow.py:151](https://github.com/A1LinLin1/AgentSecBench/blob/e27f83d631c91b80fb55a2f1d9e4112f1a080ceb/scripts/security_adg_dataflow.py#L151) implements Python analysis, with the overwrite-sensitive branch at line 282; TypeScript starts at line 393 and collects multiline calls at line 375. The product and paper algorithms are similar but not identical.

The legacy pipeline does not invoke the public project index or cross-file expansion. Its graph provenance includes a commit and split; public graph provenance includes scan_root and evidence fingerprint but does not itself record repository commit. Our outer manifests provide that missing run provenance.

## Verification, resources and incrementality

Evidence SHA256 checks verify that a matched source line agrees with the finding. They do not verify dependency causality, reachability, authorization or runtime effects. Structural validation checks record shape and linkage, not semantic completeness. We separately checked graph acyclicity because the product validator does not.

The analyzer needs only CPU, memory, Python and local source. No target runtime, LLM call or GPU is used in these extraction paths. Initial end-to-end peaks were about 33–80 MiB; see repository comparison for graph-stage timing and memory scopes. The initial demo and 36 product tests pass; additional legacy, CLI and cross-file tests pass with separate logs.

Each `analyze_repository` invocation traverses source files and rebuilds project indexes and graphs. Its source-text dictionary is a within-run cache, not a persistent incremental dependency store. Baseline/suppression policy stores finding identities and supports CI filtering, but scans still rebuild the analysis. No persistent graph invalidation or edit-history input is used by these inspected entry points. This is a positive code-path observation, not an inference solely from missing documentation.

Outputs include findings JSONL, graph JSONL, graph summary JSON, framework coverage, structural validation JSON, SARIF, HTML report and optional policy reports. The paper showcase also exports typed SVGs and layout JSON. No GraphML or DOT exporter was found in the executed paths; the analysis scripts here preserve JSON and export SVG separately.
