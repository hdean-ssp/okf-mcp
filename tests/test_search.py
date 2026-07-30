"""Tests for the search module: vector index, FTS, and hybrid search."""

import numpy as np
import pytest

from okf_tools.search import VectorIndex


@pytest.fixture
def index(tmp_path):
    db_path = tmp_path / "test.db"
    idx = VectorIndex(db_path)
    yield idx
    idx.close()


def _random_embedding():
    """Generate a random 384-dim unit vector."""
    vec = np.random.randn(384).astype(np.float32)
    return vec / np.linalg.norm(vec)


def _upsert_concept(index, concept_id, title="Test", body="Some body text", type_val="Pattern"):
    """Helper to upsert a concept with random embedding."""
    emb = _random_embedding()
    metadata = {
        "title": title,
        "type": type_val,
        "tags": ["test"],
        "mtime": 1000.0,
        "snippet": body[:200],
        "body": body,
    }
    index.upsert(concept_id, emb, metadata)
    return emb


class TestVectorIndexBasics:
    def test_create_and_count(self, index):
        assert index.concept_count() == 0
        _upsert_concept(index, "a")
        assert index.concept_count() == 1

    def test_upsert_and_delete(self, index):
        _upsert_concept(index, "a")
        _upsert_concept(index, "b")
        assert index.concept_count() == 2

        index.delete("a")
        assert index.concept_count() == 1
        assert index.get_metadata("a") is None
        assert index.get_metadata("b") is not None

    def test_get_metadata(self, index):
        _upsert_concept(index, "x", title="X Title", type_val="Decision")
        meta = index.get_metadata("x")
        assert meta["title"] == "X Title"
        assert meta["type"] == "Decision"

    def test_get_all_concept_ids(self, index):
        _upsert_concept(index, "a")
        _upsert_concept(index, "b")
        assert index.get_all_concept_ids() == {"a", "b"}

    def test_sync_timestamp(self, index):
        assert index.get_sync_timestamp() is None
        index.set_sync_timestamp(12345.0)
        assert index.get_sync_timestamp() == 12345.0

    def test_integrity_check(self, index):
        assert index.check_integrity() is True

    def test_upsert_replaces(self, index):
        _upsert_concept(index, "a", title="Old")
        _upsert_concept(index, "a", title="New")
        assert index.concept_count() == 1
        assert index.get_metadata("a")["title"] == "New"


class TestSemanticSearch:
    def test_finds_similar(self, index):
        emb = _upsert_concept(index, "target", title="Target")
        # Search with the same embedding — should find it with high score
        results = index.search_semantic(emb, top_n=5, threshold=0.0)
        assert len(results) >= 1
        assert results[0].concept_id == "target"
        assert results[0].score > 0.9

    def test_threshold_filters(self, index):
        emb = _upsert_concept(index, "a")
        _upsert_concept(index, "b")
        # Search with a's embedding but very high threshold
        results = index.search_semantic(emb, top_n=5, threshold=0.99)
        # Only 'a' should match (exact same embedding)
        ids = [r.concept_id for r in results]
        assert "a" in ids

    def test_top_n_limits(self, index):
        for i in range(10):
            _upsert_concept(index, f"c{i}")
        emb = _random_embedding()
        results = index.search_semantic(emb, top_n=3, threshold=0.0)
        assert len(results) <= 3


class TestKeywordSearch:
    def test_finds_by_keyword(self, index):
        _upsert_concept(
            index, "retry", title="Retry Pattern", body="Use exponential backoff for retries"
        )
        _upsert_concept(index, "cache", title="Cache Strategy", body="Use Redis for caching")

        results = index.search_keyword("retry backoff", top_n=5)
        assert len(results) >= 1
        assert results[0].concept_id == "retry"

    def test_no_results_for_unmatched(self, index):
        _upsert_concept(index, "a", body="Something about databases")
        results = index.search_keyword("xyzzyplugh", top_n=5)
        assert len(results) == 0

    def test_searches_title_and_body(self, index):
        _upsert_concept(index, "a", title="Circuit Breaker", body="Prevents cascading failures")
        # Search by title term
        results = index.search_keyword("circuit", top_n=5)
        assert len(results) >= 1
        assert results[0].concept_id == "a"
        # Search by body term
        results = index.search_keyword("cascading", top_n=5)
        assert len(results) >= 1
        assert results[0].concept_id == "a"

    def test_top_n_limits(self, index):
        for i in range(10):
            _upsert_concept(index, f"c{i}", body=f"common keyword repeated c{i}")
        results = index.search_keyword("common keyword", top_n=3)
        assert len(results) <= 3


class TestHybridSearch:
    def test_combines_both_sources(self, index):
        # Concept with a keyword match
        emb_kw = _upsert_concept(
            index, "keyword-match", title="Retry", body="retry with backoff pattern"
        )
        # Concept that's semantically similar (same embedding reused)
        emb_sem = _upsert_concept(
            index, "semantic-match", title="Resilience", body="handle transient failures gracefully"
        )

        # Hybrid search should find at least one result
        query_emb = emb_kw  # Use the retry embedding as query
        results = index.search_hybrid("retry", query_emb, top_n=5, threshold=0.0)
        ids = [r.concept_id for r in results]
        # The keyword match should definitely be found
        assert "keyword-match" in ids

    def test_unified_search_interface(self, index):
        emb = _upsert_concept(index, "a", body="test content here")

        # All modes should work through the unified interface
        results = index.search(emb, top_n=5, threshold=0.0, query="test", mode="hybrid")
        assert isinstance(results, list)

        results = index.search(emb, top_n=5, threshold=0.0, query="", mode="semantic")
        assert isinstance(results, list)

        results = index.search(emb, top_n=5, threshold=0.0, query="test", mode="keyword")
        assert isinstance(results, list)

    def test_keyword_mode_without_embedding(self, index):
        _upsert_concept(index, "a", body="findable content")
        # In keyword mode, embedding is ignored
        dummy_emb = _random_embedding()
        results = index.search(dummy_emb, top_n=5, threshold=0.0, query="findable", mode="keyword")
        assert len(results) >= 1


class TestFTSUpsertDelete:
    def test_delete_removes_from_fts(self, index):
        _upsert_concept(index, "a", body="unique searchable term")
        results = index.search_keyword("searchable", top_n=5)
        assert len(results) == 1

        index.delete("a")
        results = index.search_keyword("searchable", top_n=5)
        assert len(results) == 0

    def test_upsert_updates_fts(self, index):
        _upsert_concept(index, "a", body="old content")
        _upsert_concept(index, "a", body="new updated text")

        results = index.search_keyword("old content", top_n=5)
        assert len(results) == 0

        results = index.search_keyword("new updated", top_n=5)
        assert len(results) == 1


class TestThreadSafety:
    """Regression tests: the MCP server reuses a cached VectorIndex across
    asyncio.to_thread worker threads. Connections must tolerate cross-thread use
    (check_same_thread=False), and a failed write must not leave a dangling
    transaction that poisons later operations.
    """

    def test_cross_thread_write_and_read(self, index):
        """A VectorIndex created on one thread must be usable from another.

        Before the fix (check_same_thread=True) this raised
        sqlite3.ProgrammingError and the cached index stayed broken until restart.
        """
        import threading

        errors: list = []

        def worker():
            try:
                _upsert_concept(index, "cross-thread", body="written from another thread")
                assert index.concept_count() == 1
                results = index.search_keyword("another thread", top_n=5)
                assert any(r.concept_id == "cross-thread" for r in results)
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert not errors, f"cross-thread use raised: {errors}"

    def test_failed_write_rolls_back(self, index):
        """A write that raises mid-transaction must roll back, leaving the
        connection usable for the next operation."""
        import sqlite3

        def failing() -> None:
            # Start writing, then fail before commit.
            index._write_conn.execute(
                "INSERT OR REPLACE INTO concepts (concept_id, title) VALUES (?, ?)",
                ("partial", "should be rolled back"),
            )
            raise sqlite3.IntegrityError("simulated mid-write failure")

        with pytest.raises(sqlite3.IntegrityError):
            index._write_op("failing", failing)

        # The partial row must have been rolled back...
        assert index.get_metadata("partial") is None
        # ...and the connection must still work for subsequent writes.
        _upsert_concept(index, "after-failure", body="works after rollback")
        assert index.get_metadata("after-failure") is not None
