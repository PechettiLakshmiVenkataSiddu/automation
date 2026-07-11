-- Phase 21: Notifications. Apply after 0013_chat_integration.sql.

CREATE TABLE notification_preferences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channels varchar(32)[] NOT NULL DEFAULT '{"in_app"}',
    quiet_hours_start time,
    quiet_hours_end time,
    unsubscribed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX notification_pref_user_idx ON notification_preferences (organization_id, user_id);

CREATE TABLE notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title text NOT NULL,
    message text NOT NULL,
    level varchar(32) NOT NULL DEFAULT 'info' CHECK (level IN ('info', 'warning', 'error')),
    status varchar(32) NOT NULL DEFAULT 'unread' CHECK (status IN ('unread', 'read')),
    sent_channels varchar(32)[] NOT NULL DEFAULT '{}',
    dedupe_hash varchar(255),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX notifications_user_status_idx ON notifications (organization_id, user_id, status);
CREATE INDEX notifications_dedupe_idx ON notifications (dedupe_hash, created_at);
