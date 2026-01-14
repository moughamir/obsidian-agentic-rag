import asyncio
from src.agents.agent_factory import AgentFactory
from src.application.orchestrator import AgentOrchestrator
from src.domain.agent_interface import AgentTask

async def example_supervised_workflow():
    """
    Example: Supervisor-Driven Workflow
    The Supervisor creates a plan, and the Orchestrator executes the sequence.
    """
    factory = AgentFactory(use_mocks=True)
    orchestrator = AgentOrchestrator()

    # Register Supervisor and Team
    orchestrator.register(factory.create_supervisor("Supervisor"))
    orchestrator.register(factory.create_researcher("Researcher"))
    orchestrator.register(factory.create_synthesizer("Synthesizer"))
    orchestrator.register(factory.create_critic("Critic"))

    task = "Summarize the recent changes to the Obsidian vault and assess their impact."

    print(f"--- Starting Supervised Task: {task} ---")
    results = await orchestrator.execute_supervised(task)

    print("\n--- Final Results ---")
    for res in results:
        print(f"[{res.agent_name}]: {res.content[:100]}...")

async def main():
    await example_supervised_workflow()

if __name__ == "__main__":
    asyncio.run(main())
