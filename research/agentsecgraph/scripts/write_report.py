"""Assemble the report from recorded results, with immutable source citations."""
import json,statistics,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def load(name):return json.loads((R/name).read_text())
def lines(name):return [json.loads(x) for x in (R/name).read_text().splitlines()]
def write(name,text):(ROOT/name).write_text(text.strip()+'\n')
pins=load('repositories.json');sha=pins['analyzer']['commit'];rows=load('comparison.json');idx=load('indexes.json');budgets=load('budget-results.json')
def ref(path,line,label=None):return f'[{label or path+":"+str(line)}](https://github.com/A1LinLin1/AgentSecBench/blob/{sha}/{path}#L{line})'
a='src/agentsecbench/graph/analysis.py';b='src/agentsecbench/graph/builder.py';e='src/agentsecbench/scanner/engine.py';p='src/agentsecbench/graph/project.py';ts='src/agentsecbench/graph/project_typescript.py'
write('README.md',f'''
# AgentSecGraph reproduction and DeepTrace research

Research date: October 21, 2026 (America/Los_Angeles). This is a code inspection and exploratory reproduction, not an attack-detection evaluation. No DeepTrace implementation or model training was performed.

## Executive findings

The paper's **Data and Artifact Availability** section explicitly links [A1LinLin1/AgentSecBench](https://github.com/A1LinLin1/AgentSecBench), which reciprocally cites the paper in its README and package metadata. The verified checkout is `{sha}` (public package 0.2.0, Apache-2.0). It contains two materially different implementations: the paper-oriented `scripts/` pipeline in mode `v2_5`, and the installable `src/agentsecbench/` product. This study ran both without editing either.

Across three pinned public repositories, **each implementation emitted 509 candidate graphs**. Candidate sets agree in count and file/line/category keys, but dependency and guard recovery differ. These graphs are small evidence records per sensitive operation, not a complete repository dependency graph. All 509 product graphs were acyclic in our structural check; recursion in a test program did not appear as a graph cycle.

The public implementation recovers a direct cross-file MCP argument flow in an authored case. A local variable assignment before that call breaks its cross-file source recovery. Cross-file configuration return flow, dynamic process dispatch, and an early-return validation guard are missed in other controlled examples. The product also retains an overwritten parameter as a source, whereas the paper analyzer correctly terminates that dependency. These are implementation-specific observations, not a claim that static analysis cannot handle them.

A four-version experiment shows that weakening an imported authorization helper leaves the sink graph's **nodes and edges identical**. A whole-project call counter changes, so the complete JSON records are not identical. Baseline comparison recognizes a later edited sink as new, but does not flag the helper change. It does not produce a causal account of earlier edits.

Six sampled individual compact graph records cost approximately 597–931 tokens with the documented character estimator. Every individual evidence-atom set fits at 1,024 estimated tokens. Pooling six operations creates actual budget pressure, but preservation of extracted facts is not monitor accuracy. The strongest candidate DeepTrace direction is **tracking security assumptions across edits and retrieving their invalidation history for a current action**, with incremental maintenance as an efficiency component. Novelty remains unproven: incremental program analysis, causal agent defenses, and prompt compression already overlap substantially.

## Deliverables

- [Architecture and source trace](architecture.md)
- [Repository measurements and case inspection](repository_comparison.md)
- [Graph semantics and limitations](graph_analysis.md)
- [Temporal experiment](temporal_analysis.md)
- [Budgeted evidence experiments](selection_analysis.md)
- [Ranked DeepTrace opportunities and capability table](deeptrace_opportunities.md)
- [Graph catalog](visualizations/index.html): 509 complete candidate SVGs, plus full/security views for six inspected cases; original paper renderer outputs are in `results/paper/showcase/`.
- `results/`: exact pins, source snapshots, JSONL graphs, SARIF, metrics, test logs, fixtures, budget outputs, provenance and validation.

## Reproduction

Use macOS with Python 3.11+ and Git. This run used CPython 3.13.6. Runtime dependencies of the analyzer are empty in `pyproject.toml`; no GPU, model API, target dependency install, or credentials were needed. Running from source avoids executing package installation hooks. A conventional install would be `python -m pip install -e upstream`, requiring setuptools >=68, but that path was not used.

From this directory:

```sh
python3 scripts/bootstrap.py
python3 scripts/run_isolated.py isolation
python3 scripts/reproduce.py
python3 scripts/experiments.py
python3 scripts/run_isolated.py paper-probes
python3 scripts/run_isolated.py indexes
python3 scripts/additional_runs.py
python3 scripts/analyze_results.py
python3 scripts/score_relevance.py
python3 scripts/write_report.py
python3 scripts/verify_artifacts.py
```

`bootstrap.py` restores the exact commits listed in `results/repositories.json`. Existing mismatched checkouts are refused. Downloads require network access, but analyzer runs do not. The macOS Seatbelt policy denies network access, clears inherited environment variables, and confines reads to research files and runtime/system directories; writes go to result/visualization directories and temporary files. Target modules and their setup scripts are never imported or executed. Docker was installed but its daemon was unavailable, so the actual isolation was Seatbelt, not a container. The launcher deliberately fails on unsupported platforms; a Linux reproduction needs an equivalent no-network, read-only container mount with no credentials.

The demo runs with `python3 scripts/run_isolated.py cli demo --output "$PWD/results/demo"`. Its report is `results/demo/results/report/index.html`. A generic isolated scan is `python3 scripts/run_isolated.py scan /absolute/target /absolute/research/results/output`.

Timings are single-run descriptive measurements, not a statistically controlled performance comparison. Stage timings come from a separate instrumented run and are not combined with initial-run totals. Token counts are approximations, not a model-specific tokenizer.

## Scope, failures, and outstanding limits

The original 67-repository frozen manifest and source snapshots are absent from this public checkout. We reproduced the released algorithms on newly pinned versions of three repositories named in upstream experiment configuration, not the original corpus-wide numbers or the paper's nine-case annotation study. Some disclosure-related reproduction details are intentionally withheld according to the paper. No claim of exact published-result reproduction is made.

The requested small authentication/configuration example is an additional authored three-file TypeScript fixture; the public TypeScript repository has 127 scanned files. We did not assume its architecture includes a conventional authentication service. All real scans include tests and examples unless upstream defaults exclude them.

A first sandbox test run failed because temporary files were writable but not readable. TMPDIR was moved into the research results tree; the rerun passed. A legacy validator invocation with `--expected-split all_corpus` rejected development-tagged manifest rows; rerunning with their actual split passed. Initial baseline CLI calls used an invalid named argument and were corrected to the documented positional argument. These failures are recorded in `results/failures.json` and retained logs.

No safety monitor was run, no actual security effects were executed, and no precision/recall or attack-detection improvement is claimed. [DeepTrace opportunities](deeptrace_opportunities.md) states what additional evidence would justify the proposed contribution.
''')
trace=[('CLI dispatch','src/agentsecbench/cli.py',250,'main; analyze builds ScanOptions then calls analyze_repository'),('Configuration','src/agentsecbench/config.py',42,'load_project_config; TOML options and adapter declarations'),('Repository traversal',e,112,'_iter_source_files; sorted traversal, exclusions, symlink rejection'),('Candidate matching',e,152,'_scan_text; lexical rules plus Python dynamic-call AST filter'),('Operation rules','src/agentsecbench/scanner/rules.py',37,'RULES; predefined categories and operation/framework patterns'),('Finding identity',e,215,'_finding_id and _finding_fingerprint; location identity vs evidence baseline'),('Analysis orchestration',e,250,'analyze_repository; read files, findings, graph build, validation and exports'),('Python slice',a,89,'analyze_python; AST call/scope, latest assignments, name backtrace and guards'),('TS/JS slice',a,250,'analyze_typescript; bounded lexical function and definition recovery'),('Framework normalization','src/agentsecbench/frameworks.py',104,'detect_python_frameworks; TypeScript counterpart at 144'),('Python project index',p,125,'build_python_project_index; direct imports and reverse callsites'),('Python propagation',p,230,'expand_interprocedural_sources; bounded incoming argument propagation'),('TS project index',ts,171,'build_typescript_project_index; lexical ES/CommonJS resolution'),('TS propagation',ts,244,'expand_typescript_sources; bounded incoming named-function propagation'),('Graph construction',b,58,'build_graph; typed records, provenance, default boundary/effect, views'),('Project graph orchestration',b,190,'build_graphs; indexes once per run then candidate builders'),('Structural validation','src/agentsecbench/graph/validation.py',15,'validate_graphs; one-to-one IDs, evidence hashes, endpoints and views'),('HTML export','src/agentsecbench/report/renderer.py',65,'build_report; compact graph report and manifest'),('Baseline policy','src/agentsecbench/policy.py',133,'evaluate_policy; current fingerprints compared with saved findings')]
write('architecture.md',f'''
# Architecture and implementation trace

## Identity and version boundary

Official identity is established by the paper's artifact link and the repository's reciprocal citation, not by a name search. Commit `{sha}` is fixed in every source link below. The latest commit only adds citation metadata; public code and paper scripts coexist in that same tree. Their dates alone do not establish algorithm equivalence.

The experiments distinguish **paper pipeline v2_5** from **public product 0.2.0**. Neither was patched. `results/paper/` and `results/product/` are separate. In particular, do not extrapolate a product regression to the paper's claimed behavior.

## Public analyzer: entry point to outputs

| Step | Source and function | Behavior verified in source |
|---|---|---|
'''+ '\n'.join(f'| {label} | {ref(path,line)} | {behavior} |' for label,path,line,behavior in trace)+f'''

The repository directory is the input. Include/exclude patterns restrict files; the CLI does not require a build or dependency install. Supported candidate-scanning extensions are `.c .cc .cpp .cs .go .java .js .jsx .kt .kts .mjs .php .py .rb .rs .scala .sh .swift .ts .tsx`. These are not equally supported semantic languages. Dependency extraction dispatches to Python AST or JS/JSX/TS/TSX lexical code; other extensions get an unsupported-language evidence record. `.mjs` is included by the scanner and TS project index but omitted from `analyze_source`'s local-analysis dispatch, an inconsistency verified in {ref(a,322)}.

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

{ref('scripts/run_security_adg_pipeline.py',20)} orchestrates scanner, generator, validator, showcase and corpus reports. We invoked its stages explicitly to preserve line-level granularity. The wrapper's scanner command otherwise defaults to symbol aggregation, whereas upstream comments recommend line-level matching before dataflow analysis.

{ref('scripts/static_scan.py',240)} reads source blobs from a Git archive at each manifest commit; it never imports targets. {ref('scripts/generate_security_adg_v2.py',79)} loads relevant frozen blobs, calls `make_graph`, runs legacy dependency analysis and replaces heuristic source/guard nodes using `replace_heuristics` at line 24. In `v2_5`, parameter precedence, overwrite handling, intrinsic-source-operation exclusion and framework normalization are enabled. {ref('scripts/security_adg_dataflow.py',151)} implements Python analysis, with the overwrite-sensitive branch at line 282; TypeScript starts at line 393 and collects multiline calls at line 375. The product and paper algorithms are similar but not identical.

The legacy pipeline does not invoke the public project index or cross-file expansion. Its graph provenance includes a commit and split; public graph provenance includes scan_root and evidence fingerprint but does not itself record repository commit. Our outer manifests provide that missing run provenance.

## Verification, resources and incrementality

Evidence SHA256 checks verify that a matched source line agrees with the finding. They do not verify dependency causality, reachability, authorization or runtime effects. Structural validation checks record shape and linkage, not semantic completeness. We separately checked graph acyclicity because the product validator does not.

The analyzer needs only CPU, memory, Python and local source. No target runtime, LLM call or GPU is used in these extraction paths. Initial end-to-end peaks were about 33–80 MiB; see repository comparison for graph-stage timing and memory scopes. The initial demo and 36 product tests pass; additional legacy, CLI and cross-file tests pass with separate logs.

Each `analyze_repository` invocation traverses source files and rebuilds project indexes and graphs. Its source-text dictionary is a within-run cache, not a persistent incremental dependency store. Baseline/suppression policy stores finding identities and supports CI filtering, but scans still rebuild the analysis. No persistent graph invalidation or edit-history input is used by these inspected entry points. This is a positive code-path observation, not an inference solely from missing documentation.

Outputs include findings JSONL, graph JSONL, graph summary JSON, framework coverage, structural validation JSON, SARIF, HTML report and optional policy reports. The paper showcase also exports typed SVGs and layout JSON. No GraphML or DOT exporter was found in the executed paths; the analysis scripts here preserve JSON and export SVG separately.
''')
# Measurements and repository-specific interpretation.
table=[]
for x in rows:
 timing=load('graph-timing/'+x['repository']+'/graph-timing.json');functions=idx[x['repository']]['python_functions']+idx[x['repository']]['typescript_functions'];finding=lines('product/'+x['repository']+'/findings.jsonl');symbols=len({(f['path'],f['symbol']) for f in finding})
 table.append(f"| {x['repository']} | {x['files_scanned']} | {functions} | {symbols} | {x['product_candidates']} | {x['product_nodes']} / {x['product_edges']} | {x['wall_seconds']:.3f} | {timing['graph_construction_seconds']:.3f} | {x['peak_rss_bytes']/2**20:.1f} |")
write('repository_comparison.md','''
# Repository comparison

Every real repository is named in upstream `experiments/security_adg_v2_draft.json`. These are current pinned commits, not the unavailable original frozen corpus revisions. No target dependencies or target programs were run. The public analyzer scanned entire directories under its default exclusions, including tests/examples and source files in `.github`.

## Exact sources

'''+ '\n'.join(f"- [{x['url']}]({x['url']}/tree/{x['commit']}): `{x['commit']}`" for x in pins['targets'])+'''

`html-anything` is a TypeScript/Next application and CLI, `mini-swe-agent` is a modular Python agent with model/environment interfaces, and `magentic-ui` combines Python orchestration/backend/sandbox/browser code with a frontend. An additional three-file TypeScript fixture explicitly covers authorization/configuration; these capabilities are not assumed merely from a repository name.

## Public product measurements

| Repository | Scanned source files | Indexed functions | Candidate symbol records | Graphs | Nodes / edges | Full run seconds | Graph stage seconds | Initial peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

Function counts are the analyzer's index entries, not an independent exhaustive function census. Candidate symbol records count distinct (file, nearest-symbol) pairs, including module/class placeholders; this is an operational approximation of relevant functions. Node/edge totals count candidate-local instances, including repeated program symbols and default context nodes. They are not counts of unique repository entities.

Full-run timing includes scanning, graph building, validation, report and SARIF serialization. Graph-stage measurements are a separate instrumented run around `build_graphs`, including both project indexes. Do not add these stage times to the initial run. Process peak RSS includes imports and accumulated scanner/graph state, not graph-only allocations. These single observations do not establish scalability trends or statistically meaningful performance rankings.

## Paper versus public results

| Repository | Candidates, both versions | Public / paper graphs with source paths | Public / paper graphs with guard candidates | Candidate file coverage |
|---|---:|---:|---:|---:|
'''+ '\n'.join(f"| {x['repository']} | {x['product_candidates']} | {x['product_dependency_graphs']} / {x['paper_dependency_graphs']} | {x['product_guard_graphs']} / {x['paper_guard_graphs']} | {x['candidate_files']}/{x['files_scanned']} ({100*x['file_coverage_fraction']:.1f}%) |" for x in rows)+'''

The candidate keys (file, line, category) match across pipelines in this run. More retained source paths is not automatically more accurate: the controlled overwrite counterexample shows a public false dependency. Conversely, different guard counts can arise from different syntax handling, rather than better security reasoning. The public scans produced no framework-promoted cross-file sources. The legacy scans have no project propagation stage.

Candidate file coverage means the fraction of scanned files containing at least one matched operation, not the fraction of relevant repository semantics recovered. There is no independent repository-wide dependency gold standard here. Test-only candidates, regex false matches and omitted true operations prevent interpreting these counts as vulnerability prevalence.

## Category counts

'''+ '\n\n'.join('**'+x['repository']+'**: '+', '.join(f'{k}: {v}' for k,v in x['operation_categories'].items())+'.' for x in rows)+'''

## Inspected evidence and omissions

**TypeScript process launch.** `html-anything/cli/src/agents-invoke.ts:509` contains `spawn(bin, argv, {` across multiple lines. The chosen graph has the operation, effect, owner and default boundary but no input sources. It does not explain where executable/configuration/arguments originate. A second inspected match, `cli/src/skills-loader.ts:63`, is regular-expression `.exec(raw)`, not process launch, but the lexical process rule matches it. In `scripts/guard.ts:58`, a filesystem-read candidate on `JSON.parse(readFileSync(...))` is named JSON.parse by the local operation parser; rule identity and parsed operation identity can diverge. These are candidate anchoring limitations, not validated vulnerabilities.

**Python agent environment.** `mini-swe-agent/src/minisweagent/environments/docker.py:116` retains paths to cwd and timeout, through cmd for cwd. Inspecting lines 102–113 shows `action.get("command")`, configuration fields, environment forwarding, and repeated `cmd.extend(...)` mutations. The backward slice does not recover the action-to-cmd relationship from these list mutations. The assert on `self.container_id` is emitted as a related guard through the shared receiver name `self`; this does not establish that it validates the command or proves container isolation. This is an observable mismatch between useful source context and the small emitted evidence graph, with no claim that a container boundary is broken.

**Local execution sandbox.** `magentic-ui/src/magentic_ui/sandbox/_null.py:54` retains cmd, timeout, cwd and extra_env. It does not expand `_activated_env(extra_env)` into its implementation or infer deployment permissions. The sink snippet contains only the first line of the multiline call, so the `shell=True` setting at line 56 is absent from that snippet. A monitor supplied only the compact graph may need source retrieval for a security-relevant argument. Its public graph is larger than the TypeScript sample but remains a small candidate record.

**Authorization/configuration fixture.** `results/fixtures/small-auth-app/` has `auth.ts`, `config.ts` and `app.ts`. A synthetic credential environment access and fetch request are detected. The request retains payload and a lexical guard candidate, but does not incorporate the authorization helper body or the imported settings object's definition as dependencies. There are no real tokens or production endpoints. Inspect `results/experiments/small-auth-app/` for both records.

## Artifacts

`results/product/<repository>/` contains JSONL, SARIF, report, validation and initial measurement. `results/paper/` contains the legacy three-repository extraction plus original SVG showcase and validation. `results/graph-timing/<repository>/` contains separately measured construction runs. `results/comparison.json`, `results/indexes.json`, `results/manifest.csv` and `results/repositories.json` provide structured tables and pins. Graph catalogs link every candidate, rather than silently presenting a sample as full coverage.
''')
write('graph_analysis.md',f'''
# Graph construction and semantic limits

## What graph is actually emitted?

Both implementations emit one graph per candidate operation. The product builder {ref(b,58)} starts with four nodes even when no source or guard is found: owner, operation, abstract effect and a default trust boundary. This explains why graph production can succeed without recovering a dependency. There is no complete repository graph in these outputs.

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
''')
versions=load('temporal.json')
write('temporal_analysis.md',f'''
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

Each public invocation independently analyzes both files and emits one command-operation graph. Each paper v2_5 whole-pipeline run also emits one graph per version. The sink candidate ID remains `{versions[0]['candidate_id']}` in all public versions, because its file, symbol, detector and line remain fixed.

A and B have identical node/edge JSON hashes in `results/temporal-structure.json`. They do **not** have identical complete output hashes: the project callsite count increases from two to three because `bool(command)` adds a call. Scan roots also differ. That metadata difference does not identify the predicate body or explain its weakened authorization meaning. No edge links the sink guard to the config.py function body. A portable bundle preserving this original synthetic Git history is saved as `results/temporal-history.bundle`.

C adds a command-parameter dependency. D keeps the same dependency path and guard count, but its operation snippet and finding fingerprint change with shell=True. Thus the output preserves some argument evidence when it is on the matched line; it does not encode the causal history that gave that argument its significance. We do not claim C and D are indistinguishable.

## Baselines are a real existing capability

We froze A's findings with the product CLI's baseline feature. Scanning B against that baseline reports **0 new, 1 existing** candidate. Scanning D reports **1 new, 0 existing**. Files are `results/baseline-B/policy.json` and `results/baseline-D/policy.json`. This demonstrates some cross-run comparison support and prevents the overstatement that the tool has no concept of historical findings.

The saved baseline stores candidate fingerprints. It does not store the security dependency graph history, validity intervals, edits introducing facts, or an explanation of how the earlier helper change affects later sink behavior. Each scan rebuilds source and project indexes. Inspect {ref(e,228)} and {ref('src/agentsecbench/policy.py',133)}.

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
''')
# Budget table by representation and scope.
evidence=load('budget-evidence.json')
counts='\n'.join(f"| {x['case']} | {x['whole_graph_json_tokens']} | {x['compact_atom_tokens']} |" for x in evidence)
pooled=[]
for budget in [512,1024,2048,4096]:
 vals=[]
 for method in ['all_truncated','nearest','shortest_paths','security_endpoints','random','text_summary']:
  xs=[x for x in budgets if x['case']=='pooled-six' and x['budget']==budget and x['method']==method];vals.append(f'{100*statistics.mean(x["atom_fraction"] for x in xs):.1f}%')
 pooled.append('| '+str(budget)+' | '+' | '.join(vals)+' |')
write('selection_analysis.md','''
# Context-budgeted evidence selection

## Estimator and evidence contract

Token estimate is **ceil(number of Unicode characters / 4)** over the final serialized evidence string, including line separators. It is an explicitly rough English/code approximation, not tiktoken or any model-specific token count. JSON punctuation and source language can make actual counts differ. Budgets exclude monitor instructions, current action and model response allowance.

For each of six graph samples, evidence atoms are: one complete compact JSON node, one complete compact JSON edge, or one complete JSON dependency-path list. Shared graph metadata/provenance/limitations are excluded from the atom payload; the table separately measures the complete compact graph JSON with metadata. This is a study of selecting existing extracted evidence, not retrieving omitted source code. The pooled case is a disjoint evidence pool of those same six operations, without invented links among them.

| Sample | Whole compact graph estimated tokens | All evidence atoms estimated tokens |
|---|---:|---:|
'''+counts+'''

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
'''+ '\n'.join(pooled)+'''

These are descriptive observations for a hand-chosen pool, with no significance test. Unweighted atom count favors cheap edges over long source nodes. Random can beat a seemingly meaningful heuristic on that metric without being better for a monitor. The greedy methods skip oversized items while literal truncation stops, another intentional baseline difference to consider when interpreting the scores.

## Independent relevance checks and limitations

The authored challenge cases give limited independently understandable facts: a constant-overwritten parameter is not a source; the copied-local cross-file path and configuration getter flow exist in source; the early-return check constrains execution. Extraction misses or misrepresents these before any selector runs. Their results are in `graph_analysis.md`. We did not produce independent expert relevance labels for every atom of the real repositories. Therefore the experiment does not answer which selector preserves the evidence a safety monitor actually needs.

A follow-up should add source spans and edit history, independently label the minimal evidence needed to recognize a security-assumption violation, and evaluate a fixed monitor at matched false-positive rates and real tokenizer budgets. Evaluate both extraction recall and conditional selection recall, with an oracle evidence ceiling. Until then, a novelty claim based merely on context-budget packing is unsupported by these results.
''')
write('deeptrace_opportunities.md',f'''
# DeepTrace opportunities: ranked and conditional

## Recommended research question

**Can an online index of security assumptions and their invalidating edits help a fixed safety monitor recognize a current action's dependence on earlier changes, under a fixed evidence budget?**

This targets a distinction our experiments expose: current candidate graphs can retain a guard call while omitting the changed predicate implementation and the edit that altered its meaning. It asks for more than concatenating static graphs or handing them to an LLM. It remains a hypothesis, not an established novel contribution.

## 1. Security-assumption invalidation across edits — strongest conceptual direction

**Observed limitation:** A→B changes the imported authorization predicate, but emitted sink nodes/edges remain identical; baseline policy reports the candidate as existing. C/D add argument/shell behavior without any reference to B's earlier modification. Evidence: `results/temporal-structure.json`, all four saved source trees, `results/baseline-B/policy.json`, {ref(a,89)}, {ref(p,230)}.

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

**Observed limitation:** each public scan reloads files, rebuilds project indexes and regenerates candidate graphs; baseline classification occurs after extraction. A helper-only change can matter even when sink finding hashes do not change. Evidence: {ref(e,250)}, {ref(b,190)}, `results/graph-timing/` and the temporal baseline outputs.

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

**Observed limitation:** static relation statuses are explicitly candidates; SHA256 checks verify text consistency only. Dynamic getattr dispatch produces no process candidate in the authored fixture. We did not execute it or validate any real runtime flow. Evidence: `results/challenge-cases.json`, {ref(b,45)}, {ref(a,89)}.

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
''')
# Machine-readable failures and bibliography preserve the boundary between successes and blockers.
(R/'failures.json').write_text(json.dumps([
 {'stage':'container availability','outcome':'Docker daemon unavailable; used tested macOS Seatbelt instead'},
 {'stage':'initial sandbox','outcome':'Python realpath required /opt ancestor metadata; allowed /opt literal without exposing user home'},
 {'stage':'first product test run','outcome':'31 temporary-directory read errors out of 36 tests; TMPDIR moved under research results; subsequent 36 passed','log':'upstream-tests.log'},
 {'stage':'legacy validation','outcome':'all_corpus invocation rejected actual development-tagged rows; rerun expected-split development valid','log':'paper/validation-all-corpus-failure.log'},
 {'stage':'baseline CLI','outcome':'initial --findings argument invalid; changed to positional findings input; final B/D policy files exist'},
 {'stage':'published corpus reproduction','outcome':'Original dataset/corpus_manifest.csv and frozen source trees absent in public checkout; original corpus metrics not reproduced'},
 {'stage':'monitor evaluation','outcome':'Not run; no detection, attack success, precision or recall claims'},
],indent=2))
(R/'sources/bibliography.json').write_text(json.dumps({'checked_date_local':'2026-10-21','primary_sources':[
 {'url':'https://arxiv.org/html/2610.03014v1','role':'paper method sections 3.2–3.5; limitations 5.3; availability and appendices'},
 {'url':pins['analyzer']['url'],'commit':sha,'role':'primary implementation and tests'},
 {'url':'https://arxiv.org/html/2604.15384v2','role':'monitor shallow-tracing motivation'},
 {'url':'https://arxiv.org/abs/2607.01640','role':'framework-aware graph-analysis overlap'},
 {'url':'https://arxiv.org/abs/2602.22724','role':'temporal causal agent-defense overlap'},
 {'url':'https://arxiv.org/abs/2603.10749','role':'runtime causal attribution overlap'},
 {'url':'https://arxiv.org/abs/2310.05736','role':'budget compression overlap'},
 {'url':'https://arxiv.org/abs/2403.12968','role':'compression overlap'},
 {'url':'https://arxiv.org/abs/2504.18529','role':'modular taint checking overlap'},
 {'url':'https://fbinfer.com/docs/1.1.0/steps-for-ci/','role':'incremental static-analysis prior art'},
]},indent=2))
print('Wrote seven reports, failures and bibliography')

with (ROOT/'selection_analysis.md').open('a') as f:
 f.write("""
## Source-grounded relevance check on three authored operations

A separate small reference inventory was written from the fixture source, after fixing the selection methods. It labels concrete static facts, not vulnerabilities: the command/tool/helper chain, the exact authorization predicate and imported settings, and a constant overwrite. This is analyst-authored and not blind expert annotation. Complete supporting atoms are mapped to each reference fact; missing facts have an empty support set. Generic boundary/effect nodes do not count as the exact authorization predicate.

| Operation | Source-reference facts | Facts available in product evidence | Ceiling for any selection over that evidence |
|---|---:|---:|---:|
| Direct cross-file MCP command | 3 | 3 | 100% |
| TypeScript authorization/configuration request | 6 | 2 | 33.3% |
| Constant-overwritten process parameter | 2 | 1 | 50% |

At each requested budget, all five full-JSON selection methods preserve all *available* reference facts in these three small cases: respectively 3/3, 2/6 and 1/2. Random uses the same 20 recorded seeds. Thus these operations reveal an extraction ceiling rather than a relevance-selection advantage. Text summaries have the same coarse support-ID mapping but are not credited as semantically equivalent, because abbreviating the sink removes argument details. The small inventory does not establish repository-wide recall. Full labels, budgets and seeds are in `results/relevance-reference.json` and `results/relevance-results.json`; `scripts/score_relevance.py` reproduces the scores.
""")
