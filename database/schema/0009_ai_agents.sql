-- Phase 16: AI Agents. Apply after 0008_voice_assistant.sql.

CREATE TABLE agent_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    goal text NOT NULL,
    status varchar(32) NOT NULL CHECK (status IN (
        'queued', 'running', 'awaiting_approval', 'completed', 'failed', 'cancelled'
    )),
    budget_limit_usd numeric(10,4) NOT NULL DEFAULT 1.0000,
    budget_spent_usd numeric(10,4) NOT NULL DEFAULT 0.0000,
    time_limit_seconds integer NOT NULL DEFAULT 600,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX agent_runs_org_idx ON agent_runs (organization_id, status, created_at DESC);

CREATE TABLE agent_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    agent_run_id uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_index integer NOT NULL,
    assigned_agent varchar(64) NOT NULL,
    description text NOT NULL,
    requires_approval boolean NOT NULL DEFAULT false,
    status varchar(32) NOT NULL CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'rejected'
    )),
    input_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    output_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, agent_run_id, step_index)
);

CREATE TABLE agent_audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    agent_run_id uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_id uuid REFERENCES agent_plans(id) ON DELETE SET NULL,
    action_type varchar(64) NOT NULL CHECK (action_type IN (
        'policy_check', 'tool_call', 'memory_access', 'state_transition', 'budget_spent', 'error'
    )),
    message text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX agent_audit_org_run_idx ON agent_audit_logs (organization_id, agent_run_id);
