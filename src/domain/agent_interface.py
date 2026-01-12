"""
Step 1: Core Abstractions
Clean Architecture - Domain Layer (Interfaces)
Single Responsibility: Define contracts only
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Value Object - Immutable agent response"""

    content: str
    confidence: float
    agent_name: str
    sources: list[str] | None = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


@dataclass
class AgentTask:
    """Value Object - Represents a task for an agent"""

    instruction: str
    context: str = ""
    previous_results: list[AgentResponse] | None = None

    def __post_init__(self):
        if self.previous_results is None:
            self.previous_results = []


class IAgent(ABC):
    """
    Interface Segregation Principle: Minimal interface
    Agents only need to process tasks
    """

    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResponse:
        """Process a task and return response"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier"""
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role/expertise"""
        pass
