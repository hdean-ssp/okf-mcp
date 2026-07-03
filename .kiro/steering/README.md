# Steering Files

Steering files are how we encode our organisational DNA into Kiro. They're markdown files with YAML frontmatter that inject context into the agent's system prompt.

## How Steering Works

There are three inclusion modes:

| Mode | When It Loads | Use For |
|---|---|---|
| `always` | Every session, always in context | Universal rules: coding standards, security baseline, architecture principles |
| `fileMatch` | When working on files matching a pattern | Domain-specific rules: API, database, frontend, infrastructure |
| `manual` | When invoked via `/<filename>` slash command | Audits and reviews: security-review, performance-review, accessibility-review |

## Current Steering Files

### Always-On (inject into every session)
| File | Purpose |
|---|---|
| `coding-standards.md` | Naming, file organisation, error handling, logging, testing, commits |
| `architecture-principles.md` | Compute platform per cloud (AWS ECS Fargate / Azure AKS), cloud-native, service design, anti-patterns |
| `security-baseline.md` | Auth, authorisation, input validation, secrets, data protection |
| `product-context.md` | **Fill-in template.** Your product's domain, entities, business rules, user types, workflows, vocabulary. Agents load this to ground their reasoning in your actual business — without it, they only know generic coding. |
| `definition-of-done.md` | **Machine-checkable Definition of Done.** The non-negotiable quality bar (coverage, mutation, complexity, security severities, requirement traceability, contracts) every unit clears before a human reviews it. Stack-agnostic thresholds; enforced by `requirements-verifier` and the gate workflows. See `docs/AI-FIRST-DELIVERY-MODEL.md`. |
| `nfr-baseline.md` | **Non-functional requirements baseline.** Reliability, scalability, performance, observability, and data rules with citable IDs (NFR-REL/SCAL/PERF/OBS/DATA). Auto-injected by `requirements-analyst`, checked by `requirements-verifier`, version-pinned per feature. (Security NFRs live in `security-baseline.md`.) |

### Conditional (load when relevant files are touched)
| File | Trigger | Purpose |
|---|---|---|
| `api-development.md` | API/controller/route files | REST conventions, versioning, pagination, errors |
| `contract-first.md` | OpenAPI / `.proto` / `contracts/` / pact files | Frozen-contract discipline for parallel pods: freeze rule, how to change a contract, disjoint units |
| `database-work.md` | Migration/DB/SQL files | Postgres defaults, schema design, migrations, query patterns |
| `frontend-patterns.md` | React/TSX/UI files | React patterns, state management, accessibility, forms |
| `infrastructure.md` | Terraform/K8s/Docker files | IaC standards, K8s manifests, Helm, CI/CD |

### Manual (invoke by slash command)
| File | Command | Purpose |
|---|---|---|
| `security-review.md` | `/security-review` | Full security audit checklist |
| `performance-review.md` | `/performance-review` | Performance audit across API, DB, frontend, infra |
| `accessibility-review.md` | `/accessibility-review` | WCAG 2.1 AA audit for UI code |

## Maintaining Steering Files

- Review every quarter — standards drift, update accordingly
- Add examples where possible (good vs bad)
- Keep files focused — one concern per file
- Version them with your code; they're as important as the code itself

## Writing New Steering

Use this template:

```markdown
---
inclusion: always | fileMatch | manual
fileMatchPattern: "src/api/**"  # if fileMatch
---

# Title

## Rule
[Clear, specific rule]

## Why
[Rationale — helps agent apply to new situations]

## Examples

### Good
[example of correct pattern]

### Bad
[example of what to avoid]

## When Not to Apply
[Edge cases]
```
