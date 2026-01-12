"""
Phase 2: Knowledge Graph Navigator
Infrastructure Layer - GraphRAG implementation

Navigates Obsidian knowledge graph via wikilinks
Expands context by following connections
"""

from typing import Dict, List, Optional, Set

import networkx as nx

from src.infrastructure.mcp_interface import IGraphMCP, MCPDocument
from src.infrastructure.obsidian_mcp_client import IObsidianMCP


class GraphNavigator(IGraphMCP):
    """
    Navigate knowledge graph via wikilinks

    Single Responsibility: Graph traversal and path finding
    Depends on: IObsidianMCP for reading notes
    """

    def __init__(self, obsidian_client: IObsidianMCP):
        self.obsidian = obsidian_client
        self._graph_cache: Optional[nx.DiGraph] = None

    async def get_linked_notes(self, path: str) -> List[str]:
        """Get outgoing links from note"""
        note = await self.obsidian.get_note(path)
        if not note:
            return []

        wikilinks = note.metadata.get("wikilinks", [])

        # Convert wikilink to file path
        linked_paths = []
        for link in wikilinks:
            # Try with .md extension
            link_path = f"{link}.md"
            if await self.obsidian.get_note(link_path):
                linked_paths.append(link_path)

        return linked_paths

    async def get_backlinks(self, path: str) -> List[str]:
        """
        Get incoming links to note
        (notes that link to this one)
        """
        # Build graph if not cached
        if self._graph_cache is None:
            await self._build_graph()

        graph = self._graph_cache
        # Defensive: if graph build failed, return empty backlinks
        if graph is None:
            return []

        if path not in graph:
            return []

        # Get predecessors (nodes linking to this one)
        return list(graph.predecessors(path))

    async def expand_context(self, path: str, depth: int = 2) -> List[MCPDocument]:
        """
        Expand context by following wikilinks

        GraphRAG Strategy:
        1. Start from anchor note
        2. Follow outgoing links (depth levels)
        3. Include backlinks (nodes pointing to us)
        4. Return all discovered notes

        Args:
            path: Starting note path
            depth: How many link hops to follow (1-3 typical)

        Returns:
            List of connected notes with relevance scoring
        """
        visited: Set[str] = set()
        to_visit: List[tuple[str, int]] = [(path, 0)]  # (path, current_depth)
        expanded_docs: List[MCPDocument] = []

        while to_visit:
            current_path, current_depth = to_visit.pop(0)

            if current_path in visited:
                continue

            visited.add(current_path)

            # Fetch the note
            note = await self.obsidian.get_note(current_path)
            if not note:
                continue

            # Calculate relevance score based on depth
            # Closer notes are more relevant
            note.score = 1.0 / (current_depth + 1)
            expanded_docs.append(note)

            # Continue if we haven't reached max depth
            if current_depth < depth:
                # Add outgoing links to queue
                linked = await self.get_linked_notes(current_path)
                for link in linked:
                    if link not in visited:
                        to_visit.append((link, current_depth + 1))

        # Also get backlinks for the original note (high relevance)
        backlinks = await self.get_backlinks(path)
        for backlink_path in backlinks:
            if backlink_path not in visited:
                backlink_note = await self.obsidian.get_note(backlink_path)
                if backlink_note:
                    backlink_note.score = 0.9  # High relevance
                    expanded_docs.append(backlink_note)

        # Sort by relevance score
        expanded_docs.sort(key=lambda x: x.score, reverse=True)

        return expanded_docs

    async def find_path(self, start: str, end: str) -> Optional[List[str]]:
        """
        Find connection path between two notes

        Uses: BFS to find shortest path through wikilinks
        """
        if self._graph_cache is None:
            await self._build_graph()

        graph = self._graph_cache
        # If graph is still None after attempting build, return no path
        if graph is None:
            return None

        try:
            path = nx.shortest_path(graph, start, end)
            return path
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return None

    async def _build_graph(self) -> None:
        """
        Build complete knowledge graph from vault

        Cache for efficiency - rebuild when vault changes
        """
        graph = nx.DiGraph()

        # Get all notes
        all_notes = await self.obsidian.list_notes()

        # Build edges from wikilinks
        for note_path in all_notes:
            note = await self.obsidian.get_note(note_path)
            if not note:
                continue

            # Add node
            graph.add_node(note_path)

            # Add edges for wikilinks
            wikilinks = note.metadata.get("wikilinks", [])
            for link in wikilinks:
                link_path = f"{link}.md"
                if link_path in all_notes:
                    graph.add_edge(note_path, link_path)

        self._graph_cache = graph

    async def get_graph_stats(self) -> Dict[str, any]:
        """
        Analyze knowledge graph structure

        Returns statistics useful for understanding vault
        """
        if self._graph_cache is None:
            await self._build_graph()

        graph = self._graph_cache
        if graph is None:
            # Return a safe default when graph is unavailable
            return {
                "total_notes": 0,
                "total_links": 0,
                "avg_out_degree": 0,
                "avg_in_degree": 0,
                "connected_components": 0,
            }

        total_nodes = graph.number_of_nodes()
        total_links = graph.number_of_edges()
        avg_out = (
            sum(graph.out_degree(n) for n in graph.nodes()) / total_nodes
            if total_nodes > 0
            else 0
        )
        avg_in = (
            sum(graph.in_degree(n) for n in graph.nodes()) / total_nodes
            if total_nodes > 0
            else 0
        )

        return {
            "total_notes": total_nodes,
            "total_links": total_links,
            "avg_out_degree": avg_out,
            "avg_in_degree": avg_in,
            "connected_components": nx.number_weakly_connected_components(graph),
        }

    async def get_hub_notes(self, top_k: int = 10) -> List[tuple[str, int]]:
        """
        Find hub notes (most connected)

        Useful for identifying central concepts in vault
        """
        if self._graph_cache is None:
            await self._build_graph()

        graph = self._graph_cache
        if graph is None:
            return []

        # Calculate total degree (in + out)
        degrees = {}
        for node in graph.nodes():
            degrees[node] = graph.in_degree(node) + graph.out_degree(node)

        # Sort by degree
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)

        return sorted_nodes[:top_k]

    async def find_related_notes(
        self, path: str, similarity_threshold: int = 2
    ) -> List[str]:
        """
        Find notes related to given note

        Uses: Common neighbors algorithm
        Notes that share many links are likely related
        """
        if self._graph_cache is None:
            await self._build_graph()

        graph = self._graph_cache
        # Defensive: ensure graph exists and the path is present
        if graph is None or path not in graph:
            return []

        # Get neighbors of target note
        target_neighbors = set(graph.successors(path)) | set(graph.predecessors(path))

        # Find notes with overlapping neighbors
        related = []
        for node in graph.nodes():
            if node == path:
                continue

            node_neighbors = set(graph.successors(node)) | set(graph.predecessors(node))

            # Calculate overlap
            common = target_neighbors & node_neighbors

            if len(common) >= similarity_threshold:
                related.append((node, len(common)))

        # Sort by number of common neighbors
        related.sort(key=lambda x: x[1], reverse=True)

        return [note for note, _ in related]
