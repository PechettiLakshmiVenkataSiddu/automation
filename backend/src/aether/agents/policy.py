"""Policy evaluator for AI Agent tool access, security boundaries, and validation."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from aether.agents.contracts import AgentType

# Explicit tool allowlists per agent type
ALLOWED_TOOLS: dict[AgentType, set[str]] = {
    AgentType.PLANNER: {"create_plan"},
    AgentType.RESEARCH: {"search_web", "read_file", "vector_search"},
    AgentType.CODING: {"modify_file", "read_file"},
    AgentType.EMAIL: {"send_draft", "read_inbox"},
    AgentType.CALENDAR: {"list_events", "propose_event"},
    AgentType.TASK: {"delegate_task"},
    AgentType.AUTOMATION: {"trigger_workflow"},
    AgentType.VOICE: {"transcribe", "synthesize"},
    AgentType.MEMORY: {"get_memories", "store_memory", "delete_memory"},
    AgentType.BROWSER: {"run_browser_task"},
    AgentType.DEVELOPER: {"run_command", "run_tests"},
    AgentType.AIOT: {"list_devices", "control_device"},
}


class AgentPolicyEvaluator:
    """Enforces boundaries, tool allowlists, and path restrictions for AI Agents."""

    def __init__(self, organization_id: UUID) -> None:
        self.organization_id = organization_id

    def validate_tool_call(
        self, agent_type: AgentType, tool_name: str, arguments: dict[str, Any]
    ) -> None:
        """Validate if the agent type is allowed to call the tool and arguments are safe."""
        # 1. Enforce Tool Allowlist
        allowed = ALLOWED_TOOLS.get(agent_type, set())
        if tool_name not in allowed:
            raise ValueError(
                f"Agent '{agent_type.value}' is not authorized to call tool '{tool_name}'"
            )

        # 2. Enforce Path Confinement / Sandboxing for filesystem access
        for arg_name, arg_val in arguments.items():
            is_path_arg = isinstance(arg_val, str) and ("path" in arg_name or "file" in arg_name)
            is_traversal = is_path_arg and (
                ".." in arg_val or arg_val.startswith("/") or ":" in arg_val
            )
            if is_traversal and not self._is_safe_relative_path(arg_val):
                raise ValueError(
                    f"Path restriction violation in tool argument '{arg_name}': {arg_val}"
                )

    def _is_safe_relative_path(self, path: str) -> bool:
        """Ensure a path is a safe relative path and does not escape via directory traversal."""
        normalized = os.path.normpath(path)
        return not (normalized.startswith("..") or os.path.isabs(normalized))
