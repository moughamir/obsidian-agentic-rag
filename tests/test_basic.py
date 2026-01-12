import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.agent_factory import AgentFactory
from domain.agent_interface import AgentTask


@pytest.mark.asyncio
async def test_agent_creation():
    '''Test basic agent creation'''
    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()
    
    assert agent.name == "Researcher"
    assert agent.role == "researcher"


@pytest.mark.asyncio  
async def test_agent_processing():
    '''Test agent can process tasks'''
    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()
    
    task = AgentTask(instruction="What is 2+2?")
    response = await agent.process(task)
    
    assert response.agent_name == "Researcher"
    assert len(response.content) > 0
    assert 0 <= response.confidence <= 1