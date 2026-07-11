from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from aether.auth.domain import OAuthIdentity, OAuthProvider, Session, User
from aether.auth.service import AuthenticationService
from aether.auth.settings import AuthenticationSettings
from aether.auth.tokens import TokenService
from aether.shared.errors import AuthenticationError


class FakeRepository:
    def __init__(self) -> None:
        self.user = User(uuid4(), "user@example.test", "User", "active")
        self.session: Session | None = None
        self.revoked_ids: list[UUID] = []

    async def get_user_by_identity(self, provider: OAuthProvider, subject: str) -> User | None:
        del provider, subject
        return self.user

    async def create_user_from_identity(self, identity: OAuthIdentity) -> User:
        del identity
        return self.user

    async def create_session(
        self,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        parent_session_id: UUID | None,
    ) -> Session:
        del parent_session_id
        self.session = Session(uuid4(), user_id, refresh_token_hash, expires_at, None)
        return self.session

    async def get_session(self, session_id: UUID) -> Session | None:
        return self.session if self.session and self.session.id == session_id else None

    async def revoke_session(self, session_id: UUID, revoked_at: datetime) -> None:
        self.revoked_ids.append(session_id)
        if self.session and self.session.id == session_id:
            self.session = Session(
                self.session.id,
                self.session.user_id,
                self.session.refresh_token_hash,
                self.session.expires_at,
                revoked_at,
            )


def settings() -> AuthenticationSettings:
    return AuthenticationSettings(
        AUTH_JWT_SECRET=SecretStr("a" * 32),
        GOOGLE_OAUTH_CLIENT_ID="google-client",
        GOOGLE_OAUTH_CLIENT_SECRET=SecretStr("google-secret"),
        GITHUB_OAUTH_CLIENT_ID="github-client",
        GITHUB_OAUTH_CLIENT_SECRET=SecretStr("github-secret"),
    )


@pytest.mark.asyncio
async def test_refresh_rotation_revokes_prior_session() -> None:
    repository = FakeRepository()
    service = AuthenticationService(repository, TokenService(settings()))
    now = datetime(2026, 7, 10, tzinfo=UTC)
    first = await service._issue_session(repository.user.id, None, now)
    first_session = repository.session
    assert first_session is not None

    second = await service.rotate_refresh_token(
        first_session.id, first.refresh_token, now + timedelta(minutes=1)
    )

    assert first_session.id in repository.revoked_ids
    assert second.refresh_token != first.refresh_token


@pytest.mark.asyncio
async def test_replayed_refresh_token_is_rejected() -> None:
    repository = FakeRepository()
    service = AuthenticationService(repository, TokenService(settings()))
    issued = await service._issue_session(repository.user.id, None, datetime.now(UTC))
    session = repository.session
    assert session is not None
    await service.rotate_refresh_token(session.id, issued.refresh_token)

    with pytest.raises(AuthenticationError):
        await service.rotate_refresh_token(session.id, issued.refresh_token)
