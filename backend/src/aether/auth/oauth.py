"""OAuth provider adapters that return verified external identities."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import jwt

from aether.auth.domain import OAuthIdentity, OAuthProvider
from aether.auth.settings import AuthenticationSettings
from aether.shared.errors import AuthenticationError


class GoogleOAuthAdapter:
    """Google OpenID Connect code exchange with signed ID-token verification."""

    _token_url = "https://oauth2.googleapis.com/token"
    _jwks_url = "https://www.googleapis.com/oauth2/v3/certs"

    def __init__(self, settings: AuthenticationSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._jwks_client = jwt.PyJWKClient(self._jwks_url, cache_keys=True)

    async def exchange_code(
        self, code: str, redirect_uri: str, nonce: str | None, code_verifier: str
    ) -> OAuthIdentity:
        response = await self._client.post(
            self._token_url,
            data={
                "code": code,
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret.get_secret_value(),
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
            },
        )
        if response.is_error:
            raise AuthenticationError("Google authorization failed")
        id_token = response.json().get("id_token")
        if not isinstance(id_token, str):
            raise AuthenticationError("Google did not return an ID token")
        try:
            signing_key = await asyncio.to_thread(
                self._jwks_client.get_signing_key_from_jwt, id_token
            )
            claims: dict[str, Any] = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._settings.google_client_id,
                issuer=["https://accounts.google.com", "accounts.google.com"],
                options={"require": ["sub", "email", "email_verified", "exp", "iat"]},
            )
        except jwt.PyJWTError as error:
            raise AuthenticationError("Google identity token is invalid") from error
        if nonce is not None and claims.get("nonce") != nonce:
            raise AuthenticationError("Google identity nonce is invalid")
        if claims.get("email_verified") is not True:
            raise AuthenticationError("Google email is not verified")
        return OAuthIdentity(
            provider=OAuthProvider.GOOGLE,
            subject=str(claims["sub"]),
            email=str(claims["email"]),
            email_verified=True,
            display_name=str(claims.get("name") or claims["email"]),
            avatar_url=str(claims["picture"]) if claims.get("picture") else None,
        )


class GitHubOAuthAdapter:
    """GitHub OAuth code exchange requiring a verified primary email address."""

    _token_url = "https://github.com/login/oauth/access_token"
    _user_url = "https://api.github.com/user"
    _emails_url = "https://api.github.com/user/emails"

    def __init__(self, settings: AuthenticationSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def exchange_code(
        self, code: str, redirect_uri: str, nonce: str | None, code_verifier: str
    ) -> OAuthIdentity:
        del nonce
        token_response = await self._client.post(
            self._token_url,
            headers={"Accept": "application/json"},
            data={
                "code": code,
                "client_id": self._settings.github_client_id,
                "client_secret": self._settings.github_client_secret.get_secret_value(),
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
        )
        if token_response.is_error:
            raise AuthenticationError("GitHub authorization failed")
        access_token = token_response.json().get("access_token")
        if not isinstance(access_token, str):
            raise AuthenticationError("GitHub did not return an access token")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
        }
        user_response, emails_response = (
            await self._client.get(self._user_url, headers=headers),
            await self._client.get(self._emails_url, headers=headers),
        )
        if user_response.is_error or emails_response.is_error:
            raise AuthenticationError("GitHub identity lookup failed")
        user: dict[str, Any] = user_response.json()
        emails: list[dict[str, Any]] = emails_response.json()
        verified_email = next(
            (
                item
                for item in emails
                if item.get("primary") is True
                and item.get("verified") is True
                and isinstance(item.get("email"), str)
            ),
            None,
        )
        if verified_email is None or not isinstance(user.get("id"), int):
            raise AuthenticationError("GitHub account lacks a verified primary email")
        return OAuthIdentity(
            provider=OAuthProvider.GITHUB,
            subject=str(user["id"]),
            email=verified_email["email"],
            email_verified=True,
            display_name=str(user.get("name") or user.get("login") or verified_email["email"]),
            avatar_url=str(user["avatar_url"]) if user.get("avatar_url") else None,
        )
