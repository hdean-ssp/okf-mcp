"""Tests for move_concept: service layer and MCP server handler."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from okf_tools.bundle import parse_concept
from okf_tools.config import OkfConfig
from okf_tools.errors import ConceptNotFoundError, ValidationError
from okf_tools.server import _state as server_state
from okf_tools.server import move_concept as _mcp_move_async
from okf_tools.service import move_concept


def mcp_move_concept(**kw):
    return asyncio.run(_mcp_move_async(**kw))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bundle(tmp_path):
    """Create a minimal OKF bundle."""
    okf_dir = tmp_path / ".okf"
    okf_dir.mkdir()
    (okf_dir / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "index.md").write_text("# Test\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def config(bundle):
    """OkfConfig for the test bundle."""
    return OkfConfig(
        bundle_path=bundle,
        index_path=Path(".okf/index"),
        embedding_model="BAAI/bge-small-en-v1.5",
        default_top_n=5,
        similarity_threshold=0.85,
        auto_git_add=False,
    )


@pytest.fixture(autouse=True)
def mock_embeddings():
    """Mock embedding calls to avoid downloading models."""
    with (
        patch("okf_tools.service.embed_text") as mock_embed,
        patch("okf_tools.service.VectorIndex") as mock_index_cls,
    ):
        mock_embed.return_value = [0.1] * 384
        mock_index = mock_index_cls.return_value
        mock_index.search.return_value = []
        mock_index.get_sync_timestamp.return_value = None
        mock_index.concept_count.return_value = 0
        mock_index.close.return_value = None
        mock_index.upsert.return_value = None
        mock_index.delete.return_value = None
        yield {"embed_text": mock_embed, "VectorIndex": mock_index_cls, "index": mock_index}


def _create_concept(
    bundle: Path, concept_id: str, title: str = "Test", body: str = "Body."
) -> Path:
    """Write a concept file directly to disk."""
    file_path = bundle / (concept_id + ".md")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"---\ntype: Pattern\ntitle: {title}\ntags:\n- test\n---\n\n{body}\n"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------------


class TestMoveConceptService:
    """Tests for service.move_concept."""

    def test_basic_rename(self, bundle, config):
        """Rename a concept within the same directory."""
        _create_concept(bundle, "old-name", title="Old Name")

        result = move_concept(config, "old-name", "new-name")
        assert result == "new-name"

        # Old file gone, new file exists
        assert not (bundle / "old-name.md").exists()
        assert (bundle / "new-name.md").exists()

    def test_move_to_subdirectory(self, bundle, config):
        """Move a concept from root to a subdirectory."""
        _create_concept(bundle, "draft", title="Draft Idea")

        result = move_concept(config, "draft", "published/idea")
        assert result == "published/idea"

        assert not (bundle / "draft.md").exists()
        assert (bundle / "published" / "idea.md").exists()

    def test_move_between_subdirectories(self, bundle, config):
        """Move a concept from one subdirectory to another."""
        _create_concept(bundle, "drafts/scratch", title="Scratch")

        result = move_concept(config, "drafts/scratch", "guides/setup")
        assert result == "guides/setup"

        assert not (bundle / "drafts" / "scratch.md").exists()
        assert (bundle / "guides" / "setup.md").exists()

    def test_move_with_title_update(self, bundle, config):
        """Move and update the title simultaneously."""
        _create_concept(bundle, "tmp/raw", title="Raw Notes")

        result = move_concept(config, "tmp/raw", "docs/polished", new_title="Polished Guide")
        assert result == "docs/polished"

        # Verify title was updated in the file
        concept = parse_concept(bundle / "docs" / "polished.md", bundle)
        assert concept.title == "Polished Guide"

    def test_preserves_content_and_metadata(self, bundle, config):
        """Move preserves the body content and all frontmatter fields."""
        _create_concept(bundle, "original", title="My Pattern", body="Important content here.")

        move_concept(config, "original", "moved/pattern")

        concept = parse_concept(bundle / "moved" / "pattern.md", bundle)
        assert concept.title == "My Pattern"
        assert concept.type == "Pattern"
        assert concept.tags == ["test"]
        assert "Important content here." in concept.body

    def test_source_not_found_raises_error(self, bundle, config):
        """Moving a nonexistent concept raises ConceptNotFoundError."""
        with pytest.raises(ConceptNotFoundError):
            move_concept(config, "nonexistent", "somewhere/else")

    def test_destination_already_exists_raises_error(self, bundle, config):
        """Moving to a path that already has a concept raises ValidationError."""
        _create_concept(bundle, "source", title="Source")
        _create_concept(bundle, "target", title="Target")

        with pytest.raises(ValidationError) as exc_info:
            move_concept(config, "source", "target")
        assert "already exists" in str(exc_info.value).lower()

    def test_same_id_raises_error(self, bundle, config):
        """Moving a concept to the same ID raises ValidationError."""
        _create_concept(bundle, "same", title="Same")

        with pytest.raises(ValidationError) as exc_info:
            move_concept(config, "same", "same")
        assert "same as the current" in str(exc_info.value).lower()

    def test_empty_new_id_raises_error(self, bundle, config):
        """Empty new_concept_id raises ValidationError."""
        _create_concept(bundle, "something", title="Something")

        with pytest.raises(ValidationError):
            move_concept(config, "something", "")

    def test_whitespace_only_new_id_raises_error(self, bundle, config):
        """Whitespace-only new_concept_id raises ValidationError."""
        _create_concept(bundle, "something", title="Something")

        with pytest.raises(ValidationError):
            move_concept(config, "something", "   ")

    def test_slashes_only_new_id_raises_error(self, bundle, config):
        """Slashes-only new_concept_id raises ValidationError after stripping."""
        _create_concept(bundle, "something", title="Something")

        with pytest.raises(ValidationError):
            move_concept(config, "something", "///")

    def test_strips_leading_trailing_slashes(self, bundle, config):
        """Leading/trailing slashes are stripped from new_concept_id."""
        _create_concept(bundle, "source", title="Source")

        result = move_concept(config, "source", "/dest/path/")
        assert result == "dest/path"
        assert (bundle / "dest" / "path.md").exists()

    def test_path_traversal_blocked(self, bundle, config):
        """Attempting to move outside the bundle raises ValidationError."""
        _create_concept(bundle, "legit", title="Legit")

        with pytest.raises(ValidationError) as exc_info:
            move_concept(config, "legit", "../../outside")
        assert "outside the bundle" in str(exc_info.value).lower()

    def test_creates_destination_directory(self, bundle, config):
        """Move creates intermediate directories as needed."""
        _create_concept(bundle, "flat", title="Flat")

        move_concept(config, "flat", "deep/nested/dir/concept")
        assert (bundle / "deep" / "nested" / "dir" / "concept.md").exists()

    def test_updates_index_in_source_directory(self, bundle, config):
        """Move removes the entry from the source directory's index.md."""
        # Create concept and its index entry
        _create_concept(bundle, "notes/item", title="Item")
        notes_index = bundle / "notes" / "index.md"
        notes_index.write_text("# Notes\n\n- [Item](./item.md)\n", encoding="utf-8")

        move_concept(config, "notes/item", "archive/item")

        content = notes_index.read_text(encoding="utf-8")
        assert "item.md" not in content

    def test_updates_index_in_destination_directory(self, bundle, config):
        """Move adds an entry to the destination directory's index.md."""
        _create_concept(bundle, "source-concept", title="My Concept")

        move_concept(config, "source-concept", "dest/my-concept")

        dest_index = bundle / "dest" / "index.md"
        assert dest_index.exists()
        content = dest_index.read_text(encoding="utf-8")
        assert "My Concept" in content
        assert "my-concept.md" in content

    def test_title_from_concept_id_when_no_title(self, bundle, config):
        """When concept has no title, index uses last segment of concept_id."""
        # Create concept without a title field
        file_path = bundle / "no-title.md"
        file_path.write_text("---\ntype: Note\n---\n\nNo title here.\n", encoding="utf-8")

        move_concept(config, "no-title", "dest/renamed")

        dest_index = bundle / "dest" / "index.md"
        content = dest_index.read_text(encoding="utf-8")
        assert "renamed" in content


# ---------------------------------------------------------------------------
# MCP server handler tests
# ---------------------------------------------------------------------------


class TestMoveConceptMCP:
    """Tests for the MCP server move_concept tool handler."""

    def test_successful_move_returns_json(self, config):
        """MCP move_concept returns old and new concept_ids as JSON."""
        _create_concept(config.bundle_path, "mcp-source", title="MCP Source")

        with patch.object(server_state, "config", config):
            result = mcp_move_concept(concept_id="mcp-source", new_concept_id="mcp-dest")
            data = json.loads(result)
            assert data["old_concept_id"] == "mcp-source"
            assert data["new_concept_id"] == "mcp-dest"

    def test_move_with_title(self, config):
        """MCP move_concept passes new_title through."""
        _create_concept(config.bundle_path, "titled", title="Old Title")

        with patch.object(server_state, "config", config):
            result = mcp_move_concept(
                concept_id="titled", new_concept_id="renamed", new_title="New Title"
            )
            data = json.loads(result)
            assert data["new_concept_id"] == "renamed"

        # Verify title on disk
        concept = parse_concept(config.bundle_path / "renamed.md", config.bundle_path)
        assert concept.title == "New Title"

    def test_source_not_found_raises_tool_error(self, config):
        """MCP move_concept raises ToolError for missing source."""
        with patch.object(server_state, "config", config):
            with pytest.raises(ToolError) as exc_info:
                mcp_move_concept(concept_id="ghost", new_concept_id="dest")
            assert "not found" in str(exc_info.value).lower()

    def test_destination_exists_raises_tool_error(self, config):
        """MCP move_concept raises ToolError when destination exists."""
        _create_concept(config.bundle_path, "src", title="Src")
        _create_concept(config.bundle_path, "dst", title="Dst")

        with patch.object(server_state, "config", config):
            with pytest.raises(ToolError) as exc_info:
                mcp_move_concept(concept_id="src", new_concept_id="dst")
            assert "already exists" in str(exc_info.value).lower()

    def test_same_id_raises_tool_error(self, config):
        """MCP move_concept raises ToolError for no-op move."""
        _create_concept(config.bundle_path, "noop", title="NoOp")

        with patch.object(server_state, "config", config):
            with pytest.raises(ToolError) as exc_info:
                mcp_move_concept(concept_id="noop", new_concept_id="noop")
            assert "same" in str(exc_info.value).lower()

    def test_no_bundle_raises_tool_error(self):
        """MCP move_concept raises ToolError when no bundle configured."""
        with patch.object(server_state, "config", None):
            with pytest.raises(ToolError) as exc_info:
                mcp_move_concept(concept_id="x", new_concept_id="y")
            assert "no bundle configured" in str(exc_info.value).lower()

    def test_path_traversal_raises_tool_error(self, config):
        """MCP move_concept raises ToolError for path traversal attempts."""
        _create_concept(config.bundle_path, "real", title="Real")

        with patch.object(server_state, "config", config):
            with pytest.raises(ToolError) as exc_info:
                mcp_move_concept(concept_id="real", new_concept_id="../../etc/evil")
            assert "outside the bundle" in str(exc_info.value).lower()
