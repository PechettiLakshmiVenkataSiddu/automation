"""Typed application errors safe to translate at an interface boundary."""


class AetherError(Exception):
    """Base exception for expected domain and application failures."""


class AuthenticationError(AetherError):
    """Authentication failed without disclosing sensitive verification details."""


class AuthorizationError(AetherError):
    """The authenticated principal is not permitted to perform an action."""


class ConfigurationError(AetherError):
    """A required security configuration is invalid or incomplete."""
