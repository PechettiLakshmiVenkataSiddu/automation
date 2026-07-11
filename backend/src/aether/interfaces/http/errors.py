"""Consistent HTTP error envelopes without sensitive internals."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR

from aether.ai.chat import ChatProviderError
from aether.shared.errors import AuthenticationError, AuthorizationError


def install_error_handlers(app: FastAPI) -> None:
    """Install expected-domain error translation and a safe final fallback."""

    @app.exception_handler(AuthenticationError)
    async def authentication_error(_: Request, error: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "authentication_failed", "message": str(error)}},
            status_code=HTTP_401_UNAUTHORIZED,
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error(_: Request, error: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "authorization_denied", "message": str(error)}},
            status_code=HTTP_401_UNAUTHORIZED,
        )

    @app.exception_handler(ChatProviderError)
    async def provider_error(_: Request, error: ChatProviderError) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "provider_unavailable", "message": str(error)}}, status_code=503
        )

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, __: Exception) -> JSONResponse:
        error_id = str(uuid4())
        return JSONResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                    "id": error_id,
                }
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
