"""Vector index: embed, store, and query concepts using fastembed + sqlite-vec."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class SearchResult:
    """A single search result from semantic query."""

    concept_id: str
    title: str | None
    score: float
    snippet: str
    bundle: str | None = None


# --- Embedding (lazy-loaded) ---

_embedder_cache: dict[str, Any] = {}


def get_embedder(model_name: str) -> Any:
    """Lazily initialize and cache the fastembed TextEmbedding model."""
    if model_name not in _embedder_cache:
        from fastembed import TextEmbedding

        _embedder_cache[model_name] = TextEmbedding(model_name=model_name)
    return _embedder_cache[model_name]


def embed_text(text: str, model_name: str) -> np.ndarray:
    """Embed a single text string. Returns 384-dim unit vector.

    Validates the result is finite and has non-zero norm. Raises ValueError
    if the embedding model produces a degenerate vector.
    """
    embedder = get_embedder(model_name)
    results = list(embedder.embed([text]))
    vec = np.array(results[0], dtype=np.float32)
    if not np.all(np.isfinite(vec)):
        raise ValueError(f"Embedding model returned non-finite values for input: {text[:80]!r}")
    norm = float(np.linalg.norm(vec))
    if norm < 1e-8:
        raise ValueError(f"Embedding model returned near-zero vector for input: {text[:80]!r}")
    return vec


def embed_batch(texts: list[str], model_name: str) -> list[np.ndarray]:
    """Batch embed for reindex efficiency."""
    if not texts:
        return []
    embedder = get_embedder(model_name)
    results = list(embedder.embed(texts))
    return [np.array(r, dtype=np.float32) for r in results]


# --- Vector Index ---


class VectorIndex:
    """Manages the sqlite-vec sidecar database with hybrid search (vector + BM25).

    Uses separate read and write connections to exploit WAL mode:
    - Write connection: serialized access for upsert/delete/clear operations
    - Read connection: concurrent access for searches and metadata queries

    WAL mode allows unlimited concurrent readers alongside one writer.
    busy_timeout gives the writer 5 seconds to acquire the lock before failing,
    which handles brief contention from reindex or concurrent MCP requests.
    """

    BUSY_TIMEOUT_MS = 5000

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Write connection — used for upsert, delete, clear, set_* operations
        self._write_conn = sqlite3.connect(str(db_path))
        self._write_conn.execute("PRAGMA journal_mode=WAL")
        self._write_conn.execute(f"PRAGMA busy_timeout={self.BUSY_TIMEOUT_MS}")
        self._load_extension(self._write_conn)
        self._create_tables()

        # Read connection — used for searches and metadata queries
        self._read_conn = sqlite3.connect(str(db_path), uri=False)
        self._read_conn.execute(f"PRAGMA busy_timeout={self.BUSY_TIMEOUT_MS}")
        self._load_extension(self._read_conn)

    def _load_extension(self, conn: sqlite3.Connection) -> None:
        """Load the sqlite-vec extension on a connection."""
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)

    def _create_tables(self) -> None:
        """Create required tables if they don't exist."""
        self._write_conn.executescript("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS concepts (
                concept_id TEXT PRIMARY KEY,
                title TEXT,
                type TEXT,
                tags TEXT,
                mtime REAL,
                snippet TEXT
            );
        """)
        # Vector virtual table
        self._write_conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_concepts USING vec0(
                concept_id TEXT PRIMARY KEY,
                embedding FLOAT[384]
            )
        """)
        # FTS5 full-text search table
        self._write_conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_concepts USING fts5(
                concept_id UNINDEXED,
                title,
                body,
                tokenize='porter unicode61'
            )
        """)
        self._write_conn.commit()

    def _write_op(self, operation: str, fn: Any) -> Any:
        """Execute a write operation, converting lock errors to IndexBusyError."""
        from .errors import IndexBusyError

        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                raise IndexBusyError(operation) from e
            raise

    def upsert(self, concept_id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        """Add or update a concept's embedding, metadata, and full-text index."""

        def _do_upsert() -> None:
            self._write_conn.execute(
                """INSERT OR REPLACE INTO concepts
                   (concept_id, title, type, tags, mtime, snippet)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    concept_id,
                    metadata.get("title"),
                    metadata.get("type"),
                    json.dumps(metadata.get("tags", [])),
                    metadata.get("mtime"),
                    metadata.get("snippet"),
                ),
            )
            self._write_conn.execute("DELETE FROM vec_concepts WHERE concept_id = ?", (concept_id,))
            self._write_conn.execute(
                "INSERT INTO vec_concepts (concept_id, embedding) VALUES (?, ?)",
                (concept_id, embedding.tobytes()),
            )
            self._write_conn.execute("DELETE FROM fts_concepts WHERE concept_id = ?", (concept_id,))
            self._write_conn.execute(
                "INSERT INTO fts_concepts (concept_id, title, body) VALUES (?, ?, ?)",
                (concept_id, metadata.get("title", ""), metadata.get("body", "")),
            )
            self._write_conn.commit()

        self._write_op("upsert", _do_upsert)

    def delete(self, concept_id: str) -> None:
        """Remove a concept from all index tables."""

        def _do_delete() -> None:
            self._write_conn.execute("DELETE FROM concepts WHERE concept_id = ?", (concept_id,))
            self._write_conn.execute("DELETE FROM vec_concepts WHERE concept_id = ?", (concept_id,))
            self._write_conn.execute("DELETE FROM fts_concepts WHERE concept_id = ?", (concept_id,))
            self._write_conn.commit()

        self._write_op("delete", _do_delete)

    # --- Search methods ---

    def search_semantic(
        self,
        query_embedding: np.ndarray,
        top_n: int,
        threshold: float,
        type_filter: str | None = None,
        tags_filter: list[str] | None = None,
    ) -> list[SearchResult]:
        """Pure vector cosine similarity search with optional metadata filters."""
        # sqlite-vec requires fetching by k, then we filter. Fetch extra to
        # account for filtered-out results.
        fetch_k = top_n * 3 if (type_filter or tags_filter) else top_n
        rows = self._read_conn.execute(
            """
            SELECT v.concept_id, v.distance, c.title, c.snippet, c.type, c.tags
            FROM vec_concepts v
            JOIN concepts c ON v.concept_id = c.concept_id
            WHERE v.embedding MATCH ?
                AND k = ?
            ORDER BY v.distance
            """,
            (query_embedding.tobytes(), fetch_k),
        ).fetchall()

        results = []
        for concept_id, distance, title, snippet, c_type, c_tags in rows:
            if type_filter and c_type != type_filter:
                continue
            if tags_filter:
                concept_tags = json.loads(c_tags) if c_tags else []
                if not set(concept_tags) & set(tags_filter):
                    continue
            # Guard against degenerate distances from sqlite-vec (None, NaN, Inf)
            if distance is None or not np.isfinite(distance):
                continue
            score = 1.0 - distance
            if score >= threshold:
                results.append(
                    SearchResult(
                        concept_id=concept_id,
                        title=title,
                        score=round(score, 4),
                        snippet=snippet or "",
                    )
                )
            if len(results) >= top_n:
                break
        return results

    @staticmethod
    def _escape_fts5_query(query: str) -> str:
        """Escape a query string for safe use in FTS5 MATCH.

        FTS5 interprets bare hyphens as column filters (e.g. 'multi-bundle'
        becomes column 'bundle' with term 'multi'). Wrapping each token in
        double quotes prevents this misinterpretation while preserving
        tokenization across multiple words.
        """
        # Split on whitespace, quote each token individually
        tokens = query.split()
        return " ".join(f'"{token}"' for token in tokens)

    def search_keyword(
        self,
        query: str,
        top_n: int,
        type_filter: str | None = None,
        tags_filter: list[str] | None = None,
    ) -> list[SearchResult]:
        """BM25 full-text keyword search via FTS5 with optional metadata filters."""
        safe_query = self._escape_fts5_query(query)

        # Build dynamic WHERE clause for metadata filters
        conditions = ["fts_concepts MATCH ?"]
        params: list = [safe_query]

        if type_filter:
            conditions.append("c.type = ?")
            params.append(type_filter)

        params.append(top_n)

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT f.concept_id, rank, c.title, c.snippet
            FROM fts_concepts f
            JOIN concepts c ON f.concept_id = c.concept_id
            WHERE {where_clause}
            ORDER BY rank
            LIMIT ?
        """
        rows = self._read_conn.execute(sql, params).fetchall()

        if not rows:
            return []

        # Apply tags filter in Python (JSON array in SQLite is awkward to query)
        if tags_filter:
            filtered_rows = []
            for row in rows:
                concept_id = row[0]
                meta = self.get_metadata(concept_id)
                if meta and set(meta.get("tags", [])) & set(tags_filter):
                    filtered_rows.append(row)
            rows = filtered_rows

        if not rows:
            return []

        # Normalize BM25 ranks to 0-1 (rank is negative, closer to 0 = better)
        raw_scores = [-row[1] for row in rows if row[1] is not None]
        if not raw_scores:
            return []
        max_score = max(raw_scores)
        max_score = max(max_score, 0.001)  # Avoid division by zero

        results = []
        for (concept_id, _rank, title, snippet), raw in zip(rows, raw_scores, strict=False):
            score = round(raw / max_score, 4)
            results.append(
                SearchResult(
                    concept_id=concept_id,
                    title=title,
                    score=score,
                    snippet=snippet or "",
                )
            )
        return results

    def search_hybrid(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_n: int,
        threshold: float,
        semantic_weight: float = 0.6,
        type_filter: str | None = None,
        tags_filter: list[str] | None = None,
    ) -> list[SearchResult]:
        """Hybrid search: merge BM25 keyword + vector semantic results.

        Fetches 2x top_n from each source, normalizes scores, and combines
        with weighted average (default 60% semantic, 40% keyword).
        Filters are applied at the SQL level in each sub-query.
        """
        fetch_n = top_n * 2

        # Get results from both engines with filters applied
        semantic_results = self.search_semantic(
            query_embedding,
            fetch_n,
            0.0,
            type_filter=type_filter,
            tags_filter=tags_filter,
        )
        keyword_results = self.search_keyword(
            query,
            fetch_n,
            type_filter=type_filter,
            tags_filter=tags_filter,
        )

        # Build score maps
        semantic_scores: dict[str, float] = {}
        keyword_scores: dict[str, float] = {}
        metadata: dict[str, SearchResult] = {}

        for r in semantic_results:
            semantic_scores[r.concept_id] = r.score
            metadata[r.concept_id] = r

        for r in keyword_results:
            keyword_scores[r.concept_id] = r.score
            if r.concept_id not in metadata:
                metadata[r.concept_id] = r

        # Combine scores for all candidates
        all_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        combined: list[tuple] = []

        keyword_weight = 1.0 - semantic_weight
        for cid in all_ids:
            s_score = semantic_scores.get(cid, 0.0)
            k_score = keyword_scores.get(cid, 0.0)
            final = (s_score * semantic_weight) + (k_score * keyword_weight)
            if final >= threshold:
                combined.append((cid, final))

        # Sort by combined score descending, take top_n
        combined.sort(key=lambda x: x[1], reverse=True)
        combined = combined[:top_n]

        return [
            SearchResult(
                concept_id=cid,
                title=metadata[cid].title,
                score=round(score, 4),
                snippet=metadata[cid].snippet,
            )
            for cid, score in combined
        ]

    def search(
        self,
        query_embedding: np.ndarray,
        top_n: int,
        threshold: float,
        query: str = "",
        mode: str = "hybrid",
        type_filter: str | None = None,
        tags_filter: list[str] | None = None,
    ) -> list[SearchResult]:
        """Unified search interface.

        Modes: 'hybrid' (default), 'semantic', 'keyword'.
        Filters are pushed into the SQL queries for efficient filtering.
        """
        if mode == "keyword":
            if not query:
                return []
            return self.search_keyword(
                query, top_n, type_filter=type_filter, tags_filter=tags_filter
            )
        elif mode == "semantic":
            return self.search_semantic(
                query_embedding, top_n, threshold, type_filter=type_filter, tags_filter=tags_filter
            )
        else:
            # Hybrid — needs both query text and embedding
            if not query:
                return self.search_semantic(
                    query_embedding,
                    top_n,
                    threshold,
                    type_filter=type_filter,
                    tags_filter=tags_filter,
                )
            return self.search_hybrid(
                query,
                query_embedding,
                top_n,
                threshold,
                type_filter=type_filter,
                tags_filter=tags_filter,
            )

    # --- Metadata accessors ---

    def get_metadata(self, concept_id: str) -> dict[str, Any] | None:
        """Get stored metadata for a concept."""
        row = self._read_conn.execute(
            "SELECT title, type, tags, mtime, snippet FROM concepts WHERE concept_id = ?",
            (concept_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "title": row[0],
            "type": row[1],
            "tags": json.loads(row[2]) if row[2] else [],
            "mtime": row[3],
            "snippet": row[4],
        }

    def get_all_concept_ids(self) -> set[str]:
        """Return all indexed concept IDs."""
        rows = self._read_conn.execute("SELECT concept_id FROM concepts").fetchall()
        return {row[0] for row in rows}

    def get_all_mtimes(self) -> dict[str, float]:
        """Return concept_id -> mtime mapping for all indexed concepts."""
        rows = self._read_conn.execute("SELECT concept_id, mtime FROM concepts").fetchall()
        return {row[0]: row[1] for row in rows}

    def get_sync_timestamp(self) -> float | None:
        """Get last sync timestamp."""
        row = self._read_conn.execute(
            "SELECT value FROM sync_meta WHERE key = 'last_sync'"
        ).fetchone()
        return float(row[0]) if row else None

    def set_sync_timestamp(self, ts: float) -> None:
        """Persist sync timestamp."""

        def _do() -> None:
            self._write_conn.execute(
                "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_sync', ?)",
                (str(ts),),
            )
            self._write_conn.commit()

        self._write_op("set_sync_timestamp", _do)

    def set_model_info(self, model_name: str, dimensions: int) -> None:
        """Store the embedding model name and dimensions used for this index."""

        def _do() -> None:
            self._write_conn.execute(
                "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('embedding_model', ?)",
                (model_name,),
            )
            self._write_conn.execute(
                "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('embedding_dimensions', ?)",
                (str(dimensions),),
            )
            self._write_conn.commit()

        self._write_op("set_model_info", _do)

    def get_model_info(self) -> tuple[str | None, int | None]:
        """Return (model_name, dimensions) stored in this index, or (None, None)."""
        model_row = self._read_conn.execute(
            "SELECT value FROM sync_meta WHERE key = 'embedding_model'"
        ).fetchone()
        dim_row = self._read_conn.execute(
            "SELECT value FROM sync_meta WHERE key = 'embedding_dimensions'"
        ).fetchone()
        model = model_row[0] if model_row else None
        dims = int(dim_row[0]) if dim_row else None
        return model, dims

    def check_model_compatibility(self, expected_model: str) -> str | None:
        """Check if the index was built with a different model.

        Returns a warning message if there's a mismatch, None if compatible.
        """
        stored_model, _ = self.get_model_info()
        if stored_model is None:
            return None  # No metadata yet (pre-existing index)
        if stored_model != expected_model:
            return (
                f"Index was built with model '{stored_model}' but config specifies "
                f"'{expected_model}'. Run `okf reindex --full` to rebuild."
            )
        return None

    def concept_count(self) -> int:
        """Number of indexed concepts."""
        row = self._read_conn.execute("SELECT COUNT(*) FROM concepts").fetchone()
        return row[0] if row else 0

    def check_integrity(self) -> bool:
        """Verify database is openable and passes integrity_check."""
        try:
            result = self._read_conn.execute("PRAGMA integrity_check").fetchone()
            return result[0] == "ok"
        except Exception:
            return False

    def clear(self) -> None:
        """Remove all data from the index (concepts, vectors, FTS). Used by full reindex."""

        def _do() -> None:
            self._write_conn.execute("DELETE FROM concepts")
            self._write_conn.execute("DELETE FROM vec_concepts")
            self._write_conn.execute("DELETE FROM fts_concepts")
            self._write_conn.commit()

        self._write_op("clear", _do)

    def close(self) -> None:
        """Close both database connections."""
        self._read_conn.close()
        self._write_conn.close()
