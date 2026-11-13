"""Offline integrity tests; Docker fixture checks run separately via pilot.py."""
import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from pilot import canonical, delta, manifest, sha, verify, verify_saved


def archive(name="file", data=b"initial", special=False):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as output:
        member = tarfile.TarInfo(name)
        if special:
            member.type = tarfile.FIFOTYPE
        else:
            member.size = len(data)
        output.addfile(member, io.BytesIO(data))
    return raw.getvalue()


def receipt():
    before = dict(manifest(archive()), paused_ns=0, resumed_ns=1)
    after = dict(manifest(archive(data=b"partial write")), paused_ns=4, resumed_ns=5)
    return {"groups": [{"index": 0, "proposed_calls": [{"id": "partial"}],
                        "receipts": [{"call_id": "partial", "exit_code": 7, "start_ns": 2, "end_ns": 3}],
                        "before": before, "after": after, "changes": delta(before, after),
                        "per_call_intermediate_states_available": True}]}


class IntegrityTests(unittest.TestCase):
    def test_changed_saved_archive_rejected(self):
        result = receipt()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for boundary, data in (("before", b"initial"), ("after", b"partial write")):
                name = boundary + ".tar"
                result["groups"][0][boundary]["archive"] = name
                (root / name).write_bytes(archive(data=data))
            (root / "receipts.json").write_text(json.dumps(result))
            verify_saved(root)
            (root / "after.tar").write_bytes(archive(data=b"changed"))
            with self.assertRaisesRegex(ValueError, "disagrees"):
                verify_saved(root)

    def test_failed_call_can_have_persistent_effect(self):
        self.assertTrue(verify(receipt()))
        self.assertIn("file", receipt()["groups"][0]["changes"])

    def test_unsafe_or_unsupported_archive_rejected(self):
        for raw in (archive("../escape"), archive("/absolute"), archive(special=True)):
            with self.assertRaises(ValueError):
                manifest(raw)
        with self.assertRaises(ValueError):
            manifest(archive(), cap=1)

    def test_content_tamper_rejected_even_with_new_tree_hash(self):
        result = receipt()
        snap = result["groups"][0]["after"]
        snap["entries"]["file"]["base64"] = "dGFtcGVyZWQ="
        snap["tree_sha256"] = sha(canonical(snap["entries"]))
        with self.assertRaisesRegex(ValueError, "file content"):
            verify(result)

    def test_missing_receipt_and_wrong_boundary_rejected(self):
        result = receipt()
        result["groups"][0]["receipts"] = []
        with self.assertRaises(ValueError):
            verify(result)
        result = receipt()
        result["groups"][0]["receipts"][0]["end_ns"] = 10
        with self.assertRaisesRegex(ValueError, "outside capture"):
            verify(result)

    def test_unrecorded_between_group_mutation_rejected(self):
        result = receipt()
        second = copy.deepcopy(result["groups"][0])
        second["index"] = 1
        result["groups"].append(second)
        with self.assertRaisesRegex(ValueError, "unexplained mutation"):
            verify(result)

    def test_parallel_false_attribution_rejected(self):
        result = receipt()
        group = result["groups"][0]
        group["proposed_calls"].append({"id": "other"})
        group["receipts"].append(dict(group["receipts"][0], call_id="other"))
        with self.assertRaisesRegex(ValueError, "intermediate states"):
            verify(result)
        group["per_call_intermediate_states_available"] = False
        self.assertTrue(verify(result))


if __name__ == "__main__":
    unittest.main()
