BEGIN;

CREATE TYPE schedule_status AS ENUM ('scheduled', 'active', 'completed', 'missed');

CREATE TABLE schedule_entries (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status schedule_status NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX schedule_entries_user_start_idx ON schedule_entries (user_id, start_time);
CREATE INDEX schedule_entries_org_idx ON schedule_entries (organization_id);

COMMIT;