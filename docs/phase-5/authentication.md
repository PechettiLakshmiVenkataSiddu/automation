# Phase 5 — Authentication

## Delivered scope

This phase delivers the authentication domain and adapters for Google OAuth, GitHub OAuth, signed access tokens, rotating refresh tokens, and role-aware organization membership. The module is transport-independent so it can be wired into FastAPI routes in Phase 6 without coupling authentication rules to HTTP handlers.

## Authentication flow

1. The web client begins an OAuth authorization-code flow with PKCE and an opaque, server-stored state value.
2. The future API route exchanges the code through the selected provider adapter.
3. The adapter verifies the provider identity, including Google ID-token signature, issuer, audience, expiry, and nonce; GitHub email is required to be verified.
4. `AuthenticationService` resolves or creates the user identity, starts a session, and returns a signed access token plus an opaque refresh token.
5. Refresh exchanges validate the current session token hash, revoke the old session, create a new session, and return a new token pair.
6. Sign-out revokes the targeted session; privileged authorization uses the membership role resolved by the application layer.

## Security controls

- OAuth tokens and state are never returned to logs or persisted as plaintext.
- Access tokens are HMAC-SHA-256 signed, include issuer/audience/subject/session/JTI/expiry claims, and must be short lived.
- Refresh tokens are 256-bit opaque random values and only an Argon2id hash is persisted.
- OAuth identities are unique by `(provider, provider_subject)` and verified email is required.
- Authentication configuration fails fast if the signing secret lacks 32 bytes of entropy.
- Google ID tokens are verified against Google's JWKS; GitHub profile email must be verified and primary.

## Phase 6 dependency

FastAPI routes, database repositories, CSRF-protected OAuth state storage, rate limits, cookie policy, and deployment secret injection require the Backend Foundation composition root. They are intentionally not invented in this phase. The interfaces in `backend/src/aether/auth` are the contracts Phase 6 must implement.

## Tests

Run the authentication unit suite after installing the Python development dependency group:

```text
python -m pytest backend/tests/auth
```
