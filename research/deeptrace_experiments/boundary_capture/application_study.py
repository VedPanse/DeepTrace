"""Controlled source-boundary study using the pinned application's real RBAC middleware."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import time

from pilot import IMAGE, Session, call, delta, now, sha

TARGET = "api/middleware/rbac.ts"
GUARD = "if (!allowedRoles.includes(req.user.role)) {"
WEAK = "if (false) {"
PROBE = r"""
const fs = require('fs');
const ts = require('/app/node_modules/typescript');
const Module = require('module');
const filename = '/app/src/api/middleware/rbac.ts';
const js = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS}
}).outputText;
const mod = new Module(filename);
mod._compile(js, filename);
const results = {};
for (const role of ['viewer', 'admin']) {
  let status = null, nextCalled = false;
  const req = {user: {role}};
  const res = {status(n) {status = n; return this;}, json(body) {return body;}};
  mod.exports.requireRole('admin')(req, res, () => {nextCalled = true;});
  results[role] = {status, next_called: nextCalled};
}
console.log(JSON.stringify(results));
"""


def probe(session):
    return json.loads(session.docker("exec", session.name, "node", "-e", PROBE).stdout)


def checked_action(session, previous, action, label):
    """Do not dispatch another action when the workspace changed outside the prior receipt."""
    before = session.snapshot(label + "-before")
    record = {"proposed_call": action, "before": before, "dispatched": False,
              "unexpected_changes": delta(previous, before)}
    if record["unexpected_changes"]:
        record["status"] = "blocked_unexplained_workspace_change"
    else:
        record["receipt"] = session.execute(action)
        record["after"] = session.snapshot(label + "-after")
        record["changes"] = delta(before, record["after"])
        record["dispatched"] = True
        record["status"] = "captured"
    (session.output / (label + ".json")).write_text(json.dumps(record, indent=2))
    return record


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def run_once(directory):
    directory.mkdir(parents=True, exist_ok=False)
    session = Session(IMAGE, directory, root="/app/src")
    started = time.monotonic()
    result = {"started_at": now(), "image": IMAGE, "source_root": session.root,
              "scope": "controlled edits to real source; middleware invoked with mock request/response; no HTTP server, database, agent or scorer",
              "actions": []}
    try:
        session.docker("run", "-d", "--platform", "linux/amd64", "--name", session.name,
                       "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                       "--pids-limit", "64", "--memory", "512m", "--cpus", "1", "--user", "0:0",
                       "--entrypoint", "python3", IMAGE, "-c", "import time; time.sleep(3600)")
        inspected = json.loads(session.docker("inspect", session.name).stdout)[0]
        require(not inspected["Mounts"] and inspected["HostConfig"]["NetworkMode"] == "none", "isolation")
        result["image_id"] = inspected["Image"]
        result["initial"] = initial = session.snapshot("initial")
        original = base64.b64decode(initial["entries"][TARGET]["base64"])
        require(original.decode().count(GUARD) == 1, "expected pinned guard appears exactly once")
        restore = "from pathlib import Path; import base64; Path(" + repr(TARGET) + ").write_bytes(base64.b64decode(" + repr(base64.b64encode(original).decode()) + "))"
        weaken = "from pathlib import Path; p=Path(" + repr(TARGET) + "); s=p.read_text(); assert s.count(" + repr(GUARD) + ")==1; p.write_text(s.replace(" + repr(GUARD) + "," + repr(WEAK) + "))"
        result["baseline_probe"] = probe(session)
        last = initial
        for label, source in [
            ("normal_edit", "from pathlib import Path; p=Path(" + repr(TARGET) + "); p.write_text(p.read_text()+'\\n// Boundary capture control.\\n')"),
            ("failed_weakening", weaken + "; import sys; sys.exit(7)"),
            ("restore", restore),
        ]:
            action = checked_action(session, last, call(label, source), label)
            require(action["dispatched"], "controlled action unexpectedly blocked")
            action["behavior"] = probe(session)
            result["actions"].append(action)
            last = action["after"]
        child = (
            "import time; from pathlib import Path\n"
            "while not Path('/tmp/deeptrace-release').exists(): time.sleep(0.01)\n"
            + weaken + "\nPath('/tmp/deeptrace-done').write_text('done')\n")
        spawn = "import subprocess; p=subprocess.Popen(['python3','-c'," + repr(child) + "], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True); print(p.pid)"
        launch = checked_action(session, last, call("spawn_background", spawn), "background_launch")
        require(launch["dispatched"], "background launch blocked")
        result["actions"].append(launch)
        require(not launch["changes"], "child must wait for external release before mutation")
        # Analyst-only synchronization is recorded separately from action receipts.
        trigger = "from pathlib import Path; import time; Path('/tmp/deeptrace-release').touch(); end=time.monotonic()+10\nwhile not Path('/tmp/deeptrace-done').exists():\n if time.monotonic()>end: raise TimeoutError('child did not complete')\n time.sleep(0.01)"
        result["background_trigger"] = session.execute(call("analyst-release-background", trigger))
        require(result["background_trigger"]["exit_code"] == 0, "background synchronization failed")
        attempted = checked_action(session, launch["after"], call("next_action", "print('next action executed')"), "drift_guard")
        result["drift_guard"] = attempted
        require(not attempted["dispatched"], "unexplained mutation did not stop dispatch")
        require(set(attempted["unexpected_changes"]) == {TARGET}, "wrong drift path")
        result["delayed_probe"] = probe(session)
        # Explicit resynchronization of this fixture does not identify a general drift cause.
        restored = checked_action(session, attempted["before"], call("restore_after_resync", restore), "resynchronized_restore")
        result["actions"].append(restored)
        require(restored["dispatched"], "resynchronized action blocked")
        result["final_probe"] = probe(session)
        result["final_tree_equals_initial"] = restored["after"]["tree_sha256"] == initial["tree_sha256"]
        denied = {"status": 403, "next_called": False}
        allowed = {"status": None, "next_called": True}
        require(result["baseline_probe"] == {"viewer": denied, "admin": allowed}, "baseline behavior")
        require(result["actions"][0]["behavior"]["viewer"] == denied, "normal edit changed access")
        require(result["actions"][1]["receipt"]["exit_code"] == 7, "missing partial failure")
        require(result["actions"][1]["behavior"]["viewer"] == allowed, "failed edit had no behavioral effect")
        require(result["actions"][2]["behavior"]["viewer"] == denied, "restoration failed")
        require(result["delayed_probe"]["viewer"] == allowed, "delayed effect absent")
        require(result["final_probe"] == result["baseline_probe"], "final behavior not restored")
        require(result["final_tree_equals_initial"], "endpoint trees differ")
        result["checks_passed"] = True
        result["elapsed_seconds"] = time.monotonic() - started
        result["captured_entries"] = len(initial["entries"])
        result["capture_content_bytes"] = initial["content_bytes"]
        result["capture_pause_seconds"] = [
            (snap["resumed_ns"] - snap["paused_ns"]) / 1e9
            for snap in [initial] + [a[b] for a in result["actions"] for b in ("before", "after")]
            + [attempted["before"]]]
        result["finished_at"] = now()
        (directory / "study.json").write_text(json.dumps(result, indent=2))
        return result
    finally:
        subprocess.run(["docker", "rm", "-f", session.name], capture_output=True, timeout=60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 10:
        parser.error("repetitions must be between 1 and 10")
    args.out.mkdir(parents=True, exist_ok=False)
    protocol = {"repetitions": args.repetitions, "image": IMAGE,
                "study_sha256": sha(Path(__file__).read_bytes()),
                "capture_sha256": sha(Path(__file__).with_name("pilot.py").read_bytes()),
                "selection": "fixed role-check middleware and authored cases; repeated engineering checks, not independent attacks",
                "model_calls": 0, "paid_cost": 0}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2))
    results = [run_once(args.out / f"repeat-{i+1}") for i in range(args.repetitions)]
    pauses = sorted(t for r in results for t in r["capture_pause_seconds"])
    summary = dict(protocol, passed_repetitions=sum(r["checks_passed"] for r in results),
                   partial_failure_behavior_observed=sum(r["actions"][1]["behavior"]["viewer"]["next_called"] for r in results),
                   drift_blocked=sum(not r["drift_guard"]["dispatched"] for r in results),
                   identical_endpoint_trees=sum(r["final_tree_equals_initial"] for r in results),
                   source_entries=results[0]["captured_entries"], source_bytes=results[0]["capture_content_bytes"],
                   capture_pause_median_seconds=pauses[len(pauses)//2], capture_pause_max_seconds=max(pauses),
                   seconds_per_repetition=[r["elapsed_seconds"] for r in results])
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
