"""JWT issuance/verification and opaque refresh-token generation."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from aether.auth.settings import AuthenticationSettings
from aether.shared.errors import AuthenticationError


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    """Verified claims that identify a user session."""

    user_id: UUID
    session_id: UUID
    token_id: UUID
    expires_at: datetime


class TokenService:
    """Produces scoped, short-lived access credentials and hashed refresh credentials."""

    _algorithm = "HS256"

    def __init__(self, settings: AuthenticationSettings) -> None:
        self._settings = settings
        self._refresh_hasher = PasswordHasher()

    def issue_access_token(
        self, user_id: UUID, session_id: UUID, now: datetime | None = None
    ) -> tuple[str, datetime]:
        """Issue a signed access token tied to exactly one refresh session."""
        issued_at = now or datetime.now(UTC)
        expires_at = issued_at + timedelta(seconds=self._settings.access_token_ttl_seconds)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": str(uuid4()),
            "iss": self._settings.jwt_issuer,
            "aud": self._settings.jwt_audience,
            "iat": issued_at,
            "nbf": issued_at,
            "exp": expires_at,
        }
        token = jwt.encode(
            payload, self._settings.jwt_secret.get_secret_value(), algorithm=self._algorithm
        )
        return token, expires_at

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        """Validate a token's signature, registered claims, and UUID-shaped identifiers."""
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret.get_secret_value(),
                algorithms=[self._algorithm],
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={"require": ["sub", "sid", "jti", "exp", "iat", "nbf"]},
            )
            return AccessTokenClaims(
                user_id=UUID(payload["sub"]),
                session_id=UUID(payload["sid"]),
                token_id=UUID(payload["jti"]),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise AuthenticationError("Invalid access token") from error

    def create_refresh_token(self) -> tuple[str, str]:
        """Generate a high-entropy opaque token and its Argon2id hash."""
        raw_token = secrets.token_urlsafe(48)
        return raw_token, self._refresh_hasher.hash(raw_token)

    def verify_refresh_token(self, raw_token: str, stored_hash: str) -> bool:
        """Constant-work verification of an opaque refresh credential."""
        try:
            return self._refresh_hasher.verify(stored_hash, raw_token)
        except (InvalidHashError, VerifyMismatchError):
            return False
