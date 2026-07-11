"""Ports implemented by persistence and provider adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from aether.auth.domain import OAuthIdentity, OAuthProvider, Session, User


class IdentityProvider(Protocol):
    """Exchanges an OAuth code for a verified external identity."""

    async def exchange_code(
        self, code: str, redirect_uri: str, nonce: str | None, code_verifier: str
    ) -> OAuthIdentity:
        """Return an identity only after provider verification succeeds."""


class AuthenticationRepository(Protocol):
    """Persistence boundary for auth commands; all methods run transactionally."""

    async def get_user_by_identity(self, provider: OAuthProvider, subject: str) -> User | None:
        """Find a user by a provider-specific subject."""

    async def create_user_from_identity(self, identity: OAuthIdentity) -> User:
        """Create a user and linked provider identity atomically."""

    async def create_session(
        self,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        parent_session_id: UUID | None,
    ) -> Session:
        """Persist a newly issued session."""

    async def get_session(self, session_id: UUID) -> Session | None:
        """Return a session by identifier."""

    async def revoke_session(self, session_id: UUID, revoked_at: datetime) -> None:
        """Revoke a session idempotently."""
