from src.agents.concrete_agent import BaseAgent, AgentConfig
from src.domain.agent_interface import IAgent
from src.infrastructure.llm_client import ILLMClient, MockLLMClient
from src.infrastructure.prompt_manager import FilePromptLoader

class AgentFactory:
    def __init__(self, llm_client: ILLMClient | None = None, use_mocks: bool = True):
        self.prompt_loader = FilePromptLoader()
        if use_mocks:
            self._llm = MockLLMClient()
        else:
            if llm_client is None:
                raise ValueError("llm_client must be provided if use_mocks is False")
            self._llm = llm_client

    def create_researcher(self, name: str = "Researcher") -> IAgent:
        config = AgentConfig(name=name, role="researcher", temperature=0.4)
        return self._create_agent(config)

    def create_synthesizer(self, name: str = "Synthesizer") -> IAgent:
        config = AgentConfig(name=name, role="synthesizer", temperature=0.6)
        return self._create_agent(config)

    def create_critic(self, name: str = "Critic") -> IAgent:
        config = AgentConfig(name=name, role="critic", temperature=0.2)
        return self._create_agent(config)

    def create_supervisor(self, name: str = "Supervisor") -> IAgent:
        config = AgentConfig(name=name, role="supervisor", temperature=0.1)
        return self._create_agent(config)

    def create_custom(self, name: str, role: str, temperature: float = 0.7) -> IAgent:
        config = AgentConfig(name=name, role=role, temperature=temperature)
        return self._create_agent(config)

    def _create_agent(self, config: AgentConfig) -> IAgent:
        system_prompt = self.prompt_loader.load(config.role)
        return BaseAgent(config, self._llm, system_prompt)
