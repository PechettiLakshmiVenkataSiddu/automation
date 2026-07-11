from __future__ import annotations

from aether.calendar.policy import CalendarPolicyEvaluator


def test_calendar_policy_permitted_list() -> None:
    # Match specific allowed calendar IDs
    policy = CalendarPolicyEvaluator(permitted_calendars=["primary", "work-calendar"], scopes=[])
    assert policy.is_calendar_permitted("primary") is True
    assert policy.is_calendar_permitted("work-calendar") is True
    assert policy.is_calendar_permitted("personal-calendar") is False

    # Match wildcard
    wildcard_policy = CalendarPolicyEvaluator(permitted_calendars=["*"], scopes=[])
    assert wildcard_policy.is_calendar_permitted("personal-calendar") is True


def test_calendar_policy_sufficient_scopes() -> None:
    # Missing required scopes
    read_only = CalendarPolicyEvaluator(
        permitted_calendars=[], scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    assert read_only.has_sufficient_scopes() is False

    # Matches allowed write scopes
    write_events = CalendarPolicyEvaluator(
        permitted_calendars=[], scopes=["https://www.googleapis.com/auth/calendar.events"]
    )
    assert write_events.has_sufficient_scopes() is True

    full_calendar = CalendarPolicyEvaluator(
        permitted_calendars=[], scopes=["https://www.googleapis.com/auth/calendar"]
    )
    assert full_calendar.has_sufficient_scopes() is True
