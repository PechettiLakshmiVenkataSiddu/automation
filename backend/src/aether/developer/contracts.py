"""Pydantic request validation schemas for Developer Tools."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SandboxCreateRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=128)
    sandbox_path: str = Field(min_length=1, max_length=1024)


class CommandSubmitRequest(BaseModel):
    organization_id: UUID
    sandbox_id: UUID
    command_line: str = Field(min_length=1)
    timeout_seconds: int = Field(default=30, gt=0, le=300)


class CommandApprovalDecision(BaseModel):
    organization_id: UUID
    approval_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=1000)
