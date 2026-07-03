# Kiro Custom Agents

This folder contains 23 custom Kiro agents, each specialised for a specific role in the agentic development lifecycle. These agents are ported from the original Denver GitHub Copilot agents to Kiro's native custom-agent format, with additional agents added to reach full parity with the ProductStudio workflow set (plus a `course-tutor` agent that delivers the self-paced training curriculum).

## File Format

Each agent is two files:

| File | Purpose |
|---|---|
| `<name>.json` | Configuration: tools, model, resources, allowed shell commands |
| `<name>.prompt.md` | The agent's system prompt — its role, workflow, and rules |

## The Agents

### Lifecycle Management Agents

| Agent | Role |
|---|---|
| `requirements-analyst` | Intake structurer. Converts a raw ADO story/feature/task into a tight, atomic, numbered requirements document with explicit schema, edge cases, and blocking open questions, before AI-DLC inception. Fixes silent requirement drops and sample-data misinterpretation at the input gate. See `docs/AI-FIRST-DELIVERY-MODEL.md`. |
| `requirements-verifier` | Independent traceability gate. After construction, proves every requirement ID maps to a specific code location and a passing test; emits a coverage report and blocks unevidenced requirements. Fixes silent requirement drops at the output gate. Independent of the developer agent; stack-agnostic. |
| `product-owner` | Triages issues, breaks epics into stories, reprioritises work, maintains the project board |
| `project-manager` | Reviews PRs, manages agent worker assignments, ensures code quality standards |
| `architect` | Designs cloud-native architectures, creates ADRs with 5+ evaluated alternatives |
| `tech-reviewer` | Deep-reviews PRs, validates infra claims against live environments, ensures coherent direction |
| `documentation-engineer` | Reviews PR patterns and incrementally improves docs and steering files |
| `continuity-engineer` | Ensures no work falls through the cracks when issues/PRs close incomplete |
| `platform-engineer` | Runs on a schedule to inspect K8s cluster health and take corrective action |
| `developer` | Triages issues, builds features from specs, and fixes defects (triage, build, and fix modes) |
| `test-engineer` | Independent test engineer — reviews code and writes automated tests the developer missed (unit, integration, edge-case, security) |

### Quality Team Agents

| Agent | Role |
|---|---|
| `quality-lead` | Coordinates the full codebase audit suite across all genres |
| `quality-analyst` | Reviews audit findings, produces health score, escalates critical issues |
| `security-auditor` | Security-focused audit (admin endpoints, auth gaps, CVEs, secrets) |
| `infrastructure-auditor` | Infrastructure maturity assessment |
| `hosting-auditor` | Hosting and deployment assessment |
| `team-auditor` | Team health and stability assessment |
| `test-step-writer` | Generates manual QA test steps for human testers after PR merge |

### Operations Team Agents

| Agent | Role |
|---|---|
| `platform-engineer` | Monitors Kubernetes cluster health, auto-remediates simple problems |
| `continuity-engineer` | Finds closed-incomplete work, creates follow-up issues |
| `documentation-engineer` | Spots documentation gaps from PR patterns, files improvement issues |
| `ecosystem-scout` | Monthly scan for new Kiro/Anthropic/AWS features worth adopting |
| `ui-parity-scout` | Flags UI drift between frameworks when one changes |
| `support-engineer` | Triages FreshService-synced customer tickets, categorises and routes |

### Audit Framework Agents

| Agent | Role |
|---|---|
| `quality-lead` | Entry point for automated codebase audits; coordinates genre agents + reviewer |
| `quality-analyst` | Reads all filled audit templates and produces cross-genre executive overview |
| `security-auditor` | Fills security audit templates by static analysis + git blame attribution |
| `infrastructure-auditor` | Fills infrastructure maturity templates with 1-5 scoring |
| `hosting-auditor` | Fills hosting security templates by analysing IaC (Terraform/CloudFormation/Bicep/ARM) |
| `team-auditor` | Analyses git history for churn and vulnerability attribution |

### Continuous Improvement & QA Agents

| Agent | Role |
|---|---|
| `ecosystem-scout` | Monthly scanner of Kiro changelog, Anthropic releases, AWS announcements, community Kiro repos. Raises issues proposing new agents, steering rules, or model-routing changes. |
| `test-step-writer` | Generates manual QA test steps from merged PR diffs. Posts steps on the linked issue, reopens it, applies `needs-testing`. |
| `support-engineer` | First-responder for FreshService-synced customer support tickets. Classifies, adds code context, routes. |
| `ui-parity-scout` | When one UI framework (Blazor, React, mobile) gets a user-visible change, raises a ui-sync issue for the other frameworks. |

### Training Agents

| Agent | Role |
|---|---|
| `course-tutor` | Self-serve concept teacher for the 10-hour Acceleration Program (`training.md`). Replaces the instructor-led concept talk so the curriculum can be run as a self-paced kit: explains each hour's concepts in monolith→modern framing, runs a short Socratic self-check, then hands the learner back to the hands-on exercise. Read-only — it teaches, it never does the exercises. |

## Using an Agent

### From Kiro CLI

```bash
kiro-cli --agent <agent-name>
```

Example:
```bash
kiro-cli --agent tech-reviewer
```

### From Kiro IDE

In chat, use `/agent swap <agent-name>` to switch, or `/agent list` to see all available agents.

### Headless (CI/CD)

```bash
kiro-cli chat --agent <agent-name> --no-interactive --trust-tools=read,grep "your prompt"
```

## Model Routing

Each agent's JSON config specifies the default model:

| Model | Used For |
|---|---|
| `claude-opus-4.7` | Architecture, complex reasoning, executive reports (product-owner, architect, tech-reviewer, quality-lead, quality-analyst, security-auditor, infrastructure-auditor, hosting-auditor) |
| `claude-sonnet-4.6` | General code and review work (project-manager, documentation-engineer, continuity-engineer, platform-engineer, developer, test-engineer, team-auditor, course-tutor) |

You can override the model per-session via `/model <name>` in the IDE or `--model` flag in CLI.

## Tool Access

Agents use two tool categories:

- **Built-in Kiro tools** — listed flat in `tools` array: `fs_read`, `fs_write`, `grep`, `shell`
- **Shell command restrictions** — configured in `toolsSettings.shell.allowedCommands` with glob patterns

**Schema note:** Agent configs follow Kiro's official custom-agent schema:

```json
{
  "name": "...",
  "description": "...",
  "prompt": "file://./name.prompt.md",
  "tools": ["fs_read", "fs_write", "grep", "shell"],
  "allowedTools": ["fs_read", "grep"],
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["gh pr *", "gh issue *"],
      "autoAllowReadonly": true
    }
  },
  "resources": ["file://.kiro/steering/coding-standards.md"],
  "model": "claude-sonnet-4.6"
}
```

- **`tools`** declares which tools are available
- **`allowedTools`** declares which tools run without prompting (read/grep only by default)
- **`toolsSettings.shell.allowedCommands`** restricts what shell commands the shell tool can run
- **`prompt`** uses `file://` URI to reference the external prompt file

MCP tools are available. Agents that benefit from MCP servers can declare them in an `mcpServers` block in their JSON config.

## Prerequisites

For agents that use shell commands, these tools must be installed and authenticated on the machine running the agent:

| Tool | Required By | How to Authenticate |
|---|---|---|
| `gh` CLI | product-owner, project-manager, documentation-engineer, continuity-engineer, developer, platform-engineer, tech-reviewer | `gh auth login` |
| `az` CLI | platform-engineer, tech-reviewer, documentation-engineer | `az login` |
| `aws` CLI | platform-engineer, tech-reviewer, documentation-engineer | `aws configure` or SSO |
| `kubectl` | platform-engineer, tech-reviewer | configured per cluster |
| `helm` | platform-engineer | no auth required |
| `git` | team-auditor, developer, security-auditor | configured in repo |

## Steering Files

Each agent's JSON specifies which steering files it loads as resources. This gives the agent organisational context (coding standards, security baseline, architecture principles) beyond just its prompt.

See `.kiro/steering/` for the full set of steering files and their purposes.

## Adding Your Own Agent

1. Create `<name>.json` and `<name>.prompt.md` in this folder
2. Reference steering files in `resources`
3. List only the shell command patterns the agent actually needs in `allowedShellCommands`
4. Pick a model that matches the complexity of the agent's work
5. Test via `kiro-cli --agent <name>` before adding to CI workflows

## Agent Relationships

Some agents invoke others:

```
quality-lead
    ├── invokes → security-auditor
    ├── invokes → infrastructure-auditor
    ├── invokes → team-auditor
    ├── invokes → hosting-auditor
    └── invokes → quality-analyst (after all auditors complete)

project-manager
    └── triggers → developer agent (in build or fix mode) via CI workflow

documentation-engineer
    └── creates issues for → developer agent to implement

platform-engineer
    └── creates issues for → developer agent to fix (when fix is code-level)
```

This multi-agent coordination will be wired up in Phase 3 (CI/CD workflows) — each invocation becomes a `kiro-cli` command in GitHub Actions or a cron job.
