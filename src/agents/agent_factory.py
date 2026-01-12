"""
Step 6: Agent Factory
Creational Pattern: Centralized agent creation
Single Responsibility: Create and configure agents
"""

from src.agents.concrete_agent import AgentConfig, BaseAgent
from src.domain.agent_interface import IAgent
from src.infrastructure.llm_client import ILLMClient, MockLLMClient, OllamaClient
from src.infrastructure.prompt_manager import FilePromptLoader, IPromptLoader


class AgentFactory:
    """
    Factory for creating pre-configured agents

    Benefits:
    - Encapsulates creation logic
    - Easy to swap implementations (Mock vs Real)
    - Consistent configuration
    """

    def __init__(
        self,
        llm_client: ILLMClient = None,
        prompt_loader: IPromptLoader = None,
        use_mocks: bool = False,
    ):
        """
        Dependency Injection at factory level
        Allows swapping real vs mock implementations
        """
        self._llm_client = llm_client or (
            MockLLMClient() if use_mocks else OllamaClient()
        )
        self._prompt_loader = prompt_loader or FilePromptLoader()

    def create_researcher(self, name: str = "Researcher") -> IAgent:
        """Create a research agent"""
        config = AgentConfig(name=name, role="researcher", temperature=0.4)
        return self._create_agent(config)

    def create_synthesizer(self, name: str = "Synthesizer") -> IAgent:
        """Create a synthesis agent"""
        config = AgentConfig(name=name, role="synthesizer", temperature=0.6)
        return self._create_agent(config)

    def create_critic(self, name: str = "Critic") -> IAgent:
        """Create a validation agent"""
        config = AgentConfig(name=name, role="critic", temperature=0.2)
        return self._create_agent(config)

    def create_custom(self, name: str, role: str, temperature: float = 0.7) -> IAgent:
        """Create custom agent with any role"""
        config = AgentConfig(name=name, role=role, temperature=temperature)
        return self._create_agent(config)

    def _create_agent(self, config: AgentConfig) -> IAgent:
        """
        Internal factory method
        Single Responsibility: Wire dependencies
        """
        return BaseAgent(
            config=config,
            llm_client=self._llm_client,
            prompt_loader=self._prompt_loader,
        )
