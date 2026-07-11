"""Reject unsafe desktop surface access before an executor receives a task grant."""

from __future__ import annotations

import re

_HOST_WIDE_PATTERNS = (
    re.compile(r"^\*$"),
    re.compile(r"^all$", re.IGNORECASE),
    re.compile(r"^/.+"),
    re.compile(r"\.\."),
)


class UnsafeDesktopAccess(ValueError):
    """The requested desktop surface is outside the approved allowlist."""


def validate_desktop_target(
    target_application: str,
    allowed_applications: tuple[str, ...],
    allowed_mounts: tuple[str, ...],
    network_enabled: bool,
) -> None:
    normalized_target = _normalize_application(target_application)
    allowlist = {_normalize_application(item) for item in allowed_applications}
    if normalized_target not in allowlist:
        raise UnsafeDesktopAccess("Desktop target application is not allowlisted")
    for pattern in _HOST_WIDE_PATTERNS:
        if pattern.search(normalized_target):
            raise UnsafeDesktopAccess("Desktop target cannot use host-wide patterns")
    for mount in allowed_mounts:
        if mount.startswith("/") or ".." in mount or mount in {"*", "all", "/"}:
            raise UnsafeDesktopAccess("Desktop mount paths must be relative sandbox entries")
    if network_enabled:
        raise UnsafeDesktopAccess("Desktop network access is disabled by policy")


def _normalize_application(value: str) -> str:
    return value.strip().lower()
