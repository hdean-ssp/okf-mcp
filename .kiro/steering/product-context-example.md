---
inclusion: manual
---

# Product Context — Example (InsureFlow)

> **This is an example.** Copy the structure into `product-context.md` and replace with your own product's details. This file is set to `inclusion: manual` so it doesn't load into agent sessions — it's reference only.

---

## Product overview

InsureFlow is a B2B insurance policy administration platform for mid-market commercial insurers (50–500 employees). Customers replace legacy mainframe-based policy systems with a modern cloud-native workflow covering quote, bind, issue, endorse, renew, and claim notification. Users are underwriters, brokers (via a portal), claims handlers, and finance teams.

Annual contract value: £50K–£500K per customer. 38 live customers across UK and Ireland.

## Repositories and services

- `insureflow-api` — .NET 8 REST API. Owns the policy database. Deployed as a container on AKS.
- `insureflow-web` — React 18 SPA. Calls insureflow-api. Hosted on Azure Static Web Apps.
- `insureflow-portal` — Next.js broker-facing portal. Read-heavy, calls insureflow-api. Hosted on Vercel.
- `insureflow-events` — .NET 8 worker service. Consumes events from Azure Service Bus, writes to the reporting database and triggers downstream integrations (bordereaux, regulatory reporting).
- `insureflow-docs` — Internal documentation site (Docusaurus). Not part of the runtime.

```
Web SPA ──→ API ──→ Policy DB (Azure SQL)
Portal  ──→ API        │
                        ├──→ Service Bus ──→ Events Worker ──→ Reporting DB
                        └──→ Blob Storage (documents)
```

## Architecture at a glance

```text
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  React SPA  │────▶│             │────▶│  Azure SQL       │
│  (underwriters)   │  .NET 8 API │     │  (policy store)  │
└─────────────┘     │             │     └──────────────────┘
                    │  AKS cluster │
┌─────────────┐     │             │     ┌──────────────────┐
│  Next.js    │────▶│             │────▶│  Azure Blob      │
│  (brokers)  │     └──────┬──────┘     │  (documents)     │
└─────────────┘            │            └──────────────────┘
                           │
                    ┌──────▼──────┐     ┌──────────────────┐
                    │ Service Bus │────▶│  Events Worker   │
                    └─────────────┘     │  → Reporting DB  │
                                        │  → Bordereaux    │
                                        │  → FCA reports   │
                                        └──────────────────┘
```

## Core entities

| Entity | What it is | Key relationships |
|---|---|---|
| **Policy** | A contract between insurer and policyholder. Has a lifecycle: quoted → bound → issued → endorsed → renewed → lapsed/cancelled. | Belongs to Customer. Has many Endorsements, Claims, Documents. |
| **Quote** | A priced offer. Expires after 30 days. Can be revised up to 3 times before binding. | Belongs to Customer. Becomes a Policy on bind. |
| **Customer** | The insured party (a business, not an individual). Has a credit rating and risk profile. | Has many Policies, Quotes, Contacts. |
| **Endorsement** | A mid-term change to a live Policy (e.g., add a vehicle, change address, increase limit). Triggers re-rating. | Belongs to Policy. Creates a new premium transaction. |
| **Claim** | A notification that a loss event occurred. Tracked through FNOL → investigation → reserve → settlement → closed. | Belongs to Policy. Has many ClaimPayments. |
| **Premium** | The amount charged for coverage. Calculated per risk item, aggregated per policy. Stored in pence as integers. | Belongs to Policy or Endorsement. |
| **Document** | A generated or uploaded file (certificate, schedule, endorsement notice, claim form). Stored in Blob, metadata in SQL. | Belongs to Policy, Quote, or Claim. |
| **Broker** | An intermediary who places business on behalf of customers. Has a commission agreement. | Has many Customers. Accesses via the portal. |
| **Underwriter** | Internal user who assesses risk and approves quotes above authority limits. | Has an AuthorityLimit (max sum insured they can bind without referral). |
| **RiskItem** | A specific thing being insured (a vehicle, a property, a piece of equipment). Rated individually. | Belongs to Policy. Has many RiskFactors. |

## Business rules

These are non-negotiable. Code that violates them is a bug regardless of whether tests pass.

- **Quote expiry:** A Quote expires exactly 30 calendar days after creation (midnight UTC). Expired quotes cannot be bound. They can be revised (which creates a new Quote with a new 30-day window).
- **Authority limits:** An Underwriter can only bind a Quote if the total sum insured is within their AuthorityLimit. Above that, the quote enters `referred` status and requires a senior underwriter's approval.
- **Premium in pence:** All monetary values are stored as integers in minor currency units (pence for GBP, cents for EUR). Never use floating-point for money. Display formatting happens in the UI layer only.
- **No backdating:** Policy inception date cannot be in the past by more than 7 days. Endorsement effective dates cannot be before the policy inception date.
- **Endorsement re-rating:** Every endorsement triggers a full re-rate of the affected risk items. The premium difference (positive or negative) is recorded as a separate transaction. Never mutate the original premium record.
- **Claim reserves:** A claim reserve can be increased at any time but can only be decreased with a ClaimsManager-role approval. Reserves at £0 auto-close the claim.
- **Document immutability:** Once a document is issued (status = `issued`), it cannot be modified. Issue a replacement document instead. The original remains in the audit trail.
- **Broker commission:** Commission is calculated as a percentage of gross premium. The percentage is per-broker, per-product-line. Commission is earned on bind, not on quote.
- **GDPR right-to-erasure:** Customer PII (name, address, email, phone) can be erased. Transactional records (policies, claims, premiums) are retained with the customer name replaced by "Former customer [ID]". Documents containing PII are redacted, not deleted.
- **Regulatory hold:** If a policy is flagged `regulatory-hold` (FCA investigation, sanctions match), no changes can be made to it by any user except ComplianceOfficer role. The system must log every access attempt.

## Customer and user types

| User type | What they do | Permissions |
|---|---|---|
| **Underwriter** | Assess risk, price quotes, bind policies, approve endorsements | Full read/write on quotes and policies within their authority limit |
| **Senior Underwriter** | Same as Underwriter + approve referred quotes above standard authority | Elevated authority limit; can override referrals |
| **Claims Handler** | Register FNOL, investigate, set reserves, approve payments | Read/write on claims; read-only on policies |
| **Claims Manager** | Same as Claims Handler + approve reserve decreases and large payments | Elevated claims authority |
| **Finance User** | View premiums, commissions, bordereaux, reconciliation | Read-only on policies and claims; read/write on finance transactions |
| **Broker (portal)** | Submit quotes on behalf of customers, view their own book of business | Read/write on their own customers' quotes; read-only on issued policies; no access to other brokers' data |
| **System Admin** | User management, configuration, product setup | Full access except direct data modification (no SQL access) |
| **ComplianceOfficer** | Manage regulatory holds, sanctions screening, audit access | Can place/remove regulatory holds; read-only audit log access |

## Key workflows

### 1. Quote → Bind → Issue (the happy path, ~70% of volume)

Broker submits quote request via portal → Underwriter reviews risk → System calculates premium → Underwriter approves (or refers if above authority) → Broker accepts → System binds the policy → Documents generated (certificate, schedule) → Policy status = `issued`.

### 2. Mid-term endorsement

Customer requests a change (add vehicle, increase limit) → Underwriter creates endorsement → System re-rates affected risk items → Premium adjustment calculated → Underwriter approves → Endorsement applied → New documents issued → Finance records the premium transaction.

### 3. Renewal

60 days before expiry, system generates renewal invite → Underwriter reviews (re-rate, adjust terms) → Broker presented with renewal terms → Broker accepts or negotiates → On acceptance, new policy period created → Old policy lapses at expiry.

### 4. Claim notification (FNOL)

Claims Handler registers First Notification of Loss → System creates Claim record → Initial reserve set → Investigation begins → Reserve adjusted as information arrives → Settlement approved → Payment issued → Claim closed.

### 5. Bordereaux generation (monthly)

Events Worker aggregates all bound/endorsed/cancelled policies for the month → Generates bordereaux file per reinsurer → Uploads to SFTP → Logs confirmation → Finance reconciles.

## Common bug areas

| Area | Files | Typical bug | Fix pattern |
|---|---|---|---|
| **Premium calculation** | `InsureFlow.Api/Services/Rating/RatingEngine.cs` | Null risk factors, rounding errors, division by zero on zero-value rates | Validate all inputs before calculation; use `decimal` not `double`; round at the end, not per-step |
| **Quote expiry** | `InsureFlow.Api/Services/Quoting/QuoteService.cs` | Timezone issues — quote expires at wrong time for non-UTC customers | Always compare in UTC; store expiry as `DateTimeOffset`; never use `DateTime.Now` |
| **Authority referral** | `InsureFlow.Api/Services/Underwriting/AuthorityService.cs` | Sum insured calculated incorrectly when multiple risk items exist | Sum across all risk items, not just the first; include endorsement adjustments in the running total |
| **Document generation** | `InsureFlow.Api/Services/Documents/DocumentGenerator.cs` | Template merge fields missing when optional data is null | Always null-check merge field values; use empty string, never null; validate template exists before merge |
| **Endorsement re-rating** | `InsureFlow.Api/Services/Endorsements/EndorsementService.cs` | Original premium mutated instead of creating adjustment transaction | Never modify existing PremiumTransaction records; always create a new adjustment record with a reference to the endorsement |
| **Broker data isolation** | `InsureFlow.Api/Middleware/BrokerTenantFilter.cs` | Broker A can see Broker B's customers if the tenant filter is bypassed | Always apply tenant filter at the DbContext level (global query filter); never rely on controller-level checks alone |
| **Claim reserve decrease** | `InsureFlow.Api/Services/Claims/ReserveService.cs` | Reserve decreased without ClaimsManager approval | Check role before allowing decrease; throw `UnauthorizedAccessException` if role is insufficient |

## Constraints and non-negotiables

- **Never store money as floating-point.** Use `decimal` in C# and `DECIMAL(18,2)` in SQL. Display formatting is UI-only.
- **Never mutate historical records.** Policies, premiums, claims, documents — once issued, they're immutable. Create adjustments, replacements, or new versions instead.
- **Never call external payment/banking APIs from non-production environments** except with test credentials (prefix `test_`).
- **PII must never appear in log output.** Use the `[Redacted]` attribute on DTO properties containing names, addresses, emails, phone numbers.
- **All dates stored as UTC.** Display conversion happens in the UI layer based on user's timezone preference.
- **Broker isolation is non-negotiable.** A broker must never see another broker's data. This is enforced at the database query level (EF Core global query filter), not at the controller level.
- **FCA regulatory compliance:** Any change to rating logic, authority limits, or claims handling rules requires a compliance sign-off before deployment. The system logs all such changes.

## Vocabulary

| Term | Meaning in InsureFlow | Common confusion |
|---|---|---|
| **Bind** | The moment a quote becomes a live policy. Legal commitment begins. | Not the same as "issue" — binding happens first, document issuance follows. |
| **Endorse** | Make a mid-term change to a live policy. | Not "approve" — endorsing changes the policy terms, not just signing off. |
| **FNOL** | First Notification of Loss — the initial claim report. | Not the claim itself — FNOL creates the claim record. |
| **Bordereaux** | A periodic report sent to reinsurers listing all policies/claims in a period. | Plural of "bordereau". Always generated, never manually edited. |
| **Reserve** | The estimated cost of a claim (set aside for future payment). | Not a payment — reserves are estimates; payments are actuals. |
| **Refer** | Send a quote to a senior underwriter because it exceeds authority. | Not "reject" — referred quotes can still be approved. |
| **Lapse** | A policy that expired without renewal. | Not "cancelled" — lapse is passive (no action taken); cancellation is active. |
| **Inception** | The date a policy's coverage begins. | Not "creation date" — a policy can be created days before inception. |
| **Risk item** | A specific thing being insured (vehicle, property, equipment). | Not the same as "risk" in general — it's a concrete insurable object. |

## Testing patterns

- **xUnit** for all API tests. Test projects: `InsureFlow.Api.Tests`, `InsureFlow.Events.Tests`
- **WebApplicationFactory<Program>** for integration tests with in-memory SQL (SQLite provider)
- **Test data builders** in `InsureFlow.Api.Tests/Builders/` — never create entities with `new Entity()` directly; always use builders
- **Playwright** for end-to-end UI tests against a deployed dev environment (runs in CI nightly, not per-PR)
- **Contract tests** using Pact for the broker portal → API boundary
- **Naming convention:** `Should_<expected>_When_<condition>` (e.g., `Should_RejectBind_When_QuoteExpired`)
- **No test should depend on another test's state.** Each test creates its own data via builders and cleans up via transaction rollback.
- **Sensitive data in tests:** Use `Bogus` library for fake PII. Never use real customer data in test fixtures.

## References

- API reference: `docs/api/openapi.yaml` (OpenAPI 3.1 spec, auto-generated from code annotations)
- Database schema: `docs/database/schema.md` (entity-relationship diagram + table descriptions)
- Deployment: `docs/deployment/README.md` (AKS + Terraform + GitHub Actions)
- Architecture Decision Records: `docs/adrs/` (one per major decision)
- Glossary: `docs/glossary.md` (full term list beyond what's in this file)
- Regulatory requirements: `docs/compliance/fca-requirements.md`

---

*Last reviewed: May 2026. Owner: Engineering Lead. Review cadence: quarterly or when a major feature ships.*
