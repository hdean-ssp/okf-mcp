---
# This is the structured intake template. The intake structurer agent produces a
# filled copy of this from an ADO story; the BA who wrote the story reviews and
# approves it in a GitHub PR before AI-DLC inception consumes it.
#
# Two principles:
#   1. Every requirement is atomic, numbered, and individually testable. No prose hides a requirement.
#   2. Sample data carries explicit schema + units + edge cases + counter-examples. Schema wins over the sample.
ado_id: <ADO-ID>
title: <short title>
author: <ba-email>            # the BA who wrote the ADO story; required PR reviewer
intake_version: 1.0
status: draft                 # draft -> approved
created: <ISO-8601>
nfr_pins:                     # version-pin the NFR steering that applied, for audit reproducibility
  security: <version>
  reliability: <version>
  performance: <version>
  scalability: <version>
  code_quality: <version>
  observability: <version>
  data: <version>
---

# <ADO-ID> — <title>

## Source

[Link to ADO story]

## Background

Free prose context. **Contains no requirements.** Anything that is a requirement
goes in a numbered table below. The agent treats this section as context only.

---

## Design Constraints (already chosen by the team — not negotiable, not requirements)

These describe what the team has already decided, not what must be true of the behaviour.
Verified by a different evaluator than functional requirements.

| ID | Constraint | Source |
|----|------------|--------|
| DC-01 | <e.g. Runtime is API Gateway -> Step Functions -> Lambda> | <where stated> |

---

## Functional Requirements

Each row is atomic, testable, and uses MUST / SHOULD / MAY (RFC 2119).
Tag each as `explicit` (stated in source), `inferred` (implied — requires author confirmation),
or `from-comment` (added later in ADO comments).

### Explicit and from-comment

| ID | Requirement | Tag | Source phrase | Verification |
|----|-------------|-----|---------------|--------------|
| FR-01 | The system MUST ... | explicit | "<source phrase>" | Unit test |
| FR-02 | The system MUST ... | from-comment | "<comment phrase>" | Integration test |

### Inferred (requires author confirmation)

| ID | Requirement | Reasoning | Author decision |
|----|-------------|-----------|-----------------|
| FI-01 | The system MUST ... | <why the agent inferred this> | [ ] Accept  [ ] Reject  [ ] Modify |

---

## Non-Functional Requirements (auto-injected from steering — non-negotiable)

Author does not edit this section. Pulled from the version-pinned NFR steering.

| ID | Requirement | Steering source | Verification |
|----|-------------|-----------------|--------------|
| NFR-SEC-01 | All inputs validated server-side; no client-only checks | nfr-security §3 | SAST + integration test |
| NFR-PERF-01 | p95 latency < <target> at <load> | nfr-performance §1 | Load test in CI |
| NFR-REL-01 | <reliability rule> | nfr-reliability §2 | <test> |
| NFR-CQ-01 | Coverage >= <floor>% on changed lines; mutation score >= <floor>%; no new code smells | nfr-code-quality §1 | CI gate |

---

## Sample Data

For each input and output payload, declare the schema first. The schema is authoritative;
the sample is illustrative only.

### Input: <name>

#### Schema (authoritative)

| Field | Type | Required | Unit / Format | Notes |
|-------|------|----------|---------------|-------|
| <field> | <type> | yes/no | **<unit, e.g. cents NOT dollars>** | <constraint / semantics> |

#### Sample (illustrative, not authoritative)

```json
{ }
```

#### Edge cases (each row is a test the implementation MUST pass)

| Case | Expected behaviour |
|------|--------------------|
| <e.g. amount = 0> | Reject with 400 |
| <e.g. amount > max> | Reject with 422 |

#### Counter-examples (MUST be rejected)

| Bad input | Why |
|-----------|-----|
| `{ "amount": 15.00 }` | Float; expected integer cents |

### Output: <name>

(schema + sample, same shape)

---

## Open Questions (block construction until resolved)

Anything the agent had to guess at, or any conflict between description and acceptance
criteria, becomes a question the author must answer before construction starts.

| # | Question | Source |
|---|----------|--------|
| OQ-01 | <question> | <where the ambiguity came from> |

---

## Sign-off

- [ ] **Author** (<ba-email>): the explicit, accepted-inferred, and from-comment requirements
      capture my intent, and I have answered all open questions.

Approval is recorded via the GitHub PR review on this file. The PR approval is the
audit-grade attestation. Do not proceed to AI-DLC inception until this is approved
and all open questions are closed.
