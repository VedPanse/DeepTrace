"""Check that the dispatch guard cannot execute through unexplained source drift."""
import copy
from pathlib import Path
import tempfile
import unittest

from application_study import checked_action
from pilot import call
from test_pilot import receipt


class FakeSession:
    def __init__(self, output, snapshots):
        self.output = Path(output)
        self.snapshots = iter(snapshots)
        self.executions = 0

    def snapshot(self, label):
        return next(self.snapshots)

    def execute(self, action):
        self.executions += 1
        return {"call_id": action["id"], "exit_code": 7}


class DispatchTests(unittest.TestCase):
    def test_drift_blocks_execution(self):
        group = receipt()["groups"][0]
        with tempfile.TemporaryDirectory() as folder:
            session = FakeSession(folder, [group["after"]])
            result = checked_action(session, group["before"], call("next", "pass"), "guard")
            self.assertEqual(session.executions, 0)
            self.assertFalse(result["dispatched"])
            self.assertNotIn("receipt", result)

    def test_failed_action_still_gets_post_capture(self):
        group = receipt()["groups"][0]
        with tempfile.TemporaryDirectory() as folder:
            session = FakeSession(folder, [copy.deepcopy(group["before"]), group["after"]])
            result = checked_action(session, group["before"], call("next", "pass"), "guard")
            self.assertEqual(session.executions, 1)
            self.assertEqual(result["receipt"]["exit_code"], 7)
            self.assertIn("file", result["changes"])


if __name__ == "__main__":
    unittest.main()
