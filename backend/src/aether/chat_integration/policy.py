"""Slack/Teams sync scopes, target channels, and injection security policy validator."""

from __future__ import annotations

import re


class ChatPolicyEvaluator:
    """Enforces boundaries on chat OAuth scopes, channel formats, and message safety."""

    def __init__(self, scopes: list[str]) -> None:
        self.scopes = scopes

    def has_sufficient_scopes(self, provider: str) -> bool:
        """Confirm that OAuth scopes permit writing messages."""
        if provider == "slack":
            required = {
                "chat:write",
                "chat:write.public",
                "chat:write:user",
                "incoming-webhook",
            }
        else:
            required = {"ChannelMessage.Send", "Chat.ReadWrite"}
        return any(scope in required for scope in self.scopes)

    def is_safe_incoming_message(self, text_content: str) -> bool:
        """Analyze message payload to prevent context hijacking or prompt injections."""
        dangerous_patterns = [
            r"sudo\s",
            r"rm\s+-rf",
            r"delete\s+all",
            r"execute\s+command",
            r"system\s+exec",
            r"env\s+vars",
        ]
        text_lower = text_content.lower()
        return all(not re.search(pattern, text_lower) for pattern in dangerous_patterns)

    def is_channel_permitted(self, channel_id: str) -> bool:
        """Verify target channel ID matches valid Slack/Teams formats."""
        is_slack = bool(re.match(r"^[CGD][A-Z0-9]+$", channel_id))
        is_teams = channel_id.startswith("teams-")
        return is_slack or is_teams
