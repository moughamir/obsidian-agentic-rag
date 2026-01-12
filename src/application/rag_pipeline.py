"""
Phase 2: Complete RAG Pipeline
Application Layer - Orchestrates all RAG components

Combines:
- Obsidian MCP (vault access)
- Vector RAG (semantic search)
- Graph Navigator (wikilink expansion)
- TOON Converter (token efficiency)
- RT Scheduler (performance)
"""

from dataclasses import dataclass
from typing import List, Optional

from src.infrastructure.graph_navigator import GraphNavigator
from src.infrastructure.mcp_interface import MCPDocument
from src.infrastructure.obsidian_mcp_client import IObsidianMCP
from src.infrastructure.rt_scheduler import RTScheduler
from src.infrastructure.toon_converter import ContextOptimizer, TOONConverter
from src.infrastructure.vector_rag import IVectorMCP


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""

    # Search parameters
    top_k: int = 5
    graph_depth: int = 2
    use_hybrid_search: bool = True
    vector_weight: float = 0.6

    # Optimization
    use_toon: bool = True
    use_rt_scheduling: bool = True
    rerank: bool = True

    # Context management
    max_context_tokens: int = 4000
    include_metadata: bool = True


class RAGPipeline:
    """
    Complete RAG Pipeline

    Single Responsibility: Orchestrate retrieval and augmentation

    Pipeline stages:
    1. Query understanding
    2. Retrieval (vector + graph)
    3. Reranking
    4. Context optimization (TOON)
    5. Augmentation
    """

    def __init__(
        self,
        obsidian_client: IObsidianMCP,
        vector_client: IVectorMCP,
        config: Optional[RAGConfig] = None,
    ):
        self.obsidian = obsidian_client
        self.vector = vector_client
        self.graph = GraphNavigator(obsidian_client)
        self.config: RAGConfig = config or RAGConfig()

        # Initialize RT scheduling if enabled
        if self.config.use_rt_scheduling and RTScheduler.is_rt_available():
            RTScheduler.set_priority(RTScheduler.PRIORITY_HIGH)

    async def retrieve(self, query: str, strategy: str = "hybrid") -> List[MCPDocument]:
        """
        Main retrieval method

        Strategies:
        - "vector": Pure semantic search
        - "keyword": Pure keyword search
        - "hybrid": Combines vector + keyword (recommended)
        - "graph": Follows wikilinks from top results
        - "full": All methods combined

        Returns:
            Ranked list of relevant documents
        """

        if strategy == "vector":
            return await self._vector_retrieval(query)

        elif strategy == "keyword":
            return await self._keyword_retrieval(query)

        elif strategy == "hybrid":
            return await self._hybrid_retrieval(query)

        elif strategy == "graph":
            return await self._graph_retrieval(query)

        elif strategy == "full":
            return await self._full_retrieval(query)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    @RTScheduler.with_priority(RTScheduler.PRIORITY_HIGH)
    async def _vector_retrieval(self, query: str) -> List[MCPDocument]:
        """Pure semantic search"""
        results = await self.vector.semantic_search(query, k=self.config.top_k)
        return results

    async def _keyword_retrieval(self, query: str) -> List[MCPDocument]:
        """Pure keyword search via Obsidian"""
        results = await self.obsidian.search_vault(query)
        return results[: self.config.top_k]

    @RTScheduler.with_priority(RTScheduler.PRIORITY_HIGH)
    async def _hybrid_retrieval(self, query: str) -> List[MCPDocument]:
        """
        Hybrid: Vector + Keyword

        Best for most queries
        """
        results = await self.vector.hybrid_search(
            query, k=self.config.top_k, vector_weight=self.config.vector_weight
        )

        # Rerank if enabled
        if self.config.rerank and len(results) > 3:
            results = await self.vector.rerank(
                query, results, top_k=min(3, len(results))
            )

        return results

    async def _graph_retrieval(self, query: str) -> List[MCPDocument]:
        """
        GraphRAG: Follow wikilinks from initial results

        Best for: Exploratory queries, broad topics
        """
        # First, get initial results
        initial_results = await self._hybrid_retrieval(query)

        if not initial_results:
            return []

        # Expand context via graph
        expanded_docs = []
        seen_paths = set()

        for doc in initial_results[:3]:  # Expand top 3
            graph_docs = await self.graph.expand_context(
                doc.path, depth=self.config.graph_depth
            )

            # Add unique documents
            for graph_doc in graph_docs:
                if graph_doc.path not in seen_paths:
                    expanded_docs.append(graph_doc)
                    seen_paths.add(graph_doc.path)

        # Sort by relevance
        expanded_docs.sort(key=lambda x: x.score, reverse=True)

        return expanded_docs[: self.config.top_k]

    async def _full_retrieval(self, query: str) -> List[MCPDocument]:
        """
        Full retrieval: Hybrid + Graph

        Most comprehensive but slowest
        """
        # Get hybrid results
        hybrid_docs = await self._hybrid_retrieval(query)

        # Expand via graph
        graph_docs = []
        seen_paths = {doc.path for doc in hybrid_docs}

        for doc in hybrid_docs[:2]:  # Expand top 2
            expanded = await self.graph.expand_context(doc.path, depth=2)

            for exp_doc in expanded:
                if exp_doc.path not in seen_paths:
                    graph_docs.append(exp_doc)
                    seen_paths.add(exp_doc.path)

        # Combine and sort
        all_docs = hybrid_docs + graph_docs
        all_docs.sort(key=lambda x: x.score, reverse=True)

        return all_docs[: self.config.top_k]

    def build_context(self, query: str, documents: List[MCPDocument]) -> str:
        """
        Build optimized context for LLM

        Steps:
        1. Format documents
        2. Convert to TOON if enabled
        3. Ensure within token limit
        4. Add metadata if enabled
        """

        # Prepare document data
        doc_data = []
        for i, doc in enumerate(documents):
            doc_info = {
                "rank": i + 1,
                "path": doc.path,
                "score": round(doc.score, 3),
                "content": self._truncate_content(doc.content),
            }

            if self.config.include_metadata:
                doc_info["tags"] = doc.metadata.get("tags", [])
                doc_info["wikilinks"] = doc.metadata.get("wikilinks", [])

            doc_data.append(doc_info)

        # Format context
        if self.config.use_toon:
            # Use TOON for token efficiency
            context_dict = {"query": query, "documents": doc_data}
            context = TOONConverter.to_toon(context_dict)
        else:
            # Standard format
            context_parts = [f"Query: {query}\n\nRelevant Documents:\n"]

            for doc in doc_data:
                context_parts.append(
                    f"\n[{doc['rank']}] {doc['path']} (score: {doc['score']})\n"
                    f"{doc['content']}\n"
                )

            context = "\n".join(context_parts)

        # Ensure within token limit
        estimated_tokens = ContextOptimizer.estimate_tokens(context)

        if estimated_tokens > self.config.max_context_tokens:
            # Truncate
            ratio = self.config.max_context_tokens / estimated_tokens
            target_length = int(len(context) * ratio)
            context = context[:target_length] + "\n... [truncated]"

        return context

    def _truncate_content(self, content: str, max_chars: int = 1000) -> str:
        """Truncate long content intelligently"""
        if len(content) <= max_chars:
            return content

        # Try to break at sentence boundary
        truncated = content[:max_chars]
        last_period = truncated.rfind(".")

        if last_period > max_chars * 0.7:  # If we found a good break point
            return truncated[: last_period + 1]
        else:
            return truncated + "..."

    async def augmented_query(self, query: str, strategy: str = "hybrid") -> dict:
        """
        Complete RAG query

        Returns:
            Dict with context and metadata for LLM
        """
        # Retrieve relevant documents
        documents = await self.retrieve(query, strategy=strategy)

        # Build optimized context
        context = self.build_context(query, documents)

        # Calculate metrics
        metrics = {
            "num_documents": len(documents),
            "avg_score": sum(d.score for d in documents) / len(documents)
            if documents
            else 0,
            "context_tokens": ContextOptimizer.estimate_tokens(context),
            "using_toon": self.config.use_toon,
            "using_rt": self.config.use_rt_scheduling,
        }

        return {
            "query": query,
            "context": context,
            "documents": documents,
            "metrics": metrics,
        }


class RAGPipelineFactory:
    """
    Factory for creating configured RAG pipelines

    Simplifies setup with sensible defaults
    """

    @staticmethod
    def create_local_pipeline(
        vault_path: str, use_vector_search: bool = True
    ) -> RAGPipeline:
        """
        Create pipeline for local Obsidian vault

        Uses:
        - LocalObsidianReader (direct file access)
        - VectorRAG or MockVectorRAG
        """
        from src.infrastructure.obsidian_mcp_client import LocalObsidianReader
        from src.infrastructure.vector_rag import MockVectorRAG, VectorRAG

        obsidian_client = LocalObsidianReader(vault_path)

        if use_vector_search:
            try:
                vector_client = VectorRAG()
            except ImportError:
                print("Warning: Vector dependencies not found, using mock")
                vector_client = MockVectorRAG()
        else:
            vector_client = MockVectorRAG()

        config = RAGConfig(
            top_k=5,
            graph_depth=2,
            use_hybrid_search=use_vector_search,
            use_toon=True,
            use_rt_scheduling=RTScheduler.is_rt_available(),
        )

        return RAGPipeline(obsidian_client, vector_client, config)

    @staticmethod
    def create_api_pipeline(
        api_key: str, host: str = "127.0.0.1", port: int = 27124
    ) -> RAGPipeline:
        """
        Create pipeline using Obsidian REST API

        Requires: Obsidian Local REST API plugin
        """
        from src.infrastructure.obsidian_mcp_client import ObsidianMCPClient
        from src.infrastructure.vector_rag import MockVectorRAG, VectorRAG

        obsidian_client = ObsidianMCPClient(api_key, host, port)

        try:
            vector_client = VectorRAG()
        except ImportError:
            vector_client = MockVectorRAG()

        config = RAGConfig(
            use_toon=True, use_rt_scheduling=RTScheduler.is_rt_available()
        )

        return RAGPipeline(obsidian_client, vector_client, config)
