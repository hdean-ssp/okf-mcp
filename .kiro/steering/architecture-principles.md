---
inclusion: always
---

# Architecture Principles

These are the non-negotiable architectural commitments. Every design decision must align with them, or the design needs an ADR explaining why we're deviating.

## Compute Platform — per cloud

Every service is containerised. The orchestration platform depends on the target cloud (recorded in ADR-004):

- **AWS (production standard): Amazon ECS on Fargate.** Serverless containers — no nodes or control plane to manage. Use ECS services, task definitions, Service Connect for service-to-service, ALB for ingress, ECS Service Auto Scaling.
- **Azure: Azure Kubernetes Service (AKS).** Kubernetes-native patterns: Services, Ingress, NetworkPolicies, ConfigMaps, Secrets; managed Istio add-on; HPA.
- **Portable / on-prem: any CNCF-conformant Kubernetes** (see `templates/architecture/hybrid.md`).

Common to both: design stateless where possible; horizontal scaling (ECS Service Auto Scaling on AWS, HPA on Kubernetes); no long-running processes outside the orchestrator. Deviating from the per-cloud default (e.g. EKS on AWS) requires an ADR.

## Cloud-Native Defaults

- **Managed services over self-hosted** for databases, queues, secrets, logs
- **Stateless compute, stateful storage** — state lives in managed backing services
- **Infrastructure as Code** — no manual console changes; Terraform or CDK
- **GitOps / CD deployment** — Azure/hybrid: ArgoCD or Flux handles cluster state (CI produces artefacts only, never touches the cluster). AWS: CI deploys ECS services directly via CodeDeploy / CDK / Terraform (no separate GitOps agent needed).
- **Observability from day one** — metrics, logs, traces on every service

## Service Design

- Microservices only when they earn their complexity (separate team, separate lifecycle, separate scale)
- Each service owns its data; no cross-service database access
- Service-to-service communication encrypted and authenticated — ECS Service Connect on AWS, Istio mTLS on AKS, or authenticated API
- Events over sync calls where possible (event-driven decoupling)
- Idempotent operations by default; clients may retry

## Data

- PostgreSQL is the default relational database
- One database per service (logical or physical)
- Migrations in the repo, run through CI, never manually
- No ORMs that hide SQL entirely — prefer query builders
- Read replicas for heavy reporting workloads

## Security

- Zero-trust networking — assume the network is hostile
- All traffic encrypted in transit (TLS 1.2+)
- All data encrypted at rest
- Secrets in AWS Secrets Manager / Azure Key Vault, injected at runtime
- Authentication via OIDC (Keycloak or managed provider)
- Authorization via OPA or equivalent policy engine for non-trivial cases
- Least privilege on every IAM role, every service account

## Anti-Patterns — Do Not Do

- Shared mutable state between services
- Direct database access from another service's code
- "Just this once" manual changes to production
- Config via environment variables with hundreds of keys — use structured config
- Long-running synchronous chains of service calls (use events, orchestration)
- Caching without explicit invalidation strategy
- Silently retrying operations that aren't idempotent

## When Making Architectural Decisions

- Favour boring technology where the problem is solved
- Use cloud-native primitives before building custom
- Prefer managed services unless there's a specific reason not to
- Write an ADR for any decision future engineers might question
