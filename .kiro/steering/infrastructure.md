---
inclusion: fileMatch
fileMatchPattern: "**/terraform/**,**/*.tf,**/cdk/**,**/helm/**,**/k8s/**,**/*.yaml,**/*.yml,**/Dockerfile*"
---

# Infrastructure as Code Standards

Loaded when working on Terraform, CDK, Helm, Kubernetes manifests, or Dockerfiles.

**Compute platform by cloud (ADR-004):** on **AWS** (production standard) services run on **Amazon ECS on Fargate**, defined as task definitions via Terraform or CDK — no Kubernetes. On **Azure** (and hybrid/on-prem) services run on **Kubernetes (AKS)** — manifests, Kustomize, Helm, Istio. The ECS section below applies to AWS; the Kubernetes/Helm sections apply to the Azure/hybrid path.

## Terraform

- Use modules from `terraform-aws-modules/*` where they exist — don't reinvent
- State in S3 with DynamoDB lock table (AWS) or Azure Blob with lease locking (Azure)
- One state file per environment (dev, test, prod) and per significant component
- Never commit `.tfstate` — ever
- Version constraints pinned: `required_version = ">= 1.6.0"`, providers pinned
- Variables typed, with descriptions and sensible defaults
- Outputs declared for anything another stack consumes
- `terraform fmt` and `terraform validate` enforced in CI

## Dockerfiles

- Multi-stage builds: build stage + slim runtime stage
- Use official, minimal base images (`node:22-alpine`, `python:3.12-slim`)
- Never run as root; add a non-root user
- `COPY` only what you need — use `.dockerignore`
- Pin base image versions; don't use `latest`
- Healthcheck declared
- Images scanned for vulnerabilities in CI

## ECS on Fargate (AWS — production standard)

- Define services as **task definitions** + **ECS services** in Terraform or CDK; one service per application component
- **Fargate launch type** — no EC2 nodes; set CPU/memory per task and right-size from CloudWatch
- Separate the task **execution role** (pull image, read secrets) from the task **role** (app AWS access); least-privilege; no static credentials
- Inject config/secrets via the task definition `secrets` block from Secrets Manager / SSM — never bake into the image
- **ECS Service Auto Scaling** (target-tracking on CPU/memory/ALB request count); set sensible min/max
- Health checks: container `healthCheck` + ALB target-group health check; tune `deregistration_delay`
- Deployments: **CodeDeploy blue/green** or rolling with the ECS **deployment circuit breaker** (auto rollback)
- Service-to-service via **ECS Service Connect**; restrict with **security groups** (default deny)
- Logging via `awslogs` / FireLens to CloudWatch; tracing via an ADOT sidecar to X-Ray

## Kubernetes Manifests (Azure / hybrid)

- Use Kustomize for environment overlays (base + overlays/dev, overlays/test, overlays/prod)
- Resource requests AND limits on every container
- Liveness and readiness probes configured
- `imagePullPolicy: Always` only when tag is mutable (`latest`); otherwise `IfNotPresent`
- NetworkPolicies restrict traffic by default
- PodSecurityStandards enforced (`restricted` or `baseline`)
- Istio STRICT mTLS in dev — Jobs need sidecar injection, not `inject:false`
- Deployments: `holdApplicationUntilProxyStarts: true`, `preStop` hook, `terminationGracePeriodSeconds: 90`
- Probes: set `timeoutSeconds` appropriately (default 1s is often too low)

## Helm Charts (Azure / hybrid)

- Values clearly documented with comments
- Sensible defaults that work in dev without customisation
- Secrets never in values files committed to Git
- Use `helm lint` and `helm template` in CI

## CI/CD

- Progressive deployment: dev on push, test on schedule, prod on manual approval
- Kubernetes (Azure/hybrid): CI builds artefacts; ArgoCD/Flux deploys them (CI never touches the cluster). AWS (ECS Fargate): CI deploys via CodeDeploy / CDK / Terraform to the ECS service
- Image tags are immutable — SHA-based, not `latest`
- Every production deploy has a rollback plan

## Networking

- Default deny, explicit allow
- Only expose what must be exposed externally
- Internal services: ECS Service Connect + security groups (AWS); ClusterIP + Istio mTLS (Kubernetes)
- External ingress via cloud load balancer + managed certificate
