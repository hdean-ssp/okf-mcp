"""Tests for sync module: change detection, incremental reindex, and full reindex."""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from okf_tools.config import OkfConfig
from okf_tools.search import VectorIndex
from okf_tools.sync import ChangeSet, SyncSummary, detect_changes, full_reindex, incremental_reindex


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_concept(bundle_root: Path, concept_id: str, body: str = "Body text.") -> Path:
    """Create a minimal concept .md file."""
    file_path = bundle_root / (concept_id + ".md")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"---\ntype: Pattern\ntitle: {concept_id.split('/')[-1]}\n---\n\n{body}\n"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _fake_embedding(*args, **kwargs):
    """Return a list of random 384-dim embeddings matching input length."""
    texts = args[0] if args else kwargs.get("texts", [])
    return [np.random.randn(384).astype(np.float32) for _ in texts]


@pytest.fixture
def bundle(tmp_path):
    """Create a minimal bundle directory with .okf structure."""
    okf_dir = tmp_path / ".okf"
    okf_dir.mkdir()
    (okf_dir / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "index.md").write_text("# Test\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def config(bundle):
    """Return an OkfConfig for the test bundle."""
    return OkfConfig(
        bundle_path=bundle,
        index_path=Path(".okf/index"),
        embedding_model="BAAI/bge-small-en-v1.5",
        default_top_n=5,
        similarity_threshold=0.85,
        auto_git_add=False,
    )


@pytest.fixture
def index(config):
    """Create a real VectorIndex at the config's index_db_path."""
    idx = VectorIndex(config.index_db_path)
    yield idx
    idx.close()


# ---------------------------------------------------------------------------
# detect_changes tests
# ---------------------------------------------------------------------------


class TestDetectChanges:
    def test_empty_bundle_empty_index(self, bundle, index):
        """No concepts on disk and none indexed = no changes."""
        changes = detect_changes(bundle, index)
        assert changes.added == []
        assert changes.modified == []
        assert changes.deleted == []

    def test_new_files_detected_as_added(self, bundle, index):
        """Files on disk but not in index are reported as added."""
        _create_concept(bundle, "alpha")
        _create_concept(bundle, "sub/beta")

        changes = detect_changes(bundle, index)
        added_paths = [str(p) for p in changes.added]
        assert len(changes.added) == 2
        assert any("alpha.md" in p for p in added_paths)
        assert any("beta.md" in p for p in added_paths)
        assert changes.modified == []
        assert changes.deleted == []

    def test_modified_files_detected(self, bundle, index):
        """Files with newer mtime than indexed are reported as modified."""
        path = _create_concept(bundle, "concept-a")
        # Index it with the current mtime
        emb = np.zeros(384, dtype=np.float32)
        old_mtime = path.stat().st_mtime
        index.upsert("concept-a", emb, {"title": "A", "type": "P", "tags": [], "mtime": old_mtime, "snippet": "", "body": ""})

        # Touch the file to advance mtime
        time.sleep(0.05)
        path.write_text(path.read_text() + "\nUpdated.", encoding="utf-8")

        changes = detect_changes(bundle, index)
        assert len(changes.modified) == 1
        assert "concept-a.md" in str(changes.modified[0])
        assert changes.added == []
        assert changes.deleted == []

    def test_unchanged_files_not_reported(self, bundle, index):
        """Files with same mtime as indexed produce no changes."""
        path = _create_concept(bundle, "stable")
        mtime = path.stat().st_mtime
        emb = np.zeros(384, dtype=np.float32)
        index.upsert("stable", emb, {"title": "S", "type": "P", "tags": [], "mtime": mtime, "snippet": "", "body": ""})

        changes = detect_changes(bundle, index)
        assert changes.added == []
        assert changes.modified == []
        assert changes.deleted == []

    def test_deleted_files_detected(self, bundle, index):
        """Concepts in the index but not on disk are reported as deleted."""
        emb = np.zeros(384, dtype=np.float32)
        index.upsert("gone-concept", emb, {"title": "G", "type": "P", "tags": [], "mtime": 1000.0, "snippet": "", "body": ""})

        changes = detect_changes(bundle, index)
        assert changes.deleted == ["gone-concept"]
        assert changes.added == []
        assert changes.modified == []

    def test_ignores_index_and_log_files(self, bundle, index):
        """index.md and log.md are not treated as concepts."""
        (bundle / "log.md").write_text("# Log\n", encoding="utf-8")
        # index.md already exists from fixture

        changes = detect_changes(bundle, index)
        assert changes.added == []

    def test_ignores_okf_sidecar_directory(self, bundle, index):
        """Files inside .okf/ are ignored."""
        sidecar_file = bundle / ".okf" / "notes.md"
        sidecar_file.write_text("---\ntype: X\n---\n\nInternal.\n", encoding="utf-8")

        changes = detect_changes(bundle, index)
        assert changes.added == []

    def test_mixed_changes(self, bundle, index):
        """Combination of added, modified, and deleted in one pass."""
        # Pre-index two concepts
        path_mod = _create_concept(bundle, "will-modify")
        emb = np.zeros(384, dtype=np.float32)
        index.upsert("will-modify", emb, {"title": "M", "type": "P", "tags": [], "mtime": path_mod.stat().st_mtime, "snippet": "", "body": ""})
        index.upsert("will-delete", emb, {"title": "D", "type": "P", "tags": [], "mtime": 1000.0, "snippet": "", "body": ""})

        # Add a new concept
        _create_concept(bundle, "new-one")

        # Modify the existing one
        time.sleep(0.05)
        path_mod.write_text(path_mod.read_text() + "\nChanged.", encoding="utf-8")

        changes = detect_changes(bundle, index)
        assert len(changes.added) == 1
        assert len(changes.modified) == 1
        assert changes.deleted == ["will-delete"]


# ---------------------------------------------------------------------------
# incremental_reindex tests
# ---------------------------------------------------------------------------


class TestIncrementalReindex:
    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_indexes_new_concepts(self, mock_embed, bundle, index, config):
        """New concepts are embedded and upserted."""
        _create_concept(bundle, "new-a", body="Alpha content")
        _create_concept(bundle, "new-b", body="Beta content")

        summary = incremental_reindex(bundle, index, config)
        assert summary.added == 2
        assert summary.updated == 0
        assert summary.removed == 0
        assert summary.total_indexed == 2

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_updates_modified_concepts(self, mock_embed, bundle, index, config):
        """Modified concepts are re-embedded."""
        path = _create_concept(bundle, "concept-x", body="Original")
        # First index
        incremental_reindex(bundle, index, config)
        assert index.concept_count() == 1

        # Modify
        time.sleep(0.05)
        path.write_text("---\ntype: Pattern\ntitle: concept-x\n---\n\nUpdated body.\n", encoding="utf-8")

        summary = incremental_reindex(bundle, index, config)
        assert summary.updated == 1
        assert summary.added == 0
        assert summary.total_indexed == 1

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_removes_deleted_concepts(self, mock_embed, bundle, index, config):
        """Deleted files are removed from the index."""
        path = _create_concept(bundle, "to-delete", body="Will be removed")
        incremental_reindex(bundle, index, config)
        assert index.concept_count() == 1

        # Delete the file
        path.unlink()

        summary = incremental_reindex(bundle, index, config)
        assert summary.removed == 1
        assert summary.total_indexed == 0

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_skips_unparseable_files(self, mock_embed, bundle, index, config):
        """Files without valid frontmatter are skipped."""
        # Valid concept
        _create_concept(bundle, "good", body="Valid content")
        # Invalid concept (no frontmatter)
        bad_path = bundle / "bad.md"
        bad_path.write_text("No frontmatter here, just plain text.", encoding="utf-8")

        summary = incremental_reindex(bundle, index, config)
        assert summary.added == 1
        assert len(summary.skipped) == 1
        assert "bad.md" in summary.skipped[0]

    @patch("okf_tools.sync.embed_batch", side_effect=Exception("Embedding service down"))
    def test_embedding_failure_skips_all(self, mock_embed, bundle, index, config):
        """When embed_batch raises, all concepts are added to skipped list."""
        _create_concept(bundle, "a", body="Content A")
        _create_concept(bundle, "b", body="Content B")

        summary = incremental_reindex(bundle, index, config)
        # Skipped list contains concept_ids for embedding failures
        assert len(summary.skipped) == 2
        assert "a" in summary.skipped
        assert "b" in summary.skipped
        # Nothing actually made it into the index
        assert summary.total_indexed == 0

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_sets_sync_timestamp(self, mock_embed, bundle, index, config):
        """After reindex, sync timestamp is persisted."""
        assert index.get_sync_timestamp() is None
        _create_concept(bundle, "ts-test")

        before = time.time()
        incremental_reindex(bundle, index, config)
        after = time.time()

        ts = index.get_sync_timestamp()
        assert ts is not None
        assert before <= ts <= after

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_model_compatibility_warning(self, mock_embed, bundle, index, config, capsys):
        """Warns to stderr when index model doesn't match config."""
        # Store a different model name in the index
        index.set_model_info("some-other-model", 384)
        _create_concept(bundle, "compat-test")

        incremental_reindex(bundle, index, config)

        captured = capsys.readouterr()
        assert "warning" in captured.err.lower()
        assert "some-other-model" in captured.err

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_no_changes_is_noop(self, mock_embed, bundle, index, config):
        """When nothing changed, summary shows zeros."""
        summary = incremental_reindex(bundle, index, config)
        assert summary.added == 0
        assert summary.updated == 0
        assert summary.removed == 0
        assert summary.total_indexed == 0
        # embed_batch should not be called
        mock_embed.assert_not_called()


# ---------------------------------------------------------------------------
# full_reindex tests
# ---------------------------------------------------------------------------


class TestFullReindex:
    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_indexes_all_concepts(self, mock_embed, bundle, index, config):
        """Full reindex processes all concept files."""
        _create_concept(bundle, "one", body="First")
        _create_concept(bundle, "two", body="Second")
        _create_concept(bundle, "sub/three", body="Third")

        summary = full_reindex(bundle, index, config)
        assert summary.added == 3
        assert summary.total_indexed == 3

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_clears_existing_index(self, mock_embed, bundle, index, config):
        """Full reindex drops all existing data before rebuilding."""
        # Pre-populate index with a concept that doesn't exist on disk
        emb = np.zeros(384, dtype=np.float32)
        index.upsert("ghost", emb, {"title": "Ghost", "type": "P", "tags": [], "mtime": 1.0, "snippet": "", "body": ""})
        assert index.concept_count() == 1

        # Create one real concept
        _create_concept(bundle, "real", body="Exists on disk")

        summary = full_reindex(bundle, index, config)
        # Only the real concept should remain
        assert summary.total_indexed == 1
        assert index.get_metadata("ghost") is None
        assert index.get_metadata("real") is not None

    @patch("okf_tools.sync.embed_batch", side_effect=Exception("Model unavailable"))
    def test_embedding_failure_skips_all(self, mock_embed, bundle, index, config):
        """When embed_batch raises, all concepts are skipped."""
        _create_concept(bundle, "a")
        _create_concept(bundle, "b")

        summary = full_reindex(bundle, index, config)
        assert summary.added == 0
        assert len(summary.skipped) == 2
        assert summary.total_indexed == 0

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_sets_model_info(self, mock_embed, bundle, index, config):
        """Full reindex persists the model name and dimensions."""
        _create_concept(bundle, "x")
        full_reindex(bundle, index, config)

        model, dims = index.get_model_info()
        assert model == config.embedding_model
        assert dims == 384

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_sets_sync_timestamp(self, mock_embed, bundle, index, config):
        """Full reindex sets the sync timestamp."""
        _create_concept(bundle, "ts")

        before = time.time()
        full_reindex(bundle, index, config)
        after = time.time()

        ts = index.get_sync_timestamp()
        assert before <= ts <= after

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_empty_bundle_produces_empty_index(self, mock_embed, bundle, index, config):
        """Full reindex of a bundle with no concepts produces an empty index."""
        summary = full_reindex(bundle, index, config)
        assert summary.added == 0
        assert summary.total_indexed == 0

    @patch("okf_tools.sync.embed_batch", side_effect=_fake_embedding)
    def test_ignores_reserved_files(self, mock_embed, bundle, index, config):
        """index.md and log.md are not indexed."""
        _create_concept(bundle, "real")
        (bundle / "log.md").write_text("# Log\n", encoding="utf-8")

        summary = full_reindex(bundle, index, config)
        assert summary.added == 1
        assert summary.total_indexed == 1
