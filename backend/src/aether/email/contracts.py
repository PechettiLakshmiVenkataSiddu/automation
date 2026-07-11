"""Pydantic request validation schemas for Gmail integrations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EmailConnectionRequest(BaseModel):
    organization_id: UUID
    provider: str = Field(default="google")
    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    scopes: list[str] = Field(default_factory=list)
    expires_in_seconds: int = Field(default=3600, gt=0)


class EmailProposalRequest(BaseModel):
    organization_id: UUID
    recipient_address: str = Field(min_length=1, max_length=256)
    subject: str | None = Field(default=None, max_length=256)
    body_text: str = Field(min_length=1)
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ProposalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=1000)
