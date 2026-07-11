import pytest

from aether.automation.state_machine import InvalidRunTransition, RunStatus, require_transition


def test_valid_execution_and_approval_transitions() -> None:
    require_transition(RunStatus.QUEUED, RunStatus.RUNNING)
    require_transition(RunStatus.RUNNING, RunStatus.AWAITING_APPROVAL)
    require_transition(RunStatus.AWAITING_APPROVAL, RunStatus.QUEUED)
    require_transition(RunStatus.RUNNING, RunStatus.RETRY_SCHEDULED)


def test_terminal_and_invalid_transitions_are_rejected() -> None:
    with pytest.raises(InvalidRunTransition):
        require_transition(RunStatus.SUCCEEDED, RunStatus.RUNNING)
    with pytest.raises(InvalidRunTransition):
        require_transition(RunStatus.QUEUED, RunStatus.SUCCEEDED)
