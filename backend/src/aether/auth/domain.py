"""Authentication entities and immutable value types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class OAuthProvider(StrEnum):
    """Supported identity providers."""

    GOOGLE = "google"
    GITHUB = "github"


class MembershipRole(StrEnum):
    """Organization roles ordered by administrative capability."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass(frozen=True, slots=True)
class OAuthIdentity:
    """A verified identity asserted by an OAuth provider."""

    provider: OAuthProvider
    subject: str
    email: str
    email_verified: bool
    display_name: str
    avatar_url: str | None


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated product user."""

    id: UUID
    email: str
    display_name: str
    status: str


@dataclass(frozen=True, slots=True)
class Membership:
    """An active user role in an organization."""

    organization_id: UUID
    user_id: UUID
    role: MembershipRole
    status: str


@dataclass(frozen=True, slots=True)
class Session:
    """Refresh-token session state; only the token hash is persisted."""

    id: UUID
    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Credentials returned after successful authentication or rotation."""

    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
