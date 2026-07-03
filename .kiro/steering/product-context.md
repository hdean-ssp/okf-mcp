---
inclusion: always
---

# Product Context

## Product overview

okf-mcp is a local-first semantic search and CRUD tool for OKF (Open Knowledge Format) knowledge bundles. It lets developers and AI agents create, query, and maintain structured knowledge stored as markdown files with YAML frontmatter. Runs entirely offline. Exposes functionality through both a CLI (`okf`) and an MCP server (`okf-mcp`) so humans and AI agents interact with the same bundle through the same operations.

Target users: individual developers and small teams who want structured, searchable knowledge that AI agents can also consume. No cloud dependency.

## Repositories and services

- `okf-mcp` — Python 3.10+, single package (`okf_tools`). Contains both CLI and MCP server. No external services.

## Architecture at a glance

```
CLI (click) ──┐
              ├──→ Service layer (service.py) ──→ Bundle (bundle.py) ──→ Markdown files (source of truth)
MCP Server ───┘                                      │
                                                     ├──→ Search index (search.py) ──→ SQLite + sqlite-vec
                                                     └──→ Config (.okf/config.json)
```

Search combines BM25 keyword matching and vector cosine similarity (60/40 weighting). Embeddings via fastembed (BAAI/bge-small-en-v1.5, 384 dimensions), stored in SQLite via sqlite-vec. Index is a derived sidecar (gitignored, rebuildable).

## Core entities

- **Bundle** — a directory containing markdown concept files and `.okf/config.json`. The unit of knowledge. One per project/team.
- **Concept** — a single markdown file with YAML frontmatter (title, type, tags, created, modified). The atomic unit of knowledge.
- **Concept ID** — derived from the file path relative to the bundle root (e.g. `patterns/retry-pattern`).
- **Index** — SQLite database with BM25 FTS and vector embeddings. Derived from concepts, rebuildable from scratch.
- **Config** — `.okf/config.json` at bundle root. Stores bundle metadata.

## Business rules

- Concept IDs are path-based and unique within a bundle. Moving a concept changes its ID.
- The markdown files are the source of truth. The index is always rebuildable via `okf reindex --full`.
- Reindexing is incremental by default (mtime-based change detection).
- Search uses hybrid mode (BM25 + vector) by default. Supports keyword-only and semantic-only modes.
- Duplicate detection is optional on commit (`--check-duplicates`).
- The MCP server can start without a bundle configured — `init_bundle` creates one.
- All tools except `init_bundle` require a configured bundle.
- Embedding is chunked in small batches to keep memory under 500MB (designed for 2GB VPS).

## Key workflows

1. **Init → Commit → Reindex → Fetch** — the happy path. Create a bundle, add knowledge, build index, search.
2. **Incremental reindex** — after adding/modifying concepts, rebuild only changed entries.
3. **MCP agent interaction** — AI agent calls `fetch_concepts` to find relevant knowledge, `commit_concept` to store new learnings.
4. **Move/rename** — reorganise concepts without losing content or breaking references.
5. **List/filter** — browse by type, tags, date, or path prefix.

## Constraints

- Never require network access for core operations (fully offline).
- Never store secrets in bundle files.
- PII should not appear in concept content (knowledge bundles are shared).
- The index directory (`.okf/index/`) is always gitignored and rebuildable.
- Memory usage must stay under 500MB even during full reindex.

## Vocabulary

- **Bundle** — the knowledge store directory, not a software package.
- **Concept** — a single knowledge entry (markdown file), not an abstract idea.
- **Concept ID** — the relative path without `.md` extension, not a UUID.
- **Reindex** — rebuild the search index from markdown source files.
- **Hybrid search** — combined BM25 + vector cosine similarity scoring.

## Testing patterns

- pytest for all tests (190 tests across CLI, MCP server, bundle operations, search, sync, move/rename)
- hypothesis for property-based testing
- pytest-asyncio for async MCP server tests
- Tests live in `tests/` at repo root
- No external services needed — tests create temporary bundles
- Dev dependencies: `pip install -e ".[dev]"`
- Linting: ruff (check + format)
- Security: pip-audit for dependency vulnerabilities
- CI runs on Python 3.10, 3.11, 3.12

## References

- CLI reference: `docs/cli-reference.md`
- Use cases: `docs/use-cases.md`
- Getting started: `docs/getting-started.md`
- MCP setup: `docs/mcp-setup.md`
- Team setup: `docs/team-setup.md`
- Roadmap: `ROADMAP.md`
- OKF spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

---

*Last reviewed: 2026-07-03. Owner: hdean. Review cadence: quarterly.*
