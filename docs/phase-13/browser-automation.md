# Phase 13 — Browser Automation

Browser automation is confined to an isolated executor boundary. API and Celery worker code create durable PostgreSQL task records and transport only an organization-scoped, short-lived signed task grant. Playwright is prohibited from API and worker processes.

Each browser action has a typed operation, HTTPS target, timeout, public-host egress allowlist, and optional encrypted credential reference. Raw credential material never appears in a grant, queue payload, artifact, trace, or log. Targets are rejected unless their hostname is allowlisted and every resolved address is globally routable; this blocks localhost, private, link-local, metadata, and DNS-rebinding addresses.

Task and artifact records use `organization_id` predicates. Screenshots and traces must be redacted before persistence and use tenant-scoped object keys. Executor grants are HMAC-signed, bind both task and organization, and expire within ten minutes.

The browser executor is a separate Playwright container service. It verifies the grant before launch, bounds navigation to 120 seconds, masks password fields before screenshot capture, and closes the browser on all success or failure paths. It sends artifacts only to the internal executor-authenticated ingestion route; the control plane writes artifact bytes to its configured object-store adapter and persists only tenant-scoped keys, hashes, and redaction metadata in PostgreSQL.

## Container verification

On a Docker-capable host, build only the isolated service with `docker build -t aether-browser-executor services/browser-executor`. Supply distinct 32-byte-or-longer `BROWSER_GRANT_SECRET` and `BROWSER_EXECUTOR_SECRET` values plus the private control-plane URL. Verify an allowlisted public HTTPS test site succeeds; then verify localhost, RFC1918, link-local, metadata, and a hostname that resolves to a private address are rejected by both the control plane and executor. Confirm expired/tampered grants, cancellation, artifact tenant keys, redaction, and browser cleanup before approving this phase.

The executor image was built locally with Docker Desktop and an invalid-grant container request returned HTTP 422 before browser launch. A positive execution test still requires a running private Aether control plane and controlled HTTPS target because artifact ingestion is intentionally internal-only.
