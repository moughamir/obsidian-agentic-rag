"""
Phase 2: Complete RAG System Example
Demonstrates full integration of:
- Multi-agent framework
- Obsidian vault access
- Vector RAG (semantic search)
- GraphRAG (wikilink expansion)
- TOON optimization
- RT kernel scheduling

Usage:
    python examples/complete_rag_example.py --vault /path/to/obsidian/vault
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.rag_agent import RAGAgentFactory
from src.application.orchestrator import AgentOrchestrator
from src.application.rag_pipeline import RAGConfig, RAGPipelineFactory
from src.domain.agent_interface import AgentTask
from src.infrastructure.llm_client import MockLLMClient, OllamaClient
from src.infrastructure.prompt_manager import FilePromptLoader
from src.infrastructure.rt_scheduler import PerformanceOptimizer, RTScheduler
from src.infrastructure.toon_converter import ContextOptimizer


async def setup_rag_system(vault_path: str, use_real_llm: bool = False):
    """
    Initialize complete RAG system

    Returns: (rag_pipeline, orchestrator, agents)
    """

    print("\n🔧 Setting up RAG System")
    print("=" * 60)

    # 1. Create RAG Pipeline
    print("\n1️⃣  Initializing RAG Pipeline...")
    rag_pipeline = RAGPipelineFactory.create_local_pipeline(
        vault_path=vault_path,
        use_vector_search=True,  # Set False if dependencies not installed
    )
    print("   ✓ RAG Pipeline ready")

    # 2. Initialize LLM Client
    print("\n2️⃣  Initializing LLM Client...")
    if use_real_llm:
        llm_client = OllamaClient(model="llama3.1:8b")
        print("   ✓ Using Ollama (llama3.1:8b)")
    else:
        llm_client = MockLLMClient()
        print("   ✓ Using Mock LLM (for testing)")

    # 3. Create Prompt Loader
    prompt_loader = FilePromptLoader()

    # 4. Create RAG-Enabled Agents
    print("\n3️⃣  Creating RAG-Enabled Agents...")

    researcher = RAGAgentFactory.create_researcher_with_rag(
        rag_pipeline=rag_pipeline, llm_client=llm_client, prompt_loader=prompt_loader
    )
    print("   ✓ RAG_Researcher (full retrieval strategy)")

    synthesizer = RAGAgentFactory.create_synthesizer_with_rag(
        rag_pipeline=rag_pipeline, llm_client=llm_client, prompt_loader=prompt_loader
    )
    print("   ✓ RAG_Synthesizer (graph expansion strategy)")

    specialist = RAGAgentFactory.create_specialist_with_rag(
        name="PythonExpert",
        expertise="Python programming",
        rag_pipeline=rag_pipeline,
        llm_client=llm_client,
        prompt_loader=prompt_loader,
    )
    print("   ✓ PythonExpert (hybrid search strategy)")

    # 5. Register with Orchestrator
    print("\n4️⃣  Configuring Multi-Agent Orchestrator...")
    orchestrator = AgentOrchestrator()
    orchestrator.register(researcher)
    orchestrator.register(synthesizer)
    orchestrator.register(specialist)
    print(f"   ✓ Registered {len(orchestrator.list_agents())} agents")

    # 6. RT Scheduling Setup
    print("\n5️⃣  Configuring RT Kernel Optimization...")
    if RTScheduler.is_rt_available():
        PerformanceOptimizer.optimize_for_inference()
        print("   ✓ RT scheduling active")
    else:
        print("   ⚠ RT scheduling not available (normal priority)")

    print("\n" + "=" * 60)
    print("✅ RAG System Ready!\n")

    return (
        rag_pipeline,
        orchestrator,
        {
            "researcher": researcher,
            "synthesizer": synthesizer,
            "specialist": specialist,
        },
    )


async def demo_basic_rag_query(rag_pipeline, agents):
    """
    Demo 1: Basic RAG Query
    Shows single agent with vault retrieval
    """

    print("\n" + "=" * 60)
    print("DEMO 1: Basic RAG Query")
    print("=" * 60)

    researcher = agents["researcher"]

    # Create query task
    task = AgentTask(
        instruction="What are the main concepts in my notes about clean architecture?",
        context="",  # Empty - will be filled by RAG
    )

    print(f"\n📝 Query: {task.instruction}")
    print("\n🔄 Processing with RAG...")

    # Process with RAG
    response = await researcher.process(task)

    # Display results
    print(f"\n🤖 Agent: {response.agent_name}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"📚 Sources: {len(response.sources)} documents")

    if response.sources:
        print("\n   Retrieved from:")
        for i, source in enumerate(response.sources[:3], 1):
            print(f"   {i}. {source}")

    print(f"\n💬 Response:")
    print(f"   {response.content[:200]}...")

    print("\n" + "=" * 60)


async def demo_multi_agent_rag_pipeline(orchestrator):
    """
    Demo 2: Multi-Agent RAG Pipeline
    Shows agents collaborating with shared context
    """

    print("\n" + "=" * 60)
    print("DEMO 2: Multi-Agent RAG Pipeline")
    print("=" * 60)

    query = "Explain Python async programming based on my notes"

    print(f"\n📝 Query: {query}")
    print("\n🔄 Executing Agent Pipeline:")
    print("   RAG_Researcher → RAG_Synthesizer → PythonExpert")

    # Execute sequential pipeline
    results = await orchestrator.execute_sequence(
        agent_names=["RAG_Researcher", "RAG_Synthesizer", "PythonExpert"],
        task_instruction=query,
    )

    # Display each agent's contribution
    print("\n📊 Pipeline Results:\n")

    for i, result in enumerate(results, 1):
        print(f"   Step {i}: {result.agent_name}")
        print(f"   - Confidence: {result.confidence:.2f}")
        print(f"   - Sources: {len(result.sources)}")
        print(f"   - Response: {result.content[:100]}...")
        print()

    print("=" * 60)


async def demo_graph_rag_exploration(rag_pipeline):
    """
    Demo 3: GraphRAG Exploration
    Shows wikilink expansion and knowledge graph navigation
    """

    print("\n" + "=" * 60)
    print("DEMO 3: GraphRAG - Knowledge Graph Navigation")
    print("=" * 60)

    query = "Machine learning applications"

    print(f"\n📝 Query: {query}")
    print("\n🔄 Strategies Comparison:\n")

    # Compare different retrieval strategies
    strategies = ["vector", "hybrid", "graph"]

    for strategy in strategies:
        print(f"   Strategy: {strategy.upper()}")

        result = await rag_pipeline.augmented_query(query=query, strategy=strategy)

        metrics = result["metrics"]
        print(f"   - Documents: {metrics['num_documents']}")
        print(f"   - Avg Score: {metrics['avg_score']:.3f}")
        print(f"   - Tokens: {metrics['context_tokens']}")
        print(f"   - Using TOON: {metrics['using_toon']}")
        print()

    print("=" * 60)


async def demo_toon_optimization(rag_pipeline):
    """
    Demo 4: TOON Token Optimization
    Shows token savings from TOON format
    """

    print("\n" + "=" * 60)
    print("DEMO 4: TOON Token Optimization")
    print("=" * 60)

    query = "Software architecture patterns"

    print(f"\n📝 Query: {query}")
    print("\n🔄 Comparing JSON vs TOON...\n")

    # Get results with TOON
    rag_pipeline.config.use_toon = True
    result_toon = await rag_pipeline.augmented_query(query, "hybrid")

    # Get results with JSON
    rag_pipeline.config.use_toon = False
    result_json = await rag_pipeline.augmented_query(query, "hybrid")

    # Compare
    toon_tokens = ContextOptimizer.estimate_tokens(result_toon["context"])
    json_tokens = ContextOptimizer.estimate_tokens(result_json["context"])

    savings = (json_tokens - toon_tokens) / json_tokens * 100

    print("   Format Comparison:")
    print(f"   - JSON tokens: {json_tokens}")
    print(f"   - TOON tokens: {toon_tokens}")
    print(f"   - Savings: {savings:.1f}%")
    print(
        f"   - Bytes saved: {len(result_json['context']) - len(result_toon['context'])}"
    )

    print("\n   💡 TOON reduces token usage by 30-60% for structured data!")

    print("\n" + "=" * 60)


async def demo_rt_performance(agents):
    """
    Demo 5: RT Kernel Performance
    Shows scheduling optimization
    """

    print("\n" + "=" * 60)
    print("DEMO 5: RT Kernel Performance")
    print("=" * 60)

    print("\n📊 RT Scheduling Status:")

    # Check RT availability
    if RTScheduler.is_rt_available():
        info = RTScheduler.get_current_priority()
        print(f"   ✓ RT Scheduling: ACTIVE")
        print(f"   - Policy: {info['policy']}")
        print(f"   - Priority: {info['priority']}")
        print(f"   - CPU Count: {PerformanceOptimizer.get_cpu_count()}")
    else:
        print(f"   ⚠ RT Scheduling: Not available")
        print(f"   - Running with normal priority")

    print("\n   RT Optimization Benefits:")
    print("   - Predictable latency for agent operations")
    print("   - Priority-based task scheduling")
    print("   - Better concurrent agent performance")
    print("   - Reduced context switching overhead")

    print("\n   💡 To enable on Arch Linux:")
    print("   1. Install: sudo pacman -S linux-rt linux-rt-headers")
    print("   2. Grant cap: sudo setcap cap_sys_nice=eip /usr/bin/python3")
    print("   3. Reboot into RT kernel")

    print("\n" + "=" * 60)


async def main():
    """Run complete demo"""

    # Parse arguments
    parser = argparse.ArgumentParser(description="Complete RAG System Demo")
    parser.add_argument(
        "--vault", type=str, default="./test_vault", help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--use-ollama", action="store_true", help="Use real Ollama instead of mock"
    )

    args = parser.parse_args()

    # Setup system
    rag_pipeline, orchestrator, agents = await setup_rag_system(
        vault_path=args.vault, use_real_llm=args.use_ollama
    )

    # Run demos
    try:
        await demo_basic_rag_query(rag_pipeline, agents)
        await demo_multi_agent_rag_pipeline(orchestrator)
        await demo_graph_rag_exploration(rag_pipeline)
        await demo_toon_optimization(rag_pipeline)
        await demo_rt_performance(agents)

        print("\n✅ All demos complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
