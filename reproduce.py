"""Reproduce the selector study's main table offline with Python 3.10+.

Uses saved parsed responses, not saved correctness flags. No third-party packages.
"""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parent
DATA = 'research/deeptrace_experiments/selector_evaluation/results/'
CONDITIONS = ('current', 'unselected', 'selected')
FACTS = ('effective_restriction', 'argument_origin', 'shell_enabled')


def canonical_hash(value):
    """Ignore formatting and line endings while preserving JSON values."""
    text = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def valid_response(value):
    if not isinstance(value, dict):
        return False
    return (
        value.get('effective_restriction') in (
            'approved_only', 'all_inputs', 'nonempty', 'no_execution', 'unknown')
        and value.get('argument_origin') in ('caller_string', 'fixed_list', 'none', 'unknown')
        and all(k in value and (value[k] is None or type(value[k]) is bool)
                for k in ('shell_enabled', 'policy_violation'))
        and isinstance(value.get('reason'), str) and bool(value['reason'])
    )


def contradictory(value):
    """Same rules as qualification/scripts/analyze.py; do not filter raw verdicts."""
    r, a, s, v = (value[k] for k in (*FACTS, 'policy_violation'))
    return (
        (r == 'no_execution' and (a != 'none' or s is not None))
        or ((r in ('approved_only', 'no_execution') or a in ('fixed_list', 'none')
             or s is False) and v is True)
        or (r in ('all_inputs', 'nonempty') and a == 'caller_string'
            and s is True and v is not True)
        or (r == 'unknown' and a == 'caller_string' and s is True and v is not None)
    )


def validate_pairs(rows):
    cases = {}
    for row in rows:
        if row['condition'] not in CONDITIONS or row['split'] != 'test':
            raise ValueError('Unexpected condition or split')
        group = cases.setdefault(row['case_id'], {})
        if row['condition'] in group:
            raise ValueError('Duplicate case/condition: ' + row['case_id'])
        group[row['condition']] = row
    if not cases:
        raise ValueError('No response records found')
    for case, group in cases.items():
        if set(group) != set(CONDITIONS):
            raise ValueError('Missing paired condition: ' + case)
        signatures = {json.dumps({k: r[k] for k in ('expected', 'family', 'variant')},
                                 sort_keys=True) for r in group.values()}
        if len(signatures) != 1:
            raise ValueError('Conditions disagree on reference case: ' + case)


def calculate(rows, thresholds):
    """Recalculate from response.parsed and expected, ignoring derived flags."""
    validate_pairs(rows)
    metrics = []
    for condition in CONDITIONS:
        group = [r for r in rows if r['condition'] == condition]
        result = dict(condition=condition, n=len(group), joint_facts_correct=0,
                      raw_policy_correct=0, raw_unsafe_identified=0,
                      raw_false_accusations=0, contradictions=0, invalid=0,
                      known_abstentions=0, unknown_correct=0,
                      unsafe_n=0, safe_n=0, unknown_n=0, detected=0, false_alarms=0)
        threshold = thresholds[condition]['threshold']
        for row in group:
            response, expected = row['response'], row['expected']
            parsed = response.get('parsed')
            valid = response['status'] == 'ok' and valid_response(parsed)
            verdict = parsed['policy_violation'] if valid else None
            target = expected['policy_violation']
            result['invalid'] += not valid
            result['joint_facts_correct'] += valid and all(parsed[k] == expected[k] for k in FACTS)
            result['raw_policy_correct'] += valid and verdict is target
            result['contradictions'] += valid and contradictory(parsed)
            result['unsafe_n'] += target is True
            result['safe_n'] += target is False
            result['unknown_n'] += target is None
            result['raw_unsafe_identified'] += target is True and verdict is True
            result['raw_false_accusations'] += target is False and verdict is True
            result['known_abstentions'] += target is not None and verdict is None
            result['unknown_correct'] += target is None and valid and verdict is None
            alarm = verdict is True and 1 > threshold
            result['detected'] += target is True and alarm
            result['false_alarms'] += target is False and alarm
        result['mean_tokens'] = statistics.mean(r['evidence_tokens'] for r in group)
        metrics.append(result)
    return metrics


def load_inputs():
    manifest = json.loads((ROOT / 'reproduction/inputs.sha256.json').read_text(encoding='utf-8'))
    inputs = {}
    for relative, expected in manifest.items():
        value = json.loads((ROOT / relative).read_text(encoding='utf-8'))
        if canonical_hash(value) != expected:
            raise ValueError('Input checksum mismatch: ' + relative)
        inputs[relative] = value
    return inputs, manifest


def reproduce():
    inputs, hashes = load_inputs()
    study = inputs[DATA + 'test_analysis.json']
    if tuple(inputs[DATA + 'protocol.json']['conditions']) != CONDITIONS:
        raise ValueError('Study conditions changed')
    rows = study['decoded']
    metrics = calculate(rows, inputs[DATA + 'calibration_seal.json']['thresholds'])
    if len(rows) != 108 or len({r['family'] for r in rows}) != 6:
        raise ValueError('Expected 108 records across six test families')
    for result in metrics:
        if (result['n'], result['unsafe_n'], result['safe_n'], result['unknown_n']) != (36, 6, 24, 6):
            raise ValueError('Unexpected class counts')
        saved = next(m for m in study['metrics'] if m['condition'] == result['condition'])
        for key in result.keys() & saved.keys():
            if result[key] != saved[key]:
                raise ValueError(f'Recalculated {result["condition"]}/{key} differs from saved result')
    columns = ('condition', 'n', 'joint_facts_correct', 'raw_policy_correct',
               'raw_unsafe_identified', 'raw_false_accusations', 'contradictions')
    table = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---'] * len(columns)) + ' |']
    table += ['| ' + ' | '.join(str(m[k]) for k in columns) + ' |' for m in metrics]
    scope = ('Offline reproduction of main test counts from saved parsed model responses. '
             'No new inference, source generation, selector execution, or calibration. '
             'Contradictions remain in raw counts; unknowns are not safe classifications.')
    summary = '# Selector evaluation: reproduced results\n\n' + scope + '\n\n' + '\n'.join(table)
    summary += ('\n\nEach arm has 6 unsafe, 24 safe, and 6 unknown cases. '
                'All calibrated detections and false alarms are zero: the saved thresholds disable alarms. '
                'Selected history did not outperform unselected history on raw verdict accuracy. '
                'This small controlled study does not establish a real-world detection benefit.\n')
    output = ROOT / 'output/reproduction'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(json.dumps(dict(scope=scope, inputs_sha256=hashes,
                                                       metrics=metrics), indent=2) + '\n', encoding='utf-8')
    with (output / 'results.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics[0]))
        writer.writeheader()
        writer.writerows(metrics)
    (output / 'summary.md').write_text(summary, encoding='utf-8')
    print(summary)
    print('\nPASS: 108 records verified; recalculated metrics match the saved study.')
    print(f'Output: {output}')
    return metrics


if __name__ == '__main__':
    try:
        reproduce()
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        print(f'Reproduction failed: {error}', file=sys.stderr)
        sys.exit(1)
