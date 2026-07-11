"""Unit tests for voice intent parsing and policy behavior."""

from uuid import uuid4

from aether.automation.policy import PolicyOutcome
from aether.voice.intent import parse_transcript
from aether.voice.policy import VoicePolicyEvaluator


def test_chat_intent_is_parsed_from_question_phrase() -> None:
    intent = parse_transcript("What is on my schedule today?")
    assert intent.intent_type == "chat_message"
    assert "schedule" in intent.transcript.lower()


def test_high_risk_intent_is_denied_by_policy_gate() -> None:
    from aether.voice.contracts import VoiceCommandIntent

    evaluator = VoicePolicyEvaluator()
    intent = VoiceCommandIntent("send_email", "send email now", {}, True)
    assert evaluator.evaluate_intent(intent, uuid4()).outcome is PolicyOutcome.REQUIRE_APPROVAL
