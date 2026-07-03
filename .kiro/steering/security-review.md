---
inclusion: manual
---

# Security Review

Manually invoked via `/security-review` when performing a security audit of code.

## Scope

When this is invoked, perform a thorough security review of the code in context. Focus on these areas:

## Authentication

- Is every endpoint authenticated unless explicitly public?
- Are auth failures returning generic messages (no username enumeration)?
- Are tokens short-lived?
- Is refresh token rotation implemented?
- Are logout flows invalidating server-side sessions where applicable?

## Authorization

- Is every action authorised (not just authenticated)?
- Are horizontal privilege escalation checks in place (user A can't access user B's data)?
- Are vertical privilege escalation checks in place (user can't perform admin actions)?
- Are permissions checked at every layer, not just the UI?

## Input Validation

- Is every input validated against a schema?
- Are string inputs escaped/encoded for their destination (HTML, SQL, shell, URL)?
- Are file uploads restricted by type, size, and content inspection?
- Are pagination limits enforced?

## Injection

- Are database queries parameterised (no string concatenation)?
- Are shell commands avoided, or sanitised if unavoidable?
- Are template injections prevented (auto-escape on)?
- Are HTTP headers that include user data validated (CRLF injection)?

## Data Exposure

- Does the response include only fields the user should see?
- Are error messages free of stack traces and internal details in production?
- Is PII logged anywhere?
- Are tokens or secrets logged anywhere?

## Rate Limiting and DoS

- Is every endpoint rate-limited?
- Are expensive endpoints more strictly limited?
- Are unbounded operations (loops, recursion, file reads) bounded?
- Are file uploads size-limited?

## Cryptography

- Is TLS enforced everywhere?
- Are weak algorithms absent (MD5, SHA1, DES)?
- Are secrets generated with a CSPRNG?
- Are password hashes using bcrypt/argon2 with appropriate work factor?

## Dependencies

- Are dependencies up to date?
- Are known vulnerabilities addressed?
- Are transitive dependencies audited?
- Are licences compatible with our product?

## Secrets Management

- Are secrets absent from code, config, and Git history?
- Are secrets rotated on a schedule?
- Are secrets accessed via managed service (Secrets Manager, Key Vault)?

## CORS and Headers

- Is CORS configured explicitly, with specific origins for authenticated endpoints?
- Are security headers set (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS)?
- Is `Strict-Transport-Security` set with long max-age?

## Report Format

Produce a structured report:
1. **Executive summary** — overall posture, critical findings
2. **Findings by severity** (Critical, High, Medium, Low, Informational)
3. **For each finding**: location, description, impact, remediation
4. **Recommendations** — prioritised actions

Flag anything Critical or High for immediate attention.
