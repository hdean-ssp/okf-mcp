---
inclusion: manual
---

# Performance Review

Manually invoked via `/performance-review` for performance audits.

## Scope

Perform a focused performance review of the code in context.

## API / Backend Performance

- Response time: p50, p95, p99 targets met?
- N+1 queries present?
- Missing indexes on common query patterns?
- Unbounded queries (missing LIMIT)?
- Memory-unbounded operations (loading entire tables into memory)?
- Synchronous calls that should be async/streaming?
- Sequential external calls that could be parallel?
- Caching opportunities missed?

## Database Performance

- Slow queries identified (> 50ms)?
- Indexes present for WHERE, ORDER BY, JOIN columns?
- Over-indexed tables (write cost)?
- Table bloat from missed VACUUM?
- Connection pooling configured?
- Read replica utilisation?

## Frontend Performance

- Bundle size within budget?
- Unnecessary re-renders?
- Images unoptimised?
- Heavy computation on the main thread?
- Core Web Vitals: LCP, FID, CLS within targets?
- Network waterfalls avoidable?

## Infrastructure Performance

- Resource requests/limits appropriate (not over-provisioned, not throttled)?
- Horizontal scaling configured (HPA)?
- Pod disruption budgets set?
- Node affinity / anti-affinity where relevant?

## Report Format

Structured report:
1. **Summary** — current state, target state, gap
2. **Findings by impact** — High, Medium, Low
3. **For each finding**: metric, observed value, target, remediation, estimated impact
4. **Quick wins** — changes with large impact and low effort
5. **Longer-term recommendations**
