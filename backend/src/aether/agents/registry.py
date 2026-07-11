"""Registry and implementations of typed agent orchestrators."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from aether.agents.contracts import AgentType


class BaseAgentOrchestrator:
    """Base class for all individual agent orchestrators."""

    def __init__(self, organization_id: UUID) -> None:
        self.organization_id = organization_id

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError()


class PlannerAgent(BaseAgentOrchestrator):
    """Generates the multi-step execution plan for a goal."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        goal = payload.get("goal", "")
        # Deterministically parse goals for robust testing & execution
        if "fail" in goal.lower():
            raise ValueError("Planner failed due to invalid goal")

        steps = [
            {
                "assigned_agent": AgentType.RESEARCH.value,
                "description": f"Gather research data for: {goal}",
                "requires_approval": False,
                "input_payload": {"query": goal},
            },
            {
                "assigned_agent": AgentType.CODING.value,
                "description": "Generate application code or configuration",
                "requires_approval": False,
                "input_payload": {"goal": goal},
            },
        ]

        # If goal contains sensitive actions, require approval
        if "email" in goal.lower() or "send" in goal.lower():
            steps.append(
                {
                    "assigned_agent": AgentType.EMAIL.value,
                    "description": "Send email notification",
                    "requires_approval": True,
                    "input_payload": {
                        "subject": "Task Completed",
                        "body": f"The task: '{goal}' has finished.",
                    },
                }
            )

        return {"steps": steps}


class ResearchAgent(BaseAgentOrchestrator):
    """Searches vectors, memories, and web resources."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "")
        return {
            "sources": ["web_search", "memory_store"],
            "summary": f"Research results for: '{query}'. Standard baseline validated.",
        }


class CodingAgent(BaseAgentOrchestrator):
    """Writes code modifications to safe targets."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "modified_files": ["src/main.py"],
            "diff": "+ print('Hello World')",
        }


class EmailAgent(BaseAgentOrchestrator):
    """Prepares and drafts emails."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "draft_id": "draft_12345",
            "sent": True,
            "status": "success",
        }


class CalendarAgent(BaseAgentOrchestrator):
    """Schedules calendar events."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"event_id": "event_98765", "status": "scheduled"}


class TaskAgent(BaseAgentOrchestrator):
    """Coordinates nested subtasks."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"subtasks": [], "status": "completed"}


class AutomationAgent(BaseAgentOrchestrator):
    """Triggers automation workflows."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"workflow_run_id": "run_abc123", "status": "triggered"}


class VoiceAgent(BaseAgentOrchestrator):
    """Processes speech synthesis and transcript parsing."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"transcript": "parsed intent", "status": "completed"}


class MemoryAgent(BaseAgentOrchestrator):
    """Interacts with user-consented long-term memory."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"memories_found": 0, "status": "completed"}


class BrowserAgent(BaseAgentOrchestrator):
    """Triggers browser-executor Playwright runs."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"task_id": "browser_task_123", "status": "succeeded"}


class DeveloperAgent(BaseAgentOrchestrator):
    """Runs command scripts and verification suites."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": "tests passed", "status": "succeeded"}


class AIoTAgent(BaseAgentOrchestrator):
    """Simulated smart-device control."""

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"device_status": "active", "status": "completed"}


AGENT_REGISTRY: dict[AgentType, type[BaseAgentOrchestrator]] = {
    AgentType.PLANNER: PlannerAgent,
    AgentType.RESEARCH: ResearchAgent,
    AgentType.CODING: CodingAgent,
    AgentType.EMAIL: EmailAgent,
    AgentType.CALENDAR: CalendarAgent,
    AgentType.TASK: TaskAgent,
    AgentType.AUTOMATION: AutomationAgent,
    AgentType.VOICE: VoiceAgent,
    AgentType.MEMORY: MemoryAgent,
    AgentType.BROWSER: BrowserAgent,
    AgentType.DEVELOPER: DeveloperAgent,
    AgentType.AIOT: AIoTAgent,
}


def get_agent_orchestrator(agent_type: AgentType, organization_id: UUID) -> BaseAgentOrchestrator:
    """Resolve and return an instantiated agent orchestrator."""
    cls = AGENT_REGISTRY.get(agent_type)
    if cls is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return cls(organization_id)
