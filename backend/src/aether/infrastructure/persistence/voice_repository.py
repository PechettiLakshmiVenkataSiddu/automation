"""PostgreSQL authority for voice consents, sessions, artifacts, and confirmations."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.voice.contracts import VoiceCommandIntent
from aether.voice.policy import VOICE_POLICY_VERSION


class SqlAlchemyVoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_consent(
        self, org: UUID, user: UUID, capture_enabled: bool, retention_enabled: bool
    ) -> dict[str, object]:
        await self._session.execute(
            text("""
            INSERT INTO voice_consents (
                organization_id, user_id, capture_enabled, retention_enabled,
                policy_version, granted_at, withdrawn_at
            )
            VALUES (
                :org, :user, :capture, :retention, :policy,
                CASE WHEN :capture THEN now() ELSE NULL END,
                CASE WHEN :capture THEN NULL ELSE now() END
            )
            ON CONFLICT (organization_id, user_id) DO UPDATE SET
                capture_enabled = EXCLUDED.capture_enabled,
                retention_enabled = EXCLUDED.retention_enabled,
                policy_version = EXCLUDED.policy_version,
                granted_at = CASE WHEN EXCLUDED.capture_enabled THEN now() ELSE voice_consents.granted_at END,
                withdrawn_at = CASE WHEN EXCLUDED.capture_enabled THEN NULL ELSE now() END,
                updated_at = now()
        """),
            {
                "org": org,
                "user": user,
                "capture": capture_enabled,
                "retention": retention_enabled if capture_enabled else False,
                "policy": VOICE_POLICY_VERSION,
            },
        )
        return await self.get_consent(org, user) or {
            "capture_enabled": capture_enabled,
            "retention_enabled": retention_enabled,
        }

    async def get_consent(self, org: UUID, user: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    SELECT capture_enabled, retention_enabled, policy_version, granted_at, withdrawn_at
                    FROM voice_consents WHERE organization_id=:org AND user_id=:user
                """),
                    {"org": org, "user": user},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def create_session(
        self,
        org: UUID,
        user: UUID,
        conversation_id: UUID | None,
        retention_mode: str,
        idempotency_key: str,
    ) -> UUID:
        existing = await self.find_by_idempotency(org, idempotency_key)
        if existing is not None:
            return existing
        session_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO voice_sessions (
                id, organization_id, user_id, conversation_id, status,
                retention_mode, idempotency_key, expires_at
            )
            VALUES (
                :id, :org, :user, :conversation, 'active', :retention,
                :idempotency, now() + interval '30 minutes'
            )
        """),
            {
                "id": session_id,
                "org": org,
                "user": user,
                "conversation": conversation_id,
                "retention": retention_mode,
                "idempotency": idempotency_key,
            },
        )
        return session_id

    async def find_by_idempotency(self, org: UUID, idempotency_key: str) -> UUID | None:
        return (
            await self._session.execute(
                text(
                    "SELECT id FROM voice_sessions WHERE organization_id=:org AND idempotency_key=:key"
                ),
                {"org": org, "key": idempotency_key},
            )
        ).scalar_one_or_none()

    async def get_session(self, org: UUID, session_id: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    SELECT id, user_id, conversation_id, status, retention_mode, transcript,
                           cancellation_requested_at, expires_at
                    FROM voice_sessions WHERE id=:session_id AND organization_id=:org
                """),
                    {"session_id": session_id, "org": org},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def mark_transcribing(self, org: UUID, session_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE voice_sessions SET status='transcribing', updated_at=now()
            WHERE id=:session_id AND organization_id=:org AND status='active'
              AND cancellation_requested_at IS NULL AND expires_at > now()
        """),
            {"session_id": session_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def set_transcript(self, org: UUID, session_id: UUID, transcript: str) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE voice_sessions SET transcript=:transcript, status='awaiting_confirmation',
                updated_at=now()
            WHERE id=:session_id AND organization_id=:org AND status='transcribing'
        """),
            {"session_id": session_id, "org": org, "transcript": transcript},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def create_confirmation(
        self, org: UUID, session_id: UUID, user: UUID, intent: VoiceCommandIntent
    ) -> UUID:
        confirmation_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO voice_command_confirmations (
                id, organization_id, voice_session_id, requested_by_user_id,
                intent_type, intent_payload, policy_version, expires_at
            )
            VALUES (
                :id, :org, :session, :user, :intent_type,
                CAST(:payload AS jsonb), :policy, now() + interval '10 minutes'
            )
        """),
            {
                "id": confirmation_id,
                "org": org,
                "session": session_id,
                "user": user,
                "intent_type": intent.intent_type,
                "payload": json.dumps(intent.payload),
                "policy": VOICE_POLICY_VERSION,
            },
        )
        return confirmation_id

    async def decide_confirmation(
        self, org: UUID, confirmation_id: UUID, user: UUID, confirmed: bool, reason: str | None
    ) -> UUID | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    UPDATE voice_command_confirmations
                    SET status=:status, decided_by_user_id=:user, decision_reason=:reason,
                        decided_at=now()
                    WHERE id=:confirmation_id AND organization_id=:org AND status='pending'
                    RETURNING voice_session_id
                """),
                    {
                        "confirmation_id": confirmation_id,
                        "org": org,
                        "user": user,
                        "status": "confirmed" if confirmed else "rejected",
                        "reason": reason,
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        session_id = UUID(str(row["voice_session_id"]))
        await self._session.execute(
            text("""
            UPDATE voice_sessions SET status=:status, updated_at=now()
            WHERE id=:session_id AND organization_id=:org
        """),
            {
                "session_id": session_id,
                "org": org,
                "status": "completed" if confirmed else "cancelled",
            },
        )
        return session_id

    async def cancel(self, org: UUID, session_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE voice_sessions
            SET cancellation_requested_at=now(),
                status=CASE WHEN status IN ('active','transcribing','awaiting_confirmation')
                    THEN 'cancelled' ELSE status END,
                updated_at=now()
            WHERE id=:session_id AND organization_id=:org
              AND status NOT IN ('completed','failed','cancelled')
        """),
            {"session_id": session_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def add_artifact(
        self, org: UUID, session_id: UUID, artifact_type: str, object_key: str, sha256: str
    ) -> UUID:
        artifact_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO voice_session_artifacts (
                id, organization_id, voice_session_id, artifact_type, object_key, sha256, redacted
            )
            SELECT :id, :org, id, :type, :key, :sha, true
            FROM voice_sessions WHERE id=:session_id AND organization_id=:org
        """),
            {
                "id": artifact_id,
                "org": org,
                "session_id": session_id,
                "type": artifact_type,
                "key": object_key,
                "sha": sha256,
            },
        )
        return artifact_id

    async def complete_synthesis(self, org: UUID, session_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE voice_sessions SET status='completed', updated_at=now()
            WHERE id=:session_id AND organization_id=:org AND status='synthesizing'
        """),
            {"session_id": session_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def mark_synthesizing(self, org: UUID, session_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE voice_sessions SET status='synthesizing', updated_at=now()
            WHERE id=:session_id AND organization_id=:org AND status='completed'
        """),
            {"session_id": session_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]
