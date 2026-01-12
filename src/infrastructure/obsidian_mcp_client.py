"""
Phase 2: Obsidian MCP Client Implementation
Infrastructure Layer - Concrete MCP implementation

Uses Obsidian Local REST API plugin
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from src.infrastructure.mcp_interface import IObsidianMCP, MCPDocument, MCPSearchQuery


class ObsidianMCPClient(IObsidianMCP):
    """
    Concrete implementation for Obsidian vault access

    Requirements:
    - Obsidian Local REST API plugin installed
    - API key configured

    Single Responsibility: Communicate with Obsidian REST API only
    """

    def __init__(self, api_key: str, host: str = "127.0.0.1", port: int = 27124):
        self.base_url = f"http://{host}:{port}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.wikilink_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
        self.tag_pattern = re.compile(r"#[\w/-]+")

    async def search(self, query: MCPSearchQuery) -> List[MCPDocument]:
        """Search using MCP search query"""
        return await self.search_vault(query.query)

    async def fetch(self, path: str) -> Optional[MCPDocument]:
        """Fetch specific document"""
        return await self.get_note(path)

    async def list_notes(self, path: str = "") -> List[str]:
        """List all notes in vault or directory"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/vault/{path}", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Return list of file paths
            return [f["path"] for f in data.get("files", [])]

    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Get specific note with full content"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/vault/{path}", headers=self.headers
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            content = response.text

            # Extract metadata
            metadata = {
                "path": path,
                "frontmatter": await self.get_frontmatter(path),
                "tags": self.extract_tags(content),
                "wikilinks": self.extract_wikilinks(content),
            }

            return MCPDocument(path=path, content=content, metadata=metadata)

    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Search vault using text query"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/search/simple/",
                headers=self.headers,
                json={"query": query},
            )
            response.raise_for_status()
            results = response.json()

            documents = []
            for result in results:
                doc = MCPDocument(
                    path=result.get("filename", ""),
                    content=result.get("content", ""),
                    metadata={
                        "matches": result.get("matches", []),
                        "score": result.get("score", 0),
                    },
                    score=result.get("score", 0),
                )
                documents.append(doc)

            return documents

    async def get_frontmatter(self, path: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from note"""
        note = await self.get_note(path)
        if not note:
            return {}

        # Extract YAML frontmatter between --- markers
        content = note.content
        if not content.startswith("---"):
            return {}

        try:
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return {}

            yaml_content = content[3:end_idx].strip()

            # Simple YAML parser (for basic cases)
            # In production, use PyYAML
            metadata = {}
            for line in yaml_content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            return metadata
        except Exception:
            return {}

    async def get_tags(self, path: str) -> List[str]:
        """Extract tags from note"""
        note = await self.get_note(path)
        if not note:
            return []

        return self.extract_tags(note.content)

    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract [[wikilinks]] from content"""
        return self.wikilink_pattern.findall(content)

    def extract_tags(self, content: str) -> List[str]:
        """Extract #tags from content"""
        return self.tag_pattern.findall(content)


class LocalObsidianReader(IObsidianMCP):
    """
    Alternative: Direct file system access (no REST API needed)
    Faster for local development

    Use when: You don't have REST API plugin
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path not found: {vault_path}")

        self.wikilink_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
        self.tag_pattern = re.compile(r"#[\w/-]+")

    async def search(self, query: MCPSearchQuery) -> List[MCPDocument]:
        """Simple text search through files"""
        return await self.search_vault(query.query)

    async def fetch(self, path: str) -> Optional[MCPDocument]:
        """Fetch by reading file"""
        return await self.get_note(path)

    async def list_notes(self, path: str = "") -> List[str]:
        """List markdown files recursively"""
        search_path = self.vault_path / path
        md_files = list(search_path.rglob("*.md"))

        # Return paths relative to vault root
        return [str(f.relative_to(self.vault_path)) for f in md_files]

    async def get_note(self, path: str) -> Optional[MCPDocument]:
        """Read note from file system"""
        file_path = self.vault_path / path

        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")

        metadata = {
            "path": path,
            "frontmatter": await self.get_frontmatter(path),
            "tags": self.extract_tags(content),
            "wikilinks": self.extract_wikilinks(content),
        }

        return MCPDocument(path=path, content=content, metadata=metadata)

    async def search_vault(self, query: str) -> List[MCPDocument]:
        """Simple grep-like search"""
        all_notes = await self.list_notes()
        results = []

        for note_path in all_notes:
            note = await self.get_note(note_path)
            if note and query.lower() in note.content.lower():
                # Simple relevance score based on matches
                count = note.content.lower().count(query.lower())
                note.score = count / len(note.content.split())
                results.append(note)

        # Sort by relevance
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    async def get_frontmatter(self, path: str) -> Dict[str, Any]:
        """Extract frontmatter from file"""
        file_path = self.vault_path / path
        if not file_path.exists():
            return {}

        content = file_path.read_text(encoding="utf-8")

        if not content.startswith("---"):
            return {}

        try:
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return {}

            yaml_content = content[3:end_idx].strip()

            # Simple parser
            metadata = {}
            for line in yaml_content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            return metadata
        except Exception:
            return {}

    async def get_tags(self, path: str) -> List[str]:
        """Extract tags from note"""
        note = await self.get_note(path)
        if not note:
            return []
        return self.extract_tags(note.content)

    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract [[wikilinks]]"""
        return self.wikilink_pattern.findall(content)

    def extract_tags(self, content: str) -> List[str]:
        """Extract #tags"""
        return self.tag_pattern.findall(content)
