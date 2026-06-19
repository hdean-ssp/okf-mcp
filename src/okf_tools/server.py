"""MCP server exposing okf-mcp service functions as MCP tools.

All diagnostic output goes to stderr (never stdout — that's the JSON-RPC channel).
Tool handlers are async, using asyncio.to_thread() for blocking service calls
(embedding, SQLite I/O) to avoid blocking the MCP event loop.
"""

from __future__ import annotations

import argparse
import asyncio
import atexit
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from . import service
from .config import OkfConfig, find_bundle_root, load_config
from .errors import (
    BundleAlreadyInitialisedError,
    ConceptNotFoundError,
    IndexBusyError,
    OkfError,
    ValidationError,
)
from .service import close_all_indexes

mcp = FastMCP("okf-mcp")

# Write serialization lock — ensures only one write operation (commit, update, delete,
# move, reindex) executes at a time. Reads (fetch, list, show, stats) bypass this lock.
# This prevents SQLite lock contention under concurrent MCP requests from multiple agents.
_write_lock = asyncio.Lock()


@dataclass
class AppState:
    """Application state for the MCP server process.

    Encapsulates configuration and runtime state in a single object,
    replacing bare module-level globals.
    """

    config: OkfConfig | None = None

    def set_config(self, config: OkfConfig) -> None:
        """Update the active bundle configuration."""
        self.config = config

    def require_bundle(self) -> OkfConfig:
        """Return config or raise ToolError if no bundle is configured."""
        if self.config is None:
            raise ToolError(
                "No bundle configured. Use init_bundle to create one, "
                "or restart the server with --bundle-path pointing to an existing bundle."
            )
        return self.config


# Singleton application state — tool handlers access this.
_state = AppState()


def _require_bundle() -> OkfConfig:
    """Return the current config or raise a ToolError if no bundle is configured.

    Tool handlers that require a configured bundle call this before
    invoking service functions.
    """
    return _state.require_bundle()


def _handle_error(e: OkfError) -> str:
    """Map domain errors to MCP error content strings.

    Returns a human-readable message suitable for returning to the MCP client.
    """
    if isinstance(e, ValidationError):
        return "\n".join(e.errors)
    elif isinstance(e, ConceptNotFoundError):
        return f"Concept not found: {e.concept_id}"
    elif isinstance(e, BundleAlreadyInitialisedError):
        return str(e)
    elif isinstance(e, IndexBusyError):
        return f"Index busy: {e.operation}. The operation is retryable — try again shortly."
    else:
        return "An internal error occurred"


@mcp.tool()
async def commit_concept(
    title: str,
    type: str,
    content: str,
    tags: list[str] | None = None,
    path: str | None = None,
    check_duplicates: bool = True,
) -> str:
    """Commit a new concept to the knowledge bundle.

    Creates a concept file with the given title, type, and content.
    Optionally checks for duplicate concepts before committing.
    """
    async with _write_lock:
        try:
            config = _require_bundle()
            try:
                input_data = {
                    "title": title,
                    "type": type,
                    "content": content,
                    "check_duplicates": check_duplicates,
                }
                if tags is not None:
                    input_data["tags"] = tags
                if path is not None:
                    input_data["path"] = path
                concept_id = await asyncio.to_thread(service.commit_concept, config, input_data)
                return json.dumps({"concept_id": concept_id})
            except ValidationError as e:
                raise ToolError(_handle_error(e)) from e
            except IndexBusyError as e:
                raise ToolError(_handle_error(e)) from e
        except ToolError:
            raise
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in commit_concept", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def init_bundle(path: str = ".") -> str:
    """Initialize a new OKF knowledge bundle at the specified path.

    Creates .okf/config.json, a root index.md, and updates .gitignore if in a git repo.
    This is the only tool that does not require a pre-configured bundle.
    """
    async with _write_lock:
        try:
            resolved = Path(path).resolve()
            if not resolved.exists() or not resolved.is_dir():
                raise ToolError(f"Path '{path}' does not exist or is not a directory")

            try:
                await asyncio.to_thread(service.init_bundle, resolved)
            except BundleAlreadyInitialisedError as e:
                raise ToolError(str(e)) from e

            _state.set_config(load_config(resolved))
            return json.dumps({"path": str(resolved)})
        except ToolError:
            raise
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in init_bundle", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def update_concept(
    concept_id: str,
    title: str | None = None,
    type: str | None = None,
    tags: list[str] | None = None,
    content: str | None = None,
) -> str:
    """Update an existing concept in the bundle.

    Applies only the provided fields to the concept, leaving unspecified fields unchanged.
    Re-embeds the content and updates the vector index.
    """
    async with _write_lock:
        try:
            config = _require_bundle()

            updates: dict = {}
            if title is not None:
                updates["title"] = title
            if type is not None:
                updates["type"] = type
            if tags is not None:
                updates["tags"] = tags
            if content is not None:
                updates["content"] = content

            if not updates:
                raise ToolError(
                    "At least one update field must be provided (title, type, tags, or content)"
                )

            try:
                await asyncio.to_thread(service.update_concept, config, concept_id, updates)
            except ConceptNotFoundError as e:
                raise ToolError(_handle_error(e)) from e
            except ValidationError as e:
                raise ToolError(_handle_error(e)) from e
            except IndexBusyError as e:
                raise ToolError(_handle_error(e)) from e

            return json.dumps({"concept_id": concept_id})
        except ToolError:
            raise
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in update_concept", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def move_concept(
    concept_id: str,
    new_concept_id: str,
    new_title: str | None = None,
) -> str:
    """Move or rename a concept within the bundle.

    Changes the concept's location (and therefore its concept_id) without
    losing content, metadata, or vector-index history. Optionally updates
    the title in frontmatter at the same time.

    Examples:
      - Rename: concept_id="notes/old-name", new_concept_id="notes/new-name"
      - Move:   concept_id="drafts/idea", new_concept_id="published/idea"
      - Both:   concept_id="tmp/scratch", new_concept_id="guides/setup-guide",
                new_title="Setup Guide"
    """
    async with _write_lock:
        try:
            config = _require_bundle()
            try:
                result_id = await asyncio.to_thread(
                    service.move_concept, config, concept_id, new_concept_id, new_title
                )
                return json.dumps({"old_concept_id": concept_id, "new_concept_id": result_id})
            except ConceptNotFoundError as e:
                raise ToolError(_handle_error(e)) from e
            except ValidationError as e:
                raise ToolError(_handle_error(e)) from e
            except IndexBusyError as e:
                raise ToolError(_handle_error(e)) from e
        except ToolError:
            raise
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in move_concept", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def delete_concept(concept_id: str) -> str:
    """Delete a concept from the bundle by its concept_id."""
    async with _write_lock:
        try:
            config = _require_bundle()
            try:
                await asyncio.to_thread(service.delete_concept, config, concept_id)
                return json.dumps({"concept_id": concept_id})
            except ConceptNotFoundError as e:
                raise ToolError(_handle_error(e)) from e
            except IndexBusyError as e:
                raise ToolError(_handle_error(e)) from e
        except ToolError:
            raise
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in delete_concept", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def show_concept(concept_id: str) -> str:
    """Show the full details of a concept by its concept_id.

    Returns all frontmatter fields and the complete markdown body.
    """
    try:
        config = _require_bundle()
        try:
            concept = await asyncio.to_thread(service.show_concept, config, concept_id)
            result = {"concept_id": concept.concept_id, **concept.frontmatter, "body": concept.body}
            return json.dumps(result)
        except ConceptNotFoundError as e:
            raise ToolError(_handle_error(e)) from e
    except ToolError:
        raise
    except Exception:
        logging.getLogger(__name__).error("Unexpected error in show_concept", exc_info=True)
        raise ToolError("An internal error occurred") from None


@mcp.tool()
async def reindex(full: bool = False) -> str:
    """Rebuild the vector index for the knowledge bundle.

    Performs an incremental reindex by default (only processes changed files).
    Set full=True to discard the existing index and rebuild from scratch.

    Returns a JSON summary with counts of added, updated, removed, skipped concepts
    and the total number of indexed concepts.
    """
    async with _write_lock:
        try:
            config = _require_bundle()
            summary = await asyncio.to_thread(service.reindex, config, full)
            return json.dumps(summary)
        except ToolError:
            raise
        except IndexBusyError as e:
            raise ToolError(_handle_error(e)) from e
        except Exception:
            logging.getLogger(__name__).error("Unexpected error in reindex", exc_info=True)
            raise ToolError("An internal error occurred") from None


@mcp.tool()
async def fetch_concepts(
    query: str,
    top_n: int = 5,
    threshold: float = 0.0,
    type: str | None = None,
    tags: list[str] | None = None,
    mode: str = "hybrid",
) -> str:
    """Search the knowledge bundle using natural language queries.

    Returns a ranked list of matching concepts with scores and snippets.
    Supports hybrid (semantic + keyword), keyword-only, or semantic-only modes.
    """
    try:
        config = _require_bundle()

        if not query.strip():
            raise ToolError("A non-empty query is required")

        try:
            results = await asyncio.to_thread(
                service.fetch_concepts,
                config,
                query,
                top_n,
                threshold,
                type,
                tags,
                mode,
            )
        except ValueError as e:
            raise ToolError(f"Search failed: {e}") from e

        formatted_results = [
            {
                "concept_id": r.concept_id,
                "title": r.title,
                "score": r.score if np.isfinite(r.score) else 0.0,
                "snippet": (r.snippet or "")[:200],
            }
            for r in results
        ]

        return json.dumps({"results": formatted_results})
    except ToolError:
        raise
    except Exception:
        logging.getLogger(__name__).error("Unexpected error in fetch_concepts", exc_info=True)
        raise ToolError("An internal error occurred") from None


@mcp.tool()
async def list_concepts(
    type: str | None = None,
    tags: list[str] | None = None,
    since: str | None = None,
    limit: int = 100,
    path: str | None = None,
) -> str:
    """List concepts in the knowledge bundle with optional filters.

    Returns a filtered, sorted list of concepts. Supports filtering by type,
    tags, modification date, and path prefix.
    """
    try:
        config = _require_bundle()
        concepts = await asyncio.to_thread(
            service.list_concepts,
            config,
            type,
            tags,
            since,
            limit,
            path,
        )
        formatted = [
            {
                "concept_id": c.concept_id,
                "title": c.title,
                "type": c.frontmatter.get("type", ""),
                "tags": c.tags,
            }
            for c in concepts
        ]
        return json.dumps({"concepts": formatted})
    except ToolError:
        raise
    except Exception:
        logging.getLogger(__name__).error("Unexpected error in list_concepts", exc_info=True)
        raise ToolError("An internal error occurred") from None


@mcp.tool()
async def get_stats() -> str:
    """Return bundle health statistics.

    Returns concept count, type/tag distributions, last reindex timestamp,
    and the number of concepts pending re-embedding.
    """
    try:
        config = _require_bundle()
        stats = await asyncio.to_thread(service.get_stats, config)
        return json.dumps(stats)
    except ToolError:
        raise
    except Exception:
        logging.getLogger(__name__).error("Unexpected error in get_stats", exc_info=True)
        raise ToolError("An internal error occurred") from None


def main() -> None:
    """Entry point for the okf-mcp server.

    Parses --bundle-path, resolves configuration, configures stderr logging,
    and starts the MCP server over stdio transport.
    """
    parser = argparse.ArgumentParser(
        description="OKF Tools MCP Server",
        prog="okf-mcp",
    )
    parser.add_argument(
        "--bundle-path",
        type=str,
        default=None,
        help="Path to the OKF bundle root directory",
    )
    args = parser.parse_args()

    # Configure logging to stderr only (stdout is the JSON-RPC channel)
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    # Resolve bundle configuration
    if args.bundle_path is not None:
        bundle_path = Path(args.bundle_path)
        if not bundle_path.exists() or not bundle_path.is_dir():
            print(
                f"Error: --bundle-path '{args.bundle_path}' does not exist or is not a directory.",
                file=sys.stderr,
            )
            sys.exit(1)
        _state.set_config(load_config(bundle_path.resolve()))
    else:
        root = find_bundle_root()
        if root is not None:
            _state.set_config(load_config(root))
        # else: _state.config stays None — init_bundle can be called later

    # Register cleanup for cached index connections
    atexit.register(close_all_indexes)

    # Pre-warm the embedding model to avoid a 30-second delay on first tool call.
    # The model (~30MB) downloads on first use; doing it at startup means MCP
    # clients won't time out waiting for the first embed operation.
    if _state.config is not None:
        try:
            from .search import get_embedder

            print("Loading embedding model...", file=sys.stderr)
            get_embedder(_state.config.embedding_model)
            print("Embedding model ready.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: failed to pre-load embedding model: {e}", file=sys.stderr)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
