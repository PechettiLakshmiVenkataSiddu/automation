"""Pydantic request validation schemas for organization settings and administration."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PolicyUpdateRequest(BaseModel):
    organization_id: UUID
    retention_days_notifications: int = Field(default=30, ge=1, le=365)
    retention_days_audit_logs: int = Field(default=365, ge=1, le=3650)
    allow_unsecure_sandboxes: bool = Field(default=False)


class BreakGlassRequest(BaseModel):
    organization_id: UUID
    active: bool
    reason: str | None = Field(default=None, max_length=1000)


class InviteMemberRequest(BaseModel):
    organization_id: UUID
    email: str = Field(min_length=3, max_length=256)
    role: Literal["admin", "member", "viewer"] = Field(default="member")


class UpdateMemberRequest(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: Literal["admin", "member", "viewer"]


class CreateApiKeyRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = Field(default=None)
