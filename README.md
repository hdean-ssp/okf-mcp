# okf-mcp

Semantic search and CRUD tooling for [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge bundles. Runs locally, entirely offline.

OKF is a vendor-neutral format (published by Google Cloud Platform) for persisting team knowledge as markdown with YAML frontmatter. okf-mcp indexes those files and makes them searchable via hybrid BM25 + vector cosine similarity. It exposes the same functionality through both a CLI and an MCP server, so humans and AI agents can query the same bundle.

## Quick Start

```bash
# requires Python 3.10+
git clone https://github.com/hdean-ssp/okf-mcp.git
cd okf-mcp
source activate.sh

# create a bundle
mkdir ~/my-knowledge && cd ~/my-knowledge
git init && okf init

# add a concept
okf commit --check-duplicates --json '{
  "title": "Retry Pattern",
  "type": "Pattern",
  "content": "Use exponential backoff with jitter for transient failures.",
  "tags": ["reliability", "networking"]
}'

# build search index (downloads ~30MB embedding model on first run)
okf reindex

# search
okf fetch "how to handle network failures"
```

After that:

- `okf fetch "your question"` searches with natural language
- `okf list` browses all concepts
- `okf show <concept-id>` prints full content
- `okf stats` reports bundle health
- [Use Cases & Examples](docs/use-cases.md) has real-world workflows
- [Getting Started](docs/getting-started.md) is the full walkthrough

## Commands

| Command | Purpose |
|---------|---------|
| `okf init` | Initialise a new bundle |
| `okf commit` | Create a concept |
| `okf fetch <query>` | Hybrid search (BM25 + semantic) |
| `okf show <id>` | Display a concept |
| `okf list` | Browse concepts (filterable) |
| `okf update <id>` | Modify a concept |
| `okf move <id> <new-id>` | Move or rename a concept |
| `okf delete <id>` | Remove a concept |
| `okf reindex` | Rebuild the vector index |
| `okf stats` | Bundle statistics |

All commands accept `--format json|text|brief`. Piped output defaults to JSON; interactive defaults to text.

## How It Works

The markdown files in your bundle are the source of truth. The vector index is a derived sidecar (gitignored, rebuildable from scratch with `okf reindex --full`).

Search combines BM25 keyword matching and vector cosine similarity at a 60/40 weighting. Embeddings come from fastembed using BAAI/bge-small-en-v1.5 (384 dimensions), stored in SQLite via sqlite-vec. Everything runs locally.

Reindexing is incremental by default (mtime-based change detection). Embedding is chunked in small batches to keep memory usage under 500MB even on a 2GB VPS.

## MCP Server

The MCP server lets any MCP-compatible client (Kiro, Claude Desktop, etc.) interact with your bundle over stdio JSON-RPC.

```bash
# from within your bundle directory
okf-mcp

# or point to a specific bundle
okf-mcp --bundle-path ~/my-knowledge
```

You typically don't run it by hand. Instead, configure your MCP client to launch it:

### Client Configuration

**Team/shared deployment** (recommended, see [Team Setup Guide](docs/team-setup.md)):

Create `~/.kiro/settings/mcp.json` on the server:

```json
{
  "mcpServers": {
    "okf-mcp": {
      "command": "/path/to/okf-mcp/.venv/bin/okf-mcp",
      "args": [
        "--bundle-path",
        "/path/to/your/team-bundle"
      ],
      "autoApprove": [
        "commit_concept", "delete_concept", "fetch_concepts",
        "get_stats", "init_bundle", "list_concepts",
        "move_concept", "reindex", "show_concept", "update_concept"
      ]
    }
  }
}
```

**Kiro via Remote-SSH** (Kiro connects to server, MCP runs on server):

```json
{
  "mcpServers": {
    "okf-mcp": {
      "command": "/path/to/okf-mcp/.venv/bin/okf-mcp",
      "args": ["--bundle-path", "/path/to/your/bundle"],
      "autoApprove": [
        "fetch_concepts", "list_concepts", "show_concept",
        "get_stats", "reindex"
      ]
    }
  }
}
```

**Local setup** (Kiro and bundle on the same machine):

```json
{
  "mcpServers": {
    "okf-mcp": {
      "command": "okf-mcp",
      "args": ["--bundle-path", "/path/to/your/bundle"],
      "autoApprove": [
        "fetch_concepts", "list_concepts", "show_concept",
        "get_stats", "reindex"
      ]
    }
  }
}
```

See [MCP Setup Guide](docs/mcp-setup.md) for individual installation or [Team Setup Guide](docs/team-setup.md) for shared deployments.

### Available Tools

| Tool | Description |
|------|-------------|
| `init_bundle` | Create a new bundle at a given path |
| `commit_concept` | Add a new concept (title, type, content, tags) |
| `update_concept` | Modify fields on an existing concept |
| `move_concept` | Move or rename a concept |
| `delete_concept` | Remove a concept |
| `fetch_concepts` | Semantic/hybrid search with natural language |
| `list_concepts` | Browse concepts with filters (type, tags, date, path) |
| `show_concept` | Get full content of a concept |
| `reindex` | Rebuild the vector search index |
| `get_stats` | Bundle health statistics |

The server can start without a bundle configured. Pass `--bundle-path` or call `init_bundle` from the client. All tools except `init_bundle` require a configured bundle. Errors come back as structured MCP tool errors. Logging goes to stderr (stdout is the JSON-RPC channel).

## Agent Integration

Agents interact through the MCP tools directly (`fetch_concepts`, `commit_concept`, etc.). See `agent/AGENT.md` for the usage guide: when to query, when to commit, workflow patterns.

## Documentation

- [Team Setup Guide](docs/team-setup.md) - shared deployment onboarding
- [MCP Setup Guide](docs/mcp-setup.md) - individual installation and troubleshooting
- [Getting Started](docs/getting-started.md) - CLI walkthrough
- [CLI Reference](docs/cli-reference.md)
- [Use Cases & Examples](docs/use-cases.md)
- [Metrics & Impact Measurement](docs/metrics.md)
- [Validation Checklist](docs/validation-checklist.md)

## Development

```bash
git clone https://github.com/hdean-ssp/okf-mcp.git
cd okf-mcp
source activate.sh
pip install -e ".[dev]"
pytest
```

190 tests across CLI, MCP server, bundle operations, search, sync, and move/rename. Dev dependencies: `pytest`, `hypothesis`, `pytest-asyncio`.

## License

Apache 2.0
