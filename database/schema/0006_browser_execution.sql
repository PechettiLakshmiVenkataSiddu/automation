-- Phase 13: isolated browser-executor authority. Apply after 0005_workflow_execution.sql.

CREATE TABLE browser_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    workflow_run_id uuid REFERENCES workflow_runs(id) ON DELETE RESTRICT,
    workflow_step_id uuid REFERENCES workflow_steps(id) ON DELETE RESTRICT,
    requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    status varchar(32) NOT NULL CHECK (status IN ('queued', 'running', 'awaiting_approval', 'succeeded', 'failed', 'cancelled')),
    allowed_hosts jsonb NOT NULL,
    credential_reference uuid REFERENCES oauth_connections(id) ON DELETE RESTRICT,
    cancellation_requested_at timestamptz,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX browser_tasks_org_status_idx ON browser_tasks (organization_id, status, created_at DESC);

CREATE TABLE browser_task_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    browser_task_id uuid NOT NULL REFERENCES browser_tasks(id) ON DELETE CASCADE,
    artifact_type varchar(32) NOT NULL CHECK (artifact_type IN ('trace', 'screenshot')),
    object_key text NOT NULL,
    sha256 char(64) NOT NULL,
    redacted boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, object_key)
);
CREATE INDEX browser_task_artifacts_task_idx ON browser_task_artifacts (organization_id, browser_task_id);
