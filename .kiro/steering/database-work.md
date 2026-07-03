---
inclusion: fileMatch
fileMatchPattern: "**/migrations/**,**/db/**,**/database/**,**/repositories/**,**/*.sql"
---

# Database Work Standards

Loaded when working on database code, migrations, or SQL. Applies on top of always-on standards.

## PostgreSQL as Default

- PostgreSQL 16+ for all relational workloads
- Use Aurora Postgres (AWS) or Azure Database for PostgreSQL Flexible Server in production
- Local development via Docker Compose with same major version
- Never use MySQL/MariaDB unless there's a legacy constraint — get an ADR if you do

## Schema Design

- Primary keys: UUID v7 (or ULID) — sortable, no collision, externally safe
- Timestamps: `created_at`, `updated_at`, both `timestamptz NOT NULL DEFAULT now()`
- Soft delete via `deleted_at timestamptz NULL` where deletion history matters; hard delete where it doesn't
- Foreign keys always declared and indexed
- NOT NULL by default; nullability is a deliberate choice
- Check constraints for enum-like values; consider proper enum types for long-lived constraints
- Default values where semantically meaningful

## Naming

- Tables: plural, snake_case (`customers`, `order_items`)
- Columns: snake_case (`customer_id`, `created_at`)
- Indexes: `idx_<table>_<columns>` (`idx_orders_customer_id`)
- Foreign keys: `fk_<table>_<referenced_table>` (`fk_orders_customers`)
- Constraints: `chk_<table>_<description>` (`chk_orders_total_positive`)

## Migrations

- Every schema change is a migration
- Migrations are forward-only in production; rollback via a new forward migration
- Test migrations in a PR namespace before merge
- Include the DOWN migration for local development only
- One concern per migration (don't mix adding a table and changing existing columns)
- Idempotent where possible (`CREATE TABLE IF NOT EXISTS`, but only in seed/setup scripts)

## Query Patterns

- Parameterised queries only — never string concatenation
- Use the ORM/query builder consistently within a service
- Explain-analyze slow queries before merging (p95 > 50ms)
- Add indexes for every query pattern; don't over-index (write cost)
- Avoid SELECT * in production code
- Batch operations where possible (INSERT many rows in one statement)

## Transactions

- Explicit transactions for multi-statement writes
- Keep transactions short; release locks quickly
- No long-running work inside a transaction (no HTTP calls, no user input)
- Use advisory locks for application-level mutual exclusion

## Performance

- Connection pooling always — never a new connection per request
- Pool size based on workload; default to `max(cpu * 4, 10)`
- Read replicas for reporting; don't mix OLTP and analytics on the primary
- Vacuum and analyze configured to run regularly
- Monitor slow query log; action anything consistently over 100ms

## Testing

- Integration tests use testcontainers (real PostgreSQL, fresh per test run)
- Seed data minimal; tests create what they need
- Migrations run automatically in the test setup
- Never test against production or shared staging databases

## Data Safety

- No destructive migrations without a review (DROP, ALTER COLUMN TYPE)
- Backups verified by regular restore tests
- Point-in-time recovery enabled in production
- Encryption at rest (AWS RDS encryption, always on)
- Row-level security considered for multi-tenant data
