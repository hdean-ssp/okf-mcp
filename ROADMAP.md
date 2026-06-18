# Roadmap

Production readiness plan for okf-mcp. Tracks hardening, reliability, and deployment work needed to move from alpha (0.2.x) to a stable 1.0 release suitable for shared team deployments.

Target users: teams running okf-mcp on a shared Linux server behind Kiro/Remote-SSH, where the MCP server is long-lived and handles concurrent agent requests against a single knowledge bundle.

---

## 0.3.0 — Input Safety & Observability

Guard against misbehaving or overzealous agents, and give operators visibility into what the server is doing.

- [ ] **Input validation limits** — enforce maximums on content size (1MB), tag count (50), tag length (100 chars), top_n (200), concept_id length (256 chars)
- [ ] **SQLite busy_timeout** — add `PRAGMA busy_timeout=5000` to prevent "database is locked" errors under concurrent tool calls
- [ ] **Structured logging** — configure log level via `--log-level` flag / `OKF_LOG_LEVEL` env var; log tool invocations, durations, and errors as parseable single-line messages to stderr
- [ ] **Configuration validation** — reject invalid config values (empty embedding_model, negative top_n, non-existent paths) at startup rather than deep in the call stack
- [ ] **Test coverage gate** — add pytest-cov, measure branch coverage, enforce ≥85% in CI

## 0.4.0 — Data Integrity & Resilience

Protect bundle data against crashes, disk issues, and unclean shutdowns.

- [ ] **Atomic file writes** — write concept files via temp-then-rename to prevent corruption on crash mid-write
- [ ] **Signal handling** — catch SIGTERM/SIGINT, flush WAL, close SQLite connections cleanly before exit
- [ ] **Startup integrity check** — run `PRAGMA integrity_check` on the index DB at server start; log a warning and trigger automatic full reindex if corrupt or zero-byte
- [ ] **Embedding timeout** — cap individual embedding calls at 30s to prevent the server from hanging on pathological input
- [ ] **Concurrency guard** — add an asyncio.Semaphore around embedding operations to limit parallel CPU load (default: 2 concurrent embeds)

## 0.5.0 — Type Safety & CI Hardening

Catch bugs at build time and extend the test matrix.

- [ ] **mypy strict** — add mypy to CI, resolve type errors across all source modules, add `py.typed` marker
- [ ] **Python 3.13 in test matrix** — verify compatibility before users report issues
- [ ] **Integration test** — one CI-only test that loads the real embedding model and does embed → upsert → search round-trip (validates fastembed + sqlite-vec interop)
- [ ] **Dependency lock file** — generate and commit a `requirements.lock` for reproducible server installs
- [ ] **Pin sqlite-vec tightly** — it's pre-1.0; minor versions have broken APIs before

## 0.6.0 — Deployment & Operations

Make it easy to deploy, monitor, and troubleshoot in production.

- [ ] **Dockerfile + compose** — slim Python image, volume mount for bundle directory, example docker-compose.yml
- [ ] **Health check mode** — `okf-mcp --health-check` that opens the DB, verifies integrity, and exits 0/1 (for systemd ExecStartPre / Docker HEALTHCHECK)
- [ ] **Operational metrics to stderr** — periodic (or on-demand via a tool) summary: uptime, query count, avg latency, index size, error count
- [ ] **systemd unit file example** — drop-in service file for teams running on bare metal

## 1.0.0 — Stable Release

API stability commitment. After this, tool signatures and config format don't change without a major version bump.

- [ ] **CHANGELOG.md** — document all breaking changes, new features, and fixes from 0.2 onward
- [ ] **API stability guarantee** — MCP tool parameter names/types frozen; additive changes only in 1.x
- [ ] **Multi-process safety docs** — clearly document behavior when two server instances share a bundle (reads safe, concurrent writes to same concept are last-write-wins)
- [ ] **Minimum Python 3.11** — drop 3.10 (EOL October 2026) to use tomllib, ExceptionGroup, and newer typing features
- [ ] **PyPI publish workflow** — CI job that builds wheel and publishes on git tag push
- [ ] **Bundle export** — `okf export --format tar` for snapshotting (the markdown files are the source of truth, but users want a one-command backup)

---

## Out of Scope

These are explicitly not planned for 1.0:

- Multi-bundle federation (query across bundles) — revisit post-1.0 if demand exists
- Authentication/authorization layer — okf-mcp trusts the MCP client; access control belongs at the SSH/network layer
- Web UI — the interface is CLI + MCP tools consumed by agents
- Custom embedding models beyond fastembed — the current model (bge-small-en-v1.5) balances quality and resource usage well for typical bundle sizes
