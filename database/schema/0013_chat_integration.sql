-- Phase 20: Chat Integration. Apply after 0012_email.sql.

CREATE TABLE chat_connections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider varchar(64) NOT NULL DEFAULT 'slack' CHECK (provider IN ('slack', 'teams')),
    access_token text NOT NULL,
    refresh_token text NOT NULL,
    scopes text[] NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX chat_conn_user_idx ON chat_connections (organization_id, user_id, provider);

CREATE TABLE chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider varchar(64) NOT NULL DEFAULT 'slack',
    channel_id varchar(255) NOT NULL,
    thread_ts varchar(255),
    message_text text NOT NULL,
    sender_id varchar(255) NOT NULL,
    status varchar(32) NOT NULL CHECK (status IN ('received', 'sent')),
    received_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX chat_messages_channel_idx ON chat_messages (organization_id, channel_id);

CREATE TABLE chat_proposals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id varchar(255) NOT NULL,
    message_text text NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    decision_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
