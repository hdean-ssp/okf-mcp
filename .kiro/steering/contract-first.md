---
inclusion: fileMatch
fileMatchPattern: "**/openapi*.yaml,**/openapi*.yml,**/openapi*.json,**/*.proto,**/contracts/**,**/pact/**,**/*.contract.*"
---

# Contract-First Development

When a pod runs multiple agent crews in parallel against one product, the thing that stops them colliding at the seams is a **frozen interface contract**. This rule applies whenever you touch a contract artefact.

## Where contracts live

A contract is the agreed interface between units of work:

- **APIs:** an OpenAPI document (`openapi.yaml`/`.json`) or `.proto` files
- **UIs:** component contracts and the API client interface (typed schemas the UI codes against)
- **Services:** Pact files or schema contracts under `contracts/`

Keep them in a single, discoverable location (`contracts/` or `api/openapi.yaml`). They are the source of truth for the seams between units.

## The freeze rule

During an iteration the contract is **frozen**. Units are built against it independently — a unit that owns endpoint A can build and test against a mock of endpoint B without waiting for B to exist. That is what makes parallel construction safe.

- Build to the contract, not to another unit's implementation.
- Mock or stub the parts of the contract another unit owns.
- Do **not** change the frozen contract to make your unit's code easier.

## Changing a frozen contract

Sometimes the contract genuinely must change mid-iteration. That is a deliberate, gated act, not a silent edit:

1. Raise it with the iteration's **integration steward** (the rotating pod role).
2. The steward decides and, if agreed, the change is made once, centrally, and the contract re-frozen.
3. The PR that changes a contract artefact must carry the `contract-change-approved` label (applied by the steward). The contract gate blocks contract changes without it.
4. All affected units re-sync to the new contract.

## Disjoint units

Pair this with the disjoint-units rule: no two concurrent units write the same files. Partition APIs by resource/bounded-context (each owns its handlers, models, tests) and UIs by feature/route (with a shared design-system contract no crew modifies mid-flight). See `docs/AI-FIRST-DELIVERY-MODEL.md` §7.

## Verification

The `contract-gate.yml` workflow enforces this:

- Contract tests must pass (DOD-12).
- A PR that edits a frozen contract fails unless it carries `contract-change-approved`.

This is how automation holds the contract line instead of relying on seniority — which matters because pods are flat peers.
