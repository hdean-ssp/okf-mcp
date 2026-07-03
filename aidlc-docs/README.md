# aidlc-docs/

Every feature driven through the AI-DLC workflow gets a subdirectory here. This folder is the **documentation trail** for AI-assisted development — decisions, approvals, and artefacts live here. Application code does NOT live here.

## Structure

```
aidlc-docs/
└── <feature-slug>/
    ├── aidlc-state.md           # current stage, tasks, extension configuration
    ├── audit.md                 # append-only log of every decision and approval
    ├── inception/
    │   ├── requirements/
    │   │   └── requirements.md  # EARS-format requirements
    │   ├── application-design/
    │   │   └── design.md        # architecture, data model, APIs, diagrams
    │   ├── user-stories/        # optional — user stories when applicable
    │   └── plans/
    │       └── execution-plan.md
    ├── construction/
    │   └── <unit>/
    │       ├── functional-design/
    │       ├── nfr-requirements/
    │       ├── nfr-design/
    │       ├── infrastructure-design/
    │       └── code/            # summaries only — actual code is in the repo root
    └── operations/              # placeholder (stage currently not wired)
```

## How features land here

1. Open a GitHub issue whose body starts with `Using AI-DLC, ...`
2. The `aidlc-trigger.yml` workflow fires
3. The `aidlc-lead-engineer` agent creates `aidlc-docs/<slug>/` with initial scaffolding
4. It asks you structured multiple-choice questions via issue comments
5. Each phase transition requires you to apply an approval label (`aidlc:requirements-approved`, `aidlc:design-approved`, etc.)
6. When inception completes, construction work is handed to `developer` agent to implement

## Rules enforced by CI

The `aidlc-validate.yml` workflow runs on every PR that touches `aidlc-docs/` and checks:

- Every feature folder has `aidlc-state.md` and `audit.md`
- Features past inception have an `inception/` subfolder
- `audit.md` is not empty
- `aidlc-state.md` declares a `## Current Stage`

Violations fail the PR check.

## Audit log discipline

`audit.md` is **append-only**. Entries look like:

```markdown
## Requirements Analysis
**Timestamp**: 2026-05-12T14:22:00Z
**User Input**: "B - async upload with background validation"
**AI Response**: "Understood. Proceeding with async model. Recording decision."
**Context**: Question 3 of 5 in requirements analysis round 1

---
```

Never rewrite or summarise entries. The full raw user input must be preserved.

## Extensions

Extensions live under `.kiro/aws-aidlc-rule-details/extensions/` and are opted into during requirements analysis:

| Extension | Default | Effect when enabled |
|---|---|---|
| `security/baseline` | Opt-in | Enforces OWASP + secure-coding rules as hard gates |
| `testing/property-based` | Opt-in | Requires property-based tests for critical logic |

Your choices are recorded in `aidlc-state.md` under `## Extension Configuration`.

## References

- `.kiro/steering/aws-aidlc-rules/core-workflow.md` — top-level workflow
- `.kiro/aws-aidlc-rule-details/` — detailed stage-by-stage rules
- `.kiro/agents/aidlc-lead-engineer.prompt.md` — coordinator agent behaviour
- `.github/workflows/aidlc-trigger.yml` — how features are initiated
- `.github/workflows/aidlc-validate.yml` — PR validation
- External: [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) — methodology source

## Governance

See `docs/leadership/ai-dlc-governance.md` for ownership, approval authority, and extension adoption policy.
