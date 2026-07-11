from __future__ import annotations

from aether.developer.policy import DeveloperCommandPolicyEvaluator


def test_command_policy_rejection() -> None:
    evaluator = DeveloperCommandPolicyEvaluator()

    # Blocked tools must trigger immediate block
    assert evaluator.evaluate("curl -X POST http://malicious.site") == "blocked"
    assert evaluator.evaluate("wget https://untrusted-files") == "blocked"
    assert evaluator.evaluate("ping 8.8.8.8") == "blocked"
    assert evaluator.evaluate("ssh root@host") == "blocked"


def test_command_policy_approval_gate() -> None:
    evaluator = DeveloperCommandPolicyEvaluator()

    # Gated tools must trigger awaiting_approval
    assert evaluator.evaluate("rm -rf backend/") == "awaiting_approval"
    assert evaluator.evaluate("git commit -m 'new code'") == "awaiting_approval"
    assert evaluator.evaluate("git push origin main") == "awaiting_approval"
    assert evaluator.evaluate("npm install") == "awaiting_approval"
    assert evaluator.evaluate("pip install requests") == "awaiting_approval"


def test_command_policy_allowed_queued() -> None:
    evaluator = DeveloperCommandPolicyEvaluator()

    # Safe operations run directly
    assert evaluator.evaluate("echo 'hello'") == "queued"
    assert evaluator.evaluate("git status") == "queued"
    assert evaluator.evaluate("git diff HEAD") == "queued"
    assert evaluator.evaluate("uv run pytest") == "queued"
    assert evaluator.evaluate("npm test") == "queued"
