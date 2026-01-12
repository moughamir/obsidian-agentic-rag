"""
Step 7: Integration Example
Demonstrates how all components work together

KISS: Simple, linear flow showing usage
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent_factory import AgentFactory
from src.application.orchestrator import AgentOrchestrator
from src.domain.agent_interface import AgentTask


async def example_single_agent():
    """
    Example 1: Single Agent Query
    KISS: Minimal example
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Single Agent")
    print("=" * 60)

    # Create factory (using mocks for demo)
    factory = AgentFactory(use_mocks=True)

    # Create one agent
    researcher = factory.create_researcher(name="KnowledgeSeeker")

    # Create task
    task = AgentTask(
        instruction="What are the key principles of clean code?",
        context="User is learning software engineering",
    )

    # Execute
    response = await researcher.process(task)

    # Display
    print(f"\n🤖 Agent: {response.agent_name}")
    print(f"📝 Response: {response.content}")
    print(f"✓ Confidence: {response.confidence}")


async def example_multi_agent_sequence():
    """
    Example 2: Multi-Agent Sequential Pipeline
    Shows orchestration with dependency between agents
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Multi-Agent Sequential Pipeline")
    print("=" * 60)

    # Setup
    factory = AgentFactory(use_mocks=True)
    orchestrator = AgentOrchestrator()

    # Create and register agents
    researcher = factory.create_researcher("Researcher")
    synthesizer = factory.create_synthesizer("Synthesizer")
    critic = factory.create_critic("Critic")

    orchestrator.register(researcher)
    orchestrator.register(synthesizer)
    orchestrator.register(critic)

    print(f"✓ Registered agents: {orchestrator.list_agents()}")

    # Execute pipeline
    print("\n🔄 Executing pipeline: Researcher → Synthesizer → Critic")

    results = await orchestrator.execute_sequence(
        agent_names=["Researcher", "Synthesizer", "Critic"],
        task_instruction="Explain async programming in Python",
        context="User is familiar with basic Python",
    )

    # Display results
    print("\n📊 Pipeline Results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Step {i} - {result.agent_name}:")
        print(f"  {result.content[:100]}...")


async def example_parallel_execution():
    """
    Example 3: Parallel Agent Execution
    Multiple agents work independently
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Parallel Execution")
    print("=" * 60)

    # Setup
    factory = AgentFactory(use_mocks=True)
    orchestrator = AgentOrchestrator()

    # Create specialist agents for different topics
    python_expert = factory.create_custom("PythonExpert", "specialist", 0.5)
    rust_expert = factory.create_custom("RustExpert", "specialist", 0.5)
    go_expert = factory.create_custom("GoExpert", "specialist", 0.5)

    orchestrator.register(python_expert)
    orchestrator.register(rust_expert)
    orchestrator.register(go_expert)

    # Execute in parallel (independent tasks)
    print("\n⚡ Executing 3 agents in parallel...")

    results = await orchestrator.execute_parallel(
        agent_names=["PythonExpert", "RustExpert", "GoExpert"],
        task_instruction="What makes your language great for async programming?",
        context="Comparing async capabilities",
    )

    # Display
    print("\n📊 Parallel Results:")
    for result in results:
        print(f"\n  {result.agent_name}:")
        print(f"  {result.content[:80]}...")


async def main():
    """Run all examples"""

    print("\n🚀 MULTI-AGENT SYSTEM DEMO")
    print("Clean Architecture + SOLID + KISS\n")

    # Run examples
    await example_single_agent()
    await example_multi_agent_sequence()
    await example_parallel_execution()

    print("\n" + "=" * 60)
    print("✅ All examples complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
