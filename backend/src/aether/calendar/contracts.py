"""Pydantic request validation schemas for Calendar integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarConnectionRequest(BaseModel):
    organization_id: UUID
    provider: str = Field(default="google")
    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    scopes: list[str] = Field(default_factory=list)
    permitted_calendars: list[str] = Field(default_factory=list)
    expires_in_seconds: int = Field(default=3600, gt=0)


class EventProposalRequest(BaseModel):
    organization_id: UUID
    summary: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    start_time: datetime
    end_time: datetime
    attendees: list[dict[str, Any]] = Field(default_factory=list)


class ProposalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=1000)
