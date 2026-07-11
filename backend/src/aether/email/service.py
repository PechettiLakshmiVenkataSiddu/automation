"""Orchestrator for Google Gmail synchronization and draft composition approvals."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from aether.email.policy import EmailPolicyEvaluator
from aether.infrastructure.persistence.email_repository import SqlAlchemyEmailRepository


class EmailSyncService:
    def __init__(self, repository: SqlAlchemyEmailRepository) -> None:
        self._repository = repository

    async def sync_emails(self, org: UUID, user: UUID) -> int:
        """Fetch remote messages and save to cache. Returns count of messages synced."""
        connection = await self._repository.get_connection(org, user)
        if not connection:
            raise ValueError("No active email connection is established.")

        # Simulate fetching remote updates (mock Gmail API inbox response)
        mock_messages: list[dict[str, Any]] = [
            {
                "google_message_id": "gmail-mock-message-1",
                "thread_id": "thread-mock-1",
                "from_address": "client@company.com",
                "to_addresses": ["owner@company.com"],
                "subject": "Project Proposal Draft",
                "body_snippet": "Hi, please review the attached document.",
                "body_text": "Hi, please review the attached document. Best, Client.",
                "status": "received",
                "received_at": datetime.now(UTC),
            }
        ]

        synced_count = 0
        for msg in mock_messages:
            await self._repository.upsert_message(
                org,
                user,
                msg["google_message_id"],
                msg["thread_id"],
                msg["from_address"],
                msg["to_addresses"],
                msg["subject"],
                msg["body_snippet"],
                msg["body_text"],
                msg["status"],
                msg["received_at"],
            )
            synced_count += 1

        return synced_count

    async def propose_email(
        self,
        org: UUID,
        user: UUID,
        recipient_address: str,
        subject: str | None,
        body_text: str,
        attachments: list[dict[str, Any]],
    ) -> UUID:
        """Propose an outgoing email. All composings pause as a pending draft for review."""
        connection = await self._repository.get_connection(org, user)
        if not connection:
            raise ValueError("No active email connection is established.")

        # 1. Enforce OAuth scopes check
        policy = EmailPolicyEvaluator(connection["scopes"])
        if not policy.has_sufficient_scopes():
            raise ValueError("OAuth connection has insufficient permissions to send email.")

        # 2. Validate recipient structure and blocklist domains
        policy.validate_recipient(recipient_address)

        # 3. Validate attachment format safety
        policy.validate_attachments(attachments)

        # 4. Save proposal in draft pending queue
        proposal_id = await self._repository.create_proposal(
            org, user, recipient_address, subject, body_text, attachments
        )
        return proposal_id

    async def approve_proposal(
        self,
        org: UUID,
        proposal_id: UUID,
        decided_by: UUID,
        approved: bool,
        reason: str | None = None,
    ) -> bool:
        """Resolve a pending email proposal. Simulates sending and logs in cache if approved."""
        proposal = await self._repository.get_proposal(org, proposal_id)
        if not proposal or proposal["status"] != "pending":
            raise ValueError("Email proposal is not in a pending state.")

        # Update status
        status_val = "approved" if approved else "rejected"
        await self._repository.update_proposal_status(
            org, proposal_id, status_val, decided_by, reason
        )

        if approved:
            # Commit sent email record to cache representing delivery
            google_message_id = f"gmail-sent-{uuid4()}"
            await self._repository.upsert_message(
                org,
                proposal["user_id"],
                google_message_id,
                f"thread-{uuid4()}",
                "owner@company.com",
                [proposal["recipient_address"]],
                proposal["subject"],
                proposal["body_text"][:80],
                proposal["body_text"],
                "sent",
                datetime.now(UTC),
            )

        return True
class EmailSyncManager:
    """Namespace container class for email components helper."""
    pass
