import json
import numpy as np
from pathlib import Path
from src.domain.vector_store_interface import IVectorStore, DocumentChunk, SearchResult

class LocalVectorStore(IVectorStore):
    """
    A simple vector store that persists data to a local JSON file
    and uses numpy for in-memory cosine similarity search.
    """
    def __init__(self, persist_path: str = "./data/vector_store.json"):
        self.persist_path = Path(persist_path)
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._chunks: dict[str, DocumentChunk] = {}
        self._matrix: np.ndarray | None = None
        self._load()

    def _load(self):
        if self.persist_path.exists():
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    loaded_chunks = [DocumentChunk(**item) for item in data]
                    self._chunks = {c.id: c for c in loaded_chunks}
                    if self._chunks:
                        embeddings = [c.embedding for c in self._chunks.values() if c.embedding is not None]
                        if embeddings:
                            self._matrix = np.array(embeddings)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {self.persist_path}. Starting fresh.")
                    self._chunks = {}

    def _save(self):
        data = [
            {
                "id": c.id, "content": c.content, "metadata": c.metadata,
                "embedding": c.embedding
            } for c in self._chunks.values()
        ]
        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    async def add(self, chunks: list[DocumentChunk]) -> None:
        """Adds or updates document chunks in the store."""
        for chunk in chunks:
            self._chunks[chunk.id] = chunk

        # Rebuild matrix with all valid embeddings
        all_embeddings = [c.embedding for c in self._chunks.values() if c.embedding is not None]
        if all_embeddings:
            self._matrix = np.array(all_embeddings)

        self._save()

    async def search(self, query_embedding: list[float], limit: int = 5) -> list[SearchResult]:
        """Performs a cosine similarity search."""
        if self._matrix is None or len(self._chunks) == 0:
            return []

        query_vec = np.array(query_embedding)

        # Normalize vectors for cosine similarity
        norm_query = query_vec / np.linalg.norm(query_vec)
        norm_matrix = self._matrix / np.linalg.norm(self._matrix, axis=1)[:, np.newaxis]

        # Compute similarities
        similarities = np.dot(norm_matrix, norm_query)

        # Get top indices (avoiding argpartition for simplicity)
        top_indices = np.argsort(similarities)[::-1][:limit]

        chunk_list = [c for c in self._chunks.values() if c.embedding is not None]

        results = []
        for idx in top_indices:
            # Ensure index is within bounds
            if idx < len(chunk_list):
                results.append(SearchResult(
                    chunk=chunk_list[idx],
                    score=float(similarities[idx])
                ))
        return results

    def clear(self) -> None:
        """Clears all data from the vector store."""
        self._chunks = {}
        self._matrix = None
        if self.persist_path.exists():
            self.persist_path.unlink()
        print("Vector store cleared.")
