"""Tenant-confined desktop artifact storage for the control plane."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID, uuid4


class LocalArtifactStore:
    """Development object-store adapter; production supplies an equivalent object-store port."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def put(
        self, organization_id: UUID, task_id: UUID, artifact_type: str, content: bytes
    ) -> tuple[str, str]:
        if artifact_type not in {"trace", "screenshot", "window_dump"}:
            raise ValueError("Unsupported desktop artifact")
        digest = hashlib.sha256(content).hexdigest()
        key = f"desktop/{organization_id}/{task_id}/{uuid4()}.{artifact_type}"
        destination = self._root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return key, digest
