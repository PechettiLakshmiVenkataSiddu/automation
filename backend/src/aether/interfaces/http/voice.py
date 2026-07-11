"""Authenticated voice assistant HTTP routes; audio processing stays outside this process."""

from __future__ import annotations

import base64
import hmac
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.infrastructure.persistence.voice_repository import SqlAlchemyVoiceRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal
from aether.shared.errors import AuthorizationError
from aether.voice.artifacts import LocalArtifactStore
from aether.voice.contracts import VoiceAudioUpload
from aether.voice.grants import issue_grant
from aether.voice.intent import parse_transcript
from aether.voice.service import VoiceSessionService

router = APIRouter(prefix="/v1/voice", tags=["voice"])


class ConsentRequest(BaseModel):
    organization_id: UUID
    capture_enabled: bool
    retention_enabled: bool = False


class CreateSessionRequest(BaseModel):
    organization_id: UUID
    conversation_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)


class AudioUploadRequest(BaseModel):
    organization_id: UUID
    format: str
    content_base64: str = Field(min_length=1, max_length=20_000_000)
    duration_seconds: int = Field(ge=1, le=120)


class TranscriptRequest(BaseModel):
    organization_id: UUID
    session_id: UUID
    transcript: str = Field(min_length=1, max_length=5_000)


class SynthesizeRequest(BaseModel):
    organization_id: UUID
    text: str = Field(min_length=1, max_length=5_000)


class ConfirmationDecisionRequest(BaseModel):
    organization_id: UUID
    confirmed: bool
    reason: str | None = Field(default=None, max_length=2_000)


class ArtifactRequest(BaseModel):
    organization_id: UUID
    session_id: UUID
    artifact_type: str
    content_base64: str = Field(min_length=1, max_length=20_000_000)


class TranscriptIngestRequest(BaseModel):
    organization_id: UUID
    session_id: UUID
    transcript: str = Field(min_length=1, max_length=5_000)


class StatusRequest(BaseModel):
    organization_id: UUID
    session_id: UUID
    succeeded: bool
    cleanup_verified: bool


async def _membership(session: DatabaseSession, org: UUID, user: UUID) -> None:
    found = (
        await session.execute(
            text(
                "SELECT 1 FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active'"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if found is None:
        raise HTTPException(status_code=403, detail="Organization access is denied")


def _service(session: DatabaseSession) -> VoiceSessionService:
    return VoiceSessionService(session)


@router.put("/consent")
async def set_voice_consent(
    body: ConsentRequest, session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> dict[str, object]:
    await _membership(session, body.organization_id, principal.user_id)
    consent = await _service(session).set_consent(
        body.organization_id,
        principal.user_id,
        body.capture_enabled,
        body.retention_enabled if body.capture_enabled else False,
    )
    return {
        "capture_enabled": consent.get("capture_enabled"),
        "retention_enabled": consent.get("retention_enabled"),
        "policy_version": consent.get("policy_version"),
    }


@router.get("/consent")
async def get_voice_consent(
    session: DatabaseSession,
    organization_id: UUID,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _membership(session, organization_id, principal.user_id)
    consent = await SqlAlchemyVoiceRepository(session).get_consent(
        organization_id, principal.user_id
    )
    if consent is None:
        return {"capture_enabled": False, "retention_enabled": False}
    return {
        "capture_enabled": consent.get("capture_enabled"),
        "retention_enabled": consent.get("retention_enabled"),
        "policy_version": consent.get("policy_version"),
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_voice_session(
    body: CreateSessionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _membership(session, body.organization_id, principal.user_id)
    try:
        session_id, session_status = await _service(session).create_session(
            body.organization_id,
            principal.user_id,
            body.conversation_id,
            body.idempotency_key,
        )
    except AuthorizationError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return {"id": str(session_id), "status": session_status}


@router.get("/sessions/{session_id}")
async def get_voice_session(
    session_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _membership(session, organization_id, principal.user_id)
    row = await SqlAlchemyVoiceRepository(session).get_session(organization_id, session_id)
    if row is None or UUID(str(row["user_id"])) != principal.user_id:
        raise HTTPException(status_code=404, detail="Voice session was not found")
    expires_at = row["expires_at"]
    return {
        "id": str(row["id"]),
        "status": row["status"],
        "retention_mode": row["retention_mode"],
        "transcript": row.get("transcript"),
        "expires_at": expires_at.isoformat()
        if isinstance(expires_at, datetime)
        else str(expires_at),
    }


@router.post("/sessions/{session_id}/cancel")
async def cancel_voice_session(
    session_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _membership(session, organization_id, principal.user_id)
    if not await SqlAlchemyVoiceRepository(session).cancel(organization_id, session_id):
        raise HTTPException(status_code=404, detail="Voice session is not cancellable")
    return {"cancelled": True}


@router.post("/sessions/{session_id}/audio")
async def upload_voice_audio(
    session_id: UUID,
    body: AudioUploadRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _membership(session, body.organization_id, principal.user_id)
    service = _service(session)
    try:
        upload = VoiceAudioUpload(body.format, body.content_base64, body.duration_seconds)
        service.validate_audio(upload)
        if not await service.begin_transcription(
            body.organization_id, principal.user_id, session_id
        ):
            raise HTTPException(status_code=409, detail="Voice session is not ready for audio")
    except (ValueError, AuthorizationError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"session_id": str(session_id), "status": "transcribing"}


@router.post("/sessions/{session_id}/grant")
async def issue_voice_grant(
    session_id: UUID,
    organization_id: UUID,
    request: Request,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _membership(session, organization_id, principal.user_id)
    row = await SqlAlchemyVoiceRepository(session).get_session(organization_id, session_id)
    if row is None or UUID(str(row["user_id"])) != principal.user_id:
        raise HTTPException(status_code=404, detail="Voice session was not found")
    if row["status"] != "transcribing":
        raise HTTPException(status_code=409, detail="Voice session is not grantable")
    grant = issue_grant(
        request.app.state.application_settings.voice_grant_secret.encode(),
        organization_id,
        session_id,
        ttl_seconds=300,
    )
    return {"grant": grant, "session_id": str(session_id)}


@router.post("/sessions/{session_id}/commands")
async def parse_voice_command(
    session_id: UUID,
    body: TranscriptRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _membership(session, body.organization_id, principal.user_id)
    service = _service(session)
    try:
        intent = parse_transcript(body.transcript)
        confirmation_id = await service.queue_confirmation(
            body.organization_id, principal.user_id, session_id, intent
        )
    except AuthorizationError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return {
        "confirmation_id": str(confirmation_id),
        "intent_type": intent.intent_type,
        "transcript": intent.transcript,
        "requires_confirmation": intent.requires_confirmation,
    }


@router.post("/confirmations/{confirmation_id}/decision")
async def decide_voice_confirmation(
    confirmation_id: UUID,
    body: ConfirmationDecisionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _membership(session, body.organization_id, principal.user_id)
    session_id = await _service(session).decide_confirmation(
        body.organization_id,
        confirmation_id,
        principal.user_id,
        body.confirmed,
        body.reason,
    )
    if session_id is None:
        raise HTTPException(status_code=409, detail="Confirmation is unavailable")
    return {
        "voice_session_id": str(session_id),
        "decision": "confirmed" if body.confirmed else "rejected",
    }


@router.post("/sessions/{session_id}/synthesize")
async def synthesize_voice_response(
    session_id: UUID,
    body: SynthesizeRequest,
    request: Request,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _membership(session, body.organization_id, principal.user_id)
    repository = SqlAlchemyVoiceRepository(session)
    row = await repository.get_session(body.organization_id, session_id)
    if row is None or UUID(str(row["user_id"])) != principal.user_id:
        raise HTTPException(status_code=404, detail="Voice session was not found")
    if not await repository.mark_synthesizing(body.organization_id, session_id):
        raise HTTPException(status_code=409, detail="Voice session is not ready for synthesis")
    grant = issue_grant(
        request.app.state.application_settings.voice_grant_secret.encode(),
        body.organization_id,
        session_id,
        ttl_seconds=300,
    )
    return {
        "grant": grant,
        "session_id": str(session_id),
        "text": body.text,
    }


@router.post("/internal/transcript", include_in_schema=False)
async def ingest_transcript(
    body: TranscriptIngestRequest, request: Request, session: DatabaseSession
) -> dict[str, object]:
    supplied = request.headers.get("X-Voice-Executor-Secret", "")
    expected = request.app.state.application_settings.voice_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    try:
        repository = SqlAlchemyVoiceRepository(session)
        row = await repository.get_session(body.organization_id, body.session_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Voice session was not found")
        intent = await _service(session).record_transcript(
            body.organization_id, body.session_id, body.transcript
        )
        confirmation_id = await repository.create_confirmation(
            body.organization_id,
            body.session_id,
            UUID(str(row["user_id"])),
            intent,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "intent_type": intent.intent_type,
        "confirmation_id": str(confirmation_id),
        "requires_confirmation": intent.requires_confirmation,
    }


@router.post("/internal/artifacts", include_in_schema=False)
async def ingest_voice_artifact(
    body: ArtifactRequest, request: Request, session: DatabaseSession
) -> dict[str, str]:
    supplied = request.headers.get("X-Voice-Executor-Secret", "")
    expected = request.app.state.application_settings.voice_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    try:
        content = base64.b64decode(body.content_base64, validate=True)
        key, digest = LocalArtifactStore(
            request.app.state.application_settings.voice_artifact_root
        ).put(body.organization_id, body.session_id, body.artifact_type, content)
        artifact_id = await SqlAlchemyVoiceRepository(session).add_artifact(
            body.organization_id, body.session_id, body.artifact_type, key, digest
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Artifact is invalid") from error
    return {"id": str(artifact_id), "object_key": key}


@router.post("/internal/status", include_in_schema=False)
async def report_voice_status(
    body: StatusRequest, request: Request, session: DatabaseSession
) -> dict[str, bool]:
    supplied = request.headers.get("X-Voice-Executor-Secret", "")
    expected = request.app.state.application_settings.voice_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    updated = await SqlAlchemyVoiceRepository(session).complete_synthesis(
        body.organization_id, body.session_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Voice session status is not updatable")
    return {"updated": True}
