from __future__ import annotations

import os

import pytest

from aether.developer.sandbox import DeveloperSandboxManager


def test_sandbox_path_resolution_success() -> None:
    # Use current directory as a mock root workspace
    manager = DeveloperSandboxManager(workspace_root=".")

    # A safe relative path should resolve to an absolute path inside the root
    res = manager.resolve_safe_path("artifacts/my-sandbox")
    assert os.path.isabs(res)
    assert res.endswith(os.path.normpath("artifacts/my-sandbox"))


def test_sandbox_path_traversal_escapes() -> None:
    manager = DeveloperSandboxManager(workspace_root=".")

    # Simple directory traversal escape
    with pytest.raises(ValueError, match="Directory traversal escape"):
        manager.resolve_safe_path("../../outside")

    # Absolute path escape outside workspace root (e.g. system folder)
    with pytest.raises(ValueError, match="Directory traversal escape"):
        manager.resolve_safe_path("/etc/hosts")

    # Windows drive letter escape
    with pytest.raises(ValueError, match="Directory traversal escape"):
        manager.resolve_safe_path("C:\\Windows\\System32")
