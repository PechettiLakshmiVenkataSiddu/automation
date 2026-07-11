# Phase 15 — Voice Assistant

Voice capture, transcription, synthesis, and command parsing run through a consent-first control plane. Audio is ephemeral by default; retention requires explicit user consent. Whisper transcription and Piper speech synthesis execute only inside the isolated `voice-executor` service, never in API or Celery worker processes.

## Consent and retention

Users must grant voice capture consent per organization before creating a session. Retention is opt-in and disabled whenever capture consent is withdrawn. Without retention consent, the control plane stores only transcripts and command metadata required for confirmation; raw audio is processed ephemerally inside the executor sandbox and deleted after transcription or synthesis.

`voice_consents` binds `organization_id` and `user_id`. Sessions inherit `retention_mode` of `ephemeral` or `retained` from the active consent record at creation time.

## Threat model

| Threat                            | Control                                                                                                        |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Non-consensual recording          | `capture_enabled` must be true before session creation                                                         |
| Indefinite audio storage          | Default `ephemeral` retention; artifacts persisted only when `retention_enabled`                               |
| Cross-tenant access               | Every query, grant, artifact key, audit event, and idempotency record includes `organization_id`               |
| Prompt-injected voice commands    | Parsed intents require explicit user confirmation before any external effect                                   |
| Credential leakage in transcripts | `redact_transcript()` masks token-shaped values before persistence                                             |
| Executor escape                   | Ephemeral temp workspace, bounded audio size (10 MB) and duration (120s), non-root container, verified cleanup |
| Replay                            | `idempotency_key` unique per organization on `voice_sessions`                                                  |

## Control-plane API

Authenticated routes:

- `PUT /v1/voice/consent` — enable/disable capture and retention consent
- `GET /v1/voice/consent?organization_id=` — read consent state
- `POST /v1/voice/sessions` — create session after consent check
- `GET /v1/voice/sessions/{id}?organization_id=` — read session status and transcript
- `POST /v1/voice/sessions/{id}/cancel` — cancel active session
- `POST /v1/voice/sessions/{id}/audio` — upload audio for transcription
- `POST /v1/voice/sessions/{id}/grant` — issue short-lived HMAC grant for executor dispatch
- `POST /v1/voice/sessions/{id}/commands` — parse transcript into typed intent
- `POST /v1/voice/confirmations/{id}/decision` — confirm or reject parsed command
- `POST /v1/voice/sessions/{id}/synthesize` — request Piper TTS for confirmed assistant text

Executor-authenticated internal routes:

- `POST /v1/voice/internal/transcript`
- `POST /v1/voice/internal/artifacts`
- `POST /v1/voice/internal/status`

## Executor protocol

`POST http://voice-executor:8082/transcribe`

```json
{
  "grant": "<encoded>.<signature>",
  "action": {
    "organization_id": "<uuid>",
    "session_id": "<uuid>",
    "format": "webm",
    "content_base64": "..."
  }
}
```

`POST http://voice-executor:8082/synthesize`

```json
{
  "grant": "<encoded>.<signature>",
  "action": {
    "organization_id": "<uuid>",
    "session_id": "<uuid>",
    "text": "Confirmed assistant response"
  }
}
```

Grants bind organization and session, expire within ten minutes, and are verified with `VOICE_GRANT_SECRET`. Artifact ingestion and status reporting authenticate with `VOICE_EXECUTOR_SECRET`.

## Frontend

`apps/web/app/voice/page.tsx` provides consent controls, session management, audio upload, transcript command parsing, and an accessible confirmation prompt with `aria-live="polite"`.

## Configuration

```
VOICE_GRANT_SECRET=<32+ byte secret>
VOICE_EXECUTOR_SECRET=<32+ byte secret>
VOICE_ARTIFACT_ROOT=.artifacts
VOICE_WHISPER_MODEL=tiny
VOICE_PIPER_VOICE=/path/to/voice.onnx
```

Apply migration `0008_voice_assistant.sql` after `0007_desktop_execution.sql`.

Run `ruff check backend/src backend/tests services`, `mypy backend/src backend/tests services`, `pytest`, and `pnpm check` to validate the phase.
