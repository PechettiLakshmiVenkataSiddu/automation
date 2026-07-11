"""OAuth and session HTTP endpoints."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from aether.auth.domain import OAuthProvider
from aether.auth.oauth import GitHubOAuthAdapter, GoogleOAuthAdapter
from aether.auth.service import AuthenticationService
from aether.auth.settings import AuthenticationSettings
from aether.auth.tokens import TokenService
from aether.bootstrap.settings import ApplicationSettings
from aether.infrastructure.persistence.auth_repository import SqlAlchemyAuthenticationRepository
from aether.infrastructure.persistence.models import OAuthAuthorizationStateModel
from aether.interfaces.http.dependencies import DatabaseSession

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


def _provider(value: str) -> OAuthProvider:
    try:
        return OAuthProvider(value)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported OAuth provider"
        ) from error


def _hash_state(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pkce_challenge(verifier: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def _set_session_cookies(
    response: Response, session_id: UUID, refresh_token: str, secure: bool
) -> None:
    response.set_cookie(
        "aether_refresh",
        refresh_token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/v1/auth",
    )
    response.set_cookie(
        "aether_session",
        str(session_id),
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/v1/auth",
    )


def _clear_session_cookies(response: Response, secure: bool) -> None:
    response.delete_cookie(
        "aether_refresh", path="/v1/auth", secure=secure, httponly=True, samesite="lax"
    )
    response.delete_cookie(
        "aether_session", path="/v1/auth", secure=secure, httponly=True, samesite="lax"
    )


@router.get("/{provider}/login")
async def begin_login(
    provider: str,
    request: Request,
    session: DatabaseSession,
    redirect_uri: str = Query(min_length=1),
) -> RedirectResponse:
    """Persist a one-time state/PKCE verifier then redirect to the selected provider."""
    selected = _provider(provider)
    app_settings: ApplicationSettings = request.app.state.application_settings
    auth_settings: AuthenticationSettings = request.app.state.authentication_settings
    raw_state, verifier, nonce = (
        secrets.token_urlsafe(32),
        secrets.token_urlsafe(64),
        secrets.token_urlsafe(32),
    )
    session.add(
        OAuthAuthorizationStateModel(
            id=uuid4(),
            provider=selected.value,
            state_hash=_hash_state(raw_state),
            code_verifier=verifier,
            nonce=nonce if selected is OAuthProvider.GOOGLE else None,
            redirect_uri=redirect_uri,
            expires_at=datetime.now(UTC) + timedelta(seconds=app_settings.oauth_state_ttl_seconds),
        )
    )
    if selected is OAuthProvider.GOOGLE:
        query = {
            "client_id": auth_settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": raw_state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(query)}"
    else:
        query = {
            "client_id": auth_settings.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": raw_state,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
        }
        url = f"https://github.com/login/oauth/authorize?{urlencode(query)}"
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/{provider}/callback")
async def finish_login(
    provider: str, request: Request, session: DatabaseSession, code: str, state: str
) -> Response:
    """Consume one OAuth state and issue a cookie-backed refresh session."""
    selected = _provider(provider)
    result = await session.execute(
        select(OAuthAuthorizationStateModel).where(
            OAuthAuthorizationStateModel.state_hash == _hash_state(state)
        )
    )
    oauth_state = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if (
        oauth_state is None
        or oauth_state.provider != selected.value
        or oauth_state.consumed_at is not None
        or oauth_state.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state"
        )
    oauth_state.consumed_at = now
    auth_settings: AuthenticationSettings = request.app.state.authentication_settings
    async_client: httpx.AsyncClient = request.app.state.http_client
    adapter = (
        GoogleOAuthAdapter(auth_settings, async_client)
        if selected is OAuthProvider.GOOGLE
        else GitHubOAuthAdapter(auth_settings, async_client)
    )
    auth_service = AuthenticationService(
        SqlAlchemyAuthenticationRepository(session), TokenService(auth_settings)
    )
    tokens = await auth_service.authenticate_oauth_code(
        selected,
        adapter,
        code,
        oauth_state.redirect_uri,
        oauth_state.nonce,
        oauth_state.code_verifier,
        now,
    )
    session_id = TokenService(auth_settings).verify_access_token(tokens.access_token).session_id
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _set_session_cookies(
        response,
        session_id,
        tokens.refresh_token,
        request.app.state.application_settings.cookie_secure,
    )
    return response


@router.post("/refresh")
async def refresh_session(request: Request, session: DatabaseSession) -> Response:
    """Rotate a refresh session from HTTP-only cookies and return a new access token."""
    refresh_token, session_value = (
        request.cookies.get("aether_refresh"),
        request.cookies.get("aether_session"),
    )
    if refresh_token is None or session_value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is missing"
        )
    try:
        session_id = UUID(session_value)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid"
        ) from error
    auth_settings: AuthenticationSettings = request.app.state.authentication_settings
    service = AuthenticationService(
        SqlAlchemyAuthenticationRepository(session), TokenService(auth_settings)
    )
    tokens = await service.rotate_refresh_token(session_id, refresh_token)
    new_session_id = TokenService(auth_settings).verify_access_token(tokens.access_token).session_id
    response = Response(
        content='{"access_token":"' + tokens.access_token + '"}', media_type="application/json"
    )
    _set_session_cookies(
        response,
        new_session_id,
        tokens.refresh_token,
        request.app.state.application_settings.cookie_secure,
    )
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, session: DatabaseSession) -> Response:
    """Revoke the current session and clear its browser cookies."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    session_value = request.cookies.get("aether_session")
    if session_value is not None:
        try:
            session_id = UUID(session_value)
            auth_settings: AuthenticationSettings = request.app.state.authentication_settings
            await AuthenticationService(
                SqlAlchemyAuthenticationRepository(session), TokenService(auth_settings)
            ).revoke_session(session_id)
        except ValueError:
            pass
    _clear_session_cookies(response, request.app.state.application_settings.cookie_secure)
    return response
