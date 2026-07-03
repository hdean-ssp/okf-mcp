# Kiro Settings

This folder holds Kiro configuration for this repo.

## Files

| File | Purpose |
|---|---|
| `cli.json` | Kiro CLI preferences (default model, model routing, trust defaults) |

## Why No `mcp.json`

**MCP is currently unavailable in this environment.**

Your Kiro installation is subject to a system policy that prevents user-level MCP configuration (`kiroAgent.configureMCP` is locked). Attempting to configure MCP servers produces the error:

> `Unable to write kiroAgent.configureMCP because it is configured in system policy.`

We've therefore not shipped an `mcp.json` file. Kiro will use whatever MCP configuration (if any) your administrator has provisioned centrally. The agents in this repo are designed to work without MCP — they use:

1. **Built-in Kiro tools** — file read/write, grep, search, shell
2. **Shell commands** — `gh` CLI for GitHub, `az` CLI for Azure, `kubectl` for Kubernetes, etc.

This is intentionally compatible with Denver's original Copilot-based design, which also used CLI tools rather than MCP.

## If MCP Becomes Available Later

If your Kiro admin enables MCP (or you're the admin and toggle it on), you can add servers here. Common useful ones:

### GitHub
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" },
  "disabled": false
}
```

### Jira / Atlassian
```json
"jira": {
  "command": "uvx",
  "args": ["mcp-atlassian"],
  "env": {
    "JIRA_URL": "${JIRA_URL}",
    "JIRA_PERSONAL_TOKEN": "${JIRA_TOKEN}"
  },
  "disabled": false
}
```

### Postgres (read-only)
```json
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": { "POSTGRES_CONNECTION_STRING": "${DATABASE_URL_READONLY}" },
  "disabled": false
}
```

### AWS Docs
```json
"aws-docs": {
  "command": "uvx",
  "args": ["awslabs.aws-documentation-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false
}
```

### Filesystem (files outside workspace)
```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
  "disabled": false
}
```

## How Agents Work Without MCP

The agents in `.kiro/agents/` reference MCP tools in their configs, but these references are treated as optional. When MCP is unavailable, agents fall back to:

- **GitHub operations** → `gh` CLI (assumes you're authenticated via `gh auth login`)
- **Jira operations** → not supported without MCP; agent asks user to provide ticket content manually
- **Database queries** → not supported without MCP
- **AWS documentation lookup** → falls back to general knowledge + web search

## Prerequisites for CLI-Based Workflows

Since we're using CLI tools instead of MCP, ensure these are installed and authenticated:

| Tool | Purpose | Check |
|---|---|---|
| `gh` | GitHub operations | `gh auth status` |
| `az` | Azure operations | `az account show` |
| `kubectl` | Kubernetes operations | `kubectl version --client` |
| `terraform` | Infrastructure as Code | `terraform version` |
| `docker` | Container builds | `docker ps` |
| `npm` / `node` | Node.js projects | `node --version` |

## If You're the Kiro Admin

To unlock MCP for users, open your Kiro enterprise console and look for:

- **Settings > Governance > MCP Configuration**
- **Settings > Shared Settings > MCP Servers**
- Or a policy setting named `kiroAgent.configureMCP`

You can either:
- **Unlock fully** — let users configure their own MCP servers
- **Centrally manage** — admin provisions approved MCP servers that push to all users
- **Allowlist** — permit specific servers, block others

Until MCP is unlocked, leave `mcp.json` empty to avoid confusing errors.
