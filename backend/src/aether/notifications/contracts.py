"""Pydantic request validation schemas for notification delivery preferences and dispatches."""

from __future__ import annotations

from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


def _default_channels() -> list[Literal["in_app", "email", "push"]]:
    return ["in_app"]


class NotificationPreferencesUpdateRequest(BaseModel):
    organization_id: UUID
    channels: list[Literal["in_app", "email", "push"]] = Field(
        default_factory=_default_channels
    )
    quiet_hours_start: time | None = Field(default=None)
    quiet_hours_end: time | None = Field(default=None)
    unsubscribed: bool = Field(default=False)


class NotificationDispatchRequest(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=2000)
    level: Literal["info", "warning", "error"] = Field(default="info")
