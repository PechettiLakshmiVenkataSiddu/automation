from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.email.service import EmailSyncService


class FakeEmailRepository:
    """Mock email repository for synchronous unit testing."""

    def __init__(self) -> None:
        self.connections: dict[UUID, dict[str, Any]] = {}
        self.messages: dict[str, dict[str, Any]] = {}

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


@pytest.mark.asyncio
async def test_email_sync_successful_cache() -> None:
    repo = FakeEmailRepository()
    service = EmailSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Enable connection
    repo.connections[user_id] = {
        "scopes": ["https://www.googleapis.com/auth/gmail.send"],
    }

    synced = await service.sync_emails(org_id, user_id)
    assert synced == 1
    assert "gmail-mock-message-1" in repo.messages
    assert repo.messages["gmail-mock-message-1"]["subject"] == "Project Proposal Draft"
