from __future__ import annotations

from uuid import uuid4

import pytest

from aether.agents.contracts import AgentType
from aether.agents.registry import get_agent_orchestrator


@pytest.mark.asyncio
async def test_agent_registry_resolution() -> None:
    org_id = uuid4()
    for agent_type in AgentType:
        orchestrator = get_agent_orchestrator(agent_type, org_id)
        assert orchestrator is not None
        assert orchestrator.organization_id == org_id


@pytest.mark.asyncio
async def test_individual_agents_execution() -> None:
    org_id = uuid4()

    # Test Planner Agent
    planner = get_agent_orchestrator(AgentType.PLANNER, org_id)
    plan = await planner.execute({"goal": "Analyze code and draft email"})
    assert "steps" in plan
    assert len(plan["steps"]) == 3
    assert plan["steps"][0]["assigned_agent"] == AgentType.RESEARCH.value
    assert plan["steps"][2]["assigned_agent"] == AgentType.EMAIL.value

    # Test Research Agent
    researcher = get_agent_orchestrator(AgentType.RESEARCH, org_id)
    research_res = await researcher.execute({"query": "Aether project"})
    assert "summary" in research_res
    assert "sources" in research_res

    # Test Coding Agent
    coder = get_agent_orchestrator(AgentType.CODING, org_id)
    coding_res = await coder.execute({})
    assert coding_res["status"] == "success"
    assert "modified_files" in coding_res
