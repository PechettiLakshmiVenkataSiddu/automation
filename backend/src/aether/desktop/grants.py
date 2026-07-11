"""Short-lived HMAC task grants verified only by the desktop executor."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID


def issue_grant(secret: bytes, organization_id: UUID, task_id: UUID, ttl_seconds: int = 300) -> str:
    if not 30 <= ttl_seconds <= 600:
        raise ValueError("Desktop grant TTL must be between 30 and 600 seconds")
    payload = {
        "organization_id": str(organization_id),
        "task_id": str(task_id),
        "expires_at": int((datetime.now(UTC) + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    encoded = _encode(payload)
    signature = hmac.new(secret, encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_grant(secret: bytes, token: str) -> tuple[UUID, UUID]:
    encoded, separator, signature = token.partition(".")
    expected = hmac.new(secret, encoded.encode(), hashlib.sha256).hexdigest()
    if not separator or not hmac.compare_digest(signature, expected):
        raise ValueError("Desktop task grant is invalid")
    payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    if int(payload["expires_at"]) < int(datetime.now(UTC).timestamp()):
        raise ValueError("Desktop task grant has expired")
    return UUID(payload["organization_id"]), UUID(payload["task_id"])


def _encode(value: dict[str, object]) -> str:
    return (
        base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())
        .rstrip(b"=")
        .decode()
    )
