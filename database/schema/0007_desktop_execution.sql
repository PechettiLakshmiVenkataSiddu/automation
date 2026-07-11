-- Phase 14: isolated desktop-executor authority. Apply after 0006_browser_execution.sql.

CREATE TABLE desktop_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    workflow_run_id uuid REFERENCES workflow_runs(id) ON DELETE RESTRICT,
    workflow_step_id uuid REFERENCES workflow_steps(id) ON DELETE RESTRICT,
    requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    status varchar(32) NOT NULL CHECK (status IN ('queued', 'running', 'awaiting_approval', 'succeeded', 'failed', 'cancelled')),
    operation varchar(32) NOT NULL,
    target_application varchar(128) NOT NULL,
    allowed_applications jsonb NOT NULL,
    allowed_mounts jsonb NOT NULL DEFAULT '[]'::jsonb,
    network_enabled boolean NOT NULL DEFAULT false,
    credential_reference uuid REFERENCES oauth_connections(id) ON DELETE RESTRICT,
    idempotency_key varchar(255),
    timeout_seconds integer NOT NULL CHECK (timeout_seconds BETWEEN 1 AND 120),
    risk_class varchar(32) NOT NULL,
    cancellation_requested_at timestamptz,
    cleanup_verified_at timestamptz,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, idempotency_key)
);
CREATE INDEX desktop_tasks_org_status_idx ON desktop_tasks (organization_id, status, created_at DESC);

CREATE TABLE desktop_task_approvals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    desktop_task_id uuid NOT NULL REFERENCES desktop_tasks(id) ON DELETE CASCADE,
    requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    decided_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    action_summary jsonb NOT NULL,
    policy_version varchar(64) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired', 'cancelled')),
    decision_reason text,
    expires_at timestamptz NOT NULL,
    decided_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((status = 'pending' AND decided_at IS NULL) OR (status <> 'pending' AND decided_at IS NOT NULL))
);
CREATE INDEX desktop_task_approvals_pending_idx ON desktop_task_approvals (organization_id, expires_at) WHERE status = 'pending';

CREATE TABLE desktop_task_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    desktop_task_id uuid NOT NULL REFERENCES desktop_tasks(id) ON DELETE CASCADE,
    artifact_type varchar(32) NOT NULL CHECK (artifact_type IN ('screenshot', 'trace', 'window_dump')),
    object_key text NOT NULL,
    sha256 char(64) NOT NULL,
    redacted boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, object_key)
);
CREATE INDEX desktop_task_artifacts_task_idx ON desktop_task_artifacts (organization_id, desktop_task_id);
