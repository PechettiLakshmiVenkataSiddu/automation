from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.chat_integration.service import ChatSyncService


class FakeChatRepository:
    def __init__(self) -> None:
        self.connections: dict[UUID, dict[str, Any]] = {}
        self.messages: list[dict[str, Any]] = []
        self.proposals: dict[UUID, dict[str, Any]] = {}

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

    async def create_proposal(
        self,
        org: UUID,
        user: UUID,
        channel_id: str,
        message_text: str,
    ) -> UUID:
        proposal_id = uuid4()
        self.proposals[proposal_id] = {
            "id": proposal_id,
            "organization_id": org,
            "user_id": user,
            "channel_id": channel_id,
            "message_text": message_text,
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
async def test_propose_chat_draft_only() -> None:
    repo = FakeChatRepository()
    service = ChatSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    repo.connections[user_id] = {
        "provider": "slack",
        "scopes": ["chat:write"],
    }

    proposal_id = await service.propose_message(org_id, user_id, "slack", "C12345", "Welcome team!")
    assert proposal_id in repo.proposals
    assert repo.proposals[proposal_id]["status"] == "pending"
    assert len(repo.messages) == 0  # Draft only


@pytest.mark.asyncio
async def test_approve_chat_proposal_executes_dispatch() -> None:
    repo = FakeChatRepository()
    service = ChatSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    repo.connections[user_id] = {
        "provider": "slack",
        "scopes": ["chat:write"],
    }

    proposal_id = await service.propose_message(
        org_id, user_id, "slack", "C12345", "Milestone complete"
    )
    await service.approve_proposal(org_id, proposal_id, user_id, approved=True)

    assert repo.proposals[proposal_id]["status"] == "approved"
    assert len(repo.messages) == 1
    assert repo.messages[0]["message_text"] == "Milestone complete"
