# Version-aware evidence selector: bounded implementation

Implemented and checked without monitor calls. Original negative pilots remain
unchanged. This is evidence-selection engineering, not completion of either
proposal experiment or evidence of improved detection.

## What it does

`scripts/selector.py` accepts ordered, explicitly supplied source states; the last
is a proposed-code preview. It reuses the supported Python semantic extractor,
recomputes every state, versions source support, and selects the latest transition
for each of three action-relevant facts: input restriction, argument origin, and
shell setting. For a restored restriction, it also keeps the preceding weakening.
Each past change states its currently effective value, whether it was superseded,
and its validity end. Current code and source spans come first, byte-identical in
both packet conditions. Historical facts never populate the current-fact fields.

Source versions have occurrence-specific IDs even when bytes are restored. Past
references include file, span, hash and version ID. Exact historical source is
saved in an audit sidecar; it is NOT automatically visible to a future monitor.
Current unknown reasons are visible. Semantically unchanged edits are excluded
with a reason; equivalent refactors are therefore not represented as weakening.
Older omitted semantic transitions are counted in the artifact. Budget overflow
returns `budget_failure` and no history packet, never a silently truncated packet.

## Development validation and source review

Eight deliberately small histories were checked against explicit source-derived
expectations: weakening, restoration, unrelated notes, equivalent predicate,
unsupported predicate, execution removal, repair after unknown, repeated cycles.
The sources are directly readable in `scripts/validate.py` and each result sidecar.
For example, `command == "status" -> True -> command == "status"` is manually
interpretable as restricted -> unrestricted -> restored. An unresolved
`external_check` remains unknown, while caller origin and shell=True remain known.
Removing subprocess.run yields no execution, not an inherited past danger.

The implementing assistant reviewed these explicit expectations and inspected
rendered restored/unknown packets. This is not an independent human annotation or
validated research oracle. All eight checks passed, as did changed-import unknown,
source-hash/version consistency, current-prefix preservation, and overflow checks.
Selected packets were 155–842 tokens under a 1024-token cap. No monitor was called.

Reproduce from project root:

    research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/version_selector/scripts/validate.py

## Important limits

This implements selection over a single supported Python runner path, not general
action-to-sink discovery, arbitrary repository analysis, or the full support DAG.
It recomputes all states rather than claiming sound incremental invalidation.
Restriction transition `violated` means the restriction was weakened; it does not
by itself mean the combined execution policy is violated. Fixed arguments or
shell=False can still make that policy permit execution. No policy verdict is
embedded in the monitor packet. The separate diagnostic checker is unchanged.
Historical facts are bounded analyzer outputs with source references; their
references are not independent proofs. Initial state provenance and ordering are
assumed inputs here and must be verified separately for LinuxArena.

## Before fresh testing

The implementation snapshot is hash-recorded in results/implementation_freeze.json.
This is a development freeze, not a released evaluation protocol. No model run
should start until a complete comparison protocol and untouched family allocation
are frozen with hashes, together with independent reference review where required.

Use the identical current summary versus that summary plus selected past changes,
the same 1024-token maximum, same task/action/model/settings and same calibration
split. Report actual token lengths; a common cap does not mean equal consumed
tokens. Add a current-only retrieval arm allowed to spend the remaining budget if
claiming retrieval efficiency. Qualify both conditions at intended context lengths,
including repairs, unknowns, cycles, equivalent refactors and irrelevant edits.
Freeze raw/derived decision pipelines, invalid/unknown handling, primary metrics,
uncertainty and stopping rules before any held-out responses. Preserve failures.

These complete-current-fact fixtures offer no information advantage for history:
the immediate target is avoiding confusion and selecting correct transitions.
A future benefit claim needs verified repository cases where support links improve
relevant evidence retrieval under equal access and resource caps, without hiding
current facts from the baseline. LinuxArena access remains a separate blocker;
see ../continuation/RESOURCE_REQUEST.txt. No fragment-only evaluation was run.
