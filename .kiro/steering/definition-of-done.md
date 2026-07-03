---
inclusion: always
---

# Definition of Done (machine-checkable)

This is the non-negotiable quality bar every unit of work must clear before a human reviews it. It operationalises the guardrail catalogue in `docs/AI-FIRST-DELIVERY-MODEL.md` §6. The `requirements-verifier` and the gate workflows enforce these thresholds; the construction crew (developer, test-engineer) must meet them; humans only see work that has already passed.

These thresholds are **stack-agnostic**. The numbers are universal. The *tool* that measures each one is detected per project (Jest/Vitest/pytest/xUnit/go test/cargo, SonarQube/built-in linters, etc.). If a project cannot measure a given threshold, that is itself a blocking gap to resolve, not a reason to skip the check.

A unit is **not done** until every blocking item below is green or has a recorded waiver (see Waivers).

## Blocking thresholds

| # | Check | Threshold | Blocks if | Measured by (detect per project) |
|---|---|---|---|---|
| DOD-1 | Build | Compiles / builds clean | any build error | project build command |
| DOD-2 | Lint / static analysis | zero new errors | any new lint error | project linter |
| DOD-3 | Unit + integration tests | 100% pass | any test fails | detected test runner |
| DOD-4 | Requirement traceability | every requirement ID evidenced (code location + passing, asserting test) | any MUST requirement unevidenced or weakly evidenced | `requirements-verifier` |
| DOD-5 | Line coverage on changed code | >= 80% | below 80% on changed lines | coverage tool |
| DOD-6 | Mutation score on changed code | >= 70% | below 70%, where a mutation tool exists for the stack | mutation tool (e.g. Stryker, mutmut, PIT, go-mutesting) |
| DOD-7 | Edge cases & counter-examples | every intake edge case and counter-example has a test | any uncovered | `requirements-verifier` |
| DOD-8 | Cyclomatic complexity | <= 15 per function/method | any new function exceeds | complexity analyser |
| DOD-9 | Security — SAST | zero critical/high findings | any critical or high | SAST tool |
| DOD-10 | Security — dependencies (CVE) | zero critical/high CVEs | any critical or high | SCA / dependency scanner |
| DOD-11 | Secrets | zero secrets in diff or history | any secret detected | secret scanner |
| DOD-12 | Contract | frozen API/component contract honoured | any contract test fails | contract tests |
| DOD-13 | NFR steering | applicable NFR rules satisfied; version pinned in spec frontmatter | any mechanically-checkable NFR violated | per NFR rule |
| DOD-14 | No protected-path edits | `.github/workflows/*`, IaC, policies, `SECURITY.md` unchanged unless explicitly authorised | unauthorised edit | path check |

## Severity policy for security findings

| Severity | Policy |
|---|---|
| Critical / High | **Blocks.** Must be fixed, or waived via a human-signed ADR (DOD waiver). |
| Medium | Does not block, but must be logged as a tracked follow-up issue. |
| Low / Informational | Logged in the report; no action required. |

Security and contract findings **cannot be self-dismissed by an agent**. Suppression requires a human-signed waiver.

## When a stack cannot measure a threshold

If the project's language/ecosystem has no available tool for a check (most often DOD-6 mutation testing or DOD-8 complexity):

1. The verifier records the threshold as `not-measurable: <reason>` rather than silently passing it.
2. This is surfaced as a judgement item for the human, not a silent skip.
3. Where a reasonable tool exists but is not yet wired, that is a tracked gap, not a waiver.

Never report a threshold as passed when it was not actually measured.

## Per-unit Definition of Done checklist

A unit is done when all of the following hold:

- [ ] All requirement IDs from the intake document are evidenced (DOD-4)
- [ ] Every intake edge case and counter-example has a passing test (DOD-7)
- [ ] Build, lint, and the full test suite are green (DOD-1, 2, 3)
- [ ] Coverage on changed lines >= 80%; mutation score >= 70% where measurable (DOD-5, 6)
- [ ] No function over complexity 15 introduced (DOD-8)
- [ ] No critical/high SAST, no critical/high CVE, no secrets (DOD-9, 10, 11)
- [ ] Contract tests pass against the frozen contract (DOD-12)
- [ ] Applicable NFR rules satisfied and version-pinned (DOD-13)
- [ ] No unauthorised edits to protected paths (DOD-14)
- [ ] A verification report exists and its verdict is PASS

Only when this checklist is complete does the work reach the human gate, where the human reviews **judgement items only** (does this satisfy intent, is the design tradeoff right) on top of the green wall above.

## Waivers

A blocking item may be waived only by a human, never by an agent, and only with a recorded rationale:

1. Create an ADR under `docs/adrs/` titled `waiver: <DOD-NN> for <unit>`
2. State which threshold is waived, why, the risk accepted, and an expiry or follow-up
3. The waiver is approved by the role that owns that guardrail (Security Lead for DOD-9/10/11, Tech Lead for the rest)
4. The verification report links the waiver; the audit trail records who approved it and when

A waiver is an explicit, attributable, time-bound exception. It is not a way to routinely skip the bar; repeated waivers of the same threshold signal the threshold or the tooling needs revisiting.

## Tuning

These numbers are the baseline. They are tuned with evidence, not feel:

- If a threshold blocks consistently for good work, it may be too strict; revisit with data.
- If defects escape past a green gate, the bar is too low or a guardrail is missing; tighten.
- Threshold changes go through the same review as any steering change and are recorded.
