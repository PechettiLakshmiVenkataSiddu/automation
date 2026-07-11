"""Pydantic request validation schemas for Slack/Teams integrations."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ChatConnectionRequest(BaseModel):
    organization_id: UUID
    provider: str = Field(default="slack", pattern="^(slack|teams)$")
    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    scopes: list[str] = Field(default_factory=list)
    expires_in_seconds: int = Field(default=3600, gt=0)


class ChatProposalRequest(BaseModel):
    organization_id: UUID
    channel_id: str = Field(min_length=1, max_length=256)
    message_text: str = Field(min_length=1)


class ProposalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=1000)
