from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import SecretStr

from aether.auth.settings import AuthenticationSettings
from aether.auth.tokens import TokenService
from aether.shared.errors import AuthenticationError


def settings() -> AuthenticationSettings:
    return AuthenticationSettings(
        AUTH_JWT_SECRET=SecretStr("a" * 32),
        GOOGLE_OAUTH_CLIENT_ID="google-client",
        GOOGLE_OAUTH_CLIENT_SECRET=SecretStr("google-secret"),
        GITHUB_OAUTH_CLIENT_ID="github-client",
        GITHUB_OAUTH_CLIENT_SECRET=SecretStr("github-secret"),
    )


def test_access_token_round_trip() -> None:
    service = TokenService(settings())
    user_id, session_id = uuid4(), uuid4()
    now = datetime.now(UTC).replace(microsecond=0)

    token, expires_at = service.issue_access_token(user_id, session_id, now)
    claims = service.verify_access_token(token)

    assert claims.user_id == user_id
    assert claims.session_id == session_id
    assert claims.expires_at == expires_at


def test_tampered_access_token_is_rejected() -> None:
    service = TokenService(settings())
    token, _ = service.issue_access_token(uuid4(), uuid4())

    with pytest.raises(AuthenticationError):
        service.verify_access_token(f"{token}x")


def test_refresh_token_is_opaque_and_verifiable() -> None:
    service = TokenService(settings())
    raw_token, token_hash = service.create_refresh_token()

    assert raw_token not in token_hash
    assert service.verify_refresh_token(raw_token, token_hash)
    assert not service.verify_refresh_token("wrong-token", token_hash)
