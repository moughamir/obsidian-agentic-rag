"""
Phase 2: RAG-Enabled Agent
Agent Layer - Agent with RAG capabilities

Extends BaseAgent with:
- Automatic context retrieval
- Knowledge grounding
- Source citation
"""

from typing import Optional

from src.agents.concrete_agent import AgentConfig, BaseAgent
from src.application.rag_pipeline import RAGPipeline
from src.domain.agent_interface import AgentResponse, AgentTask
from src.infrastructure.llm_client import ILLMClient
from src.infrastructure.prompt_manager import IPromptLoader, PromptBuilder


class RAGAgent(BaseAgent):
    """
    Agent with RAG capabilities

    Enhancement over BaseAgent:
    - Automatically retrieves relevant context
    - Grounds responses in vault knowledge
    - Includes source citations

    Dependency Injection: RAGPipeline injected
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_client: ILLMClient,
        prompt_loader: IPromptLoader,
        rag_pipeline: Optional[RAGPipeline] = None,
        rag_strategy: str = "hybrid",
    ):
        """
        Initialize RAG-enabled agent

        Args:
            config: Agent configuration
            llm_client: LLM client
            prompt_loader: Prompt loader
            rag_pipeline: Optional RAG pipeline (for knowledge retrieval)
            rag_strategy: "vector", "keyword", "hybrid", "graph", "full"
        """
        super().__init__(config, llm_client, prompt_loader)
        self.rag_pipeline = rag_pipeline
        self.rag_strategy = rag_strategy
        self._rag_enabled = rag_pipeline is not None

    async def process(self, task: AgentTask) -> AgentResponse:
        """
        Process task with RAG enhancement

        Flow:
        1. Check if RAG should be used
        2. Retrieve relevant context if needed
        3. Build enhanced prompt
        4. Call LLM
        5. Return response with citations
        """

        # Determine if RAG should be used
        should_use_rag = self._should_use_rag(task)

        if should_use_rag and self._rag_enabled:
            # RAG-enhanced processing
            return await self._process_with_rag(task)
        else:
            # Standard processing (fallback to base)
            return await super().process(task)

    def _should_use_rag(self, task: AgentTask) -> bool:
        """
        Decide if RAG should be used

        Don't use RAG for:
        - Tasks with explicit context provided
        - Meta/reasoning tasks
        - Simple queries

        Use RAG for:
        - Factual questions
        - Research tasks
        - Knowledge-intensive queries
        """

        # Skip RAG if context already provided
        if task.context and len(task.context) > 200:
            return False

        # Check for RAG-appropriate keywords
        instruction_lower = task.instruction.lower()

        rag_keywords = [
            "what",
            "how",
            "why",
            "explain",
            "describe",
            "find",
            "search",
            "research",
            "information",
            "according to",
            "in my notes",
            "from vault",
        ]

        return any(keyword in instruction_lower for keyword in rag_keywords)

    async def _process_with_rag(self, task: AgentTask) -> AgentResponse:
        """
        Enhanced processing with RAG

        Steps:
        1. Retrieve context from vault
        2. Build enhanced prompt
        3. Generate response
        4. Extract citations
        """

        # 1. Retrieve context
        rag_result = await self.rag_pipeline.augmented_query(
            query=task.instruction, strategy=self.rag_strategy
        )

        context = rag_result["context"]
        documents = rag_result["documents"]

        # 2. Build enhanced prompt
        enhanced_task = AgentTask(
            instruction=task.instruction,
            context=context,
            previous_results=task.previous_results,
        )

        prompt = self._build_enhanced_prompt(enhanced_task, rag_result["metrics"])

        # 3. Generate response
        response_text = await self._llm.generate(prompt, self._config.temperature)

        # 4. Extract citations and create response
        sources = [doc.path for doc in documents]

        return AgentResponse(
            content=response_text,
            confidence=self._calculate_confidence(rag_result["metrics"]),
            agent_name=self.name,
            sources=sources,
        )

    def _build_enhanced_prompt(self, task: AgentTask, metrics: dict) -> str:
        """
        Build prompt with RAG context

        Includes:
        - System prompt (role)
        - Retrieved context
        - Task instruction
        - Citation requirements
        """

        # Format previous results
        previous = self._format_previous_results(task.previous_results)

        # Enhanced system prompt for RAG
        rag_system_prompt = f"""{self._system_prompt}

IMPORTANT INSTRUCTIONS FOR USING CONTEXT:
- You have access to relevant documents from the knowledge base
- Ground your response in the provided context
- Cite sources when making specific claims
- If information is not in the context, acknowledge the gap
- Be precise and factual

Context Statistics:
- Documents retrieved: {metrics["num_documents"]}
- Average relevance: {metrics["avg_score"]:.2f}
- Context format: {"TOON (optimized)" if metrics["using_toon"] else "Standard"}
"""

        # Build complete prompt
        parts = [f"SYSTEM: {rag_system_prompt}"]

        if task.context:
            parts.append(f"\nKNOWLEDGE BASE CONTEXT:\n{task.context}")

        if previous:
            parts.append(f"\nPREVIOUS RESULTS:\n{previous}")

        parts.append(f"\nQUERY: {task.instruction}")
        parts.append("\nRESPONSE (with citations):")

        return "\n".join(parts)

    def _calculate_confidence(self, metrics: dict) -> float:
        """
        Calculate confidence based on RAG metrics

        Higher confidence when:
        - More documents retrieved
        - Higher relevance scores
        - Good context coverage
        """

        num_docs = metrics["num_documents"]
        avg_score = metrics["avg_score"]

        # Base confidence on retrieval quality
        if num_docs == 0:
            return 0.3  # Low confidence without context

        # Scale based on documents and scores
        doc_factor = min(num_docs / 5, 1.0)  # Max at 5 docs
        score_factor = avg_score  # Already 0-1

        confidence = 0.5 + (doc_factor * 0.25) + (score_factor * 0.25)

        return min(confidence, 0.95)  # Cap at 0.95


class RAGAgentFactory:
    """
    Factory for creating RAG-enabled agents

    Simplifies agent creation with RAG capabilities
    """

    @staticmethod
    def create_rag_agent(
        name: str,
        role: str,
        rag_pipeline: RAGPipeline,
        llm_client: ILLMClient,
        prompt_loader: IPromptLoader,
        rag_strategy: str = "hybrid",
        temperature: float = 0.7,
    ) -> RAGAgent:
        """Create RAG-enabled agent with custom config"""

        config = AgentConfig(name=name, role=role, temperature=temperature)

        return RAGAgent(
            config=config,
            llm_client=llm_client,
            prompt_loader=prompt_loader,
            rag_pipeline=rag_pipeline,
            rag_strategy=rag_strategy,
        )

    @staticmethod
    def create_researcher_with_rag(
        rag_pipeline: RAGPipeline, llm_client: ILLMClient, prompt_loader: IPromptLoader
    ) -> RAGAgent:
        """Create research agent with RAG"""

        return RAGAgentFactory.create_rag_agent(
            name="RAG_Researcher",
            role="researcher",
            rag_pipeline=rag_pipeline,
            llm_client=llm_client,
            prompt_loader=prompt_loader,
            rag_strategy="full",  # Use comprehensive retrieval
            temperature=0.4,
        )

    @staticmethod
    def create_synthesizer_with_rag(
        rag_pipeline: RAGPipeline, llm_client: ILLMClient, prompt_loader: IPromptLoader
    ) -> RAGAgent:
        """Create synthesis agent with RAG"""

        return RAGAgentFactory.create_rag_agent(
            name="RAG_Synthesizer",
            role="synthesizer",
            rag_pipeline=rag_pipeline,
            llm_client=llm_client,
            prompt_loader=prompt_loader,
            rag_strategy="graph",  # Use graph expansion for synthesis
            temperature=0.6,
        )

    @staticmethod
    def create_specialist_with_rag(
        name: str,
        expertise: str,
        rag_pipeline: RAGPipeline,
        llm_client: ILLMClient,
        prompt_loader: IPromptLoader,
    ) -> RAGAgent:
        """Create domain specialist with RAG"""

        return RAGAgentFactory.create_rag_agent(
            name=name,
            role="specialist",
            rag_pipeline=rag_pipeline,
            llm_client=llm_client,
            prompt_loader=prompt_loader,
            rag_strategy="hybrid",
            temperature=0.5,
        )
