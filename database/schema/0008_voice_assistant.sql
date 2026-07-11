-- Phase 15: consented voice assistant authority. Apply after 0007_desktop_execution.sql.

CREATE TABLE voice_consents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    capture_enabled boolean NOT NULL,
    retention_enabled boolean NOT NULL DEFAULT false,
    policy_version varchar(64) NOT NULL,
    granted_at timestamptz,
    withdrawn_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((capture_enabled AND granted_at IS NOT NULL AND withdrawn_at IS NULL)
        OR (NOT capture_enabled AND withdrawn_at IS NOT NULL)),
    UNIQUE (organization_id, user_id)
);

CREATE TABLE voice_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    conversation_id uuid REFERENCES conversations(id) ON DELETE SET NULL,
    status varchar(32) NOT NULL CHECK (status IN (
        'active', 'transcribing', 'awaiting_confirmation', 'synthesizing',
        'completed', 'failed', 'cancelled'
    )),
    retention_mode varchar(32) NOT NULL DEFAULT 'ephemeral'
        CHECK (retention_mode IN ('ephemeral', 'retained')),
    transcript text,
    idempotency_key varchar(255),
    cancellation_requested_at timestamptz,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, idempotency_key)
);
CREATE INDEX voice_sessions_org_user_idx ON voice_sessions (organization_id, user_id, created_at DESC);

CREATE TABLE voice_session_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    voice_session_id uuid NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    artifact_type varchar(32) NOT NULL CHECK (artifact_type IN ('audio_input', 'audio_output', 'transcript')),
    object_key text NOT NULL,
    sha256 char(64) NOT NULL,
    redacted boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, object_key)
);
CREATE INDEX voice_session_artifacts_session_idx
    ON voice_session_artifacts (organization_id, voice_session_id);

CREATE TABLE voice_command_confirmations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    voice_session_id uuid NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    decided_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    intent_type varchar(64) NOT NULL,
    intent_payload jsonb NOT NULL,
    policy_version varchar(64) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'rejected', 'expired')),
    decision_reason text,
    expires_at timestamptz NOT NULL,
    decided_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((status = 'pending' AND decided_at IS NULL) OR (status <> 'pending' AND decided_at IS NOT NULL))
);
CREATE INDEX voice_command_confirmations_pending_idx
    ON voice_command_confirmations (organization_id, expires_at) WHERE status = 'pending';
