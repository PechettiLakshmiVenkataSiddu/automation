"""Manages directory sanitization and secure path confinement checks."""

from __future__ import annotations

import os


class DeveloperSandboxManager:
    """Ensures directories remain confined within the authorized workspace."""

    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = os.path.abspath(workspace_root)

    def resolve_safe_path(self, relative_path: str) -> str:
        """Resolve and verify that a target path lies strictly inside the workspace root."""
        is_absolute = (
            os.path.isabs(relative_path)
            or relative_path.startswith("/")
            or relative_path.startswith("\\")
        )
        if is_absolute:
            resolved = os.path.abspath(relative_path)
        else:
            resolved = os.path.abspath(os.path.join(self.workspace_root, relative_path))

        # Check path containment
        common = os.path.commonpath([self.workspace_root, resolved])
        if common != self.workspace_root:
            raise ValueError(
                f"Directory traversal escape: '{relative_path}' "
                "is outside the authorized workspace."
            )
        return resolved

    def ensure_sandbox(self, relative_path: str) -> str:
        """Verify the sandbox path and create the directory if it does not exist."""
        resolved = self.resolve_safe_path(relative_path)
        os.makedirs(resolved, exist_ok=True)
        return resolved
