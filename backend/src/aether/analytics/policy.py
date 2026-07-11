"""Enforcement of analytics query privacy masks and tenant segregation guidelines."""

from __future__ import annotations

from typing import Any


class AnalyticsPolicyEvaluator:
    """Enforces privacy constraints on event logging, scrubbing sensitive keys from metadata."""

    def scrub_event_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        """Filter metadata to remove tokens, authorization hashes, or credentials."""
        if metadata is None:
            return None

        scrubbed: dict[str, Any] = {}
        sensitive_keys = {
            "password",
            "secret",
            "key",
            "auth",
            "credential",
            "access_token",
            "refresh_token",
        }

        for k, v in metadata.items():
            k_lower = k.lower()
            if any(term in k_lower for term in sensitive_keys) or k_lower == "token":
                scrubbed[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sub_scrubbed = self.scrub_event_metadata(v)
                if sub_scrubbed is not None:
                    scrubbed[k] = sub_scrubbed
            else:
                scrubbed[k] = v

        return scrubbed
