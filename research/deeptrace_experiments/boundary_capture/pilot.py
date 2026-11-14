"""Controlled Docker execution boundaries; no historical attack replay or model calls.

Only /deeptrace-pilot is captured. Parallel calls have group-level boundaries,
not inferred per-call states. This is not a LinuxArena harness integration.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import time
import uuid

ROOT = "/deeptrace-pilot"
IMAGE = "linuxarena/env-auto_workflow@sha256:7566d00723aea2eae68d896695548fad7b3d746a2762547315f7e81c728bcbf1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(entries):
    return json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()


def manifest(raw, cap=32 * 1024 * 1024):
    """Read inert archive members without extracting paths onto the host."""
    if len(raw) > cap:
        raise ValueError("archive exceeds capture limit")
    entries = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("unsafe archive path")
            if str(path) in (".", ""):
                continue
            key = str(path)
            if key in entries:
                raise ValueError("duplicate archive path")
            entry = {"mode": member.mode}
            if member.isfile():
                total += member.size
                if total > cap:
                    raise ValueError("content exceeds capture limit")
                data = archive.extractfile(member).read()
                entry.update(kind="file", bytes=len(data), sha256=sha(data),
                             base64=base64.b64encode(data).decode())
            elif member.isdir():
                entry.update(kind="directory")
            elif member.issym():
                entry.update(kind="symlink", target=member.linkname)
            else:
                raise ValueError("unsupported archive member: " + key)
            entries[key] = entry
    return {"entries": entries, "tree_sha256": sha(canonical(entries)),
            "archive_sha256": sha(raw), "content_bytes": total}


def delta(before, after):
    left, right = before["entries"], after["entries"]
    return {key: {"before": left.get(key), "after": right.get(key)}
            for key in sorted(left.keys() | right.keys()) if left.get(key) != right.get(key)}


def verify(result):
    """Reject corrupted captures, missing call receipts, or broken ordering."""
    previous = None
    ids = set()
    for index, group in enumerate(result["groups"]):
        if group["index"] != index:
            raise ValueError("noncontiguous groups")
        for boundary in ("before", "after"):
            snap = group[boundary]
            if sha(canonical(snap["entries"])) != snap["tree_sha256"]:
                raise ValueError("tree hash mismatch")
            for entry in snap["entries"].values():
                if entry["kind"] == "file":
                    data = base64.b64decode(entry["base64"], validate=True)
                    if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
                        raise ValueError("file content mismatch")
        if previous is not None and previous != group["before"]["tree_sha256"]:
            raise ValueError("unexplained mutation between groups")
        previous = group["after"]["tree_sha256"]
        calls = group["proposed_calls"]
        receipts = group["receipts"]
        if not calls or {c["id"] for c in calls} != {r["call_id"] for r in receipts}:
            raise ValueError("missing or mismatched call receipts")
        if len(calls) != len(receipts) or len({c["id"] for c in calls}) != len(calls):
            raise ValueError("duplicate call or receipt")
        for call in calls:
            if call["id"] in ids:
                raise ValueError("reused call ID")
            ids.add(call["id"])
        for receipt in receipts:
            if not isinstance(receipt["exit_code"], int):
                raise ValueError("missing execution status")
            if not (group["before"]["resumed_ns"] <= receipt["start_ns"]
                    <= receipt["end_ns"] <= group["after"]["paused_ns"]):
                raise ValueError("receipt outside capture boundaries")
        if group["changes"] != delta(group["before"], group["after"]):
            raise ValueError("incorrect change receipt")
        if len(calls) > 1 and group["per_call_intermediate_states_available"]:
            raise ValueError("parallel group cannot claim intermediate states")
    return True


def verify_saved(directory):
    """Re-read original tar bytes, not just the derived JSON manifests."""
    directory = Path(directory)
    result = json.loads((directory / "receipts.json").read_text())
    verify(result)
    for group in result["groups"]:
        for boundary in ("before", "after"):
            saved = group[boundary]
            name = saved["archive"]
            if Path(name).name != name:
                raise ValueError("archive must be a local filename")
            derived = manifest((directory / name).read_bytes())
            for key, value in derived.items():
                if value != saved[key]:
                    raise ValueError("saved archive disagrees with receipt: " + name)
    return result


class Session:
    def __init__(self, image, output, root=ROOT):
        self.image = image
        self.output = output
        self.root = root
        self.name = "deeptrace-capture-" + uuid.uuid4().hex[:12]

    def docker(self, *args, **kwargs):
        return subprocess.run(["docker", *args], check=True, capture_output=True,
                              timeout=60, **kwargs)

    def snapshot(self, label):
        self.docker("pause", self.name)
        paused = time.monotonic_ns()
        try:
            state = json.loads(self.docker("inspect", self.name).stdout)[0]["State"]
            if not state["Paused"]:
                raise RuntimeError("container did not pause")
            raw = self.docker("cp", self.name + ":" + self.root + "/.", "-").stdout
            snap = manifest(raw)
            (self.output / (label + ".tar")).write_bytes(raw)
            snap.update(archive=label + ".tar", paused_ns=paused, captured_at=now())
        finally:
            self.docker("unpause", self.name)
        snap["resumed_ns"] = time.monotonic_ns()
        return snap

    def execute(self, call):
        start = time.monotonic_ns()
        proc = subprocess.run(["docker", "exec", "-w", self.root, self.name, "python3", "-c",
                               call["python"]], capture_output=True, timeout=30)
        return {"call_id": call["id"], "exit_code": proc.returncode,
                "stdout": proc.stdout.decode(errors="replace"),
                "stderr": proc.stderr.decode(errors="replace"),
                "start_ns": start, "end_ns": time.monotonic_ns()}

    def run(self, groups):
        result = {"schema": 1, "started_at": now(), "image": self.image,
                  "workspace": ROOT, "groups": [], "scope": {
                      "captured": "file bytes, modes, directories and symlinks under /deeptrace-pilot",
                      "excluded": "services, databases, process memory and all other filesystem paths",
                      "background_completion_verified": False,
                      "independent_harm_review": False,
                      "linuxarena_harness_integrated": False,
                      "purpose": "controlled infrastructure pilot; no detection score"}}
        # No host mounts, credentials, network, or recorded attack commands.
        try:
            self.docker("run", "-d", "--name", self.name, "--network", "none",
                        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                        "--pids-limit", "64", "--memory", "512m", "--cpus", "1",
                        "--user", "0:0", "--entrypoint", "python3", self.image,
                        "-c", "import time; time.sleep(3600)")
            inspected = json.loads(self.docker("inspect", self.name).stdout)[0]
            if inspected["Mounts"] or inspected["HostConfig"]["NetworkMode"] != "none":
                raise RuntimeError("unexpected mounts or networking")
            result["container_id"] = inspected["Id"]
            result["image_id"] = inspected["Image"]
            result["docker_version"] = self.docker("version", "--format", "{{.Server.Version}}").stdout.decode().strip()
            self.docker("exec", self.name, "python3", "-c",
                        "from pathlib import Path; p=Path('" + ROOT + "'); p.mkdir(); "
                        "(p/'guard.txt').write_text('restricted\\n'); (p/'empty').mkdir()")
            for index, (label, calls) in enumerate(groups):
                before = self.snapshot(f"{index:02d}-before")
                # Durable intent is saved before any action is dispatched.
                intent = {"index": index, "label": label, "proposed_calls": calls, "before": before}
                (self.output / f"{index:02d}-intent.json").write_text(json.dumps(intent, indent=2))
                with ThreadPoolExecutor(max_workers=len(calls)) as pool:
                    receipts = list(pool.map(self.execute, calls))
                after = self.snapshot(f"{index:02d}-after")
                group = dict(intent, receipts=receipts, after=after, changes=delta(before, after),
                             per_call_intermediate_states_available=len(calls) == 1)
                result["groups"].append(group)
                (self.output / "receipts.json").write_text(json.dumps(result, indent=2))
            verify(result)
            result["receipt_integrity_passed"] = True
            return result
        finally:
            subprocess.run(["docker", "rm", "-f", self.name], capture_output=True, timeout=60)


def call(name, source):
    return {"id": name, "python": source}


def cases():
    return [
        ("normal_edit", [call("edit", "from pathlib import Path; Path('guard.txt').write_text('restricted-v2\\n')")]),
        ("partial_failure", [call("partial", "from pathlib import Path; import sys; Path('partial.txt').write_text('write survived failure\\n'); sys.exit(7)")]),
        ("read_only", [call("read", "from pathlib import Path; print(Path('partial.txt').read_text())")]),
        ("delete_binary_symlink", [call("types", "from pathlib import Path; Path('partial.txt').unlink(); Path('binary').write_bytes(bytes([0,255,10])); Path('link').symlink_to('guard.txt')")]),
        ("parallel_disjoint", [call("left", "from pathlib import Path; Path('left.txt').write_text('left')"),
                               call("right", "from pathlib import Path; Path('right.txt').write_text('right')")]),
        ("parallel_conflict", [call("writer-a", "from pathlib import Path; Path('shared.txt').write_text('A')"),
                               call("writer-b", "from pathlib import Path; Path('shared.txt').write_text('B')")]),
    ]


def check_cases(result):
    groups = result["groups"]
    expected = [{"guard.txt"}, {"partial.txt"}, set(), {"partial.txt", "binary", "link"},
                {"left.txt", "right.txt"}, {"shared.txt"}]
    for group, paths in zip(groups, expected):
        assert set(group["changes"]) == paths, (group["label"], group["changes"])
    assert len(groups) == len(expected)
    assert groups[1]["receipts"][0]["exit_code"] == 7
    assert all(r["exit_code"] == 0 for i, g in enumerate(groups) if i != 1 for r in g["receipts"])
    assert groups[3]["after"]["entries"]["link"]["kind"] == "symlink"
    assert base64.b64decode(groups[3]["after"]["entries"]["binary"]["base64"]) == bytes([0, 255, 10])
    assert base64.b64decode(groups[5]["after"]["entries"]["shared.txt"]["base64"]) in (b"A", b"B")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        result = verify_saved(args.verify)
        check_cases(result)
        print("PASS: saved archives, receipts, ordering and fixture outcomes verified")
        return
    args.out.mkdir(parents=True, exist_ok=False)
    result = Session(IMAGE, args.out).run(cases())
    check_cases(result)
    result["fixture_checks_passed"] = True
    result["finished_at"] = now()
    result["producer_sha256"] = sha(Path(__file__).read_bytes())
    (args.out / "receipts.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"groups": len(result["groups"]), "calls": sum(len(g["receipts"]) for g in result["groups"]),
                      "receipt_integrity_passed": True, "fixture_checks_passed": True,
                      "result": str(args.out / "receipts.json")}, indent=2))


if __name__ == "__main__":
    main()
