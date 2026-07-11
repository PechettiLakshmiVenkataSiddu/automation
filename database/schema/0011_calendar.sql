-- Phase 18: Calendar Integration. Apply after 0010_developer_tools.sql.

CREATE TABLE calendar_connections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider varchar(64) NOT NULL DEFAULT 'google',
    access_token text NOT NULL,
    refresh_token text NOT NULL,
    scopes text[] NOT NULL,
    permitted_calendars text[] NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX calendar_conn_user_idx ON calendar_connections (organization_id, user_id);

CREATE TABLE calendar_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_event_id varchar(255) NOT NULL,
    summary text NOT NULL,
    description text,
    start_time timestamptz NOT NULL,
    end_time timestamptz NOT NULL,
    attendees jsonb NOT NULL DEFAULT '[]',
    status varchar(32) NOT NULL CHECK (status IN ('confirmed', 'tentative', 'cancelled')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX calendar_event_google_idx ON calendar_events (organization_id, google_event_id);
CREATE INDEX calendar_events_time_idx ON calendar_events (organization_id, start_time, end_time);

CREATE TABLE calendar_proposals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary text NOT NULL,
    description text,
    start_time timestamptz NOT NULL,
    end_time timestamptz NOT NULL,
    attendees jsonb NOT NULL DEFAULT '[]',
    status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    conflict_detected boolean NOT NULL DEFAULT false,
    decision_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
