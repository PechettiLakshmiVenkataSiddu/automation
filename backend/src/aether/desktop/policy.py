"""Policy evaluation for desktop automation actions."""

from __future__ import annotations

from uuid import UUID

from aether.automation.policy import ActionIntent, PolicyDecision, PolicyOutcome
from aether.desktop.contracts import SENSITIVE_OPERATIONS, SUPPORTED_OPERATIONS, DesktopAction


class DesktopPolicyEvaluator:
    """Deny-by-default desktop policy with explicit approval for sensitive UI actions."""

    policy_version = "desktop-v1"

    def evaluate(self, action: DesktopAction, organization_id: UUID) -> PolicyDecision:
        _ = organization_id
        if action.operation not in SUPPORTED_OPERATIONS:
            return PolicyDecision(PolicyOutcome.DENY, self.policy_version, "unknown operation")
        if action.risk_class == "high":
            return PolicyDecision(
                PolicyOutcome.DENY, self.policy_version, "high-risk desktop action is denied"
            )
        if action.operation in SENSITIVE_OPERATIONS or action.requires_approval:
            return PolicyDecision(
                PolicyOutcome.REQUIRE_APPROVAL,
                self.policy_version,
                "sensitive desktop UI action requires explicit approval",
            )
        return PolicyDecision(
            PolicyOutcome.ALLOW, self.policy_version, "low-risk desktop action is allowed"
        )

    def evaluate_intent(self, intent: ActionIntent, organization_id: UUID) -> PolicyDecision:
        _ = organization_id
        if intent.risk_class == "high":
            return PolicyDecision(
                PolicyOutcome.DENY, self.policy_version, "high-risk desktop action is denied"
            )
        if intent.action_type.startswith("desktop.") and intent.risk_class == "medium":
            return PolicyDecision(
                PolicyOutcome.REQUIRE_APPROVAL,
                self.policy_version,
                "sensitive desktop UI action requires explicit approval",
            )
        return PolicyDecision(
            PolicyOutcome.ALLOW, self.policy_version, "low-risk desktop action is allowed"
        )
