"""Gmail sync scopes, attachment format, and recipient security policy validator."""

from __future__ import annotations

import re
from typing import Any


class EmailPolicyEvaluator:
    """Enforces boundaries on Gmail scopes, file attachment types, and recipients."""

    def __init__(self, scopes: list[str]) -> None:
        self.scopes = scopes
        self.blocked_extensions = {".exe", ".bat", ".sh", ".cmd", ".msi", ".jar", ".vbs"}

    def has_sufficient_scopes(self) -> bool:
        """Verify connection scopes support send/compose actions."""
        required = {
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://mail.google.com/",
        }
        return any(scope in required for scope in self.scopes)

    def validate_recipient(self, recipient: str) -> None:
        """Validate recipient address structure and block list domains."""
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", recipient):
            raise ValueError(f"Invalid email address structure: '{recipient}'")

        blocked_domains = {"malicious.com", "spam.org"}
        domain = recipient.split("@")[-1].lower()
        if domain in blocked_domains:
            raise ValueError(f"Recipient domain '{domain}' is blocked by safety policy.")

    def validate_attachments(self, attachments: list[dict[str, Any]]) -> None:
        """Validate file extensions of attachments to block potential malware."""
        for attachment in attachments:
            filename = attachment.get("filename", "").lower()
            for ext in self.blocked_extensions:
                if filename.endswith(ext):
                    raise ValueError(
                        f"Unsafe attachment extension blocked: '{filename}'"
                    )
