from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.email.service import EmailSyncService


class FakeEmailRepository:
    def __init__(self) -> None:
        self.connections: dict[UUID, dict[str, Any]] = {}
        self.messages: dict[str, dict[str, Any]] = {}
        self.proposals: dict[UUID, dict[str, Any]] = {}

    async def get_connection(self, org: UUID, user: UUID) -> dict[str, Any] | None:
        return self.connections.get(user)

    async def upsert_message(
        self,
        org: UUID,
        user: UUID,
        google_message_id: str,
        thread_id: str,
        from_address: str,
        to_addresses: list[str],
        subject: str | None,
        body_snippet: str | None,
        body_text: str | None,
        status: str,
        received_at: datetime,
    ) -> UUID:
        msg_id = uuid4()
        self.messages[google_message_id] = {
            "id": msg_id,
            "organization_id": org,
            "user_id": user,
            "google_message_id": google_message_id,
            "thread_id": thread_id,
            "from_address": from_address,
            "to_addresses": to_addresses,
            "subject": subject,
            "body_snippet": body_snippet,
            "body_text": body_text,
            "status": status,
            "received_at": received_at,
        }
        return msg_id

    async def create_proposal(
        self,
        org: UUID,
        user: UUID,
        recipient_address: str,
        subject: str | None,
        body_text: str,
        attachments: list[dict[str, Any]],
    ) -> UUID:
        proposal_id = uuid4()
        self.proposals[proposal_id] = {
            "id": proposal_id,
            "organization_id": org,
            "user_id": user,
            "recipient_address": recipient_address,
            "subject": subject,
            "body_text": body_text,
            "attachments": attachments,
            "status": "pending",
        }
        return proposal_id

    async def get_proposal(self, org: UUID, proposal_id: UUID) -> dict[str, Any] | None:
        return self.proposals.get(proposal_id)

    async def update_proposal_status(
        self,
        org: UUID,
        proposal_id: UUID,
        status: str,
        approved_by: UUID | None = None,
        reason: str | None = None,
    ) -> bool:
        if proposal_id not in self.proposals:
            return False
        self.proposals[proposal_id]["status"] = status
        self.proposals[proposal_id]["approved_by"] = approved_by
        return True


@pytest.mark.asyncio
async def test_propose_email_draft_only() -> None:
    repo = FakeEmailRepository()
    service = EmailSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    repo.connections[user_id] = {
        "scopes": ["https://www.googleapis.com/auth/gmail.send"],
    }

    proposal_id = await service.propose_email(
        org_id, user_id, "recipient@company.com", "Project Status", "Everything is on track.", []
    )
    assert proposal_id in repo.proposals
    assert repo.proposals[proposal_id]["status"] == "pending"
    assert len(repo.messages) == 0  # Not sent yet


@pytest.mark.asyncio
async def test_approve_email_proposal_executes_send() -> None:
    repo = FakeEmailRepository()
    service = EmailSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    repo.connections[user_id] = {
        "scopes": ["https://www.googleapis.com/auth/gmail.send"],
    }

    proposal_id = await service.propose_email(
        org_id, user_id, "recipient@company.com", "Milestone 1", "Body text details", []
    )

    # Approve
    await service.approve_proposal(org_id, proposal_id, user_id, approved=True)
    assert repo.proposals[proposal_id]["status"] == "approved"
    assert len(repo.messages) == 1

    # Verify message cached as sent
    sent_msg = list(repo.messages.values())[0]
    assert sent_msg["status"] == "sent"
    assert sent_msg["to_addresses"] == ["recipient@company.com"]
