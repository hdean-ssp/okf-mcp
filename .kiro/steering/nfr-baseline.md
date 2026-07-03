---
inclusion: always
nfr_version: 1.0.0
---

# Non-Functional Requirements Baseline

These are non-negotiable quality requirements auto-injected into every piece of work. The `requirements-analyst` cites them in the NFR section of each intake doc; the `requirements-verifier` checks the mechanically-verifiable ones; the `definition-of-done` enforces the thresholds. They are stack-agnostic — the right technology is chosen per requirement by the architect agent, but these properties hold regardless of stack.

Security NFRs live in `security-baseline.md` (cited as NFR-SEC-*). Code-quality NFRs live in `definition-of-done.md` and `coding-standards.md` (cited as NFR-CQ-*). This file covers reliability, scalability, performance, observability, and data.

Version-pin this file in each feature's intake frontmatter (`nfr_pins`) so an audit can reproduce the exact ruleset that applied.

## Reliability (NFR-REL)

- **NFR-REL-01** — External calls MUST have explicit timeouts and MUST handle 4xx/5xx responses; no unbounded waits.
- **NFR-REL-02** — Operations that can be retried MUST be idempotent on a client-supplied request/correlation ID (same ID returns the original result, no duplicate side effect).
- **NFR-REL-03** — A multi-step write that must not partially apply MUST be atomic, or compensate on failure; no orphaned state.
- **NFR-REL-04** — Transient failures of dependencies SHOULD be retried with backoff; repeated failure MUST surface, not hang.
- **NFR-REL-05** — The service MUST expose health and readiness checks so the platform can detect and replace unhealthy instances.

## Scalability (NFR-SCAL)

- **NFR-SCAL-01** — Compute MUST be stateless; no in-process session or request state that prevents horizontal scaling. Shared state goes to a backing service.
- **NFR-SCAL-02** — Backing services (DB, cache, queue) MUST be accessed as attached resources via configuration, not hardcoded.
- **NFR-SCAL-03** — List/query endpoints MUST be bounded (pagination or explicit limits); no unbounded result sets.
- **NFR-SCAL-04** — Long-running or bulk work MUST be offloaded to a job/queue, not run inline in a request handler.

## Performance (NFR-PERF)

- **NFR-PERF-01** — Each feature MUST declare a latency target (e.g. p95 < 200ms at a stated load) in its requirements; where unstated, the analyst raises it as an open question.
- **NFR-PERF-02** — Synchronous request paths MUST respect any hard platform ceiling (e.g. gateway timeout); work that cannot fit goes async.
- **NFR-PERF-03** — Database access MUST avoid N+1 patterns; queries on filtered/sorted columns MUST be index-backed.
- **NFR-PERF-04** — Performance-sensitive requirements SHOULD have a load/perf test that proves the target.

## Observability (NFR-OBS)

- **NFR-OBS-01** — Every request MUST carry a correlation/trace ID, propagated to downstream calls and included in logs.
- **NFR-OBS-02** — Logs MUST be structured (machine-parseable), with consistent levels; no secrets or PII beyond an account/correlation ID (see NFR-SEC and NFR-DATA).
- **NFR-OBS-03** — Key operations MUST emit metrics (rate, errors, duration) so SLOs can be measured.
- **NFR-OBS-04** — Errors MUST be logged with enough context to diagnose without reproducing locally.

## Data (NFR-DATA)

- **NFR-DATA-01** — Schema changes MUST be expressed as versioned migrations; no ad hoc schema edits.
- **NFR-DATA-02** — Migrations that touch existing data MUST be forward-compatible with the previous running version (safe rollback), or ship as a two-phase change.
- **NFR-DATA-03** — PII MUST be classified, minimised to what the feature needs, and kept out of logs (cross-references NFR-SEC and NFR-OBS-02).
- **NFR-DATA-04** — Data retention and purge MUST follow the applicable policy per scheme/jurisdiction; where unstated, the analyst raises it as an open question.
- **NFR-DATA-05** — Sample/test data MUST NOT be real customer data.

## How these are applied

| Stage | Use of this file |
|---|---|
| Intake (`requirements-analyst`) | Inject the applicable NFR IDs into the intake doc's NFR table; raise open questions where a target (latency, retention) is unstated |
| Verification (`requirements-verifier`) | Evidence the mechanically-checkable NFRs (idempotency, validation, pagination, structured logs, migrations) with a test; mark genuinely non-mechanical ones (e.g. availability SLO) as not-mechanically-verifiable-here |
| Definition of Done | Enforce the thresholds (DOD-13 covers NFR compliance, version-pinned) |

A waiver of any NFR requires a human-signed ADR, as per `definition-of-done.md`.
