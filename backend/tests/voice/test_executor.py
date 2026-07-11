"""Unit tests for voice executor validation."""

from __future__ import annotations

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "services" / "voice-executor" / "src"))

from voice_access import validate_audio_payload, validate_synthesis_text  # noqa: E402


def test_validate_audio_rejects_oversized_payload() -> None:
    try:
        validate_audio_payload(
            {
                "format": "wav",
                "content_base64": base64.b64encode(b"x" * 11_000_000).decode(),
            }
        )
        raise AssertionError("expected validation failure")
    except ValueError as error:
        assert "exceeds" in str(error)


def test_validate_synthesis_text_requires_content() -> None:
    try:
        validate_synthesis_text("   ")
        raise AssertionError("expected validation failure")
    except ValueError as error:
        assert "required" in str(error)
