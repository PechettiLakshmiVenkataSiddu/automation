"""Unit tests for desktop executor sandbox validation and cleanup."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "services" / "desktop-executor" / "src")
)

from access import validate_action  # noqa: E402
from executor import DesktopSandbox  # noqa: E402


def test_validate_action_rejects_network_and_host_wide_targets() -> None:
    try:
        validate_action(
            {
                "operation": "screenshot",
                "target_application": "*",
                "allowed_applications": ["*"],
                "allowed_mounts": [],
                "network_enabled": False,
                "timeout_seconds": 30,
            }
        )
        raise AssertionError("expected validation failure")
    except ValueError as error:
        assert "host-wide" in str(error)


def test_sandbox_cleanup_verifies_temp_directory_removal(tmp_path: Path) -> None:
    sandbox = DesktopSandbox(tmp_path / "session")
    sandbox.prepare_mounts(["workspace"])
    assert sandbox.cleanup() is True
    assert not (tmp_path / "session").exists()
