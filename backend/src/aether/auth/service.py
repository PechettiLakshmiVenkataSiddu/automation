"""Transport-independent authentication use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from aether.auth.domain import OAuthProvider, TokenPair
from aether.auth.ports import AuthenticationRepository, IdentityProvider
from aether.auth.tokens import TokenService
from aether.shared.errors import AuthenticationError


class AuthenticationService:
    """Coordinates verified provider identity, session issuance, and rotation."""

    def __init__(self, repository: AuthenticationRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    async def authenticate_oauth_code(
        self,
        provider: OAuthProvider,
        adapter: IdentityProvider,
        code: str,
        redirect_uri: str,
        nonce: str | None,
        code_verifier: str,
        now: datetime | None = None,
    ) -> TokenPair:
        """Exchange an OAuth code and establish a user session."""
        identity = await adapter.exchange_code(code, redirect_uri, nonce, code_verifier)
        if identity.provider is not provider or not identity.email_verified:
            raise AuthenticationError("OAuth identity could not be verified")
        user = await self._repository.get_user_by_identity(provider, identity.subject)
        if user is None:
            user = await self._repository.create_user_from_identity(identity)
        if user.status != "active":
            raise AuthenticationError("User is not active")
        return await self._issue_session(user.id, parent_session_id=None, now=now)

    async def rotate_refresh_token(
        self,
        session_id: UUID,
        refresh_token: str,
        now: datetime | None = None,
    ) -> TokenPair:
        """Rotate a valid refresh session; replayed or revoked sessions are rejected."""
        current_time = now or datetime.now(UTC)
        session = await self._repository.get_session(session_id)
        if (
            session is None
            or session.revoked_at is not None
            or session.expires_at <= current_time
            or not self._token_service.verify_refresh_token(
                refresh_token, session.refresh_token_hash
            )
        ):
            raise AuthenticationError("Invalid refresh session")
        await self._repository.revoke_session(session.id, current_time)
        return await self._issue_session(
            session.user_id, parent_session_id=session.id, now=current_time
        )

    async def revoke_session(self, session_id: UUID, now: datetime | None = None) -> None:
        """End a session without exposing whether it existed."""
        await self._repository.revoke_session(session_id, now or datetime.now(UTC))

    async def _issue_session(
        self, user_id: UUID, parent_session_id: UUID | None, now: datetime | None
    ) -> TokenPair:
        current_time = now or datetime.now(UTC)
        refresh_token, refresh_hash = self._token_service.create_refresh_token()
        refresh_expires_at = current_time + timedelta(
            days=self._token_service._settings.refresh_token_ttl_days
        )
        session = await self._repository.create_session(
            user_id, refresh_hash, refresh_expires_at, parent_session_id
        )
        access_token, access_expires_at = self._token_service.issue_access_token(
            user_id, session.id, current_time
        )
        return TokenPair(access_token, refresh_token, access_expires_at, refresh_expires_at)
