"""SQLAlchemy implementations of authentication persistence ports."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aether.auth.domain import OAuthIdentity, OAuthProvider, Session, User
from aether.infrastructure.persistence.models import OAuthIdentityModel, SessionModel, UserModel


class SqlAlchemyAuthenticationRepository:
    """Auth repository backed by the transaction session supplied by the API dependency."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_identity(self, provider: OAuthProvider, subject: str) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .join(OAuthIdentityModel, OAuthIdentityModel.user_id == UserModel.id)
            .where(
                OAuthIdentityModel.provider == provider.value,
                OAuthIdentityModel.provider_subject == subject,
            )
        )
        model = result.scalar_one_or_none()
        return (
            None if model is None else User(model.id, model.email, model.display_name, model.status)
        )

    async def create_user_from_identity(self, identity: OAuthIdentity) -> User:
        user = UserModel(
            id=uuid4(), email=identity.email, display_name=identity.display_name, status="active"
        )
        self._session.add(user)
        await self._session.flush()
        self._session.add(
            OAuthIdentityModel(
                id=uuid4(),
                user_id=user.id,
                provider=identity.provider.value,
                provider_subject=identity.subject,
                email=identity.email,
                email_verified=identity.email_verified,
            )
        )
        await self._session.flush()
        return User(user.id, user.email, user.display_name, user.status)

    async def create_session(
        self,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        parent_session_id: UUID | None,
    ) -> Session:
        model = SessionModel(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            parent_session_id=parent_session_id,
        )
        self._session.add(model)
        await self._session.flush()
        return Session(
            model.id, model.user_id, model.refresh_token_hash, model.expires_at, model.revoked_at
        )

    async def get_session(self, session_id: UUID) -> Session | None:
        model = await self._session.get(SessionModel, session_id)
        return (
            None
            if model is None
            else Session(
                model.id,
                model.user_id,
                model.refresh_token_hash,
                model.expires_at,
                model.revoked_at,
            )
        )

    async def revoke_session(self, session_id: UUID, revoked_at: datetime) -> None:
        await self._session.execute(
            update(SessionModel)
            .where(SessionModel.id == session_id, SessionModel.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
