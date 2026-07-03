# AI-DLC — Local Changelog

This file tracks upstream version upgrades and any local deviations from [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) rule files.

## 1.0.0 — 2026-06-17 (current)

- **Source**: [awslabs/aidlc-workflows v1.0.0](https://github.com/awslabs/aidlc-workflows/releases/tag/v1.0.0)
- **Upgraded**: 2026-06-17 (this session, from v0.1.8)
- **Local deviations**: none — exact copy of the tagged release's rule files

### What was upgraded

Vendored from the tag's `aidlc-rules/aws-aidlc-rule-details/` and `aidlc-rules/aws-aidlc-rules/core-workflow.md`:

- `.kiro/aws-aidlc-rule-details/` — all rule-detail files refreshed to v1.0.0
- `.kiro/steering/aws-aidlc-rules/core-workflow.md` — refreshed to v1.0.0

The local-only `VERSION` and `CHANGELOG.md` (this file) are not part of the upstream rule set and were preserved.

### Changes from previous upstream (v0.1.8 → v1.0.0)

Despite the major-version bump, the rule-detail changes are small and non-breaking. Nothing was removed; the changes are clarity/consistency fixes plus one new opt-in extension:

- **"Units Planning" ghost stage reconciled to the canonical "Units Generation"** (upstream #156). Renames and clarifies that Planning/Generation are sub-steps within the single Units Generation stage, not two separate stages. Touches `common/terminology.md`, `common/error-handling.md`, `common/workflow-changes.md`, `inception/units-generation.md`, `inception/workflow-planning.md`. No behavioural reordering — this repo's agents and the sample `aidlc-docs/` already use "Units Generation", so no local impact.
- **Multiple-choice options now blank-line separated** so strict CommonMark renderers display them on separate lines (upstream #246, #278). Touches `common/question-format-guide.md`, both extension `*.opt-in.md` files, and the `common/session-continuity.md` welcome prompt.
- **Per-unit artifact loading scoped to unit directories** on session resume (upstream #276). Touches `common/session-continuity.md`.
- **OpenAI Codex** added to the IDE list in `core-workflow.md` (upstream #153). The `.kiro/aws-aidlc-rule-details/` rule-loading path is unchanged, so all agent `resources` references remain valid.
- **New opt-in extension: `extensions/resiliency/baseline/`** (`resiliency-baseline.md` + `resiliency-baseline.opt-in.md`) (upstream #265). Follows the same opt-in mechanism the `aidlc-lead-engineer` already scans for during Requirements Analysis. Not auto-enforced; the user opts in per feature.

### Reconciliation notes (overlap with this repo's home-grown additions)

v1.0.0 also ships standalone tools and an extension that overlap with capabilities this repo already built independently. These were reviewed during the upgrade and **intentionally not adopted** as part of the methodology vendoring (they live under the upstream `scripts/` tree, outside the vendored rule-details):

| Upstream v1.0.0 addition | This repo's existing equivalent | Decision |
|---|---|---|
| `aidlc-traceability` matrix tool (#236) | `requirements-verifier` agent (traceability gate) | Keep home-grown; revisit if the upstream tool proves stronger. |
| `aidlc-designreview` tool + arch-pattern library (#152) | `architect` + `tech-reviewer` agents | Keep home-grown. |
| `resiliency` extension (#265) | `nfr-baseline.md` (NFR-REL rules) | Extension vendored (it is part of the rule set) but **left opt-in**; NFR-REL in `nfr-baseline.md` remains the always-on baseline. Reconcile the two if resiliency is ever opted into a feature. |
| `AGENTS.md` cross-agent guidance (#198) | `.kiro/steering/` files | Not adopted; steering covers this. |

Upstream also added "AIDLC v2 alpha" support (#284), signalling a larger v2 is in progress; v1.0.0 is a stabilisation milestone.

## 0.1.8 — 2026-04-20

- **Source**: [awslabs/aidlc-workflows v0.1.8](https://github.com/awslabs/aidlc-workflows/releases/tag/v0.1.8)
- **Installed**: 2026-05 (this session)
- **Local deviations**: none — exact copy of the tagged release

### Changes from previous upstream

v0.1.8 contains the following changes from v0.1.7 (per upstream CHANGELOG):

- Small text corrections in `core-workflow.md` and `inception/requirements-analysis.md`
- Added markdownlint configuration for rule files
- No behavioural rule changes

## Divergence policy

If a local edit to any file under this directory is required:

1. Add a comment at the top of the affected file:
   `<!-- LOCAL DEVIATION FROM UPSTREAM vX.Y.Z: <reason> -->`
2. Record the deviation in this changelog under the current version heading
3. When upgrading to a new upstream version, reconcile the deviation explicitly — either reapply it or drop it

## Previous versions

- **0.1.8** — first install in this repo (2026-05), exact copy of upstream v0.1.8.
- **1.0.0** — upgraded 2026-06-17 (current).
