-- Phase 19: Email Integration. Apply after 0011_calendar.sql.

CREATE TABLE email_connections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider varchar(64) NOT NULL DEFAULT 'google',
    access_token text NOT NULL,
    refresh_token text NOT NULL,
    scopes text[] NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX email_conn_user_idx ON email_connections (organization_id, user_id);

CREATE TABLE email_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_message_id varchar(255) NOT NULL,
    thread_id varchar(255) NOT NULL,
    from_address text NOT NULL,
    to_addresses text[] NOT NULL,
    subject text,
    body_snippet text,
    body_text text,
    status varchar(32) NOT NULL CHECK (status IN ('received', 'draft', 'sent')),
    received_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX email_message_google_idx ON email_messages (organization_id, google_message_id);
CREATE INDEX email_messages_thread_idx ON email_messages (organization_id, thread_id);

CREATE TABLE email_proposals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_address text NOT NULL,
    subject text,
    body_text text NOT NULL,
    attachments jsonb NOT NULL DEFAULT '[]',
    status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    decision_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
