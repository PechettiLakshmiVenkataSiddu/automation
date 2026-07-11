BEGIN;

CREATE TABLE oauth_identities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    provider varchar(32) NOT NULL CHECK (provider IN ('google', 'github')),
    provider_subject varchar(255) NOT NULL,
    email citext NOT NULL,
    email_verified boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (provider, provider_subject),
    UNIQUE (user_id, provider)
);
CREATE INDEX oauth_identities_email_idx ON oauth_identities (email);

COMMIT;
