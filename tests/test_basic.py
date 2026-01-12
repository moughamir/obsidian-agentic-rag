import pytest

from src.agents.agent_factory import AgentFactory
from src.domain.agent_interface import AgentTask


@pytest.mark.asyncio
async def test_agent_creation():
    """Test basic agent creation"""
    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()

    assert agent.name == "Researcher"
    # Agent implementations may expose role either as a public property or via internal config.
    role = getattr(agent, "role", None)
    if role is None and hasattr(agent, "_config"):
        role = getattr(agent._config, "role", None)
    assert role == "researcher"


@pytest.mark.asyncio
async def test_agent_processing():
    """Test agent can process tasks"""

    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()

    task = AgentTask(instruction="What is 2+2?")
    response = await agent.process(task)

    assert response.agent_name == "Researcher"
    assert len(response.content) > 0
    # Confidence should be present and between 0 and 1 (defaults to 0.0 if not set)
    assert hasattr(response, "confidence")
    assert isinstance(response.confidence, (int, float))
    assert 0 <= response.confidence <= 1
