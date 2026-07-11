"""Desktop surface validation inside the executor boundary."""

from __future__ import annotations

import re
from typing import Any

_HOST_WIDE_PATTERNS = (
    re.compile(r"^\*$"),
    re.compile(r"^all$", re.IGNORECASE),
    re.compile(r"^/.+"),
    re.compile(r"\.\."),
)

SUPPORTED_OPERATIONS = frozenset(
    {"focus_app", "screenshot", "read_window", "click", "type_text", "paste"}
)


def normalize_application(value: str) -> str:
    return value.strip().lower()


def validate_action(action: dict[str, Any]) -> None:
    operation = str(action["operation"])
    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError("Unsupported desktop operation")
    target = normalize_application(str(action["target_application"]))
    allowlist = {normalize_application(str(item)) for item in action["allowed_applications"]}
    if target not in allowlist:
        raise ValueError("Desktop target application is not allowlisted")
    for pattern in _HOST_WIDE_PATTERNS:
        if pattern.search(target):
            raise ValueError("Desktop target cannot use host-wide patterns")
    allowed_mounts = action.get("allowed_mounts", [])
    if not isinstance(allowed_mounts, list):
        raise ValueError("Desktop mount paths must be relative sandbox entries")
    for mount in allowed_mounts:
        mount_value = str(mount)
        if mount_value.startswith("/") or ".." in mount_value or mount_value in {"*", "all", "/"}:
            raise ValueError("Desktop mount paths must be relative sandbox entries")
    if bool(action.get("network_enabled")):
        raise ValueError("Desktop network access is disabled by policy")
    timeout = int(str(action["timeout_seconds"]))
    if not 1 <= timeout <= 120:
        raise ValueError("Desktop timeout must be between 1 and 120 seconds")
