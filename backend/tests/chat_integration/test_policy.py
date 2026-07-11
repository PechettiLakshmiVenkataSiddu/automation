from __future__ import annotations

from aether.chat_integration.policy import ChatPolicyEvaluator


def test_chat_policy_channel_containment() -> None:
    policy = ChatPolicyEvaluator(scopes=[])

    # Valid Slack/Teams channels
    assert policy.is_channel_permitted("C12345") is True
    assert policy.is_channel_permitted("G98765") is True
    assert policy.is_channel_permitted("D44444") is True
    assert policy.is_channel_permitted("teams-channel-abc") is True

    # Invalid channels (escape characters or paths)
    assert policy.is_channel_permitted("/etc/passwd") is False
    assert policy.is_channel_permitted("..\\escape") is False


def test_chat_policy_incoming_injection() -> None:
    policy = ChatPolicyEvaluator(scopes=[])

    # Safe text
    assert policy.is_safe_incoming_message("Can we review the project specs?") is True

    # Command injections
    assert policy.is_safe_incoming_message("rm -rf /var/log") is False
    assert policy.is_safe_incoming_message("execute command 'whoami'") is False
    assert policy.is_safe_incoming_message("sudo systemctl stop docker") is False


def test_chat_policy_sufficient_scopes() -> None:
    slack_policy = ChatPolicyEvaluator(scopes=["chat:write"])
    assert slack_policy.has_sufficient_scopes("slack") is True

    teams_policy = ChatPolicyEvaluator(scopes=["ChannelMessage.Send"])
    assert teams_policy.has_sufficient_scopes("teams") is True

    insufficient = ChatPolicyEvaluator(scopes=["users:read"])
    assert insufficient.has_sufficient_scopes("slack") is False
