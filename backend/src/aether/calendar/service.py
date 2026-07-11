"""Orchestrator for Google Calendar sync cycles, availability checks, and scheduling."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from aether.calendar.policy import CalendarPolicyEvaluator
from aether.infrastructure.persistence.calendar_repository import (
    SqlAlchemyCalendarRepository,
)


class CalendarSyncService:
    def __init__(self, repository: SqlAlchemyCalendarRepository) -> None:
        self._repository = repository

    async def sync_events(self, org: UUID, user: UUID) -> int:
        """Fetch remote calendar items and save to cache. Returns count of events synced."""
        connection = await self._repository.get_connection(org, user)
        if not connection:
            raise ValueError("No active calendar connection is established.")

        # Simulate fetching remote delta updates (mock feed representing google calendar response)
        mock_events: list[dict[str, Any]] = [
            {
                "google_event_id": "google-mock-event-1",
                "summary": "Synchronized Status Meeting",
                "description": "Weekly alignment sync",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "attendees": [{"email": "owner@company.com"}],
                "status": "confirmed",
            }
        ]

        synced_count = 0
        for ev in mock_events:
            await self._repository.upsert_event(
                org,
                user,
                ev["google_event_id"],
                ev["summary"],
                ev["description"],
                ev["start_time"],
                ev["end_time"],
                ev["attendees"],
                ev["status"],
            )
            synced_count += 1

        return synced_count

    async def check_availability(
        self, org: UUID, start_time: datetime, end_time: datetime
    ) -> bool:
        """Check if target time overlaps with any confirmed cached events."""
        overlapping = await self._repository.get_events_in_range(
            org, start_time, end_time
        )
        return len(overlapping) > 0

    async def propose_event(
        self,
        org: UUID,
        user: UUID,
        summary: str,
        description: str | None,
        start_time: datetime,
        end_time: datetime,
        attendees: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Propose an event. Pauses in proposals table if safety policy gates it."""
        connection = await self._repository.get_connection(org, user)
        if not connection:
            raise ValueError("No active calendar connection is established.")

        # 1. Enforce Scopes Check
        policy = CalendarPolicyEvaluator(
            connection["permitted_calendars"], connection["scopes"]
        )
        if not policy.has_sufficient_scopes():
            raise ValueError("OAuth connection has insufficient permissions to write events.")

        # 2. Check availability
        conflict = await self.check_availability(org, start_time, end_time)

        # 3. Check if approval is required
        if policy.requires_approval(conflict):
            proposal_id = await self._repository.create_proposal(
                org, user, summary, description, start_time, end_time, attendees, conflict
            )
            return {
                "id": str(proposal_id),
                "type": "proposal",
                "status": "pending",
                "conflict_detected": conflict,
            }

        # Safe to commit directly
        google_event_id = f"google-created-{uuid4()}"
        event_id = await self._repository.upsert_event(
            org,
            user,
            google_event_id,
            summary,
            description,
            start_time,
            end_time,
            attendees,
            "confirmed",
        )
        return {
            "id": str(event_id),
            "type": "event",
            "status": "confirmed",
            "conflict_detected": False,
        }

    async def approve_proposal(
        self,
        org: UUID,
        proposal_id: UUID,
        decided_by: UUID,
        approved: bool,
        reason: str | None = None,
    ) -> bool:
        """Resolve a pending proposal. Commits to cache if approved."""
        proposal = await self._repository.get_proposal(org, proposal_id)
        if not proposal or proposal["status"] != "pending":
            raise ValueError("Proposal is not in a pending state.")

        # Update status
        status_val = "approved" if approved else "rejected"
        await self._repository.update_proposal_status(org, proposal_id, status_val, reason)

        if approved:
            # Commit mock google event write to cache
            google_event_id = f"google-created-{uuid4()}"
            await self._repository.upsert_event(
                org,
                proposal["user_id"],
                google_event_id,
                proposal["summary"],
                proposal["description"],
                proposal["start_time"],
                proposal["end_time"],
                proposal["attendees"],
                "confirmed",
            )

        return True
