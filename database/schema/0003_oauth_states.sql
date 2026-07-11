BEGIN;

CREATE TABLE oauth_authorization_states (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider varchar(32) NOT NULL CHECK (provider IN ('google', 'github')),
    state_hash char(64) NOT NULL UNIQUE,
    code_verifier varchar(128) NOT NULL,
    nonce varchar(128),
    redirect_uri text NOT NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > created_at)
);
CREATE INDEX oauth_authorization_states_active_idx ON oauth_authorization_states (expires_at) WHERE consumed_at IS NULL;

COMMIT;
