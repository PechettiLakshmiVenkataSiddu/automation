"""FastAPI dependencies for request context and persistence."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aether.bootstrap.database import session_scope


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide exactly one transaction-scoped database session per request."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async for session in session_scope(factory):
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
