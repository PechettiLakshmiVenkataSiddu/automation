"""Pydantic validation schemas for logging computing usage costs and steps."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UsageLogRequest(BaseModel):
    organization_id: UUID
    user_id: UUID | None = Field(default=None)
    event_name: str = Field(min_length=1, max_length=100)
    category: Literal["model_call", "tool_execution", "workflow_step", "api_sync"]
    cost: float = Field(default=0.0, ge=0.0)
    units: int = Field(default=0, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowRunMetricRequest(BaseModel):
    organization_id: UUID
    workflow_id: UUID
    success: bool
    duration_seconds: float = Field(ge=0.0)
