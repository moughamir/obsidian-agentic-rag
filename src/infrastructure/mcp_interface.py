"""
Phase 2: MCP (Model Context Protocol) Integration
Domain Layer - MCP Abstractions

Single Responsibility: Define MCP contracts
Interface Segregation: Separate concerns (search, fetch, graph)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MCPDocument:
    """Value object representing a document from MCP server"""

    path: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0  # Relevance score


@dataclass
class MCPSearchQuery:
    """Value object for search queries"""

    query: str
    max_results: int = 10
    filters: Optional[Dict[str, Any]] = None


class IMCPClient(ABC):
    """
    Base interface for MCP clients
    Abstracts communication with MCP servers
    """

    @abstractmethod
    async def search(self, query: MCPSearchQuery) -> List[MCPDocument]:
        """Search for documents"""
        pass

    @abstractmethod
    async def fetch(self, path: str) -> Optional[MCPDocument]:
        """Fetch specific document"""
        pass


class IObsidianMCP(IMCPClient):
    """
    Interface for Obsidian-specific MCP operations
    """

    @abstractmethod
    async def list_notes(self, path: str = "") -> List[str]:
        """List all notes in vault"""
        pass

    @abstractmethod
    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Get specific note with metadata"""
        pass

    @abstractmethod
    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Search vault with text/regex"""
        pass

    @abstractmethod
    async def get_frontmatter(self, path: str) -> Dict[str, Any]:
        """Extract YAML frontmatter"""
        pass

    @abstractmethod
    async def get_tags(self, path: str) -> List[str]:
        """Extract tags from note"""
        pass


class IGraphMCP(ABC):
    """
    Interface for knowledge graph operations
    Navigate wikilinks and connections
    """

    @abstractmethod
    async def get_linked_notes(self, path: str) -> List[str]:
        """Get notes linked from this note"""
        pass

    @abstractmethod
    async def get_backlinks(self, path: str) -> List[str]:
        """Get notes linking to this note"""
        pass

    @abstractmethod
    async def expand_context(self, path: str, depth: int = 2) -> List[MCPDocument]:
        """
        Expand context by following wikilinks
        depth: how many link hops to follow
        """
        pass

    @abstractmethod
    async def find_path(self, start: str, end: str) -> Optional[List[str]]:
        """Find connection path between notes"""
        pass


class IVectorMCP(ABC):
    """
    Interface for vector database operations
    Semantic search via embeddings
    """

    @abstractmethod
    async def semantic_search(self, query: str, k: int = 5) -> List[MCPDocument]:
        """Semantic similarity search"""
        pass

    @abstractmethod
    async def hybrid_search(
        self, query: str, k: int = 5, vector_weight: float = 0.6
    ) -> List[MCPDocument]:
        """Hybrid search: vector + keyword (BM25)"""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[MCPDocument]) -> None:
        """Add/update documents in vector store"""
        pass
