"""Authored static-analysis demo. This file is never executed by AgentSecBench."""

import subprocess
from pathlib import Path


def agent_tool(command: str, workspace: str) -> None:
    """Illustrate agent-facing input reaching two security-sensitive effects."""
    subprocess.run(command, shell=True, check=False)
    Path(workspace, "last-command.txt").write_text(command, encoding="utf-8")
