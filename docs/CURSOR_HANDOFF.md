# Cursor Agent Handoff — Aether

## Workspace and current state

Workspace: `C:\Users\peche\OneDrive\Documents\automation`

Completed phases: 0, 2, 3, 4, 5, 6, 7, 8, and 9. Phase 1 (Software Requirements Specification) is deferred. Start at Phase 10 and complete one phase at a time; stop for approval after each phase.

Do not discard or overwrite existing work. Inspect the existing architecture documents before changing code, preserve database migration order, and use additive forward-compatible migrations.

## Immediate prerequisites

1. Install Python 3.12+ and `uv` or another supported Python package manager.
2. Install pnpm 9+ through Corepack: `corepack enable` then `corepack prepare pnpm@9.15.4 --activate`.
3. Create `.env` from `.env.example`; configure PostgreSQL, OAuth credentials, and an OpenAI-compatible chat provider.
4. Run `pnpm install`, `uv sync --group dev`, migrations, and all current lint/type/test commands before feature work.
5. Repair any validation failures before adding a new phase; previous work has only structural validation because this environment lacked Python and pnpm.

## Existing implementation review required

- Review `docs/phase-0` through `docs/phase-9` and `docs/phase-2/architecture-decision-records.md` before architectural changes.
- Complete the deferred SRS in Phase 1 before a production release; reconcile conflicts with implemented behavior.
- Replace raw SQL where it obstructs maintainability with typed repository methods while retaining parameterized queries and tenant enforcement.
- Add Alembic configuration and convert `database/schema/0001_core.sql` through `0003_oauth_states.sql` into migration history before applying to a shared environment.
- Run and harden OAuth, refresh-token, dashboard, and chat flows under actual integration tests. Do not claim production readiness until this is done.

## Remaining phases

### Phase 10 — Memory

Build user-controlled long-term memory on the existing `memories` table.

- Add typed domain/application/repository layers and migrations needed for memory provenance, visibility, retention, correction, export, and deletion requests.
- Add authenticated CRUD, search, export, forget, and consent endpoints. Enforce organization/user scope on every query.
- Inject only opt-in, non-expired memory into chat through a bounded retrieval policy; expose the source and allow removal.
- Build memory settings/list/edit/delete UI with explicit consent and deletion confirmation.
- Add unit, API authorization, retention, and chat-injection tests.

### Phase 11 — Automation Engine

Build durable workflow execution on `workflows`, `workflow_versions`, `workflow_runs`, `workflow_steps`, `approvals`, `schedules`, and `outbox_events`.

- Add Celery and Redis configuration, queue names, retry classification, idempotency ledger, transactional outbox publisher, dead-letter handling, cancellation, and run state machine enforcement.
- Implement typed trigger/action contracts and risk metadata. Every external action must pass policy evaluation, approval, audit, and idempotency controls.
- Add workflow run APIs, run logs, retry/cancel controls, and tests for duplicate delivery, recovery, approval, and state transitions.

### Phase 12 — Workflow Builder

- Implement a visual, accessible workflow editor with typed nodes, edge validation, draft/version lifecycle, schedule controls, import/export, and templates.
- Add backend validation that rejects cycles unless an explicit supported loop node is used; validate input/output schemas before activation.
- Provide run history, per-step diagnostics, approval prompts, and rollback/clone behavior.

### Phase 13 — Browser Automation

- Run Playwright only in isolated executor containers, never API/worker processes.
- Implement signed task grants, network egress allowlists, per-task credentials, trace/screenshot artifacts with redaction, timeouts, cancellation, and approval policies.
- Add browser tool contracts and integration tests against a controlled test site.

### Phase 14 — Desktop Automation

- Implement a separate hardened executor protocol for desktop tasks; document supported operating systems and threat model.
- Require short-lived grants, explicit approval for sensitive UI actions, restricted mounts/network, artifact sanitization, and cleanup verification.
- Do not grant host-wide unrestricted control.

### Phase 15 — Voice Assistant

- Add consented audio capture/upload, Whisper transcription, Piper speech output, voice-command intent parsing, task confirmation, and retention controls.
- Use streaming where appropriate, never persist audio by default without policy/consent, and test accessibility/failure behavior.

### Phase 16 — AI Agents

- Implement planner, research, coding, email, calendar, task, automation, voice, memory, browser, developer, and AIoT agents as typed orchestrators.
- Agents must never receive implicit authority: use tool allowlists, policy evaluation, scoped memory, approval gates, budget/time limits, traceability, and full audit records.
- Add agent run state, plan visibility, evaluation tests, and failure/recovery behavior.

### Phase 17 — Developer Tools

- Add repository-aware tools, terminal/code execution in isolated sandboxes, code review/task actions, tool permissions, artifact capture, and safe patch approval.
- Enforce path confinement, command allow/deny policy, secret redaction, resource limits, and audit logs.

### Phase 18 — Calendar

- Add Google Calendar integration using scoped OAuth connections; synchronize only permitted resources.
- Implement availability, event proposal/create/update/cancel, reminders, conflict handling, idempotency, approval policy, and revocation behavior.

### Phase 19 — Email

- Add Gmail/approved provider connector, least-privilege scopes, draft-first flows, recipient/attachment validation, send approval, thread history, and delivery auditability.
- Prevent prompt-injected email content from directly authorizing sends or data disclosure.

### Phase 20 — Notifications

- Add durable notification preferences, in-app delivery, email/push channel adapters, retry/deduplication, quiet hours, and unsubscribe controls.

### Phase 21 — Admin Panel

- Implement organization/user/role management, policy configuration, connection management, API-key lifecycle, audit search, retention controls, and break-glass audit flow.
- Require owner/admin authorization and exhaustive audit coverage.

### Phase 22 — Analytics

- Add privacy-conscious product/usage analytics, model/tool cost allocation, workflow reliability metrics, dashboards, exports, access control, and retention policy.
- Keep analytics data separate from operational authorization decisions.

### Phase 23 — Testing

- Establish unit, integration, contract, E2E, security, performance, accessibility, chaos/recovery, migration, and regression test suites.
- Enforce coverage thresholds by risk; add CI gates for lint, formatting, type-checking, tests, dependency scanning, secret scanning, and migration validation.

### Phase 24 — Docker

- Add production-quality Dockerfiles, Compose topology for web/API/workers/scheduler/Postgres/Redis/Chroma/object storage emulator/Nginx, health checks, non-root users, volumes, networks, secrets, and local bootstrap.

### Phase 25 — CI/CD

- Add GitHub Actions with pinned actions, least-privilege permissions, build/test/security/migration jobs, artifact provenance, image scanning/signing, staged deployments, and rollback controls.

### Phase 26 — Deployment

- Produce production environment architecture, managed secrets/TLS, database backup and restoration drills, monitoring/alerting, capacity/runbooks, disaster recovery, incident response, and staged rollout plan.

### Phase 27 — Documentation

- Complete user, admin, API, architecture, security, privacy, operations, disaster recovery, contribution, integration, and release documentation.
- Ensure all docs match the tested implementation and contain no invented behavior.

## Required engineering standards

- Clean Architecture, DDD, SOLID, strict type safety, OWASP-aligned security, structured logs, metrics/traces, correlation IDs, validation, error handling, and full tenant isolation.
- Use `organization_id` scoping in database queries, cache keys, queue messages, object keys, vector filters, and executor grants.
- Do not store plaintext provider credentials, API keys, or refresh tokens. Encrypt secrets at rest and redact them from all logs, errors, traces, and artifacts.
- No TODOs, fake implementations, or static mock dashboard/chat data in completed features.
- Add tests and documentation with each phase. Stop after each approved phase.

## Cursor prompt

Use this as the initial Cursor Agent instruction:

```text
You are continuing the Aether Personal AI Automation Platform at C:\Users\peche\OneDrive\Documents\automation. Read docs/CURSOR_HANDOFF.md, docs/CONTINUATION.md, and all relevant existing phase documents before editing. Preserve existing work and database migration order. First install prerequisites, run the existing validation commands, and fix existing validation failures. Then implement Phase 10 only: user-controlled long-term memory with consent, CRUD/search/export/deletion, strict tenant authorization, bounded chat-memory injection, UI, tests, documentation, and migrations where needed. Do not begin Phase 11 until Phase 10 is fully verified and I approve it. Do not use placeholder or mock implementations.
```
