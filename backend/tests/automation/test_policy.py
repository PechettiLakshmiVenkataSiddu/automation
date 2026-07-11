from aether.automation.policy import PolicyDecision, PolicyOutcome, may_execute
from aether.automation.retry import RetryDisposition, classify_failure


def test_only_explicit_allow_can_execute() -> None:
    assert may_execute(PolicyDecision(PolicyOutcome.ALLOW, "v1", "approved"))
    assert not may_execute(PolicyDecision(PolicyOutcome.REQUIRE_APPROVAL, "v1", "review"))
    assert not may_execute(PolicyDecision(PolicyOutcome.DENY, "v1", "denied"))


def test_only_transient_transport_failures_are_retryable() -> None:
    assert classify_failure(TimeoutError()) is RetryDisposition.RETRY
    assert classify_failure(ValueError()) is RetryDisposition.FAIL
