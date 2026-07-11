"""HMAC grant verification for the voice executor."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from uuid import UUID


def verify_grant(secret: bytes, token: str) -> tuple[UUID, UUID]:
    encoded, separator, signature = token.partition(".")
    expected = hmac.new(secret, encoded.encode(), hashlib.sha256).hexdigest()
    if not separator or not hmac.compare_digest(signature, expected):
        raise ValueError("Voice session grant is invalid")
    payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    if int(payload["expires_at"]) < int(time.time()):
        raise ValueError("Voice session grant has expired")
    return UUID(payload["organization_id"]), UUID(payload["session_id"])
