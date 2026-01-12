"""
Phase 2: Vector RAG Implementation
Infrastructure Layer - Semantic search and hybrid retrieval

Combines:
- Vector embeddings (semantic similarity)
- BM25 keyword search
- Reranking for precision
"""

from dataclasses import dataclass
from typing import Any, List, Optional

import numpy as np

from src.infrastructure.mcp_interface import IVectorMCP, MCPDocument

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model"""

    model_name: str = "all-MiniLM-L6-v2"  # Fast, 80MB
    # Alternatives:
    # - "BAAI/bge-small-en-v1.5" (better quality, 130MB)
    # - "nomic-ai/nomic-embed-text-v1.5" (high quality, 550MB)
    device: str = "cpu"  # or "cuda"


class VectorRAG(IVectorMCP):
    """
    Vector-based RAG implementation

    Single Responsibility: Semantic search via embeddings

    Features:
    - Embedding generation
    - Vector similarity search
    - Hybrid search (vector + BM25)
    - CrossEncoder reranking
    """

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        persist_directory: str = "./data/vector_db",
    ):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers required. "
                "Install: pip install sentence-transformers"
            )

        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb required. Install: pip install chromadb")

        # Normalize config and pre-declare attributes for static typing
        self.config: EmbeddingConfig = config or EmbeddingConfig()

        # Attributes that depend on optional third-party packages
        self.embedder: Any = None
        self.client: Any = None
        self.collection: Any = None

        # Load embedding model
        self.embedder = SentenceTransformer(
            self.config.model_name, device=self.config.device
        )

        # Initialize ChromaDB
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet", persist_directory=persist_directory
            )
        )

        self.collection = self.client.get_or_create_collection(
            name="obsidian_notes", metadata={"hnsw:space": "cosine"}
        )

        # BM25 for keyword search
        self._bm25: Any = None
        self._documents: List[str] = []
        self._doc_ids: List[str] = []

        # Immediately build BM25 index from existing documents in ChromaDB
        self._rebuild_bm25_from_chroma()

    def _rebuild_bm25_from_chroma(self):
        """Helper to build BM25 index from all docs in ChromaDB."""
        if not BM25_AVAILABLE:
            return

        all_docs = self.collection.get()
        if not all_docs or not all_docs["ids"]:
            return

        self._documents = all_docs["documents"]
        self._doc_ids = all_docs["ids"]
        tokenized_docs = [doc.lower().split() for doc in self._documents]
        self._bm25 = BM25Okapi(tokenized_docs)

    async def semantic_search(self, query: str, k: int = 5) -> List[MCPDocument]:
        """
        Pure semantic search via embeddings

        Best for: Conceptual queries, synonyms, related ideas
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Search vector database
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)

        # Convert to MCPDocument
        documents = []

        if results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                doc = MCPDocument(
                    path=results["metadatas"][0][i].get("path", ""),
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    score=1
                    - results["distances"][0][i],  # Convert distance to similarity
                )
                documents.append(doc)

        return documents

    async def hybrid_search(
        self, query: str, k: int = 5, vector_weight: float = 0.6
    ) -> List[MCPDocument]:
        """
        Hybrid search: Vector (60%) + BM25 (40%)

        Best for: Balancing semantic and exact keyword matches

        Algorithm:
        1. Get 2*k candidates from vector search
        2. Get 2*k candidates from BM25
        3. Normalize and combine scores
        4. Return top k
        """
        if not BM25_AVAILABLE:
            # Fallback to pure vector search
            return await self.semantic_search(query, k)

        # Vector search
        vector_docs = await self.semantic_search(query, k * 2)

        # BM25 search
        if self._bm25 is None:
            return vector_docs[:k]  # Return vector only if BM25 not initialized

        tokenized_query = query.lower().split()
        bm25_scores = self._bm25.get_scores(tokenized_query)

        # Get top BM25 candidates
        bm25_indices = np.argsort(bm25_scores)[::-1][: k * 2]

        # Combine scores
        doc_scores = {}

        # Add vector scores (normalized)
        max_vector_score = max([d.score for d in vector_docs]) if vector_docs else 1.0
        for doc in vector_docs:
            doc_id = doc.path
            normalized_score = doc.score / max_vector_score
            doc_scores[doc_id] = {
                "vector": normalized_score * vector_weight,
                "bm25": 0,
                "doc": doc,
            }

        # Add BM25 scores (normalized)
        max_bm25_score = max(bm25_scores) if len(bm25_scores) > 0 else 1.0
        for idx in bm25_indices:
            doc_id = self._doc_ids[idx]
            normalized_score = bm25_scores[idx] / max_bm25_score

            if doc_id in doc_scores:
                doc_scores[doc_id]["bm25"] = normalized_score * (1 - vector_weight)
            else:
                # Create doc from stored data
                doc_scores[doc_id] = {
                    "vector": 0,
                    "bm25": normalized_score * (1 - vector_weight),
                    "doc": MCPDocument(
                        path=doc_id,
                        content=self._documents[idx],
                        metadata={"source": "bm25"},
                    ),
                }

        # Calculate final scores and sort
        ranked_docs = []
        for doc_id, scores in doc_scores.items():
            final_score = scores["vector"] + scores["bm25"]
            doc = scores["doc"]
            doc.score = final_score
            ranked_docs.append(doc)

        ranked_docs.sort(key=lambda x: x.score, reverse=True)

        return ranked_docs[:k]

    async def add_documents(self, documents: List[MCPDocument]) -> None:
        """
        Add or update documents in vector store

        Called when: Vault is indexed or updated
        """
        if not documents:
            return

        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for doc in documents:
            ids.append(doc.path)
            texts.append(doc.content)
            metadatas.append(doc.metadata)

        # Generate embeddings in batch (faster)
        embeddings = self.embedder.encode(texts).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings
        )

        # Update BM25 index
        if BM25_AVAILABLE:
            self._documents = texts
            self._doc_ids = ids
            tokenized_docs = [doc.lower().split() for doc in texts]
            self._bm25 = BM25Okapi(tokenized_docs)

    async def rerank(
        self, query: str, candidates: List[MCPDocument], top_k: int = 3
    ) -> List[MCPDocument]:
        """
        Rerank candidates using CrossEncoder

        More accurate but slower than embeddings
        Use after initial retrieval to refine top results
        """
        try:
            reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except (
            OSError,
            ValueError,
        ):  # Catch common model loading errors (e.g., model not found, network issues)
            # Fallback: return original ranking
            return candidates[:top_k]

        # Create query-document pairs
        pairs = [[query, doc.content] for doc in candidates]

        # Get reranking scores
        scores = reranker.predict(pairs)

        # Combine with documents
        reranked = [(doc, score) for doc, score in zip(candidates, scores)]

        # Sort by reranking score
        reranked.sort(key=lambda x: x[1], reverse=True)

        # Update document scores
        result = []
        for doc, score in reranked[:top_k]:
            doc.score = float(score)
            result.append(doc)

        return result


class MockVectorRAG(IVectorMCP):
    """
    Mock implementation for testing without dependencies
    """

    def __init__(self):
        self._documents: List[MCPDocument] = []

    async def semantic_search(self, query: str, k: int = 5) -> List[MCPDocument]:
        """Simple keyword matching"""
        results = []
        query_lower = query.lower()

        for doc in self._documents:
            if query_lower in doc.content.lower():
                doc.score = doc.content.lower().count(query_lower) / len(
                    doc.content.split()
                )
                results.append(doc)

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    async def hybrid_search(
        self, query: str, k: int = 5, vector_weight: float = 0.6
    ) -> List[MCPDocument]:
        """Fallback to semantic search"""
        return await self.semantic_search(query, k)

    async def add_documents(self, documents: List[MCPDocument]) -> None:
        """Store in memory"""
        self._documents.extend(documents)
