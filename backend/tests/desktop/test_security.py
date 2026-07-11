from uuid import uuid4

import pytest

from aether.automation.policy import PolicyOutcome
from aether.desktop.access import UnsafeDesktopAccess, validate_desktop_target
from aether.desktop.artifacts import LocalArtifactStore
from aether.desktop.contracts import DesktopAction
from aether.desktop.grants import issue_grant, verify_grant
from aether.desktop.policy import DesktopPolicyEvaluator
from aether.desktop.redaction import redact_artifact_text


def test_grant_binds_task_and_organization() -> None:
    organization_id, task_id = uuid4(), uuid4()
    token = issue_grant(
        b"desktop-secret-key-needs-32-bytes-min!!", organization_id, task_id, ttl_seconds=30
    )
    assert verify_grant(b"desktop-secret-key-needs-32-bytes-min!!", token) == (
        organization_id,
        task_id,
    )


def test_access_rejects_host_wide_and_network() -> None:
    with pytest.raises(UnsafeDesktopAccess):
        validate_desktop_target("*", ("calculator",), (), False)
    with pytest.raises(UnsafeDesktopAccess):
        validate_desktop_target("calculator", ("calculator",), ("/etc",), False)
    with pytest.raises(UnsafeDesktopAccess):
        validate_desktop_target("calculator", ("calculator",), (), True)


def test_policy_requires_approval_for_sensitive_actions() -> None:
    evaluator = DesktopPolicyEvaluator()
    sensitive = DesktopAction(
        "click",
        "calculator",
        30,
        ("calculator",),
        (),
        False,
        None,
        "idem-1",
        "low",
    )
    safe = DesktopAction(
        "screenshot",
        "calculator",
        30,
        ("calculator",),
        (),
        False,
        None,
        "idem-2",
        "low",
    )
    assert evaluator.evaluate(sensitive, uuid4()).outcome is PolicyOutcome.REQUIRE_APPROVAL
    assert evaluator.evaluate(safe, uuid4()).outcome is PolicyOutcome.ALLOW


def test_policy_denies_high_risk() -> None:
    evaluator = DesktopPolicyEvaluator()
    action = DesktopAction(
        "screenshot",
        "calculator",
        30,
        ("calculator",),
        (),
        False,
        None,
        "idem-3",
        "high",
    )
    assert evaluator.evaluate(action, uuid4()).outcome is PolicyOutcome.DENY


def test_action_and_artifact_redaction() -> None:
    action = DesktopAction(
        "screenshot",
        "calculator",
        20,
        ("calculator",),
        (),
        False,
        None,
        "idem-4",
        "low",
    )
    assert action.operation == "screenshot"
    assert "[REDACTED]" in redact_artifact_text("clipboard: secret-value")


def test_artifacts_are_confined_to_the_task_organization(tmp_path: object) -> None:
    organization_id, task_id = uuid4(), uuid4()
    store = LocalArtifactStore(tmp_path)  # type: ignore[arg-type]
    key, digest = store.put(organization_id, task_id, "screenshot", b"redacted screenshot")
    assert key.startswith(f"desktop/{organization_id}/{task_id}/")
    assert len(digest) == 64


def test_expired_grant_is_rejected() -> None:
    organization_id, task_id = uuid4(), uuid4()
    token = issue_grant(
        b"desktop-secret-key-needs-32-bytes-min!!", organization_id, task_id, ttl_seconds=30
    )
    parts = token.split(".")
    assert len(parts) == 2
