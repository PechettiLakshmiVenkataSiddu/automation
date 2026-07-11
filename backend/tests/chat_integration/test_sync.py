from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.chat_integration.service import ChatSyncService


class FakeChatRepository:
    """Mock chat repository for unit testing."""

    def __init__(self) -> None:
        self.connections: dict[UUID, dict[str, Any]] = {}
        self.messages: list[dict[str, Any]] = []

    async def get_connection(self, org: UUID, user: UUID, provider: str) -> dict[str, Any] | None:
        return self.connections.get(user)

    async def upsert_message(
        self,
        org: UUID,
        user: UUID,
        provider: str,
        channel_id: str,
        thread_ts: str | None,
        message_text: str,
        sender_id: str,
        status: str,
        received_at: datetime,
    ) -> UUID:
        msg_id = uuid4()
        self.messages.append({
            "id": msg_id,
            "organization_id": org,
            "user_id": user,
            "provider": provider,
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "message_text": message_text,
            "sender_id": sender_id,
            "status": status,
            "received_at": received_at,
        })
        return msg_id


@pytest.mark.asyncio
async def test_chat_sync_injection_quarantine() -> None:
    repo = FakeChatRepository()
    service = ChatSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Setup active connection
    repo.connections[user_id] = {
        "provider": "slack",
        "scopes": ["chat:write"],
    }

    synced_count = await service.sync_messages(org_id, user_id, "slack", "C12345")
    # Only safe message should be synced, malicious skipped
    assert synced_count == 1
    assert len(repo.messages) == 1
    assert repo.messages[0]["message_text"] == "Hello, please list active tasks."
