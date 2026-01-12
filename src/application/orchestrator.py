"""
Step 5: Agent Orchestrator
Single Responsibility: Coordinate agents
Composition over Inheritance: Composes agents
KISS: Simple sequential execution
"""

from typing import Dict

from src.domain.agent_interface import AgentResponse, AgentTask, IAgent


class AgentOrchestrator:
    """
    Orchestrates multiple agents

    SOLID Principles:
    - Single Responsibility: Only coordinates agents
    - Open/Closed: Add agents without modifying code
    - Dependency Inversion: Depends on IAgent abstraction
    """

    def __init__(self):
        """KISS: Start with empty registry"""
        self._agents: Dict[str, IAgent] = {}

    def register(self, agent: IAgent) -> None:
        """
        Register an agent (Open/Closed principle)
        Can add new agents without changing orchestrator
        """
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> IAgent:
        """Retrieve agent by name"""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found")
        return self._agents[name]

    async def execute_sequence(
        self, agent_names: list[str], task_instruction: str, context: str = ""
    ) -> list[AgentResponse]:
        """
        Execute agents in sequence

        KISS: Simple for-loop, each agent sees previous results

        Args:
            agent_names: Ordered list of agent names
            task_instruction: The task to perform
            context: Optional context/background

        Returns:
            List of all agent responses
        """
        results: list[AgentResponse] = []

        for agent_name in agent_names:
            agent = self.get_agent(agent_name)

            # Create task with previous results as context
            task = AgentTask(
                instruction=task_instruction, context=context, previous_results=results
            )

            # Execute agent
            response = await agent.process(task)
            results.append(response)

        return results

    async def execute_parallel(
        self, agent_names: list[str], task_instruction: str, context: str = ""
    ) -> list[AgentResponse]:
        """
        Execute agents in parallel (for independent tasks)

        Use when agents don't need each other's results
        """
        import asyncio

        tasks = []
        for agent_name in agent_names:
            agent = self.get_agent(agent_name)
            task = AgentTask(instruction=task_instruction, context=context)
            tasks.append(agent.process(task))

        return await asyncio.gather(*tasks)

    def list_agents(self) -> list[str]:
        """List all registered agents"""
        return list(self._agents.keys())
