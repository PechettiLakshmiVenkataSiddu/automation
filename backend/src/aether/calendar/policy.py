"""Google Calendar sync scopes and write permission evaluator."""

from __future__ import annotations


class CalendarPolicyEvaluator:
    """Enforces boundaries on scopes, permitted resources, and scheduling safety."""

    def __init__(self, permitted_calendars: list[str], scopes: list[str]) -> None:
        self.permitted_calendars = permitted_calendars
        self.scopes = scopes

    def is_calendar_permitted(self, calendar_id: str) -> bool:
        """Verify if target calendar ID falls within permitted synchronization list."""
        if "*" in self.permitted_calendars:
            return True
        return calendar_id in self.permitted_calendars

    def has_sufficient_scopes(self) -> bool:
        """Confirm that OAuth scopes permit event modifications."""
        required = {
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        }
        return any(scope in required for scope in self.scopes)

    def requires_approval(self, conflict_detected: bool) -> bool:
        """Evaluate if an event proposal requires explicit human approval."""
        # Double scheduling conflicts always gate execution
        return bool(conflict_detected)
