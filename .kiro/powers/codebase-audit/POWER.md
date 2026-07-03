---
name: codebase-audit
description: >
  Comprehensive codebase auditing capability. Activates when the user asks about
  running an audit, checking codebase health, security assessment, compliance
  review, infrastructure maturity, team stability, or cloud security posture.
keywords:
  - audit
  - codebase audit
  - security audit
  - infrastructure audit
  - maturity assessment
  - compliance check
  - cis benchmark
  - vulnerability scan
  - team stability
  - vulnerability attribution
  - git blame
  - hosting audit
  - terraform audit
  - iac audit
  - cloud security
  - health score
agents:
  - quality-lead
  - quality-analyst
  - security-auditor
  - infrastructure-auditor
  - team-auditor
  - hosting-auditor
---

# Codebase Audit Power

Expert-level capability for conducting multi-genre codebase audits that produce evidence-based, severity-rated findings with a cross-genre executive overview.

## What This Power Provides

### Agents (6)

| Agent | Role |
|---|---|
| `quality-lead` | Entry point. Coordinates genre agents and the reviewer. Reads `audit-config.yml`. Scans the codebase for genre relevance (AWS detected? Azure detected? Team history available?). |
| `quality-analyst` | Reads all filled templates and produces the executive overview with health scores, cross-genre patterns, and priority action plan. |
| `security-auditor` | Static analysis for vulnerabilities. Produces severity-rated findings with git-blame attribution. |
| `infrastructure-auditor` | Technology maturity assessment. 1-5 rubric scoring across architecture dimensions. |
| `team-auditor` | Git history analysis for team stability (churn) and vulnerability attribution. |
| `hosting-auditor` | IaC security analysis for AWS (`aws_*` Terraform, CloudFormation, CDK, SAM) and Azure (`azurerm_*`, Bicep, ARM). |

### Templates (59 across 5 genres)

- **Security** (17 templates) — authentication, API, crypto, database, dependencies, etc.
- **Infrastructure** (17 templates) — API design, databases, frontend, backend, CI/CD, etc.
- **Team** (3 templates) — developer churn, vulnerability attribution, executive summary
- **Hosting AWS** (8 templates) — IAM, network, compute, database, storage, logging, compliance
- **Hosting Azure** (8 templates) — identity, network, compute, database, storage, logging, compliance
- **Executive summaries** per genre

### Configuration

- `audit-config.yml` — genre enable/disable, rubric thresholds, exclude paths, health-score weights
- Rubric-based scoring with normalised metrics (per 1,000 LOC for security, per 10 IaC resources for hosting)

## When This Power Activates

Automatically loads when you mention any of these keywords or ask about:

- "Run an audit on this codebase"
- "Check our security posture"
- "Assess infrastructure maturity"
- "Review our cloud security"
- "Run CIS benchmark check"
- "Analyse developer churn"
- "Attribute vulnerabilities to developers"
- "Generate health score"

## How to Invoke

### Quick Start

```
I want to run a codebase audit.
```

The orchestrator will:
1. Read `audit-config.yml` (or use defaults)
2. Detect which genres apply (skips hosting if no IaC detected, skips team if no git history, etc.)
3. Delegate to genre agents
4. Produce a cross-genre executive overview

### Targeted Audit

```
Run a security-only audit for PCI-DSS compliance.
```

Or:

```
Audit our AWS hosting posture against CIS benchmarks.
```

### Via Kiro CLI (headless)

```bash
kiro-cli chat --agent quality-lead --no-interactive \
  --trust-tools=fs_read,fs_write,grep \
  "Run a full codebase audit."
```

### Via GitHub Actions

`.github/workflows/run-audit.yml` triggers this flow on manual dispatch or on a monthly schedule.

## Output Structure

```
audits/YYYY-MM-DD/
├── executive-overview.md       # Cross-genre summary + health score
├── audit-metadata.json         # What ran, what skipped, why
├── security/                   # Filled security templates + executive-summary.md
├── infrastructure/             # Filled infra templates + executive-summary.md
├── team/                       # Filled team templates + executive-summary.md
└── hosting/
    ├── aws/                    # Filled AWS templates + executive-summary.md (if detected)
    └── azure/                  # Filled Azure templates + executive-summary.md (if detected)
```

## Design Principles

### Evidence-Based

Every finding cites specific files and line numbers. Vague findings like "authentication could be improved" are explicitly rejected. The agents are instructed to provide:

```
File: src/auth/login.controller.ts:42
Issue: Timing-safe comparison not used for password verification
Committed By: jane@example.com (2025-10-14)
Approved By: bob@example.com
Impact: Potential timing attack enabling password enumeration
```

### Normalised Scoring

Scores account for codebase size:

- **Security** — findings per 1,000 lines of code
- **Hosting** — findings per 10 IaC resources
- **Infrastructure** — 1-5 dimension maturity with weak-area penalty
- **Team** — stability maturity × 20 with tenure and departure modifiers

This means a 100K-LOC codebase with 10 medium findings scores the same as a 1K-LOC codebase with 0.1 medium findings per 1K LOC.

### Consistent and Reproducible

The rubrics in `audit-config.yml` are fixed. Two audit runs on the same codebase produce the same scores. Trend analysis over time is meaningful.

### Agent-Filled, Human-Reviewed

Agents do the scanning and initial filling. Humans review the executive overview, prioritise findings, and sign off on remediation. The process is designed to scale analysis while keeping humans in the judgement seat.

## Limitations

What this power **does well**:

- Static analysis of source code
- IaC security review (Terraform, CloudFormation, Bicep, ARM, CDK)
- Git history analysis
- Dependency auditing
- Architectural maturity assessment

What this power **does not do** (needs separate tooling):

- Dynamic application security testing (DAST)
- Runtime cloud environment scanning (use AWS Config, Azure Defender)
- Penetration testing
- Load and performance testing
- Compliance certification (requires certified auditor)

## Integration Points

This power works well alongside:

- **FOSSA / Snyk** — CVE and licence scanning (in `pr-validation.yml`)
- **GitHub Advanced Security** — CodeQL semantic analysis
- **TruffleHog / gitleaks** — git history secret scanning
- **OWASP ZAP** — dynamic testing
- **Azure Defender / AWS Security Hub** — live cloud posture

The audit framework focuses on static analysis and reporting. Runtime testing and certified compliance audits remain separate.

## Customising

### Skip a template

In `audit-config.yml`:

```yaml
genres:
  security:
    skip:
      - mobile
      - voice
```

### Force a template always

```yaml
genres:
  security:
    force-include:
      - supply-chain
```

### Adjust health-score weights

```yaml
review:
  health-score-weights:
    security: 50       # Default 35 — higher weight if security-critical
    infrastructure: 20
    team: 15
    hosting: 15
```

### Change rubric thresholds

See `audit-config.yml` — full rubric is configurable per genre.

## Compliance Framework Mappings

Templates map to:

- CIS AWS Foundations Benchmark v3.0.0
- CIS Microsoft Azure Foundations Benchmark v2.0.0
- OWASP Top 10 2021
- CWE Top 25
- NIST SP 800-53 Rev 5
- ISO 27001:2022 Annex A
- SOC 2 Trust Services Criteria
- PCI-DSS v4.0
- FedRAMP Moderate / High (for GovCloud)

Cross-references appear in each template where relevant.

## Related Files

- `.kiro/agents/audit-*.json` and `.kiro/agents/*-auditor.json` — agent definitions
- `.github/audits/` — all 59 templates
- `.github/audit-config.yml` — configuration
- `.github/workflows/run-audit.yml` — CI workflow
- `.github/workflows/scheduled-audit.yml` — monthly trigger
