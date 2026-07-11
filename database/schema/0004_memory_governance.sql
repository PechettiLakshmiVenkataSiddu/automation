-- Phase 10: consented, user-controlled long-term memory.
-- Apply after 0001_core.sql, 0002_auth_identities.sql, and 0003_oauth_states.sql.

ALTER TABLE memories
    ADD COLUMN visibility varchar(32) NOT NULL DEFAULT 'owner_only'
        CHECK (visibility IN ('owner_only')),
    ADD COLUMN retention_until timestamptz,
    ADD COLUMN corrected_from_memory_id uuid REFERENCES memories(id) ON DELETE RESTRICT,
    ADD COLUMN deleted_reason varchar(64),
    ADD COLUMN deleted_by_user_id uuid REFERENCES users(id) ON DELETE RESTRICT;

CREATE TABLE memory_consents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    enabled boolean NOT NULL,
    policy_version varchar(64) NOT NULL,
    granted_at timestamptz,
    withdrawn_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((enabled AND granted_at IS NOT NULL AND withdrawn_at IS NULL)
        OR (NOT enabled AND withdrawn_at IS NOT NULL)),
    UNIQUE (organization_id, user_id)
);

CREATE TABLE memory_deletion_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    requested_by_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    scope varchar(32) NOT NULL CHECK (scope IN ('memory', 'all_memories')),
    memory_id uuid REFERENCES memories(id) ON DELETE RESTRICT,
    status varchar(32) NOT NULL DEFAULT 'completed'
        CHECK (status IN ('completed', 'failed')),
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((scope = 'all_memories' AND memory_id IS NULL)
        OR (scope = 'memory' AND memory_id IS NOT NULL))
);

CREATE INDEX memories_retrieval_idx
    ON memories (organization_id, user_id, updated_at DESC)
    WHERE deleted_at IS NULL AND visibility = 'owner_only';
CREATE INDEX memory_deletion_requests_user_idx
    ON memory_deletion_requests (organization_id, user_id, created_at DESC);
