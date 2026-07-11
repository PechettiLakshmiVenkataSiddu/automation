from __future__ import annotations

import pytest

from aether.email.policy import EmailPolicyEvaluator


def test_email_policy_recipient_filtering() -> None:
    policy = EmailPolicyEvaluator(scopes=[])

    # Valid format
    policy.validate_recipient("owner@company.com")
    policy.validate_recipient("client@gmail.com")

    # Invalid structures
    with pytest.raises(ValueError, match="Invalid email address structure"):
        policy.validate_recipient("owner")

    with pytest.raises(ValueError, match="Invalid email address structure"):
        policy.validate_recipient("owner@")

    # Blocked domains
    with pytest.raises(ValueError, match="is blocked by safety policy"):
        policy.validate_recipient("hacker@malicious.com")

    with pytest.raises(ValueError, match="is blocked by safety policy"):
        policy.validate_recipient("spam@spam.org")


def test_email_policy_attachments() -> None:
    policy = EmailPolicyEvaluator(scopes=[])

    # Safe attachments
    policy.validate_attachments([{"filename": "document.pdf"}, {"filename": "image.png"}])

    # Unsafe extensions
    with pytest.raises(ValueError, match="Unsafe attachment extension blocked"):
        policy.validate_attachments([{"filename": "malware.exe"}])

    with pytest.raises(ValueError, match="Unsafe attachment extension blocked"):
        policy.validate_attachments([{"filename": "script.sh"}])

    with pytest.raises(ValueError, match="Unsafe attachment extension blocked"):
        policy.validate_attachments([{"filename": "installer.msi"}])


def test_email_policy_sufficient_scopes() -> None:
    # Insufficient scopes
    read_only = EmailPolicyEvaluator(scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    assert read_only.has_sufficient_scopes() is False

    # Valid send/compose scopes
    send_scope = EmailPolicyEvaluator(scopes=["https://www.googleapis.com/auth/gmail.send"])
    assert send_scope.has_sufficient_scopes() is True

    modify_scope = EmailPolicyEvaluator(scopes=["https://www.googleapis.com/auth/gmail.modify"])
    assert modify_scope.has_sufficient_scopes() is True
