# Services

This directory hosts independently isolated runtime services. Browser, desktop, and voice automation each run in dedicated executor containers that never share a process with the API or Celery workers.

- `browser-executor/` — Playwright-based HTTPS browser automation (Phase 13)
- `desktop-executor/` — Xvfb-based sandboxed desktop automation (Phase 14)
- `voice-executor/` — Whisper transcription and Piper synthesis (Phase 15)

Each executor verifies short-lived HMAC grants, enforces bounded payloads, reports artifacts through executor-authenticated control-plane routes, and verifies cleanup before completion.
