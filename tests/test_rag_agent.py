import pytest

from src.agents.concrete_agent import AgentConfig
from src.agents.rag_agent import RAGAgent
from src.domain.agent_interface import AgentResponse, AgentTask
from src.infrastructure.llm_client import MockLLMClient
from src.infrastructure.mcp_interface import MCPDocument


class MockRAGPipeline:
    async def augmented_query(self, query, strategy="hybrid"):
        return {
            "query": query,
            "context": "ctx",
            "documents": [],
            "metrics": {
                "num_documents": 0,
                "avg_score": 0.0,
                "context_tokens": 10,
                "using_toon": False,
            },
        }


class DummyPromptLoader:
    def load(self, role: str) -> str:
        return f"You are a dummy {role}"


@pytest.mark.asyncio
async def test_rag_agent_process_with_mock_pipeline():
    """
    Basic end-to-end check: RAGAgent uses the pipeline, calls LLM and returns
    an AgentResponse with confidence and sources fields.
    """
    config = AgentConfig(name="TestAgent", role="researcher", temperature=0.5)
    llm = MockLLMClient()
    loader = DummyPromptLoader()
    pipeline = MockRAGPipeline()

    agent = RAGAgent(
        config=config, llm_client=llm, prompt_loader=loader, rag_pipeline=pipeline
    )
    task = AgentTask(instruction="What is X?")
    resp = await agent.process(task)

    assert resp.agent_name == agent.name
    assert isinstance(resp.content, str) and resp.content.startswith(
        "[MOCK LLM RESPONSE]"
    )
    # With 0 documents the implementation returns a baseline confidence of 0.3
    assert resp.confidence == pytest.approx(0.3, rel=1e-3)
    assert isinstance(resp.sources, list)
    assert resp.sources == []


@pytest.mark.asyncio
async def test_rag_agent_with_documents_and_scores():
    """
    When the pipeline returns documents and an average score, RAGAgent should
    reflect those in `sources` and compute confidence accordingly.
    """

    config = AgentConfig(name="T2", role="researcher", temperature=0.5)
    llm = MockLLMClient()
    loader = DummyPromptLoader()

    class PipelineWithDocs:
        async def augmented_query(self, query, strategy="hybrid"):
            docs = [
                MCPDocument(
                    path="a.md", content="alpha content", metadata={}, score=0.8
                ),
                MCPDocument(
                    path="b.md", content="beta content", metadata={}, score=0.9
                ),
            ]
            metrics = {
                "num_documents": len(docs),
                "avg_score": sum(d.score for d in docs) / len(docs),
                "context_tokens": 40,
                "using_toon": False,
            }
            return {
                "query": query,
                "context": "ctx",
                "documents": docs,
                "metrics": metrics,
            }

    pipeline = PipelineWithDocs()
    agent = RAGAgent(
        config=config, llm_client=llm, prompt_loader=loader, rag_pipeline=pipeline
    )
    task = AgentTask(instruction="What are the main points?")
    resp = await agent.process(task)

    assert resp.sources == ["a.md", "b.md"]
    # Compute expected confidence using the same formula as the code
    expected_confidence = 0.5 + (min(2 / 5, 1) * 0.25) + (0.85 * 0.25)
    assert resp.confidence == pytest.approx(expected_confidence, rel=1e-3)


@pytest.mark.asyncio
async def test_rag_agent_without_pipeline_fallsback_to_baseagent():
    """
    If no RAG pipeline is configured, the agent should fall back to BaseAgent.process
    and return an AgentResponse with the default confidence (0.0).
    """
    config = AgentConfig(name="NoPipeline", role="researcher", temperature=0.5)
    llm = MockLLMClient()
    loader = DummyPromptLoader()
    agent = RAGAgent(
        config=config, llm_client=llm, prompt_loader=loader, rag_pipeline=None
    )

    task = AgentTask(instruction="What is Y?")
    resp = await agent.process(task)

    assert isinstance(resp.content, str)
    # BaseAgent does not set confidence, dataclass default is 0.0
    assert resp.confidence == pytest.approx(0.0)


def test_format_previous_results_method():
    """
    Ensure the helper that formats previous results returns a readable string
    including confidence and source information.
    """
    config = AgentConfig(name="FormatCheck", role="researcher", temperature=0.5)
    llm = MockLLMClient()
    loader = DummyPromptLoader()
    agent = RAGAgent(
        config=config, llm_client=llm, prompt_loader=loader, rag_pipeline=None
    )

    res1 = AgentResponse(
        agent_name="A", content="first result", confidence=0.45, sources=["x.md"]
    )
    res2 = AgentResponse(agent_name="B", content="second", confidence=0.85, sources=[])

    out = agent._format_previous_results([res1, res2])
    assert "A (confidence: 0.45)" in out
    assert "Sources: x.md" in out
    assert "first result" in out
    assert "B (confidence: 0.85)" in out
