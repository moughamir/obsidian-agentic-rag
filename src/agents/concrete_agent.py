"""
Step 4: Concrete Agent Implementation
Dependency Injection: Constructor injection of dependencies
Single Responsibility: Execute tasks using injected services
Open/Closed: Easily extend by creating new agent types
"""

from dataclasses import dataclass

from src.domain.agent_interface import AgentResponse, AgentTask, IAgent
from src.infrastructure.llm_client import ILLMClient
from src.infrastructure.prompt_manager import IPromptLoader, PromptBuilder


@dataclass
class AgentConfig:
    """Configuration value object"""

    name: str
    role: str
    temperature: float = 0.7
    model: str = "llama3.1:8b"


class BaseAgent(IAgent):
    """
    Concrete Agent Implementation

    Dependencies injected via constructor (DI):
    - LLM client (abstraction)
    - Prompt loader (abstraction)
    - Configuration (value object)
    """

    def __init__(
        self, config: AgentConfig, llm_client: ILLMClient, prompt_loader: IPromptLoader
    ):
        """
        Dependency Injection: All dependencies provided externally
        Testable: Can inject mocks for testing
        """
        self._config = config
        self._llm = llm_client
        self._prompt_loader = prompt_loader
        self._system_prompt = prompt_loader.load(config.role)

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def role(self) -> str:
        return self._config.role

    async def process(self, task: AgentTask) -> AgentResponse:
        """
        Single Responsibility: Process task through LLM
        KISS: Simple sequential steps
        """
        # 1. Build prompt
        prompt = self._build_prompt(task)

        # 2. Call LLM
        response_text = await self._llm.generate(prompt, self._config.temperature)

        # 3. Create response object
        return AgentResponse(
            content=response_text,
            confidence=0.85,  # TODO: Extract from LLM if available
            agent_name=self.name,
            sources=[],  # TODO: Extract citations
        )

    def _build_prompt(self, task: AgentTask) -> str:
        """Private helper - KISS principle"""
        previous = self._format_previous_results(task.previous_results)

        return PromptBuilder.build(
            system_prompt=self._system_prompt,
            task=task.instruction,
            context=task.context,
            previous=previous,
        )

    def _format_previous_results(self, results: list[AgentResponse]) -> str:
        """Format previous agent results for context"""
        if not results:
            return ""

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"[{result.agent_name}]: {result.content}")

        return "\n\n".join(formatted)
