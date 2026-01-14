from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class DocumentChunk:
    """Represents a piece of text from the Obsidian vault"""
    id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None

@dataclass
class SearchResult:
    chunk: DocumentChunk
    score: float

class IVectorStore(ABC):
    """Interface for storing and retrieving document embeddings"""

    @abstractmethod
    async def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks to the store"""
        pass

    @abstractmethod
    async def search(self, query_embedding: list[float], limit: int = 5) -> list[SearchResult]:
        """Search for similar chunks"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all data"""
        pass

class IEmbedder(ABC):
    """Interface for generating text embeddings"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        pass
