# src/agents/concrete_agent.py
from dataclasses import dataclass
from src.domain.agent_interface import IAgent, AgentTask, AgentResponse
from src.infrastructure.llm_client import ILLMClient

@dataclass
class AgentConfig:
    """Configuration for a concrete agent."""
    name: str
    role: str
    temperature: float

class BaseAgent(IAgent):
    """A concrete implementation of the IAgent interface."""
    def __init__(self, config: AgentConfig, llm_client: ILLMClient, system_prompt: str):
        self._config = config
        self._llm = llm_client
        self.system_prompt = system_prompt

    @property
    def name(self) -> str:
        return self._config.name

    async def process(self, task: AgentTask) -> AgentResponse:
        """
        Formats a prompt and uses the LLM client to generate a response.
        """
        # Simple prompt formatting
        full_prompt = (
            f"SYSTEM: {self.system_prompt}\n\n"
            f"CONTEXT: {task.context}\n\n"
            f"INSTRUCTION: {task.instruction}"
        )

        raw_response = await self._llm.generate(
            prompt=full_prompt,
            temperature=self._config.temperature
        )

        return AgentResponse(agent_name=self.name, content=raw_response)
