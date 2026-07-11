"""Consent, policy, audit, and confirmation gate for voice sessions."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.automation.policy import PolicyDecision, PolicyOutcome
from aether.infrastructure.persistence.voice_repository import SqlAlchemyVoiceRepository
from aether.shared.errors import AuthorizationError
from aether.voice.contracts import MAX_AUDIO_BYTES, VoiceAudioUpload, VoiceCommandIntent
from aether.voice.intent import parse_transcript
from aether.voice.policy import VoicePolicyEvaluator
from aether.voice.redaction import redact_transcript


class VoiceSessionService:
    """Enforces voice consent and confirmation before any external voice effect."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = SqlAlchemyVoiceRepository(session)
        self._evaluator = VoicePolicyEvaluator()

    async def set_consent(
        self, org: UUID, user: UUID, capture_enabled: bool, retention_enabled: bool
    ) -> dict[str, object]:
        return await self._repository.set_consent(org, user, capture_enabled, retention_enabled)

    async def require_capture_consent(self, org: UUID, user: UUID) -> dict[str, object]:
        consent = await self._repository.get_consent(org, user)
        if consent is None or not consent.get("capture_enabled"):
            raise AuthorizationError("Voice capture consent is required")
        return consent

    async def create_session(
        self,
        org: UUID,
        user: UUID,
        conversation_id: UUID | None,
        idempotency_key: str,
    ) -> tuple[UUID, str]:
        consent = await self.require_capture_consent(org, user)
        retention_mode = "retained" if consent.get("retention_enabled") else "ephemeral"
        session_id = await self._repository.create_session(
            org, user, conversation_id, str(retention_mode), idempotency_key
        )
        existing = await self._repository.get_session(org, session_id)
        status = str(existing["status"]) if existing else "active"
        return session_id, status

    async def begin_transcription(self, org: UUID, user: UUID, session_id: UUID) -> bool:
        await self._require_session_owner(org, user, session_id)
        return await self._repository.mark_transcribing(org, session_id)

    async def record_transcript(
        self, org: UUID, session_id: UUID, transcript: str
    ) -> VoiceCommandIntent:
        cleaned = redact_transcript(transcript)
        if not await self._repository.set_transcript(org, session_id, cleaned):
            raise ValueError("Voice session transcript could not be recorded")
        intent = parse_transcript(cleaned)
        decision = self._evaluator.evaluate_intent(intent, org)
        await self._audit(org, session_id, intent, decision)
        return intent

    async def queue_confirmation(
        self, org: UUID, user: UUID, session_id: UUID, intent: VoiceCommandIntent
    ) -> UUID:
        await self._require_session_owner(org, user, session_id)
        return await self._repository.create_confirmation(org, session_id, user, intent)

    async def decide_confirmation(
        self, org: UUID, user: UUID, confirmation_id: UUID, confirmed: bool, reason: str | None
    ) -> UUID | None:
        return await self._repository.decide_confirmation(
            org, confirmation_id, user, confirmed, reason
        )

    def validate_audio(self, upload: VoiceAudioUpload) -> None:
        import base64

        try:
            decoded = base64.b64decode(upload.content_base64, validate=True)
        except ValueError as error:
            raise ValueError("Audio content is invalid") from error
        if len(decoded) > MAX_AUDIO_BYTES:
            raise ValueError("Audio payload exceeds the allowed limit")

    async def _audit(
        self, org: UUID, session_id: UUID, intent: VoiceCommandIntent, decision: PolicyDecision
    ) -> None:
        outcome = (
            "allowed"
            if decision.outcome is PolicyOutcome.ALLOW
            else ("pending" if decision.outcome is PolicyOutcome.REQUIRE_APPROVAL else "denied")
        )
        await self._session.execute(
            text("""
            INSERT INTO audit_events (
                organization_id, actor_user_id, event_type, target_type, target_id,
                outcome, policy_version, correlation_id, metadata
            )
            VALUES (
                :org, NULL, 'voice.command.policy', 'voice_session', :session,
                :outcome, :policy, :correlation, CAST(:metadata AS jsonb)
            )
        """),
            {
                "org": org,
                "session": session_id,
                "outcome": outcome,
                "policy": decision.policy_version,
                "correlation": uuid4(),
                "metadata": json.dumps(
                    {"intent_type": intent.intent_type, "transcript": intent.transcript[:500]}
                ),
            },
        )

    async def _require_session_owner(self, org: UUID, user: UUID, session_id: UUID) -> None:
        row = await self._repository.get_session(org, session_id)
        if row is None or UUID(str(row["user_id"])) != user:
            raise AuthorizationError("Voice session access is denied")
