"""FastAPI composition root for the control-plane HTTP service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from aether.auth.settings import AuthenticationSettings
from aether.bootstrap.database import create_engine, create_session_factory
from aether.bootstrap.settings import ApplicationSettings
from aether.interfaces.http import (
    auth,
    automation,
    browser,
    chat,
    dashboard,
    desktop,
    health,
    memory,
    voice,
    workflows,
)
from aether.interfaces.http.errors import install_error_handlers


def create_app(
    application_settings: ApplicationSettings, authentication_settings: AuthenticationSettings
) -> FastAPI:
    """Build a fully configured ASGI application without global mutable configuration."""
    engine: AsyncEngine = create_engine(application_settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0), follow_redirects=False
        )
        try:
            yield
        finally:
            await app.state.http_client.aclose()
            await engine.dispose()

    app = FastAPI(
        title="Aether API", version="0.1.0", lifespan=lifespan, docs_url="/docs", redoc_url=None
    )
    app.state.application_settings = application_settings
    app.state.authentication_settings = authentication_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(application_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def correlation_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(chat.router)
    app.include_router(memory.router)
    app.include_router(automation.router)
    app.include_router(workflows.router)
    app.include_router(browser.router)
    app.include_router(desktop.router)
    app.include_router(voice.router)
    return app
