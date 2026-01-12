from src.domain.agent_interface import AgentTask, AgentResponse, IAgent

class AgentOrchestrator:
    def __init__(self):
        self._agents: dict[str, IAgent] = {}

    def register(self, agent: IAgent) -> None:
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> IAgent:
        if name not in self._agents:
            raise ValueError(f"Agent {name} not registered")
        return self._agents[name]

    async def execute_sequence(self, agent_names: list[str], task_instruction: str, context: str = "") -> list[AgentResponse]:
        """
        Execute agents in sequence.
        KISS: Simple for-loop, each agent sees previous results.
        """
        import asyncio
        results: list[AgentResponse] = []
        current_context = context

        for agent_name in agent_names:
            agent = self.get_agent(agent_name)
            task = AgentTask(
                instruction=task_instruction,
                context=current_context,
                previous_results=results
            )
            response = await agent.process(task)
            results.append(response)
            # Update context for the next agent with the latest response
            current_context = f"Previous Output: {response.content}"

        return results

    async def execute_parallel(self, agent_names: list[str], task_instruction: str, context: str = "") -> list[AgentResponse]:
        """
        Execute agents in parallel (for independent tasks).
        Use when agents don't need each other's results.
        """
        import asyncio

        tasks = []
        for agent_name in agent_names:
            agent = self.get_agent(agent_name)
            task = AgentTask(instruction=task_instruction, context=context)
            tasks.append(agent.process(task))

        return await asyncio.gather(*tasks)

    async def execute_supervised(self, task_instruction: str, context: str = "") -> list[AgentResponse]:
        """
        NEW: Supervisor Workflow.
        1. Supervisor analyzes the task.
        2. Orchestrator routes to Researcher -> Synthesizer -> Critic based on plan.
        """
        supervisor = self.get_agent("Supervisor")

        # Step 1: Ask Supervisor for a plan
        planning_task = AgentTask(
            instruction=f"Create a plan for: {task_instruction}",
            context=context
        )
        plan_response = await supervisor.process(planning_task)

        # In Phase 1, we hardcode the sequence, but we log the plan
        print(f"Supervisor Plan: {plan_response.content}")

        # Step 2: Execute the standard sequence (Simulated Routing)
        # In future phases, the Supervisor response would be parsed to determine the sequence.
        sequence = ["Researcher", "Synthesizer", "Critic"]
        return await self.execute_sequence(sequence, task_instruction, context)

    def list_agents(self) -> list[str]:
        """List all registered agents"""
        return list(self._agents.keys())
