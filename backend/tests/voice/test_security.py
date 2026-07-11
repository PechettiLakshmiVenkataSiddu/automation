from uuid import uuid4

import pytest

from aether.automation.policy import PolicyOutcome
from aether.voice.artifacts import LocalArtifactStore
from aether.voice.contracts import VoiceAudioUpload, VoiceCommandIntent
from aether.voice.grants import issue_grant, verify_grant
from aether.voice.intent import parse_transcript
from aether.voice.policy import VoicePolicyEvaluator
from aether.voice.redaction import redact_transcript


def test_grant_binds_session_and_organization() -> None:
    organization_id, session_id = uuid4(), uuid4()
    token = issue_grant(b"voice-secret-key-needs-32-bytes-min!!", organization_id, session_id, 30)
    assert verify_grant(b"voice-secret-key-needs-32-bytes-min!!", token) == (
        organization_id,
        session_id,
    )


def test_intent_requires_confirmation_for_automation() -> None:
    intent = parse_transcript("Please run workflow billing")
    assert intent.intent_type == "automation_action"
    assert intent.requires_confirmation is True


def test_policy_requires_confirmation_for_voice_commands() -> None:
    evaluator = VoicePolicyEvaluator()
    intent = VoiceCommandIntent("chat_message", "ask what is next", {"message": "ask"}, True)
    assert evaluator.evaluate_intent(intent, uuid4()).outcome is PolicyOutcome.REQUIRE_APPROVAL


def test_redaction_masks_sensitive_transcript_values() -> None:
    assert "[REDACTED]" in redact_transcript("api_key=secret-value")


def test_audio_upload_rejects_unsupported_formats() -> None:
    with pytest.raises(ValueError):
        VoiceAudioUpload("exe", "aGVsbG8=", 5)


def test_artifacts_are_confined_to_session_organization(tmp_path: object) -> None:
    organization_id, session_id = uuid4(), uuid4()
    store = LocalArtifactStore(tmp_path)  # type: ignore[arg-type]
    key, digest = store.put(organization_id, session_id, "transcript", b"redacted transcript")
    assert key.startswith(f"voice/{organization_id}/{session_id}/")
    assert len(digest) == 64
