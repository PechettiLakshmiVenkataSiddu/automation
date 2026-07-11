-- Phase 23: Analytics. Apply after 0015_admin_panel.sql.

CREATE TABLE usage_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    event_name varchar(100) NOT NULL,
    category varchar(32) NOT NULL CHECK (category IN ('model_call', 'tool_execution', 'workflow_step', 'api_sync')),
    cost numeric(12, 6) NOT NULL DEFAULT 0.0,
    units integer NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX usage_events_org_cat_idx ON usage_events (organization_id, category, created_at DESC);

CREATE TABLE workflow_metrics (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workflow_id uuid NOT NULL,
    run_count integer NOT NULL DEFAULT 0,
    success_count integer NOT NULL DEFAULT 0,
    failure_count integer NOT NULL DEFAULT 0,
    avg_duration_seconds numeric(10, 2) NOT NULL DEFAULT 0.00,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, workflow_id)
);
