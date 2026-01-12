import pytest

from src.infrastructure.graph_navigator import GraphNavigator
from src.infrastructure.mcp_interface import MCPDocument
from src.infrastructure.obsidian_mcp_client import LocalObsidianReader


def _create_sample_vault(tmp_path):
    """
    Vault structure used across tests:

    a.md: links to b and c
    b.md: links to c and d
    c.md: no links
    d.md: links to a (backlink to a)
    """
    files = {
        "a.md": "# A\n\nThis is A\n\n[[b]]\n[[c]]\n",
        "b.md": "# B\n\nThis is B\n\n[[c]]\n[[d]]\n",
        "c.md": "# C\n\nContent of C\n",
        "d.md": "# D\n\nLinks back to A\n\n[[a]]\n",
    }

    for name, content in files.items():
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")

    return tmp_path


@pytest.mark.asyncio
async def test_graph_building_and_basic_queries(tmp_path):
    vault = _create_sample_vault(tmp_path)

    obsidian = LocalObsidianReader(str(vault))
    navigator = GraphNavigator(obsidian)

    # Linked notes from 'a.md' should be b.md and c.md
    linked = await navigator.get_linked_notes("a.md")
    assert set(linked) == {"b.md", "c.md"}

    # Backlinks for c.md should include a.md and b.md
    backlinks = await navigator.get_backlinks("c.md")
    assert set(backlinks) == {"a.md", "b.md"}

    # Graph stats
    stats = await navigator.get_graph_stats()
    assert stats["total_notes"] == 4
    assert stats["total_links"] == 5
    # Average in/out degree should equal 5/4 == 1.25
    assert stats["avg_out_degree"] == pytest.approx(1.25)
    assert stats["avg_in_degree"] == pytest.approx(1.25)
    assert stats["connected_components"] == 1


@pytest.mark.asyncio
async def test_expand_context_and_find_path(tmp_path):
    vault = _create_sample_vault(tmp_path)

    obsidian = LocalObsidianReader(str(vault))
    navigator = GraphNavigator(obsidian)

    # Expand context from a.md with depth=1
    expanded = await navigator.expand_context("a.md", depth=1)
    # Expect that a.md (score 1.0) is first, and the backlink d.md (0.9) is second
    paths = [doc.path for doc in expanded]
    scores = {doc.path: doc.score for doc in expanded}

    assert paths[0] == "a.md"
    assert scores["a.md"] == pytest.approx(1.0)
    assert "d.md" in paths
    assert scores["d.md"] == pytest.approx(0.9)

    # Ensure b and c are present with lower scores (0.5)
    assert "b.md" in paths and scores["b.md"] == pytest.approx(0.5)
    assert "c.md" in paths and scores["c.md"] == pytest.approx(0.5)

    # Find shortest path from a.md to d.md (should be a -> b -> d)
    path = await navigator.find_path("a.md", "d.md")
    assert path == ["a.md", "b.md", "d.md"]

    # No path from c.md to d.md (c has no outgoing edges)
    no_path = await navigator.find_path("c.md", "d.md")
    assert no_path is None


@pytest.mark.asyncio
async def test_get_hub_and_related_notes(tmp_path):
    vault = _create_sample_vault(tmp_path)

    obsidian = LocalObsidianReader(str(vault))
    navigator = GraphNavigator(obsidian)

    # Hubs: nodes with highest degree (in + out). Here a.md and b.md should be top with degree 3
    hubs = await navigator.get_hub_notes(top_k=2)
    assert len(hubs) == 2
    hub_nodes = {n for n, deg in hubs}
    assert hub_nodes == {"a.md", "b.md"}
    assert all(deg == 3 for _, deg in hubs)

    # Related notes: nodes sharing at least 2 neighbors with 'a.md' -> should be ['b.md']
    related = await navigator.find_related_notes("a.md", similarity_threshold=2)
    assert related == ["b.md"]


@pytest.mark.asyncio
async def test_get_linked_notes_missing_file(tmp_path):
    # Empty vault (no files)
    obsidian = LocalObsidianReader(str(tmp_path))
    navigator = GraphNavigator(obsidian)

    # Query for a non-existing note should return empty lists
    assert await navigator.get_linked_notes("nonexistent.md") == []
    assert await navigator.get_backlinks("nonexistent.md") == []
