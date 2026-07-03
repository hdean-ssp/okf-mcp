---
inclusion: always
---

# Coding Standards

These standards apply to every piece of code the agent generates. They are not optional.

## Naming

- **Services / repos:** kebab-case (`customer-api`, `order-service`)
- **Files:** kebab-case (`csv-export-service.ts`)
- **Classes / types:** PascalCase (`CsvExportService`, `OrderDto`)
- **Functions / variables:** camelCase (`exportOrders`, `customerId`)
- **Constants:** SCREAMING_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT_MS`)
- **API paths:** kebab-case, plural resources (`/customers/{id}/orders`, `/order-history`)
- **Environment variables:** SCREAMING_SNAKE_CASE (`DATABASE_URL`, `JWT_SECRET`)

## File Organisation

- One class or primary concept per file
- Tests co-located: `foo.ts` pairs with `foo.test.ts`
- Avoid `index.ts` re-export sprawl; keep imports explicit
- Folder structure by feature, not by file type

## Error Handling

- Every async operation uses try/catch; unhandled rejections are bugs
- Errors include a correlation ID via our logging context
- External API errors wrap in our `ApiError` class with status, code, message
- Never swallow errors silently — log at minimum, re-throw when needed
- Validation errors return 400 with clear messages
- Not found returns 404 with resource identifier
- Unauthorised returns 401; Forbidden returns 403 (know the difference)

## Logging

- Structured JSON logs only (no `console.log` in production paths)
- Every log entry includes: timestamp, correlation ID, service name, log level
- Log at the boundaries: incoming request, outgoing request, errors, key business events
- Do not log PII, secrets, tokens, or full request bodies that may contain them
- Use log levels correctly: ERROR (action required), WARN (unusual), INFO (business event), DEBUG (verbose)

## Testing

- Every public function has a unit test
- Integration tests for every API endpoint
- Test the behaviour, not the implementation
- Minimum 80% coverage on business logic
- No snapshot tests for component logic (too brittle)
- Mocks at the system boundary, not within your own code

## Documentation

- Every new API endpoint updates the OpenAPI spec in the same PR
- Public functions have JSDoc/docstring explaining purpose, parameters, return, errors
- README in every service/repo explains: purpose, how to run, how to test, architecture summary
- ADRs for any significant architectural decision

## Commits and PRs

- Conventional Commits format (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`)
- One logical change per PR — avoid "while I'm here" scope creep
- PR description: what changed, why, how tested, risks, screenshots if UI
- No draft PRs (suppresses CI) — use `[WIP]` prefix in title instead

## Rules the Agent Must Follow

- All code changes MUST include tests
- No hardcoded secrets — ever
- Protected paths (`.github/workflows/`, `ops/iac/`, `platform/policies/`, `SECURITY.md`) require maintainer review
- Max 3 self-heal attempts — escalate to a human after that
- Never commit `.env` files or credential material

## When Unsure

- Prefer readability over cleverness
- Prefer composition over inheritance
- Prefer explicit over implicit
- Ask for a human review rather than guess
