from __future__ import annotations

from uuid import uuid4

import pytest

from aether.agents.contracts import AgentType
from aether.agents.policy import AgentPolicyEvaluator


def test_policy_evaluator_tool_allowlist() -> None:
    org_id = uuid4()
    evaluator = AgentPolicyEvaluator(org_id)

    # Valid tool calls should pass
    evaluator.validate_tool_call(AgentType.RESEARCH, "search_web", {})
    evaluator.validate_tool_call(AgentType.CODING, "modify_file", {})
    evaluator.validate_tool_call(AgentType.DEVELOPER, "run_command", {})

    # Invalid tool calls should be blocked with ValueError
    with pytest.raises(ValueError, match="is not authorized to call tool"):
        evaluator.validate_tool_call(AgentType.RESEARCH, "modify_file", {})

    with pytest.raises(ValueError, match="is not authorized to call tool"):
        evaluator.validate_tool_call(AgentType.PLANNER, "run_command", {})


def test_policy_evaluator_path_restrictions() -> None:
    org_id = uuid4()
    evaluator = AgentPolicyEvaluator(org_id)

    # Safe relative paths should pass validation
    evaluator.validate_tool_call(AgentType.CODING, "modify_file", {"file_path": "src/main.py"})
    evaluator.validate_tool_call(AgentType.CODING, "modify_file", {"target_path": "config.json"})

    # Absolute paths and traversal escapes should be rejected
    with pytest.raises(ValueError, match="Path restriction violation"):
        evaluator.validate_tool_call(AgentType.CODING, "modify_file", {"file_path": "../escape.py"})

    with pytest.raises(ValueError, match="Path restriction violation"):
        evaluator.validate_tool_call(
            AgentType.CODING, "modify_file", {"target_file": "/absolute/path.py"}
        )

    with pytest.raises(ValueError, match="Path restriction violation"):
        evaluator.validate_tool_call(
            AgentType.CODING, "modify_file", {"file": "C:\\escaped\\windows.py"}
        )
