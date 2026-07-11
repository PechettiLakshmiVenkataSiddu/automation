"""Command policy evaluator enforcing security filters and approval rules."""

from __future__ import annotations

import re


class DeveloperCommandPolicyEvaluator:
    """Enforces boundaries and access control lists on proposed shell inputs."""

    def __init__(self) -> None:
        # Blocked commands (e.g. remote network tools, raw shell piping)
        self.blocked_regex = re.compile(
            r"\b(curl|wget|nc|ncat|ping|ssh|ftp|telnet)\b", re.IGNORECASE
        )

        # Gated commands requiring human approval (e.g. destructive edits, installations, builds)
        self.gated_regex = re.compile(
            r"\b(rm|rmdir|del|erase|git\s+(commit|push|checkout|reset|rebase|merge)|"
            r"npm\s+(install|i|ci|run\s+build)|pip\s+install|uv\s+pip\s+install|"
            r"yarn\s+install|pnpm\s+install|setup\.py)\b",
            re.IGNORECASE,
        )

    def evaluate(self, command_line: str) -> str:
        """Evaluate command line.

        Returns 'blocked' (rejected), 'awaiting_approval' (gated), or 'queued' (safe).
        """
        cmd = command_line.strip()

        if self.blocked_regex.search(cmd):
            return "blocked"

        if self.gated_regex.search(cmd):
            return "awaiting_approval"

        return "queued"
