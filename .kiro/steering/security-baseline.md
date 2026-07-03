---
inclusion: always
---

# Security Baseline

Every service inherits these security requirements. They're enforced by hooks, CI checks, and reviews.

## Authentication

- All external endpoints require authentication (no anonymous access unless explicitly designed for public)
- JWT tokens for service-to-service auth; short-lived (≤15 min)
- Refresh tokens where long-lived sessions are needed, with rotation
- Auth failures return 401 with no information leakage (no "user not found" vs "wrong password")

## Authorization

- Authorisation checks at every endpoint — never trust the caller's claims
- RBAC for simple cases; OPA/policy engine for complex cases
- Resource-scoped permissions (this user can access this resource, not all resources of this type)

## Input Validation

- Every input is validated at the boundary
- Use schema validation (Zod, Joi, Pydantic) rather than ad-hoc checks
- Reject unknown fields; do not silently accept
- Sanitise strings that will be rendered as HTML
- Parameterised queries only; no string concatenation in SQL

## Rate Limiting

- Every public endpoint has a rate limit
- Expensive endpoints (reports, exports, search): 3-10 requests/hour per user
- Standard endpoints: 60-300 requests/minute per user
- Use Redis for distributed rate limiting; fail open only with explicit sign-off

## Secrets

- No secrets in code, config files, or environment variables committed to Git
- Secrets live in AWS Secrets Manager or Azure Key Vault
- Rotated at least every 90 days
- Access audited; use IAM roles, not long-lived credentials
- Developers get read access via their IAM Identity Center role, not shared credentials

## Data Protection

- PII encrypted at rest (field-level where the data model allows)
- PII never logged (use correlation IDs, not user IDs, in logs)
- PII never in URL query strings
- Data retention policies enforced — don't keep what you don't need
- Data exports rate-limited and audited

## Dependencies

- OSS licence scan on every PR (FOSSA or equivalent)
- Vulnerability scan on every PR (Snyk or equivalent)
- Deny copyleft (GPL, AGPL) unless explicitly approved
- Pin versions in lockfiles; review dependency updates, don't auto-merge

## Logging and Observability

- Log authentication events (success and failure)
- Log authorization failures
- Log access to sensitive data
- Alert on patterns (brute force, anomalous access, privilege escalation attempts)
- Logs retained per regulatory requirements, not less than 90 days

## For AI-Generated Code

- Every PR scanned by headless Kiro security agent before human review
- FOSSA check runs before merge (blocks on licence contamination)
- Secret detection on every commit (pre-commit hook + CI check)
- Enterprise Kiro tier required for IP indemnity

## Incident Response

- Security incidents have a separate escalation path (not just the normal on-call)
- If an incident involves potential data exposure, notify security team immediately
- Document the incident, the response, and the remediation
- Root cause analysis for every security incident, published to the team
