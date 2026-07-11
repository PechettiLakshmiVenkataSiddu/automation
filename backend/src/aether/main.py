"""ASGI entrypoint for Aether's FastAPI control plane."""

from aether.auth.settings import AuthenticationSettings
from aether.bootstrap.settings import ApplicationSettings
from aether.interfaces.http.app import create_app

app = create_app(ApplicationSettings(), AuthenticationSettings())  # type: ignore[call-arg]
