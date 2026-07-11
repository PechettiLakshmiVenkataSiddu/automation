-- Phase 17: Developer Tools. Apply after 0009_ai_agents.sql.

CREATE TABLE developer_sandboxes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name varchar(128) NOT NULL,
    sandbox_path text NOT NULL,
    status varchar(32) NOT NULL CHECK (status IN ('active', 'archived')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX dev_sandboxes_org_idx ON developer_sandboxes (organization_id);

CREATE TABLE developer_commands (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    sandbox_id uuid NOT NULL REFERENCES developer_sandboxes(id) ON DELETE CASCADE,
    command_line text NOT NULL,
    status varchar(32) NOT NULL CHECK (status IN (
        'queued', 'running', 'awaiting_approval', 'succeeded', 'failed', 'cancelled'
    )),
    exit_code integer,
    stdout_redacted text,
    stderr_redacted text,
    timeout_seconds integer NOT NULL DEFAULT 30,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX dev_commands_status_idx ON developer_commands (organization_id, status);

CREATE TABLE developer_command_approvals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    command_id uuid NOT NULL REFERENCES developer_commands(id) ON DELETE CASCADE,
    requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    decided_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    policy_version varchar(64) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    decision_reason text,
    expires_at timestamptz NOT NULL,
    decided_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((status = 'pending' AND decided_at IS NULL) OR (status <> 'pending' AND decided_at IS NOT NULL))
);
