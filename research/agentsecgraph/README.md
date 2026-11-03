# AgentSecGraph reproduction and DeepTrace research

Research date: October 21, 2026 (America/Los_Angeles). This is a code inspection and exploratory reproduction, not an attack-detection evaluation. No DeepTrace implementation or model training was performed.

## Executive findings

The paper's **Data and Artifact Availability** section explicitly links [A1LinLin1/AgentSecBench](https://github.com/A1LinLin1/AgentSecBench), which reciprocally cites the paper in its README and package metadata. The verified checkout is `e27f83d631c91b80fb55a2f1d9e4112f1a080ceb` (public package 0.2.0, Apache-2.0). It contains two materially different implementations: the paper-oriented `scripts/` pipeline in mode `v2_5`, and the installable `src/agentsecbench/` product. This study ran both without editing either.

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
