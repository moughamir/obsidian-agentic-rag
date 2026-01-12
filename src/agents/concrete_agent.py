# src/agents/concrete_agent.py
from dataclasses import dataclass

from src.domain.agent_interface import AgentResponse, AgentTask, IAgent
from src.infrastructure.llm_client import ILLMClient


@dataclass
class AgentConfig:
    """Configuration for a concrete agent."""

    name: str
    role: str
    temperature: float


class BaseAgent(IAgent):
    """A concrete implementation of the IAgent interface."""

    def __init__(
        self, config: AgentConfig, llm_client: ILLMClient, system_prompt: str = ""
    ):
        self._config = config
        self._llm = llm_client
        # Accept either a prompt string or a prompt loader with `.load(role)` for flexibility.
        # This makes BaseAgent resilient to callers that accidentally pass a loader object.
        if hasattr(system_prompt, "load") and callable(system_prompt.load):
            try:
                # If a prompt loader (e.g., FilePromptLoader) was passed, load the prompt for this role
                self._system_prompt = system_prompt.load(config.role)
            except Exception:
                # Fall back to empty prompt if loader fails
                self._system_prompt = ""
        else:
            self._system_prompt = system_prompt or ""

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def role(self) -> str:
        return self._config.role

    @property
    def system_prompt(self) -> str:
        """System prompt text used when formatting prompts."""
        return getattr(self, "_system_prompt", "")

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
            prompt=full_prompt, temperature=self._config.temperature
        )

        return AgentResponse(agent_name=self.name, content=raw_response)
