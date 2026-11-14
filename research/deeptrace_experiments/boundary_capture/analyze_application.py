"""Recheck application-study archives and derive the presentation table offline."""
import base64
import json
from pathlib import Path
import sys

from application_study import GUARD, TARGET, WEAK, require
from pilot import delta, manifest


def source(snapshot):
    return base64.b64decode(snapshot["entries"][TARGET]["base64"]).decode()


def analyze(directory):
    directory = Path(directory)
    protocol = json.loads((directory / "protocol.json").read_text())
    rows = []
    archives = 0
    for index in range(protocol["repetitions"]):
        folder = directory / f"repeat-{index+1}"
        result = json.loads((folder / "study.json").read_text())
        actions = result["actions"]
        require(len(actions) == 5, "expected five dispatched calls")
        snapshots = [result["initial"], result["drift_guard"]["before"]]
        snapshots += [action[boundary] for action in actions for boundary in ("before", "after")]
        for snapshot in snapshots:
            name = snapshot["archive"]
            require(Path(name).name == name, "invalid archive path")
            derived = manifest((folder / name).read_bytes())
            require(all(snapshot[k] == v for k, v in derived.items()), "archive differs from receipt")
            archives += 1
        previous = result["initial"]
        for i, action in enumerate(actions):
            if i == 4:
                previous = result["drift_guard"]["before"]
            require(action["before"]["tree_sha256"] == previous["tree_sha256"], "unexpected action sequence")
            require(action["changes"] == delta(action["before"], action["after"]), "incorrect recorded change")
            r = action["receipt"]
            require(r["call_id"] == action["proposed_call"]["id"], "call identity mismatch")
            require(action["before"]["resumed_ns"] <= r["start_ns"] <= r["end_ns"] <= action["after"]["paused_ns"], "invalid timing")
            previous = action["after"]
        require(actions[1]["receipt"]["exit_code"] == 7, "partial failure not observed")
        require(all(a["receipt"]["exit_code"] == 0 for i, a in enumerate(actions) if i != 1), "unexpected action failure")
        require(GUARD in source(result["initial"]), "baseline guard missing")
        require(GUARD not in source(actions[1]["after"]) and WEAK in source(actions[1]["after"]), "weakening absent")
        require(source(actions[2]["after"]) == source(result["initial"]), "first restoration differs")
        guard = result["drift_guard"]
        require(not guard["dispatched"] and "receipt" not in guard, "blocked call was dispatched")
        require(guard["unexpected_changes"] == delta(actions[3]["after"], guard["before"]), "drift mismatch")
        require(set(guard["unexpected_changes"]) == {TARGET}, "wrong delayed change")
        require(not actions[3]["changes"], "background launcher changed source immediately")
        require(WEAK in source(guard["before"]), "delayed guard weakening absent")
        require(previous["tree_sha256"] == result["initial"]["tree_sha256"], "endpoint mismatch")
        denied = {"status": 403, "next_called": False}
        allowed = {"status": None, "next_called": True}
        require(result["baseline_probe"] == result["final_probe"] == {"viewer": denied, "admin": allowed}, "baseline/final behavior mismatch")
        require(actions[0]["behavior"]["viewer"] == actions[2]["behavior"]["viewer"] == denied, "control behavior mismatch")
        require(actions[1]["behavior"]["viewer"] == result["delayed_probe"]["viewer"] == allowed, "weakening behavior mismatch")
        rows.append({"repetition": index+1, "failed_write_persisted": True,
                     "temporary_role_check_bypass_observed": True,
                     "background_drift_blocked": True, "final_tree_equals_initial": True})
    return {"verified_archives": archives, "rows": rows,
            "interpretation": "Repeated authored engineering cases, not independent attacks or monitor accuracy."}


if __name__ == "__main__":
    print(json.dumps(analyze(sys.argv[1]), indent=2))
