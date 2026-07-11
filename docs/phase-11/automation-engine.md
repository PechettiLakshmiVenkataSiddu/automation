# Phase 11 — Automation engine

Phase 11 introduces a durable execution layer over the Phase 4 workflow schema. The forward-only migration `0005_workflow_execution.sql` adds execution leases, cancellation requests, an operation-scoped idempotency ledger, correlation IDs, append-only run events, and leased outbox retry/dead-letter fields.

The workflow state machine permits only these transitions: `queued → running/cancelled`, `running → awaiting_approval/retry_scheduled/succeeded/failed/cancelled`, `awaiting_approval → queued/cancelled`, and `retry_scheduled → queued/cancelled`. Terminal states are immutable.

No external action may execute until a typed action contract is evaluated by policy and, when required, approved. `ActionExecutionService` creates a policy audit event, creates approval records for gated actions, and reserves the organization-scoped idempotency record before calling an adapter. A duplicate reservation never reaches an external adapter.

The authenticated API is scoped by `organization_id` on every read and write: `POST /v1/automation/runs`, `GET /v1/automation/runs`, `GET /v1/automation/runs/{id}/logs`, cancel/retry controls, and approval decisions. Active membership is required; viewers cannot mutate runs and only owners/admins may decide approvals.

Workers claim a PostgreSQL lease before transitioning a run to `running`; duplicate Celery delivery is therefore harmless. Cancellation is checked after claiming and persisted before any action. Expired `running` leases are recovered through `retry_scheduled` and re-enqueued atomically. Retry classification permits only transient connection and timeout failures to be retried automatically. Every transition, retry request, cancellation request, and approval decision emits a tenant-scoped run event, while enqueue work is written to `outbox_events` in the same database transaction. The outbox claims events with `FOR UPDATE SKIP LOCKED`, leases each dispatch, exponentially backs off failed dispatches, and dead-letters after ten failures. Redis/Celery are transport only; PostgreSQL remains authoritative.

Celery uses separate `automation` and `outbox` queues, late acknowledgements, worker-loss rejection, and hard/soft task limits. Configure `AUTOMATION_REDIS_URL` and `AUTOMATION_RESULT_BACKEND` in the environment.

Run `ruff check backend/src backend/tests`, `mypy backend/src backend/tests`, `pytest`, and `pnpm check` to validate the phase.
