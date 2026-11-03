# Repository comparison

Every real repository is named in upstream `experiments/security_adg_v2_draft.json`. These are current pinned commits, not the unavailable original frozen corpus revisions. No target dependencies or target programs were run. The public analyzer scanned entire directories under its default exclusions, including tests/examples and source files in `.github`.

## Exact sources

- [https://github.com/nexu-io/html-anything](https://github.com/nexu-io/html-anything/tree/975fb3bcb98f1777781fb4c738902d36e32c8c46): `975fb3bcb98f1777781fb4c738902d36e32c8c46`
- [https://github.com/SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent/tree/04d809ceab9df28f9adaed044884180159172930): `04d809ceab9df28f9adaed044884180159172930`
- [https://github.com/microsoft/magentic-ui](https://github.com/microsoft/magentic-ui/tree/d3c9d13c39288257286a66daabf7c5b5fb72ee69): `d3c9d13c39288257286a66daabf7c5b5fb72ee69`

`html-anything` is a TypeScript/Next application and CLI, `mini-swe-agent` is a modular Python agent with model/environment interfaces, and `magentic-ui` combines Python orchestration/backend/sandbox/browser code with a frontend. An additional three-file TypeScript fixture explicitly covers authorization/configuration; these capabilities are not assumed merely from a repository name.

## Public product measurements

| Repository | Scanned source files | Indexed functions | Candidate symbol records | Graphs | Nodes / edges | Full run seconds | Graph stage seconds | Initial peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| html-anything | 127 | 408 | 74 | 130 | 576 / 490 | 0.889 | 0.396 | 33.0 |
| magentic-ui | 344 | 1889 | 183 | 256 | 1214 / 1113 | 5.559 | 3.752 | 80.5 |
| mini-swe-agent | 115 | 836 | 103 | 123 | 571 / 519 | 1.459 | 1.141 | 50.5 |

Function counts are the analyzer's index entries, not an independent exhaustive function census. Candidate symbol records count distinct (file, nearest-symbol) pairs, including module/class placeholders; this is an operational approximation of relevant functions. Node/edge totals count candidate-local instances, including repeated program symbols and default context nodes. They are not counts of unique repository entities.

Full-run timing includes scanning, graph building, validation, report and SARIF serialization. Graph-stage measurements are a separate instrumented run around `build_graphs`, including both project indexes. Do not add these stage times to the initial run. Process peak RSS includes imports and accumulated scanner/graph state, not graph-only allocations. These single observations do not establish scalability trends or statistically meaningful performance rankings.

## Paper versus public results

| Repository | Candidates, both versions | Public / paper graphs with source paths | Public / paper graphs with guard candidates | Candidate file coverage |
|---|---:|---:|---:|---:|
| html-anything | 130 | 39 / 46 | 11 / 24 | 37/127 (29.1%) |
| magentic-ui | 256 | 127 / 107 | 28 / 26 | 64/344 (18.6%) |
| mini-swe-agent | 123 | 57 / 56 | 8 / 8 | 37/115 (32.2%) |

The candidate keys (file, line, category) match across pipelines in this run. More retained source paths is not automatically more accurate: the controlled overwrite counterexample shows a public false dependency. Conversely, different guard counts can arise from different syntax handling, rather than better security reasoning. The public scans produced no framework-promoted cross-file sources. The legacy scans have no project propagation stage.

Candidate file coverage means the fraction of scanned files containing at least one matched operation, not the fraction of relevant repository semantics recovered. There is no independent repository-wide dependency gold standard here. Test-only candidates, regex false matches and omitted true operations prevent interpreting these counts as vulnerability prevalence.

## Category counts

**html-anything**: browser_control: 22, command_execution: 26, filesystem_delete: 12, filesystem_read: 23, filesystem_write: 27, network_access: 20.

**magentic-ui**: browser_control: 78, command_execution: 14, credential_access: 1, database_access: 19, external_tool_invocation: 22, filesystem_delete: 5, filesystem_read: 16, filesystem_write: 95, network_access: 6.

**mini-swe-agent**: command_execution: 30, credential_access: 35, filesystem_delete: 4, filesystem_read: 1, filesystem_write: 48, network_access: 5.

## Inspected evidence and omissions

**TypeScript process launch.** `html-anything/cli/src/agents-invoke.ts:509` contains `spawn(bin, argv, {` across multiple lines. The chosen graph has the operation, effect, owner and default boundary but no input sources. It does not explain where executable/configuration/arguments originate. A second inspected match, `cli/src/skills-loader.ts:63`, is regular-expression `.exec(raw)`, not process launch, but the lexical process rule matches it. In `scripts/guard.ts:58`, a filesystem-read candidate on `JSON.parse(readFileSync(...))` is named JSON.parse by the local operation parser; rule identity and parsed operation identity can diverge. These are candidate anchoring limitations, not validated vulnerabilities.

**Python agent environment.** `mini-swe-agent/src/minisweagent/environments/docker.py:116` retains paths to cwd and timeout, through cmd for cwd. Inspecting lines 102–113 shows `action.get("command")`, configuration fields, environment forwarding, and repeated `cmd.extend(...)` mutations. The backward slice does not recover the action-to-cmd relationship from these list mutations. The assert on `self.container_id` is emitted as a related guard through the shared receiver name `self`; this does not establish that it validates the command or proves container isolation. This is an observable mismatch between useful source context and the small emitted evidence graph, with no claim that a container boundary is broken.

**Local execution sandbox.** `magentic-ui/src/magentic_ui/sandbox/_null.py:54` retains cmd, timeout, cwd and extra_env. It does not expand `_activated_env(extra_env)` into its implementation or infer deployment permissions. The sink snippet contains only the first line of the multiline call, so the `shell=True` setting at line 56 is absent from that snippet. A monitor supplied only the compact graph may need source retrieval for a security-relevant argument. Its public graph is larger than the TypeScript sample but remains a small candidate record.

**Authorization/configuration fixture.** `results/fixtures/small-auth-app/` has `auth.ts`, `config.ts` and `app.ts`. A synthetic credential environment access and fetch request are detected. The request retains payload and a lexical guard candidate, but does not incorporate the authorization helper body or the imported settings object's definition as dependencies. There are no real tokens or production endpoints. Inspect `results/experiments/small-auth-app/` for both records.

## Artifacts

`results/product/<repository>/` contains JSONL, SARIF, report, validation and initial measurement. `results/paper/` contains the legacy three-repository extraction plus original SVG showcase and validation. `results/graph-timing/<repository>/` contains separately measured construction runs. `results/comparison.json`, `results/indexes.json`, `results/manifest.csv` and `results/repositories.json` provide structured tables and pins. Graph catalogs link every candidate, rather than silently presenting a sample as full coverage.
