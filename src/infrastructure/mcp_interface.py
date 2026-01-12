"""
Phase 2: Model Context Protocol (MCP) Interface
Domain Layer - Defines contracts for data access

MCP provides a standardized way for agents to interact with
knowledge sources (Obsidian, web, etc.) without being coupled
to a specific implementation.

Key Principles:
- Abstraction: Hides data source details
- Decoupling: Agents depend on interfaces, not concrete classes
- Testability: Allows for mock implementations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MCPDocument:
    """Standardized document format for MCP"""
    path: str  # Unique identifier (file path, URL)
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # For relevance scoring


class IObsidianMCP(ABC):
    """Interface for Obsidian vault operations"""

    @abstractmethod
    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Retrieve a single note by path"""
        pass

    @abstractmethod
    async def list_notes(self) -> List[str]:
        """List all notes in the vault"""
        pass

    @abstractmethod
    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Perform a keyword search in the vault"""
        pass


class IVectorMCP(ABC):
    """Interface for vector search operations"""

    @abstractmethod
    async def semantic_search(
        self,
        query: str,
        k: int = 5
    ) -> List[MCPDocument]:
        """Find documents by semantic similarity"""
        pass

    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_weight: float = 0.6
    ) -> List[MCPDocument]:
        """Combine semantic and keyword search"""
        pass


class IGraphMCP(ABC):
    """Interface for knowledge graph navigation"""

    @abstractmethod
    async def get_linked_notes(self, path: str) -> List[str]:
        """Get outgoing links from a note"""
        pass

    @abstractmethod
    async def get_backlinks(self, path: str) -> List[str]:
        """Get incoming links to a note"""
        pass

    @abstractmethod
    async def expand_context(
        self,
        path: str,
        depth: int = 2
    ) -> List[MCPDocument]:
        """Follow links to expand context"""
        pass

    @abstractmethod
    async def find_path(
        self,
        start: str,
        end: str
    ) -> Optional[List[str]]:
        """Find connection between two notes"""
        pass
