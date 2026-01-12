"""
Phase 2: Obsidian MCP Client
Infrastructure Layer - Concrete implementation for Obsidian access

Two implementations provided:
1. LocalObsidianReader: Direct file system access (recommended for simplicity)
2. ObsidianMCPClient: Uses Obsidian Local REST API plugin (more features)
"""

from typing import List, Optional
import os
import re
import httpx
from src.infrastructure.mcp_interface import IObsidianMCP, MCPDocument


class LocalObsidianReader(IObsidianMCP):
    """
    Read Obsidian vault from local file system

    Advantages:
    - No Obsidian plugin required
    - Fast and simple
    - Works with any Obsidian vault structure
    """

    def __init__(self, vault_path: str):
        if not os.path.isdir(vault_path):
            raise ValueError(f"Vault path not found: {vault_path}")
        self.vault_path = vault_path

    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Read a single note from file"""
        full_path = os.path.join(self.vault_path, path)

        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic metadata extraction
            metadata = self._extract_metadata(content)

            return MCPDocument(
                path=path,
                content=content,
                metadata=metadata
            )
        except Exception:
            return None

    async def list_notes(self) -> List[str]:
        """List all markdown files in vault"""
        markdown_files = []
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    # Get relative path
                    rel_path = os.path.relpath(
                        os.path.join(root, file),
                        self.vault_path
                    )
                    markdown_files.append(rel_path)
        return markdown_files

    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Simple keyword search (grep-like)"""
        results = []
        all_notes = await self.list_notes()
        query_lower = query.lower()

        for note_path in all_notes:
            note = await self.get_note(note_path)
            if note and query_lower in note.content.lower():
                # Score based on keyword frequency
                score = note.content.lower().count(query_lower)
                note.score = score
                results.append(note)

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _extract_metadata(self, content: str) -> dict:
        """
        Extract metadata from note content
        - Tags: #tag
        - Wikilinks: [[link]]
        - Frontmatter (basic)
        """
        metadata = {}

        # Extract tags
        metadata["tags"] = re.findall(r'#(\w+)', content)

        # Extract wikilinks, handling aliases
        metadata["wikilinks"] = [link.split('|')[0] for link in re.findall(r'\[\[(.*?)\]\]', content)]

        # Extract frontmatter
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Simple YAML-like parsing
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

        return metadata


class ObsidianMCPClient(IObsidianMCP):
    """
    MCP client for Obsidian via Local REST API

    Requires: Obsidian Local REST API plugin
    https://github.com/coddingtonbear/obsidian-local-rest-api
    """

    def __init__(
        self,
        api_key: str,
        host: str = "127.0.0.1",
        port: int = 27124
    ):
        self.base_url = f"http://{host}:{port}"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient()

    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Fetch a note via API"""
        try:
            response = await self.client.get(
                f"{self.base_url}/vault/{path}",
                headers=self.headers
            )
            response.raise_for_status()

            content = response.text
            metadata = self._extract_metadata(content)

            return MCPDocument(
                path=path,
                content=content,
                metadata=metadata
            )
        except httpx.HTTPError:
            return None

    async def list_notes(self) -> List[str]:
        """List notes via API"""
        # API doesn't have a direct list endpoint, so use search
        # This is a limitation of the plugin
        results = await self.search_vault("")
        return [doc.path for doc in results]

    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Search vault via API"""
        # Implementation depends on the API's search capabilities
        # This is a placeholder for a more complete implementation
        return []

    def _extract_metadata(self, content: str) -> dict:
        """Leverage API for metadata if possible, else parse"""
        # For now, reuse local parser
        return LocalObsidianReader("")._extract_metadata(content)
