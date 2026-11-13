# Frozen three-condition selector evaluation

## Outcome

No demonstrated benefit from the version-aware selector. It preserved correct
current-fact interpretation, but did not outperform unselected history on verdict
accuracy. The monitor continues to misapply the narrow policy even when its facts
are correct. This is a small controlled evaluation, not LinuxArena or completion
of H1/H2. Previous negative results remain unchanged.

Test: six whole source/history families, six variants each, 36 cases per arm:
six unsafe, 24 safe, six correctly unknown. Calibration: four separate families,
24 cases per arm. All 180 logical prompts were unique, with zero exact overlap
with earlier qualification/comparison prompts. Fresh source variants remain close
relatives of the same synthetic policy; no new vulnerability-domain claim.

| Raw test outcome | Current | Unselected history | Selected history |
|---|---:|---:|---:|
| Joint facts correct | 36/36 | 36/36 | 36/36 |
| Policy verdict correct, including correct unknowns | 20/36 | 26/36 | 24/36 |
| Unsafe identified before thresholding | 6/6 | 4/6 | 6/6 |
| Safe cases falsely accused before thresholding | 13/24 | 5/24 | 9/24 |
| Contradictory responses | 13 | 7 | 9 |
| Null verdicts, including appropriate unknowns | 9 | 11 | 9 |
| Abstentions on known-answer cases | 3 | 5 | 3 |
| Correct unknown verdicts | 6/6 | 6/6 | 6/6 |
| Invalid responses | 0 | 0 | 0 |
| Raw safe alarm-or-abstention burden | 16/24 | 8/24 | 12/24 |
| Mean evidence tokens | 134 | 737 | 513 |
| Mean response latency, seconds | 1.18 | 1.11 | 1.24 |

Rows overlap; do not sum them. Contradictions were reported, not silently removed
from raw primary decisions. Unknowns are not safe classifications.

Selected minus unselected policy accuracy: -5.6 percentage points; whole-family
bootstrap interval [-19.4, +11.1]. Selected minus current: +11.1 points, interval
[-2.8, +25.0]. Six related families and one draw per prompt give weak uncertainty
estimates; these do not establish an improvement, equivalence or general harm.
Perfect fact scores on this finite set are not population reliability guarantees.

## Calibration failed to yield a useful alarm system

The frozen rule allowed at most floor(.05*n_safe) calibration false alarms.
With 16 safe calibration cases this means zero, an intentionally disclosed coarse
small-sample constraint. Raw calibration false accusations were 9, 4 and 6.
The only scores are binary verdicts, so all three thresholds became 1 and the rule
score>threshold disabled all alarms. No threshold was adjusted on test outcomes.

Consequently all calibrated systems had 0/6 detection and 0/24 test false alarms.
The descriptive Wilson intervals are [0, .390] and [0, .138], respectively.
Zero test alarms here is a disabled detector, not a successful or empirically
matched useful false-positive operating point. Raw false-accusation rates were
54.2%, 20.8%, and 37.5%, respectively. Both raw and calibrated results are saved.

## Separate checker diagnosis

The deterministic experimental policy applied to model-reported facts returned
the correct result on 36/36 in every arm, including six required unknowns.
It is a separate diagnostic pipeline and does not repair the original scores.
The evidence did not produce current-state confusion on this set; verdict
generation remains the failure. The checker applies only to this precisely
specified rule, not general LinuxArena sabotage.

## Evidence and provenance

Protocol frozen before preparation and inference. Preparation initially failed on
a restricted-translator expression (`len(command)>0`). Before any model calls it
was changed to a supported equivalent (`bool(command)`); the initial protocol and
explicit amendment are retained. Runner, analyzer, extractor and selector hashes
were sealed before calibration. Thresholds were sealed before test release.

Same Nano model/system/settings, legitimate task and proposed-state action across
arms. The current summary is identical in all three. Common evidence cap: 2048
tokens; actual maximum: 947. No truncation or over-budget exclusions. This is
equal-cap, not equal consumed-token evaluation. Unselected history includes all
earlier version facts and source references; selected history includes selected
transitions with explicit temporal labels. Both already distinguish past from
current, so this is not a comparison against deliberately misleading raw text.
The comparison bundles selection and representation; it does not isolate their
individual causal contributions. Historical full source remains in audit sidecars
for both arms; references do not imply the monitor saw that full source.

Weakened, restored, equivalent-refactor, irrelevant-edit, unsupported-analysis and
removed-execution histories occur in both splits. All related variants stay in
their source/history family. The implementing assistant checked explicit source
expectations; symbolic results and inert concrete interpretation agreed on known
cases. Independent human review was unavailable, so these are not an independently
validated oracle. No target subprocess or recorded LinuxArena action was executed.

Complete current facts already determine this rule. History cannot supply missing
policy information here. The study tests robustness and confusion, not the proposed
retrieval benefit in large repositories. That benefit still needs verified real
cases with equal current-state access, evidence/compute caps, and a strong search
baseline. LinuxArena access was blocked at the time of this study; the subsequent
`../linuxarena_reassessment/README.md` records successful public access. No
fragment-only rerun was substituted and no real-cohort detection result is claimed.

## Reproduce and artifacts

From the project root:

    research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/selector_evaluation/scripts/checks.py
    research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/selector_evaluation/scripts/report.py test

Do not rerun preparation or calibration over frozen files. Network runner is kept
for reproducibility, not an instruction to repeat inference. One saved draw per
exact prompt; no cached old responses, response repairs or favorable resampling.

Results include protocol and amendment, manifest, source cases/selection artifacts,
exact prompts, original provider responses, calibration seal, test release,
raw/derived metrics, source-expectation audit and integrity checks. New study cost
was $0.0125825; accounted project total $0.96991277, below the existing $3 cap.
Provider routing OpenAI-only with data collection denied; no ZDR or immutable-model
weight guarantee. No credentials are included in exported artifacts.

No further tuning or inference was performed after this outcome. All these cases
are now spent diagnostic data.
