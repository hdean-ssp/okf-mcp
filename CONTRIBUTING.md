# Contributing to okf-mcp

## Development Setup

```bash
git clone https://github.com/hdean-ssp/okf-mcp.git
cd okf-mcp
source activate.sh        # detects best Python, creates venv, installs
pip install -e ".[dev]"   # adds pytest, hypothesis, pytest-asyncio
```

## Running Tests

```bash
pytest                    # all tests
pytest tests/test_bundle.py  # specific module
pytest -v                 # verbose output
```

The first run of tests that touch semantic search will download the embedding model (~30MB). Subsequent runs use the cached model at `~/.cache/fastembed/`.

## Code Style

- Python 3.10 compatible — use `from __future__ import annotations` for cleaner type hints
- Type hints on all public functions
- Docstrings on all public functions and classes
- Keep modules focused — one responsibility per file
- Prefer clarity over cleverness

## Project Structure

```
src/okf_tools/
├── __init__.py     # Package metadata and version constants
├── cli.py          # Click commands (thin — delegates to service)
├── service.py      # Workflow orchestration
├── bundle.py       # File parsing, writing, validation
├── search.py       # Hybrid search: vector (sqlite-vec) + BM25 (FTS5) + fastembed
├── sync.py         # Incremental reindexing
├── config.py       # Configuration loading
├── server.py       # MCP server (exposes service functions as MCP tools)
└── errors.py       # Error hierarchy
```

## OKF Spec Reference

The spec we target is vendored at `spec/OKF_SPEC_v0.1.md`. The version constant lives in `src/okf_tools/__init__.py` as `OKF_SPEC_VERSION`. When the upstream spec changes, update both.

## Pull Request Guidelines

1. Branch from `main`
2. Keep PRs focused — one logical change per PR
3. Add tests for new functionality
4. All tests must pass before merge
5. Update docs if you change CLI behaviour
