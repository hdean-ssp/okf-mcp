# MCP Server Setup Guide

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Your Desktop                                   │
│  ┌───────────────────────────────────────────┐  │
│  │  Kiro (Remote-SSH to server)              │  │
│  │  ─ reads .kiro/settings/mcp.json          │  │
│  │  ─ spawns okf-mcp as a local process      │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      │ SSH
                      ▼
┌─────────────────────────────────────────────────┐
│  Linux Server                                   │
│                                                 │
│  /path/to/okf-mcp/                              │
│    .venv/bin/okf-mcp  ← MCP server binary       │
│                                                 │
│  /path/to/your/bundle/                          │
│    .okf/config.json   ← OKF bundle             │
│    concepts/...                                 │
└─────────────────────────────────────────────────┘
```

Since Kiro is connected via Remote-SSH, it runs commands **on the server** directly. No SSH tunneling needed in the MCP config — `okf-mcp` runs as a local process from the server's perspective.

## Prerequisites

- Python 3.10+ on the server
- Kiro connected to the server via Remote-SSH
- An OKF bundle initialised on the server

## Server Installation

```bash
# Clone okf-mcp
git clone https://github.com/hdean-ssp/okf-mcp.git
cd okf-mcp

# Create venv with Python 3.12 (or 3.10+)
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# Verify
okf-mcp --help
```

## Bundle Setup

If you don't have a bundle yet:

```bash
mkdir -p ~/knowledge && cd ~/knowledge
okf init
```

Or point to an existing bundle path.

## Kiro Configuration

Create or edit `.kiro/settings/mcp.json` **on the server** (Kiro reads this via Remote-SSH):

```json
{
  "mcpServers": {
    "okf-mcp": {
      "command": "/path/to/okf-mcp/.venv/bin/okf-mcp",
      "args": [
        "--bundle-path",
        "/path/to/your/bundle"
      ]
    }
  }
}
```

Replace paths with your actual locations.

### Auto-Approve (Recommended)

By default, Kiro prompts for approval on every MCP tool call. You can auto-approve non-destructive (read-only) tools so searches and lookups don't interrupt your flow, while keeping approval required for write operations:

```json
{
  "mcpServers": {
    "okf-mcp": {
      "command": "/path/to/okf-mcp/.venv/bin/okf-mcp",
      "args": [
        "--bundle-path",
        "/path/to/your/bundle"
      ],
      "autoApprove": [
        "fetch_concepts",
        "list_concepts",
        "show_concept",
        "get_stats",
        "reindex"
      ]
    }
  }
}
```

**Auto-approved (read-only):**
- `fetch_concepts` — search queries
- `list_concepts` — browse/filter
- `show_concept` — view full content
- `get_stats` — bundle health check
- `reindex` — rebuild search index (reads files, writes only to the sidecar index)

**Requires approval (write operations):**
- `commit_concept` — creates files
- `update_concept` — modifies files
- `move_concept` — renames/relocates files
- `delete_concept` — removes files
- `init_bundle` — creates bundle structure

If you trust the agent fully (e.g. personal bundle, automated workflows), you can auto-approve everything:

```json
"autoApprove": [
  "fetch_concepts", "list_concepts", "show_concept",
  "get_stats", "reindex", "commit_concept",
  "update_concept", "move_concept", "delete_concept",
  "init_bundle"
]
```

This can live at:
- `~/.kiro/settings/mcp.json` (user-level, applies to all workspaces)
- `<workspace>/.kiro/settings/mcp.json` (workspace-level, applies to that project only)

## Verify Connection

1. Reconnect the MCP server from Kiro's command palette (search "MCP")
2. The server should show as connected with 10 tools available
3. Test by asking Kiro: "list all concepts in my knowledge bundle"

## Available Tools

| Tool | Description |
|------|-------------|
| `init_bundle` | Create a new bundle at a given path |
| `commit_concept` | Add a new concept (title, type, content, tags) |
| `update_concept` | Modify fields on an existing concept |
| `move_concept` | Move or rename a concept |
| `delete_concept` | Remove a concept |
| `fetch_concepts` | Semantic/hybrid search with natural language |
| `list_concepts` | Browse concepts with filters |
| `show_concept` | Get full content of a concept |
| `reindex` | Rebuild the vector search index |
| `get_stats` | Bundle health statistics |

## Troubleshooting

### Request timed out

The server starts but doesn't respond. Common causes:

1. **Bundle path doesn't exist** — verify the path in your config exists on the server
2. **Wrong Python version** — `mcp` package requires Python 3.10+. Check with `python3 --version` in the venv
3. **First-run embedding model download** — the first `reindex` or `commit_concept` downloads a ~30MB model. This is one-time only but can cause the first request to be slow.

### Test manually

Run the exact command from your config in a terminal on the server:

```bash
/path/to/okf-mcp/.venv/bin/okf-mcp --bundle-path /path/to/your/bundle
```

It should sit silently waiting for input. If it prints an error, that's the problem. Ctrl+C to exit.

### Permission denied

The `okf-mcp` binary isn't executable or the venv is broken. Rebuild:

```bash
cd /path/to/okf-mcp
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```
