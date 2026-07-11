"""Authenticated principal resolution for protected HTTP routes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aether.auth.tokens import TokenService
from aether.infrastructure.persistence.auth_repository import SqlAlchemyAuthenticationRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.shared.errors import AuthenticationError

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: UUID
    session_id: UUID


async def get_principal(
    request: Request,
    session: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    """Resolve a valid, non-revoked access-token session."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Bearer authentication is required")
    claims = TokenService(request.app.state.authentication_settings).verify_access_token(
        credentials.credentials
    )
    stored = await SqlAlchemyAuthenticationRepository(session).get_session(claims.session_id)
    if stored is None or stored.user_id != claims.user_id or stored.revoked_at is not None:
        raise AuthenticationError("Access session is not active")
    return Principal(claims.user_id, claims.session_id)
