"""Typed policy outcomes for workflow actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PolicyOutcome(StrEnum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class ActionIntent:
    action_type: str
    risk_class: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    outcome: PolicyOutcome
    policy_version: str
    reason: str


def may_execute(decision: PolicyDecision) -> bool:
    """Only an explicit allow can reach an external action adapter."""
    return decision.outcome is PolicyOutcome.ALLOW
