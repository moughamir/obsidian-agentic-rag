"""
Phase 2: Knowledge Graph Navigator
Infrastructure Layer - GraphRAG implementation

Navigates Obsidian knowledge graph via wikilinks
Expands context by following connections
"""

from typing import Any, Dict, List, Optional, Set

# Optional networkx import: provide a small fallback implementation when networkx is not installed.
try:
    import networkx as nx  # type: ignore

    NX_AVAILABLE = True
except Exception:
    NX_AVAILABLE = False

    class SimpleDiGraph:
        """Minimal directed graph fallback used when networkx is unavailable."""

        def __init__(self):
            self._succ = {}
            self._pred = {}

        def add_node(self, n):
            self._succ.setdefault(n, {})
            self._pred.setdefault(n, {})

        def add_edge(self, u, v):
            self.add_node(u)
            self.add_node(v)
            self._succ[u].setdefault(v, True)
            self._pred[v].setdefault(u, True)

        def predecessors(self, n):
            return list(self._pred.get(n, {}).keys())

        def successors(self, n):
            return list(self._succ.get(n, {}).keys())

        def number_of_nodes(self):
            return len(self._succ)

        def number_of_edges(self):
            return sum(len(s) for s in self._succ.values())

        def in_degree(self, n):
            return len(self._pred.get(n, {}))

        def out_degree(self, n):
            return len(self._succ.get(n, {}))

        def nodes(self):
            return list(self._succ.keys())

        def __contains__(self, n):
            return n in self._succ

    def shortest_path(graph, source, target):
        """Simple BFS-based shortest path."""
        if source == target:
            return [source]
        from collections import deque

        q = deque([source])
        prev = {source: None}
        while q:
            cur = q.popleft()
            for neigh in graph.successors(cur):
                if neigh not in prev:
                    prev[neigh] = cur
                    if neigh == target:
                        path = [target]
                        while prev[path[-1]] is not None:
                            path.append(prev[path[-1]])
                        return path[::-1]
                    q.append(neigh)
        raise Exception("No path")

    def number_weakly_connected_components(graph):
        """Compute weakly connected components count treating graph as undirected."""
        visited = set()
        comps = 0
        for n in graph.nodes():
            if n not in visited:
                comps += 1
                stack = [n]
                while stack:
                    cur = stack.pop()
                    if cur in visited:
                        continue
                    visited.add(cur)
                    neighbors = set(graph.successors(cur)) | set(
                        graph.predecessors(cur)
                    )
                    for nb in neighbors:
                        if nb not in visited:
                            stack.append(nb)
        return comps

    import types

    nx = types.SimpleNamespace(
        DiGraph=SimpleDiGraph,
        shortest_path=shortest_path,
        number_weakly_connected_components=number_weakly_connected_components,
    )

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
        # Use Any here so the code can operate with either real networkx graphs or the fallback graph.
        self._graph_cache: Optional[Any] = None

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
            # graph is now guaranteed to be non-None
            path = nx.shortest_path(graph, start, end)
            return path
        except Exception:
            # NetworkX raises specific exceptions (NodeNotFound, NetworkXNoPath).
            # Our fallback raises a generic Exception when no path exists, so catch broadly.
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
