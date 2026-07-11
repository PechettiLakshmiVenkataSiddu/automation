from uuid import uuid4

import pytest

from aether.browser.artifacts import LocalArtifactStore
from aether.browser.contracts import BrowserAction
from aether.browser.egress import UnsafeBrowserEgress, validate_browser_url
from aether.browser.grants import issue_grant, verify_grant
from aether.browser.redaction import redact_artifact_text


def test_grant_binds_task_and_organization() -> None:
    organization_id, task_id = uuid4(), uuid4()
    token = issue_grant(b"test-secret", organization_id, task_id, ttl_seconds=30)
    assert verify_grant(b"test-secret", token) == (organization_id, task_id)


def test_egress_rejects_private_resolution_and_unlisted_host() -> None:
    with pytest.raises(UnsafeBrowserEgress):
        validate_browser_url("https://example.test", ("example.test",), lambda _: ["127.0.0.1"])
    with pytest.raises(UnsafeBrowserEgress):
        validate_browser_url("https://other.test", ("example.test",), lambda _: ["8.8.8.8"])


def test_action_and_artifact_redaction() -> None:
    action = BrowserAction("navigate", "https://example.test", 20, ("example.test",), None)
    assert action.operation == "navigate"
    assert "[REDACTED]" in redact_artifact_text("Authorization=Bearer abc.def")


def test_artifacts_are_confined_to_the_task_organization(tmp_path: object) -> None:
    organization_id, task_id = uuid4(), uuid4()
    store = LocalArtifactStore(tmp_path)  # type: ignore[arg-type]
    key, digest = store.put(organization_id, task_id, "screenshot", b"redacted screenshot")
    assert key.startswith(f"browser/{organization_id}/{task_id}/")
    assert len(digest) == 64
