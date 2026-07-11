"""Notification quiet hours boundary and delivery channels policy evaluator."""

from __future__ import annotations

from datetime import time


class NotificationPolicyEvaluator:
    """Enforces boundaries on quiet hours and handles active channel dispatch resolution."""

    def is_in_quiet_hours(
        self, quiet_start: time | None, quiet_end: time | None, current_time: time
    ) -> bool:
        """Verify if current time falls within active quiet hours window."""
        if quiet_start is None or quiet_end is None:
            return False

        if quiet_start <= quiet_end:
            return quiet_start <= current_time <= quiet_end

        # Quiet hours cross midnight (e.g. 22:00 to 06:00)
        return current_time >= quiet_start or current_time <= quiet_end

    def determine_active_channels(
        self, pref_channels: list[str], in_quiet_hours: bool
    ) -> list[str]:
        """Determine active delivery channels, suppressing during quiet hours."""
        if in_quiet_hours:
            # Suppress external push/email alerts
            return ["in_app"]
        return pref_channels
