# src/domain/agent_interface.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class AgentResponse:
    """Data class for a response from an agent."""
    agent_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentTask:
    """Data class for a task to be processed by an agent."""
    instruction: str
    context: str = ""
    previous_results: List[AgentResponse] = field(default_factory=list)

class IAgent(ABC):
    """Abstract interface for an agent."""
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the agent."""
        pass

    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResponse:
        """Processes a given task and returns a response."""
        pass
