-- Phase 11: durable workflow execution controls. Apply after 0004_memory_governance.sql.

ALTER TABLE workflow_runs
    ADD COLUMN cancellation_requested_at timestamptz,
    ADD COLUMN execution_lease_expires_at timestamptz,
    ADD COLUMN execution_attempt integer NOT NULL DEFAULT 0 CHECK (execution_attempt >= 0),
    ADD COLUMN correlation_id uuid NOT NULL DEFAULT gen_random_uuid();

ALTER TABLE outbox_events
    ADD COLUMN dispatch_lease_expires_at timestamptz,
    ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN dead_lettered_at timestamptz;

CREATE TABLE workflow_idempotency_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    idempotency_key varchar(255) NOT NULL,
    operation varchar(128) NOT NULL,
    resource_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, operation, idempotency_key)
);

CREATE TABLE workflow_run_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    workflow_run_id uuid NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    event_type varchar(64) NOT NULL,
    actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    detail jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX workflow_run_events_run_idx ON workflow_run_events (organization_id, workflow_run_id, occurred_at);

CREATE INDEX workflow_runs_lease_idx
    ON workflow_runs (execution_lease_expires_at)
    WHERE status IN ('queued', 'running', 'retry_scheduled');
CREATE INDEX outbox_dispatchable_idx ON outbox_events (next_attempt_at, occurred_at)
    WHERE published_at IS NULL AND dead_lettered_at IS NULL;
