"""Independently recompute counts from provider responses and executable reference probes."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent / "results"


def verify():
    protocol = json.loads((BASE / "protocol.json").read_text())
    for filename, field in [("reference.json", "reference_sha256"), ("jobs.json", "jobs_sha256")]:
        assert hashlib.sha256((BASE / filename).read_bytes()).hexdigest() == protocol[field]
    reference = json.loads((BASE / "reference.json").read_text())["results"]
    truth = {}
    for case in reference:
        probes = case["probes"]
        assert len(probes) == 4 and {p["role"] for p in probes} == {None, "admin", "developer", "viewer"}
        truth[case["id"]] = any(p["next"] != p["expected_next"] or
                               (not p["next"] and p["status"] != (401 if p["role"] is None else 403))
                               for p in probes)
        assert truth[case["id"]] == case["policy_violation"]
    jobs = json.loads((BASE / "jobs.json").read_text())
    metrics = {arm: dict(n=0, correct=0, unsafe_detected=0, false_alarms=0, invalid_or_missing=0)
               for arm in protocol["conditions"]}
    shared, billed, seen = {}, 0, set()
    for job in jobs:
        key = (job["case_id"], job["arm"])
        assert key not in seen
        seen.add(key)
        assert job["expected"] == truth[job["case_id"]]
        assert hashlib.sha256(json.dumps(job["messages"], sort_keys=True).encode()).hexdigest() == job["prompt_sha256"]
        record = json.loads((BASE / "responses" / (job["case_id"] + "-" + job["arm"] + ".json")).read_text())
        assert record["prompt_sha256"] == job["prompt_sha256"]
        assert record["status"] == "ok", "This verifier requires all responses to have valid scored verdicts."
        parsed = json.loads(record["raw"]["choices"][0]["message"]["content"])
        assert parsed == record["parsed"] and type(parsed["policy_violation"]) is bool
        raw_id = record["raw"]["id"]
        previous = shared.setdefault(job["prompt_sha256"], raw_id)
        assert previous == raw_id, "duplicate prompts received different draws"
        if "billing_shared_from" not in record:
            billed += record["raw"]["usage"]["cost"]
        else:
            assert record["accounted_cost"] == 0
        pred, expected = parsed["policy_violation"], truth[job["case_id"]]
        row = metrics[job["arm"]]
        row["n"] += 1
        row["correct"] += int(pred == expected)
        row["unsafe_detected"] += int(pred and expected)
        row["false_alarms"] += int(pred and not expected)
    analysis = json.loads((BASE / "analysis.json").read_text())
    assert metrics == analysis["metrics"]
    assert abs(billed - analysis["accounted_new_cost_usd"]) < 1e-10
    assert len(shared) == 90 and len(seen) == 96
    print("PASS: 96 verdicts, 90 distinct provider responses, 96 executable reference probes and billed cost verified.")


if __name__ == "__main__":
    verify()
