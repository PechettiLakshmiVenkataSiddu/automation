"""Voice retention and command policy evaluation."""

from __future__ import annotations

from uuid import UUID

from aether.automation.policy import PolicyDecision, PolicyOutcome
from aether.voice.contracts import VoiceCommandIntent

VOICE_POLICY_VERSION = "voice-v1"
HIGH_RISK_INTENTS = frozenset({"automation_action", "send_email", "delete_data"})


class VoicePolicyEvaluator:
    """Deny-by-default voice policy; external effects require explicit confirmation."""

    policy_version = VOICE_POLICY_VERSION

    def evaluate_intent(self, intent: VoiceCommandIntent, organization_id: UUID) -> PolicyDecision:
        _ = organization_id
        if intent.intent_type in HIGH_RISK_INTENTS:
            return PolicyDecision(
                PolicyOutcome.REQUIRE_APPROVAL,
                self.policy_version,
                "high-risk voice command requires explicit confirmation",
            )
        if intent.requires_confirmation:
            return PolicyDecision(
                PolicyOutcome.REQUIRE_APPROVAL,
                self.policy_version,
                "voice command requires explicit confirmation",
            )
        return PolicyDecision(
            PolicyOutcome.ALLOW, self.policy_version, "low-risk voice command is allowed"
        )

    def retention_allowed(self, retention_enabled: bool) -> bool:
        return retention_enabled
