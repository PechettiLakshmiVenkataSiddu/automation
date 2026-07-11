"""Data contracts, schemas, and enums for secure agent orchestrations."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    PLANNER = "planner"
    RESEARCH = "research"
    CODING = "coding"
    EMAIL = "email"
    CALENDAR = "calendar"
    TASK = "task"
    AUTOMATION = "automation"
    VOICE = "voice"
    MEMORY = "memory"
    BROWSER = "browser"
    DEVELOPER = "developer"
    AIOT = "aiot"


class AgentRunCreate(BaseModel):
    goal: str = Field(min_length=1)
    budget_limit_usd: float = Field(default=1.0000, gt=0.0)
    time_limit_seconds: int = Field(default=600, gt=0)


class AgentPlanStep(BaseModel):
    step_index: int
    assigned_agent: AgentType
    description: str
    requires_approval: bool = False
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    goal: str
    status: str
    budget_limit_usd: float
    budget_spent_usd: float
    time_limit_seconds: int
    created_at: str
    updated_at: str
