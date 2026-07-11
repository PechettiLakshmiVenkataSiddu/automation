# Phase 14 — Desktop Automation

Desktop automation is confined to an isolated executor boundary. API and Celery worker code create durable PostgreSQL task records and transport only an organization-scoped, short-lived signed task grant. Desktop UI control libraries are prohibited from API and worker processes.

## Supported operating systems

| Runtime surface            | Supported | Notes                                                                                                               |
| -------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------- |
| Executor container (Linux) | Yes       | Primary runtime. Uses Xvfb, Openbox, xdotool, and scrot inside a non-root container with no host mounts by default. |
| macOS host integration     | Planned   | Requires a separately reviewed native agent; the control plane never executes desktop work locally.                 |
| Windows host integration   | Planned   | Same boundary as macOS; grants remain organization-scoped and short-lived.                                          |

Production desktop execution runs only inside the hardened Linux executor container until a host agent passes the same threat-model review.

## Threat model

| Threat                            | Control                                                                                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Host-wide UI takeover             | Application allowlists reject wildcards, absolute paths, and `all`/`/` patterns. Grants bind one organization and one task.                                   |
| Credential exfiltration           | Raw credential material never appears in grants, queue payloads, artifacts, or logs. Artifacts are redacted before persistence.                               |
| Network egress from desktop tasks | `network_enabled` defaults to false and is rejected by policy and executor validation.                                                                        |
| Unauthorized filesystem access    | Mount paths must be relative sandbox entries inside the executor temp workspace; absolute paths and `..` are rejected.                                        |
| Sensitive UI without approval     | `click`, `type_text`, and `paste` require explicit owner/admin approval before a grant can be issued.                                                         |
| Replay or duplicate submission    | `idempotency_key` is unique per organization on `desktop_tasks`.                                                                                              |
| Executor escape                   | Ephemeral sandbox directory, resource timeout (1–120 seconds), non-root container user, no privileged host mounts, verified cleanup before success reporting. |
| Cross-tenant artifact access      | Object keys use `desktop/{organization_id}/{task_id}/...` and PostgreSQL enforces `organization_id` on every task and artifact row.                           |

## Control-plane behavior

Each desktop action declares an operation, target application, timeout, application allowlist, optional relative mount allowlist, optional encrypted credential reference, idempotency key, and risk class. `DesktopTaskService` evaluates policy, writes a tenant-scoped audit event, creates an approval record for sensitive actions, and persists the task in PostgreSQL.

Task and artifact records use `organization_id` predicates. Screenshots and window dumps are redacted before persistence and stored under tenant-scoped object keys. Executor grants are HMAC-signed, bind both task and organization, and expire within ten minutes.

Authenticated API routes:

- `POST /v1/desktop-tasks` — create task after policy, audit, approval, and idempotency checks
- `GET /v1/desktop-tasks/{id}` — read task status
- `POST /v1/desktop-tasks/{id}/cancel` — request cancellation
- `POST /v1/desktop-tasks/{id}/grant` — issue a short-lived grant (owner/admin only, queued tasks only)
- `POST /v1/desktop-tasks/approvals/{id}/decision` — approve or reject sensitive actions
- `POST /v1/desktop-tasks/internal/artifacts` — executor-authenticated artifact ingestion
- `POST /v1/desktop-tasks/internal/status` — executor-authenticated completion and cleanup reporting

## Executor protocol

`POST http://desktop-executor:8081/execute`

Request:

```json
{
  "grant": "<encoded>.<signature>",
  "action": {
    "organization_id": "<uuid>",
    "task_id": "<uuid>",
    "operation": "screenshot",
    "target_application": "calculator",
    "allowed_applications": ["calculator"],
    "allowed_mounts": [],
    "network_enabled": false,
    "timeout_seconds": 30
  }
}
```

Success (200):

```json
{
  "task_id": "<uuid>",
  "artifact": { "id": "...", "object_key": "desktop/..." },
  "text": "<redacted window text>",
  "cleanup_verified": true
}
```

Failure (422):

```json
{
  "error": "desktop_task_rejected",
  "detail": "<redacted error message>"
}
```

The executor verifies the grant, re-validates the action allowlist, bounds execution to the configured timeout, captures artifacts only through the internal ingestion route, reports cleanup verification, and removes the sandbox workspace on all paths.

## Container verification

On a Docker-capable host, build the isolated service with:

```bash
docker build -t aether-desktop-executor services/desktop-executor
```

Supply distinct 32-byte-or-longer `DESKTOP_GRANT_SECRET` and `DESKTOP_EXECUTOR_SECRET` values plus the private control-plane URL. Verify a low-risk `screenshot` task succeeds for an allowlisted application; verify host-wide targets, absolute mount paths, network-enabled tasks, expired or tampered grants, cancellation, artifact tenant keys, redaction metadata, SHA-256 hashes, and sandbox cleanup before approving this phase.

Configure the control plane with `DESKTOP_ARTIFACT_ROOT`, `DESKTOP_GRANT_SECRET`, and `DESKTOP_EXECUTOR_SECRET`. Apply migration `0007_desktop_execution.sql` after `0006_browser_execution.sql`.

Run `ruff check backend/src backend/tests services`, `mypy backend/src backend/tests services`, `pytest`, and `pnpm check` to validate the phase.
