# Bob's Brain - Comprehensive DevOps Onboarding Analysis
**Date:** 2025-11-21
**Version:** 0.10.0
**Status:** Production-Ready
**Audience:** DevOps Engineers, Infrastructure Teams, Site Reliability Engineers

---

## Executive Summary

Bob's Brain is a production-grade **ADK (Agent Development Kit) agent department** deployed on Google Cloud's Vertex AI Agent Engine with strict architectural constraints (8 Hard Mode rules enforced via CI/CD). This analysis provides a complete operational guide for DevOps teams to operate and maintain the system independently.

**Key Characteristics:**
- Multi-agent architecture (bob orchestrator + 8 iam-* specialists)
- Vertex AI Agent Engine runtime (managed, no self-hosted runners)
- Cloud Run HTTP gateways (A2A protocol + Slack webhooks)
- Terraform infrastructure as code (3 environments: dev/staging/prod)
- Automated CI/CD with drift detection and ARV readiness gates
- GCS-based org-wide storage for audit results (LIVE1-GCS v0.9.0)
- 100% Python 3.12+ codebase with comprehensive test coverage

---

## Part 1: Initial Survey

### 1.1 Key Files & Configuration

**README.md** (`/home/jeremy/000-projects/iams/bobs-brain/README.md`)
- **Length:** 1,027 lines
- **Purpose:** Primary documentation for users and operators
- **Key Sections:**
  - Architecture overview (multi-agent model)
  - Hard Mode rules (R1-R8) explained
  - Quick start guide
  - Portfolio multi-repo audits
  - Deployment to Agent Engine
  - Troubleshooting guide
  - Testing framework details
- **Operator Relevance:** READ FIRST - comprehensive guide to system capabilities and deployment

**CLAUDE.md** (`/home/jeremy/000-projects/iams/bobs-brain/CLAUDE.md`)
- **Length:** 209 lines (slimmed from 42K chars)
- **Purpose:** AI agent working guide (recent refactor)
- **Key Sections:**
  - Repo context and architecture pattern
  - Hard Mode rules reference (R1-R8)
  - Architecture standards
  - Coding style guidelines
  - Documentation standards
  - Quick reference commands
  - Pointer to deeper docs in `000-docs/`
- **Operator Relevance:** Reference for understanding architectural constraints

**CHANGELOG.md** (`/home/jeremy/000-projects/iams/bobs-brain/CHANGELOG.md`)
- **Length:** 1,000+ lines with detailed versioning
- **Current Version:** 0.10.0 (released 2025-11-21)
- **Key Versions:**
  - **v0.10.0:** Contract-first prompt design, AgentCard alignment, 18 validation tests
  - **v0.9.0:** Org-wide storage (LIVE1-GCS), portfolio orchestration (PORT1-3), IAM templates
  - **v0.7.0+:** Hard Mode enforcement, Agent Engine deployment
- **Operator Relevance:** CRITICAL - track changes, understand feature flags, monitor upgrade path

**VERSION** (`/home/jeremy/000-projects/iams/bobs-brain/VERSION`)
- **Content:** `0.9.0` (source control version)
- **Note:** CHANGELOG shows 0.10.0 released, VERSION file may lag behind

### 1.2 Operational Documentation Structure

**000-docs/ Directory** (1,684 files, 12 MB)
- **Format:** Document Filing System v2.0: `NNN-CC-ABCD-description.md`
- **Categories:**
  - **PP** = Planning & Product
  - **AT** = Architecture & Technical
  - **AA** = After-Action Reports (AARs)
  - **DR** = Documentation & Reference
  - **OD** = Operations & Deployment
  - **RB** = Runbooks
  - **PM** = Project Management
  - **LS** = Logs & Status

**Key Operational Documents** (6767-series = canonical standards):
1. `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Architecture standard
2. `070-OD-RBOK-deployment-runbook.md` - Step-by-step deployment procedures
3. `069-OD-TELE-observability-telemetry-guide.md` - Monitoring & logging setup
4. `068-OD-CONF-github-secrets-configuration.md` - CI/CD authentication
5. `000-RB-OPS-adk-department-operations-runbook.md` - Daily operations
6. `000-DR-GUIDE-porting-iam-department-to-new-repo.md` - Template porting
7. `000-AT-ARCH-org-storage-architecture.md` - GCS knowledge hub design
8. `6767-113-AA-REPT-live1-gcs-implementation.md` - Storage implementation AAR

---

## Part 2: Infrastructure Analysis

### 2.1 Terraform Configuration

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/infra/terraform/`

**Core Terraform Files:**

| File | Purpose | Key Resources |
|------|---------|---------------|
| `main.tf` (51 lines) | Core configuration | API enablement, locals, resource imports |
| `variables.tf` (166 lines) | Input variables | Project, environment, machine types, org storage |
| `provider.tf` | GCP provider setup | Google Cloud authentication |
| `iam.tf` | Service accounts & IAM | Runtime SA, policy bindings, WIF setup |
| `agent_engine.tf` | Vertex AI Agent Engine | Agent resource definition, model config |
| `cloud_run.tf` | Cloud Run gateways | A2A gateway, Slack webhook services |
| `storage.tf` | Storage resources | GCS buckets, lifecycle policies |
| `knowledge_hub.tf` | Org knowledge hub | Org-wide audit storage (LIVE1) |
| `outputs.tf` | Output values | Deployed resource endpoints |

**Enabled Google Cloud APIs:**
```
- aiplatform.googleapis.com           # Vertex AI Agent Engine
- run.googleapis.com                  # Cloud Run
- compute.googleapis.com              # Compute Engine
- storage-api.googleapis.com          # Cloud Storage
- discoveryengine.googleapis.com      # Vertex AI Search
- iam.googleapis.com                  # IAM
- cloudresourcemanager.googleapis.com # Resource Manager
- serviceusage.googleapis.com         # Service Usage
```

**Environment-Specific Configuration:**

| Environment | Config File | Machine Type | Replicas | Storage |
|------------|-------------|--------------|----------|---------|
| Dev | `envs/dev.tfvars` | n1-standard-2 | 2 | Enabled (optional) |
| Staging | `envs/staging.tfvars` | n1-standard-4 | 3 | Enabled |
| Prod | `envs/prod.tfvars` | n1-standard-4 | 3-5 | Enabled |

**Key Terraform Variables:**
```hcl
# Core
project_id         = "your-gcp-project"
environment        = "dev|staging|prod"
region             = "us-central1"
app_name           = "bobs-brain"
app_version        = "0.10.0"

# Agent Engine
agent_docker_image = "gcr.io/project/agent:tag"
agent_machine_type = "n1-standard-4"
agent_max_replicas = 3

# Gateways
a2a_gateway_image     = "gcr.io/project/a2a-gateway:tag"
slack_webhook_image   = "gcr.io/project/slack-webhook:tag"
gateway_max_instances = 10

# Identity (R7)
agent_spiffe_id = "spiffe://intent.solutions/agent/bobs-brain/{env}/{region}/{version}"

# Org Storage (LIVE1)
org_storage_enabled     = true|false
org_storage_bucket_name = "intent-org-knowledge-hub-{env}"
```

### 2.2 Docker Configuration

**Dockerfile** (`/home/jeremy/000-projects/iams/bobs-brain/Dockerfile`)
- **Base Image:** `python:3.12-slim`
- **Working Directory:** `/app`
- **Key Features:**
  - Minimal system dependencies (lean image)
  - Layer-cached dependency installation
  - Unprivileged user recommended for production
  - Port: 8080 (Agent Engine managed)
  - Health check: Basic Python exit code check
  - Entry point: `python -m my_agent.agent`
- **Note:** Agent Engine manages container lifecycle; local testing only

**Docker Image Paths:**
```
Development:   gcr.io/{project-dev}/agent:0.10.0
Staging:       gcr.io/{project-staging}/agent:0.10.0
Production:    gcr.io/{project}/agent:0.10.0
```

### 2.3 Service Architecture

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/service/`

**A2A Gateway** (`service/a2a_gateway/`)
- **Purpose:** HTTP proxy to Agent Engine (A2A protocol endpoint)
- **Technology:** FastAPI + Uvicorn
- **Port:** 8080
- **Key Constraint:** No `Runner` imports (R3) - proxies only
- **Deployment:** Cloud Run, auto-scaled 0-10 instances
- **Authentication:** OpenID Connect with Workload Identity

**Slack Webhook** (`service/slack_webhook/`)
- **Purpose:** Slack events → Agent Engine routing
- **Technology:** Slack Bolt + FastAPI
- **Features:**
  - Message event handling
  - Signature verification (SLACK_SIGNING_SECRET)
  - A2A gateway routing (preferred) or direct Agent Engine calls
- **Deployment:** Cloud Run, separate service
- **Configuration:**
  - SLACK_BOT_TOKEN (OAuth token)
  - SLACK_SIGNING_SECRET (verification)
  - A2A_GATEWAY_URL (preferred routing)

**Architectural Pattern:**
```
Slack App → Webhook (R3 proxy) → A2A Gateway (R3 proxy) → Agent Engine (R2 runtime)
   OR
Slack App → Webhook → Agent Engine (R2 runtime) [direct, if A2A unavailable]
```

---

## Part 3: Architecture Deep Dive

### 3.1 Agent Architecture

**Multi-Tier Agent System:**

```
Tier 1: Bob (Global Orchestrator)
├── agents/bob/agent.py
├── A2A Card: .well-known/agent-card.json
└── Tools: shared tools (GitHub, Vertex Search, ADK docs)

Tier 2: iam-senior-adk-devops-lead (Foreman)
├── agents/iam-senior-adk-devops-lead/agent.py
├── Orchestrator: portfolio_orchestrator.py
├── Storage: storage_writer.py (GCS writes)
└── A2A Card: .well-known/agent-card.json

Tier 3: Specialists (8 total)
├── iam-adk (Pattern expert)
├── iam-issue (Drift detector)
├── iam-fix-plan (Fix strategy planner)
├── iam-fix-impl (Fix implementer)
├── iam-qa (Compliance QA)
├── iam-doc (Documentation)
├── iam-cleanup (Code cleanup)
└── iam-index (Knowledge curator)
```

**Agent Framework Stack:**

| Layer | Technology | Purpose | Location |
|-------|-----------|---------|----------|
| Framework | google-adk (≥0.1.0) | Agent implementation (R1) | agents/* |
| Protocol | a2a-sdk (≥0.3.0) | Agent-to-agent communication (A2A) | agents/*.py |
| Runtime | Vertex AI Agent Engine | Managed runtime (R2) | GCP (deployed) |
| Memory | VertexAiSessionService + VertexAiMemoryBankService | Dual memory (R5) | agents/bob/agent.py |
| Gateways | FastAPI + Uvicorn | HTTP proxies (R3) | service/* |

**Hard Mode Rules Enforced:**

| Rule | Constraint | Enforcement | Violation Impact |
|------|-----------|------------|------------------|
| R1 | ADK-only (no LangChain/CrewAI) | Drift detection (CI) | Build fails |
| R2 | Agent Engine runtime required | Terraform dependency | Can't deploy elsewhere |
| R3 | Cloud Run proxy only (no Runner in service/) | Code review + drift check | Build fails |
| R4 | CI-only deploys (no local gcloud) | GitHub Actions WIF | Manual deploys blocked |
| R5 | Dual memory wiring required | Agent code inspection | Tests fail |
| R6 | Single `000-docs/` folder | File structure validation | PR blocked |
| R7 | SPIFFE ID propagation | Environment validation | Deployment blocked |
| R8 | Drift detection first in CI | Job ordering | Build fails first |

### 3.2 Agent Modules & Entry Points

**Main Agents:**

```
agents/bob/
├── agent.py                 # Core agent initialization
├── tools/                   # Tool implementations
│   ├── github_client.py    # GitHub API client
│   ├── vertex_search.py    # Vertex AI Search tool
│   └── __init__.py
├── .well-known/
│   └── agent-card.json     # A2A discovery metadata
├── system-prompt.md         # System instructions
└── config/                  # Local configuration

agents/iam-senior-adk-devops-lead/
├── agent.py                # Foreman orchestrator
├── portfolio_orchestrator.py # Multi-repo coordination
├── storage_writer.py       # GCS writing (LIVE1)
├── orchestrator.py         # Legacy orchestrator
├── .well-known/
│   └── agent-card.json
├── system-prompt.md
└── config/

agents/iam_adk/
├── agent.py                # Specialist (pattern expert)
├── tools/                  # Specialist tools
├── .well-known/
│   └── agent-card.json
├── system-prompt.md        # Specialized instructions (v0.10.0: 120 lines, contract-first)
└── config/

agents/shared_contracts.py    # A2A contracts (dataclasses)
agents/shared_tools/          # Shared tool implementations
agents/iam_contracts.py       # Department-specific contracts
```

**Entry Points:**

```python
# Agent Engine entry point (R2)
python -m agents.bob.agent

# Portfolio orchestration (LIVE1)
python scripts/run_portfolio_swe.py --repos all --output results.json

# ARV checks (CI gate)
python scripts/check_arv_minimum.py

# Drift detection (CI gate first)
bash scripts/ci/check_nodrift.sh
```

### 3.3 Database & Storage Patterns

**Memory Wiring (R5 - Dual Memory):**

```python
# Session Memory (R5)
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(
    project_id=PROJECT_ID,
    location=LOCATION
)

# Memory Bank (R5)
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project_id=PROJECT_ID,
    location=LOCATION
)

# After-agent callback to persist (R5)
async def after_agent_callback(agent_response):
    await session_service.save_session(user_id, session_data)
    await memory_service.store_memory(interaction_data)
```

**Org-Wide Storage (LIVE1-GCS):**

```
gs://intent-org-knowledge-hub-{env}/
├── portfolio/
│   └── runs/
│       ├── {run_id}/
│       │   ├── summary.json           # Portfolio metrics
│       │   └── per-repo/
│       │       ├── repo-1.json        # Per-repo audit results
│       │       ├── repo-2.json
│       │       └── ...
```

**GCS Configuration:**

| Setting | Value | Purpose |
|---------|-------|---------|
| Location | US | Multi-region resilience |
| Storage Class | STANDARD | Hot access (portfolio writes) |
| Lifecycle | 90 days (per-repo), indefinite (summaries) | Cost optimization |
| Versioning | Enabled | Audit trail |
| Access | IAM service accounts | Workload Identity |

**API Integrations:**

| Service | SDK | Purpose | Rate Limit |
|---------|-----|---------|-----------|
| Vertex AI Agent Engine | google-cloud-aiplatform | Agent runtime | API quota |
| Vertex AI Search | google-cloud-discoveryengine | RAG/documentation | 10k req/day (free tier) |
| Cloud Logging | google-cloud-logging | Structured logging | 50 GB/month (free) |
| Cloud Trace | Built into Agent Engine | Distributed tracing | 2.5M spans/month (free) |
| GitHub API | requests + github-client | Code analysis | 5k req/hour (auth) |

---

## Part 4: Deployment & Operations

### 4.1 Deployment Processes & Environments

**Three-Tier Environment Strategy:**

| Environment | Purpose | Auto-Deploy | Approval | Data |
|------------|---------|-----------|----------|------|
| **Dev** | Development & testing | On every push | None | Test data (ephemeral) |
| **Staging** | Pre-prod validation | Manual trigger | Manual review | Staging data |
| **Prod** | Live user traffic | Manual trigger | Approvals required | Production data |

**Deployment Workflow:**

```
1. Developer pushes code to feature branch
   ↓
2. CI workflow runs (drift check → tests → build)
   - R8: Drift detection MUST pass first (blocks if violations)
   - ARV: Agent readiness verification gates
   - Tests: Pytest suite (~40 tests)
   - Build: Docker image → GCR
   ↓
3. If merge to main:
   - Auto-deploy to dev environment
   - Manual workflow trigger for staging/prod
   ↓
4. Deployment workflow runs (ARV gate → deploy)
   - ARV: Comprehensive department readiness check
   - Agent Engine: adk deploy agent_engine
   - Gateways: Terraform apply (A2A + Slack via terraform-prod.yml)
   - Infrastructure: Terraform apply to create/update all resources
   ↓
5. Post-deployment validation
   - Health checks
   - Smoke tests
   - ARV validation
```

**CI Workflow** (`.github/workflows/ci.yml`)

```yaml
jobs:
  drift-check:          # R8: MUST run first, blocks if violations
    - Checks for forbidden frameworks (R1)
    - Validates gateway code (R3)
    - Detects credential leaks (R4)

  arv-check:            # ARV minimum gates
    - Agent readiness verification
    - Contract validation
    - Configuration consistency

  test:                 # Python tests
    - pytest suite
    - Coverage reporting

  lint:                 # Code quality
    - Flake8 (linting)
    - Black (formatting check)
    - Mypy (type checking)

  security:             # Security scans
    - Bandit (SAST)
    - Safety (dependency vulns)

  terraform:            # IaC validation
    - Plan validation
    - Format checking

  docs:                 # Documentation
    - Structure validation
    - Naming compliance (000-docs/)
```

**Deployment Workflow** (`.github/workflows/deploy-dev.yml`, `deploy-staging.yml`, `deploy-prod.yml`)

```yaml
jobs:
  arv-gate:             # ARV readiness verification
    - Department-level checks
    - Optional skip (emergency deploys only)

  deploy-agent-engine:  # Vertex AI Agent Engine
    - Build & push Docker image to GCR
    - adk deploy agent_engine (ADK CLI)
    - Environment-specific config

  deploy-gateways:      # Cloud Run services
    - A2A Gateway deploy
    - Slack Webhook deploy
    - Service routing configuration

  terraform-apply:      # Infrastructure updates
    - Plan validation
    - Apply configuration
    - Output new endpoints

  post-deploy:          # Validation
    - Health checks
    - Smoke tests
    - ARV final validation
```

### 4.2 Monitoring & Logging

**Observability Stack:**

| Component | Technology | Purpose | Configuration |
|-----------|-----------|---------|---------------|
| **Tracing** | Cloud Trace (OpenTelemetry) | Distributed tracing | Auto-enabled in Agent Engine |
| **Logging** | Cloud Logging | Structured logs | App/agent/gateway logs forwarded |
| **Metrics** | Cloud Monitoring | Resource metrics | CPU, memory, latency tracking |
| **Profiling** | Cloud Profiler | Performance analysis | CPU/memory hot spots |
| **Error Reporting** | Error Reporting API | Exception tracking | Unhandled errors captured |

**Log Collection:**

```
Agent Engine (Vertex AI)
  └→ Cloud Logging (automatic)
      ├── Agent execution logs
      ├── Tool invocation logs
      ├── API call traces
      └── Error stack traces

Cloud Run Gateways
  └→ Cloud Logging (stdout/stderr)
      ├── Request logs (A2A + Slack)
      ├── Authentication logs
      ├── Routing logs
      └── Error logs

Application Code
  └→ google-cloud-logging library
      ├── Structured JSON logging
      ├── SPIFFE ID correlation (R7)
      ├── Portfolio orchestration progress
      └── GCS write status
```

**Trace Propagation (R7 - SPIFFE):**

```
Agent Execution Header:
X-Agent-SPIFFE-ID: spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0

Cloud Trace:
- Automatically correlates requests with SPIFFE ID
- Enables service-to-service tracing
- Shows agent-to-agent call chains
```

**Key Metrics to Monitor:**

```
Agent Engine:
- Requests/sec (throughput)
- P50/P95/P99 latency
- Error rate (5xx responses)
- Agent Engine CPU/memory utilization
- Session creation rate
- Memory Bank operations/sec

Cloud Run Gateways:
- Request count (A2A + Slack endpoints)
- Response time (gateway proxy overhead)
- HTTP error rates
- Cold start latency
- Instance count (auto-scaling)

Portfolio/Org Storage:
- GCS write latency
- Portfolio run success rate
- Per-repo audit execution time
- Storage quota usage
```

**Alerting Configuration (Recommended):**

```
CRITICAL:
- Agent Engine down (no responses)
- Cloud Run gateway error rate > 5%
- GCS write failures (storage unavailable)

WARNING:
- Agent latency P95 > 10s
- Cloud Run scaling max instances reached
- Portfolio run exceeds 30 minutes
- Error rate > 1%

INFO:
- Portfolio run started/completed
- New deployment successful
- Daily metrics summary
```

### 4.3 Testing Framework

**Test Coverage:**

| Category | Framework | Location | Count | Status |
|----------|-----------|----------|-------|--------|
| Unit Tests | pytest | `tests/unit/` | 40+ | ✅ All passing |
| A2A Contracts | pytest | `tests/unit/test_agentcard_json.py` | 18 | ✅ All passing (v0.10.0) |
| Storage Config | pytest | `tests/unit/test_storage_*.py` | 36 | ✅ All passing |
| Integration | pytest-asyncio | `tests/integration/` | 20+ | ✅ |
| Smoke Tests | Custom scripts | `scripts/run_*_smoke.py` | Various | Ad-hoc |

**Test Commands:**

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_agentcard_json.py -v

# With coverage
pytest --cov=agents --cov-report=html

# Integration tests
pytest tests/integration/ -v

# A2A contract validation
make check-a2a-contracts

# ARV minimum gate
make check-arv-minimum

# Portfolio orchestration
python3 scripts/check_org_storage_readiness.py --write-test
```

**Test Coverage Targets:**

```
Agents: > 65% code coverage
Services: > 60% code coverage
Tools: > 70% code coverage
Contracts: 100% validation (18 tests)
Storage: 100% coverage (36 tests)
```

### 4.4 Security Configurations

**Authentication & Authorization:**

| Component | Auth Method | Credentials | Rotation |
|-----------|------------|-------------|----------|
| Agent Engine | Workload Identity (WIF) | Service account | Auto (GCP) |
| Cloud Run | Workload Identity (WIF) | Service account | Auto (GCP) |
| Slack | OAuth token | Secret Manager | Manual (90 days) |
| GitHub Actions | WIF (OIDC) | No keys stored | Auto (tokens) |
| GCS (org storage) | ADC (App Default Credentials) | Service account | Auto |

**Service Account Setup:**

```
bob-agent@{project}.iam.gserviceaccount.com
  ├── Vertex AI Agent Engine roles
  ├── Cloud Run invoker
  ├── GCS org storage writer
  ├── Cloud Logging writer
  └── Cloud Trace agent

a2a-gateway@{project}.iam.gserviceaccount.com
  ├── Cloud Run invoker
  ├── Agent Engine invoker
  └── Cloud Logging writer

slack-webhook@{project}.iam.gserviceaccount.com
  ├── Cloud Run invoker
  ├── Agent Engine invoker
  └── Cloud Logging writer
```

**Workload Identity Federation (WIF) - R4 Compliance:**

```
GitHub Repository
  └→ GitHub OIDC Provider (OpenID Connect)
      └→ GCP Workload Identity Pool
          └→ Service Account Key (temporary, time-limited)
              └→ Cloud Run / Agent Engine operations
```

**Key Security Practices:**

1. **No Local Credentials (R4):** All deployments via GitHub Actions WIF
2. **Secret Manager Integration:** GitHub Secrets → Secret Manager → runtime
3. **SPIFFE Identity (R7):** All requests include agent identity header
4. **Drift Detection (R8):** Prevents credential leaks in code
5. **Pre-commit Hooks:** Detects secrets before commit

---

## Part 5: Dependencies & Integrations

### 5.1 Python Package Dependencies

**Core Dependencies** (`requirements.txt`):

```
# Agent Framework (R1)
google-adk>=0.1.0                    # Agent Development Kit
a2a-sdk>=0.3.0                       # Agent-to-Agent protocol

# GCP Services
google-cloud-aiplatform>=1.112.0     # Vertex AI Agent Engine (R2)
google-cloud-discoveryengine>=0.11.0 # Vertex AI Search (RAG)
google-auth>=2.23.0                  # GCP authentication
google-cloud-logging>=3.8.0           # Structured logging
google-cloud-storage>=2.10.0          # GCS access

# Gateway Services (R3)
fastapi>=0.104.0                     # A2A gateway HTTP
httpx>=0.25.0                        # Async HTTP client
pydantic>=2.4.0                      # Request validation
uvicorn[standard]>=0.24.0            # ASGI server

# Slack Integration
slack-sdk>=3.23.0                    # Slack API
slack-bolt>=1.18.0                   # Slack event handling
python-dotenv>=1.0.0                 # Environment config

# Observability
opentelemetry-api>=1.21.0            # OpenTelemetry SDK
opentelemetry-exporter-gcp-trace>=1.5.0 # Cloud Trace export

# Code Quality
black>=23.10.0                       # Code formatting
flake8>=6.1.0                        # Linting
mypy>=1.6.0                          # Type checking
bandit>=1.7.5                        # Security scanning
safety>=2.3.5                        # Dependency vuln scanning

# Testing
pytest>=7.4.0                        # Test framework
pytest-asyncio>=0.21.0               # Async test support
pytest-cov>=4.1.0                    # Coverage reporting
```

**Development Dependencies:**

```
pytest-asyncio              # Async test execution
pytest-cov                  # Coverage analysis
black                       # Code formatting
flake8                      # Linting
mypy                        # Type checking
bandit                      # SAST
safety                      # Dependency scanning
pre-commit                  # Git hooks
```

### 5.2 Third-Party Services & APIs

**Google Cloud Platform:**

| Service | Usage | Configuration | Quota |
|---------|-------|---------------|-------|
| **Vertex AI Agent Engine** | Agent runtime (R2) | `AGENT_ENGINE_ID` env var | 1000 req/min (default) |
| **Vertex AI Search** | RAG documentation (LIVE2) | `VERTEX_SEARCH_DATASTORE_ID` | 10k req/day (free tier) |
| **Cloud Run** | Gateway hosting (R3) | Terraform provisioning | 2 million req/month (free) |
| **Cloud Storage (GCS)** | Org knowledge hub (LIVE1) | `ORG_STORAGE_BUCKET` | 1 GB/month (free) |
| **Cloud Logging** | Structured logs | Auto-configured | 50 GB/month (free) |
| **Cloud Trace** | Distributed tracing | Built into Agent Engine | 2.5M spans/month (free) |
| **Secret Manager** | GitHub secrets | Terraform-managed | 6 operations/hour (free) |

**GitHub Integration:**

| API | Usage | Rate Limit | Auth |
|-----|-------|-----------|------|
| GitHub REST API | Code analysis, PR checks | 5,000 req/hour | OAuth token |
| GitHub GraphQL API | Commit history, issues | 5,000 points/hour | OAuth token |
| GitHub Actions | CI/CD workflows | Unlimited (GH hosted) | WIF (OIDC) |

**Slack Integration:**

| API | Usage | Rate Limit | Auth |
|-----|-------|-----------|------|
| Slack Bot API | Message posting | 1 msg/sec | OAuth token |
| Slack Events API | Webhook events | Varies | Signing secret |
| Slack Interactivity | Interactive components | N/A | Signing secret |

**ADK Documentation Search (Future - LIVE2):**

```
Vertex AI Search (Discovery Engine)
  └→ Crawled ADK documentation
      ├── API references
      ├── Code patterns
      ├── Architecture guides
      └── Integration examples
```

### 5.3 External Webhooks & Event Handlers

**Slack Webhook Endpoint:**

```
URL: https://slack-webhook-{env}.run.app
Method: POST
Content-Type: application/json
Auth: Slack signing secret (SLACK_SIGNING_SECRET)

Events:
- app_mention (@bobs_brain in Slack)
- message (DMs to bot)
- slash_commands (future)
```

**A2A Gateway Endpoint:**

```
URL: https://a2a-gateway-{env}.run.app
Method: POST
Content-Type: application/json
Auth: Service account (Workload Identity)
Path: /call/{agent_id}

Routing:
- bob → foreman
- foreman → iam-* specialists
- Cross-agent A2A calls
```

**GitHub Webhook (CI/CD Triggers):**

```
URL: GitHub API (automated)
Triggers:
- Push to main/develop/feature/* → CI workflow
- Pull request → CI + tests
- Manual trigger → Deploy workflow
```

---

## Part 6: Operational Runbooks

### 6.1 Startup & Health Checks

**Pre-Deployment Checklist:**

```bash
# 1. Environment validation
export PROJECT_ID=your-gcp-project
export LOCATION=us-central1
export DEPLOYMENT_ENV=dev

# 2. Drift detection (must pass)
bash scripts/ci/check_nodrift.sh

# 3. ARV minimum gate
python3 scripts/check_arv_minimum.py

# 4. Infrastructure readiness
python3 scripts/check_arv_config.py

# 5. Org storage readiness (if enabled)
python3 scripts/check_org_storage_readiness.py
python3 scripts/check_org_storage_readiness.py --write-test  # Optional write test
```

**Deployment:**

```bash
# 1. Apply infrastructure (first time only)
cd infra/terraform
terraform init
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# 2. Build & push Docker images
gcloud builds submit --tag gcr.io/${PROJECT_ID}/agent:0.10.0 agents/bob/
gcloud builds submit --tag gcr.io/${PROJECT_ID}/a2a-gateway:0.10.0 service/a2a_gateway/
gcloud builds submit --tag gcr.io/${PROJECT_ID}/slack-webhook:0.10.0 service/slack_webhook/

# 3. Deploy via CI/CD (RECOMMENDED)
git push origin main
# GitHub Actions handles everything

# 4. Manual deployment (local testing only)
cd agents/bob
adk deploy agent_engine \
  --project-id=${PROJECT_ID} \
  --region=${LOCATION} \
  --staging-bucket=gs://${PROJECT_ID}-adk-staging
```

**Health Check:**

```bash
# 1. Agent Engine status
gcloud ai agent-engines list --region=${LOCATION}
gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION}

# 2. Cloud Run services
gcloud run services list --region=${LOCATION}
gcloud run services describe a2a-gateway --region=${LOCATION}

# 3. Agent readiness
curl -X POST https://a2a-gateway-${DEPLOYMENT_ENV}.run.app/call/bob \
  -H "Content-Type: application/json" \
  -d '{"query": "health check"}'

# 4. Slack integration (if enabled)
curl -X POST https://slack-webhook-${DEPLOYMENT_ENV}.run.app/slack/events \
  -H "Content-Type: application/json" \
  -d '{"challenge": "test"}'

# 5. Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=a2a-gateway" \
  --limit 50 --format json

# 6. GCS org storage (if enabled)
gsutil ls gs://intent-org-knowledge-hub-${DEPLOYMENT_ENV}/
gsutil stat gs://intent-org-knowledge-hub-${DEPLOYMENT_ENV}/portfolio/runs/
```

### 6.2 Troubleshooting Guide

**Drift Detection Failed (R8)**

```
Symptom: CI fails with "Drift violations detected"

Causes & Fixes:

1. Alternative framework detected
   Error: "VIOLATION R1: Alternative framework imports found"
   Fix: Remove LangChain/CrewAI/AutoGen imports
   Command: grep -r "from langchain\|from crewai" agents/

2. Runner import in service/ (R3 violation)
   Error: "VIOLATION R3: Runner imports found in service/"
   Fix: Remove Runner imports, use REST API calls
   Command: grep -r "from google.adk.runner" service/

3. Credentials in code (R4 violation)
   Error: "VIOLATION R4: Credentials detected"
   Fix: Remove hardcoded keys, use Secret Manager
   Command: grep -r "private_key\|secret\|token" --include="*.py"

4. Custom framework imports
   Error: "VIOLATION R1: Custom agent framework detected"
   Fix: Use only google-adk, remove custom wrappers
```

**Agent Engine Deployment Failed**

```
Symptom: adk deploy fails with "Agent Engine not found"

Causes & Fixes:

1. Infrastructure not created
   Command: terraform apply -var-file=envs/{env}.tfvars

2. Docker image not pushed
   Command: gcloud builds submit --tag gcr.io/${PROJECT_ID}/agent:tag agents/bob/

3. Service account lacking permissions
   Fix: Check IAM roles for bob-agent SA
   Command: gcloud projects get-iam-policy ${PROJECT_ID} \
     --flatten="bindings[].members" \
     --filter="bindings.members:bob-agent@"

4. Staging bucket missing
   Command: gsutil mb gs://${PROJECT_ID}-adk-staging

5. ADK version mismatch
   Fix: Update google-adk in requirements.txt
   Command: pip install --upgrade google-adk
```

**Agent Not Responding**

```
Symptom: A2A gateway returns 503 or timeout

Causes & Fixes:

1. Agent Engine cold start
   Wait 30-60 seconds, retry request

2. Agent Engine replica scaling
   Check: gcloud ai agent-engines describe ${AGENT_ENGINE_ID}
   Look for: "desiredReplicaCount" vs "actualReplicaCount"
   Wait for: actualReplicaCount ≥ desiredReplicaCount

3. Memory Bank initialization failure
   Check logs: gcloud logging read "agent_id=bob"
   Look for: VertexAiMemoryBankService errors
   Fix: Verify Firestore/BigTable access

4. Gateway routing issue
   Check A2A gateway logs:
   gcloud logging read "resource.type=cloud_run_revision AND \
     resource.labels.service_name=a2a-gateway"
   Look for: HTTP error, timeout, or routing error

5. SPIFFE authentication (R7)
   Check: X-Agent-SPIFFE-ID header in request
   Fix: Verify agent_spiffe_id in .env and agent-card.json
```

**GCS Org Storage Not Writing**

```
Symptom: Portfolio runs complete but no files in GCS

Causes & Fixes:

1. Feature flag disabled
   Fix: export ORG_STORAGE_WRITE_ENABLED=true

2. Bucket doesn't exist
   Command: gsutil ls gs://intent-org-knowledge-hub-${DEPLOYMENT_ENV}/
   Fix: terraform apply -var-file=envs/{env}.tfvars (with org_storage_enabled=true)

3. Service account lacks write permission
   Check: gcloud projects get-iam-policy ${PROJECT_ID} \
     --flatten="bindings[].members" \
     --filter="bindings.members:bob-agent@" \
     --filter="bindings.role:*Storage*"
   Fix: Add storage.objects.create role

4. GCS library not installed
   Command: pip install google-cloud-storage>=2.10.0

5. Write test failing
   Command: python3 scripts/check_org_storage_readiness.py --write-test
   Look for: Errors in test object creation/cleanup
```

**Slack Integration Not Working**

```
Symptom: Slack messages not triggering agent

Causes & Fixes:

1. Bot token expired/invalid
   Check: Slack API → OAuth tokens
   Fix: Regenerate token, update Secret Manager
   Command: gcloud secrets versions add slack-bot-token --data-file=<(echo 'xoxb-...')

2. Signing secret mismatch
   Fix: Copy from Slack App settings
   Command: gcloud secrets versions add slack-signing-secret --data-file=<(echo '...')

3. Webhook URL not configured in Slack
   Slack → Settings → Event Subscriptions
   Fix: Set Request URL to: https://slack-webhook-${DEPLOYMENT_ENV}.run.app/slack/events

4. Permissions insufficient
   Slack → App settings → Bot Token Scopes
   Required: chat:write, app_mentions:read, commands

5. Gateway not reachable
   Check: curl https://slack-webhook-${DEPLOYMENT_ENV}.run.app/health
   Fix: Check Cloud Run service is deployed and public
```

### 6.3 Daily Operations

**Morning Health Check (5 minutes):**

```bash
#!/bin/bash
# Quick daily validation

PROJECT_ID="your-project"
LOCATION="us-central1"
DEPLOYMENT_ENV="prod"

echo "🔍 Daily Health Check..."

# 1. Agent Engine status
echo -n "Agent Engine: "
gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION} \
  --format="value(state)" 2>/dev/null || echo "❌ FAILED"

# 2. Cloud Run services
echo -n "A2A Gateway: "
gcloud run services describe a2a-gateway --region=${LOCATION} \
  --format="value(status.url)" 2>/dev/null | grep -q "https" && echo "✅" || echo "❌"

# 3. Error rate (last 1 hour)
ERROR_COUNT=$(gcloud logging read \
  "resource.type=cloud_run_revision AND severity=ERROR" \
  --limit 1000 --format json 2>/dev/null | grep -c "severity")
echo "Recent errors: $ERROR_COUNT"

# 4. Storage quota
echo -n "Org storage quota: "
gsutil du -s gs://intent-org-knowledge-hub-${DEPLOYMENT_ENV}/ 2>/dev/null || echo "N/A (disabled)"

echo "✅ Health check complete"
```

**Weekly Audit (30 minutes):**

```bash
#!/bin/bash
# Weekly operational audit

# 1. Dependency updates
pip list --outdated | grep -E "google-|adk|a2a"

# 2. Test coverage
pytest --cov=agents --cov-report=html
echo "Coverage report: htmlcov/index.html"

# 3. Code quality
flake8 agents/ service/ --statistics
black --check agents/ service/

# 4. Compliance check
bash scripts/ci/check_nodrift.sh

# 5. Documentation sync
ls -la 000-docs/ | wc -l
echo "Total docs: $(find 000-docs/ -name '*.md' | wc -l)"

# 6. Secret rotation status
gcloud secrets list --format="table(name,created.date())" | grep -E "slack|github"
```

**Monthly Maintenance (2 hours):**

```bash
#!/bin/bash
# Monthly maintenance tasks

# 1. Update dependencies
pip install --upgrade google-adk google-cloud-aiplatform google-cloud-discoveryengine

# 2. Run comprehensive test suite
pytest --cov=agents --cov-report=html tests/

# 3. GCS cleanup (delete old portfolio runs > 90 days)
# Note: Lifecycle policies handle this automatically
gsutil retention event set gs://intent-org-knowledge-hub-prod/

# 4. Update documentation
# - Review 000-docs/ for outdated content
# - Archive stale phase docs
# - Update CHANGELOG with changes

# 5. Terraform state backup
cd infra/terraform
terraform state pull > terraform-backup-$(date +%Y%m%d).json

# 6. Security audit
bandit -r agents/ service/ -v
safety check --json
```

---

## Part 7: Feature Flags & Configuration

### 7.1 Environment Variables

**Core Configuration:**

```bash
# GCP Project
PROJECT_ID=your-gcp-project              # Required
LOCATION=us-central1                      # Required
DEPLOYMENT_ENV=dev|staging|prod           # Required

# Application
APP_NAME=bobs-brain                       # Required
APP_VERSION=0.10.0                        # Required

# Agent Engine
AGENT_ENGINE_ID=your-engine-id            # Required
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0

# Gateway URLs
PUBLIC_URL=https://a2a-gateway-dev.run.app
SLACK_WEBHOOK_URL=https://slack-webhook-dev.run.app
```

**Feature Flags:**

```bash
# LIVE2: RAG/Vertex AI Search
LIVE_RAG_BOB_ENABLED=false                # Enable RAG for bob agent
LIVE_RAG_FOREMAN_ENABLED=false            # Enable RAG for foreman
VERTEX_SEARCH_DATASTORE_ID_DEV=adk-documentation-dev
VERTEX_SEARCH_DATASTORE_ID_PROD=adk-documentation-prod

# LIVE2: Agent Engine A2A routing
ENGINE_MODE_FOREMAN_TO_IAM_ADK=false      # Route to Agent Engine vs local
ENGINE_MODE_FOREMAN_TO_IAM_ISSUE=false
ENGINE_MODE_FOREMAN_TO_IAM_FIX=false

# LIVE1: Org storage
ORG_STORAGE_WRITE_ENABLED=false           # Enable GCS writes
ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev

# Slack integration
SLACK_BOB_ENABLED=false                   # Enable Slack bot
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

### 7.2 Terraform Variables by Environment

**Dev Environment** (`envs/dev.tfvars`):
```hcl
project_id             = "bobs-brain-dev"
environment            = "dev"
agent_machine_type     = "n1-standard-2"
agent_max_replicas     = 2
gateway_max_instances  = 5
org_storage_enabled    = false  # Optional in dev
```

**Staging Environment** (`envs/staging.tfvars`):
```hcl
project_id             = "bobs-brain-staging"
environment            = "staging"
agent_machine_type     = "n1-standard-4"
agent_max_replicas     = 3
gateway_max_instances  = 8
org_storage_enabled    = true
org_storage_bucket_name = "intent-org-knowledge-hub-staging"
```

**Production Environment** (`envs/prod.tfvars`):
```hcl
project_id             = "bobs-brain-prod"
environment            = "prod"
agent_machine_type     = "n1-standard-4"
agent_max_replicas     = 5
gateway_max_instances  = 15
org_storage_enabled    = true
org_storage_bucket_name = "intent-org-knowledge-hub-prod"
```

---

## Part 8: Upgrade & Migration Path

### 8.1 Version Upgrade Process

**From v0.9.0 → v0.10.0:**

```bash
# 1. Check changes
git log v0.9.0..v0.10.0 --oneline

# 2. Review changelog
cat CHANGELOG.md | head -100

# 3. Migrate prompts (if custom)
# v0.10.0: Contract-first prompt design
# Reduce system prompt tokens by 40-50%
# See: 000-docs/6767-115-DR-STND-prompt-design-and-a2a-contracts-for-department-adk-iam.md

# 4. Update agent cards
# v0.10.0: Added $comment fields referencing contracts
# See: agents/{agent}/.well-known/agent-card.json

# 5. Validate contracts
pytest tests/unit/test_agentcard_json.py -v

# 6. Deploy
git add .
git commit -m "chore(upgrade): upgrade to v0.10.0"
git push origin main
# CI/CD handles deployment
```

### 8.2 Breaking Changes

**v0.10.0 Breaking Changes:**
- System prompts now expect contract-first design (schemas referenced, not duplicated)
- AgentCard validation tests added; custom AgentCards must pass validation
- Specialist prompt reduced from 271 → 120 lines (old format incompatible)

**Migration Guide:**

1. Update system prompts to contract-first format
2. Reference contracts by name in AgentCard $comment fields
3. Run validation tests: `pytest tests/unit/test_agentcard_json.py`
4. Deploy in staging first

### 8.3 Template Porting to New Repositories

**Porting Bob's Brain to Your Product:**

```bash
# 1. Copy template
cp -r templates/iam-department/ ../your-product/agents/iam-department/

# 2. Customize
# - Update agent names
# - Customize system prompts
# - Adapt tools to your domain
# - Update A2A contracts

# 3. Validate
bash scripts/ci/check_nodrift.sh
pytest tests/

# 4. Deploy infrastructure
cd infra/terraform
terraform apply -var-file=envs/dev.tfvars

# 5. Deploy agents
git push origin main  # Triggers CI/CD
```

**See:** `000-docs/6767-105-DR-GUIDE-porting-iam-department-to-new-repo.md`

---

## Part 9: Cost Optimization

### 9.1 Resource Sizing

**Agent Engine Cost Estimation:**

```
Machine: n1-standard-4
- Hourly: ~$0.19
- Monthly (24/7): ~$140

n1-standard-2 (dev):
- Hourly: ~$0.095
- Monthly (24/7): ~$70
```

**Cloud Run Cost Estimation:**

```
Gateway instances (each):
- Hourly (running): ~$0.04
- Monthly (24/7): ~$30
- Requests: $0.40 per million

Slack webhook + A2A gateway = ~$60/month
```

**GCS Org Storage Cost:**

```
Storage: $0.02/GB/month
Lifecycle rules: Auto-delete > 90 days
- Typical monthly: $5-20/month

Estimated total: ~$250/month (all components, prod)
```

### 9.2 Cost Optimization Strategies

1. **Use Committed Use Discounts (CUDs):**
   - 25% discount for 1-year commitment
   - 52% discount for 3-year commitment
   - Recommended for prod Agent Engine

2. **Auto-scaling Configuration:**
   - Dev: min=0, max=2 (scale down after hours)
   - Prod: min=1, max=5 (maintain minimum availability)

3. **GCS Lifecycle Policies:**
   - Per-repo audit results: 90 days, then delete
   - Portfolio summaries: Indefinite retention
   - Total storage savings: ~40% over time

4. **Scheduled Down Time (Dev):**
   - Cloud Scheduler to pause dev Agent Engine overnight
   - Saves ~$70/month in dev costs

5. **Network Optimization:**
   - Use same region for all resources (lower egress costs)
   - Cloud CDN for frequently accessed objects

---

## Part 10: Disaster Recovery & Backup

### 10.1 Backup Strategy

**What to Backup:**

| Asset | Location | Frequency | Retention |
|-------|----------|-----------|-----------|
| Terraform State | GCS state bucket | Per deploy | Indefinite (versioned) |
| Source Code | GitHub | Automatic | Indefinite |
| Configuration | Secret Manager | Per change | Indefinite (versioned) |
| Audit Results | GCS org storage | Per portfolio run | 90 days (per-repo), indefinite (summary) |

**Backup Procedures:**

```bash
# 1. Terraform state backup
cd infra/terraform
terraform state pull > terraform-state-backup-$(date +%Y%m%d-%H%M%S).json
gsutil cp terraform-state-backup-*.json gs://backups-prod/terraform/

# 2. Secrets backup (encrypted in Secret Manager)
gcloud secrets versions list slack-bot-token --limit=10
# Versions are immutable; Secret Manager handles versioning

# 3. Configuration backup
git tag -a "backup-prod-$(date +%Y%m%d)" -m "Production backup"
git push origin "backup-prod-$(date +%Y%m%d)"
```

### 10.2 Disaster Recovery Procedures

**Agent Engine Failure (Complete Wipe):**

```bash
# 1. Assess damage
gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION}

# 2. Recreate infrastructure
cd infra/terraform
terraform destroy -var-file=envs/prod.tfvars  # Careful!
terraform apply -var-file=envs/prod.tfvars    # Rebuild

# 3. Redeploy agent
adk deploy agent_engine \
  --project-id=${PROJECT_ID} \
  --region=${LOCATION} \
  --staging-bucket=gs://${PROJECT_ID}-adk-staging

# 4. Verify
curl -X POST https://a2a-gateway-prod.run.app/call/bob \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 5. Rollback if issues
git revert ${BROKEN_COMMIT}
git push origin main  # Retrigger CI/CD
```

**Cloud Run Gateway Failure:**

```bash
# 1. Check service status
gcloud run services describe a2a-gateway --region=${LOCATION}

# 2. Recreate service
# ⚠️ DEPRECATED (R4 Violation) - Use Terraform instead:
# cd infra/terraform && terraform apply -var-file=envs/prod.tfvars
#
# ❌ DO NOT USE:
# gcloud run deploy a2a-gateway \
#   --image=gcr.io/${PROJECT_ID}/a2a-gateway:0.10.0 \
#   --region=${LOCATION} \
#   --service-account=a2a-gateway@${PROJECT_ID}.iam.gserviceaccount.com
#
# ✅ CORRECT: Use Terraform + GitHub Actions
terraform -chdir=infra/terraform apply -var-file=envs/prod.tfvars -target=google_cloud_run_service.a2a_gateway

# 3. Verify routing
curl https://a2a-gateway-prod.run.app/health
```

**Org Storage Bucket Corruption:**

```bash
# 1. Check bucket integrity
gsutil -D du gs://intent-org-knowledge-hub-prod/

# 2. Identify problematic files
gsutil ls -l gs://intent-org-knowledge-hub-prod/portfolio/runs/

# 3. Restore from versioning (if enabled)
gsutil cp gs://intent-org-knowledge-hub-prod/portfolio/runs/corrupt-file \
  gs://intent-org-knowledge-hub-prod/portfolio/runs/corrupt-file.backup

# 4. Verify portfolio runs still work
python3 scripts/run_portfolio_swe.py --dry-run
```

---

## Part 11: Team Onboarding Checklist

**Week 1 - Fundamentals:**
- [ ] Read README.md (understand what Bob does)
- [ ] Read CLAUDE.md (understand Hard Mode rules)
- [ ] Review 000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md (architecture)
- [ ] Set up local development environment
- [ ] Clone repo and install dependencies
- [ ] Run `bash scripts/ci/check_nodrift.sh` (understand drift detection)
- [ ] Run `pytest` (understand test suite)

**Week 2 - Deployment:**
- [ ] Review .env.example (understand configuration)
- [ ] Review Terraform configuration (infra/terraform/)
- [ ] Read 000-docs/068-OD-CONF-github-secrets-configuration.md (CI/CD auth)
- [ ] Review CI/CD workflows (.github/workflows/)
- [ ] Set up GCP project with required APIs enabled
- [ ] Configure GitHub secrets for Workload Identity
- [ ] Perform test deployment to dev environment

**Week 3 - Operations:**
- [ ] Read 000-docs/070-OD-RBOK-deployment-runbook.md (operational procedures)
- [ ] Read 000-docs/069-OD-TELE-observability-telemetry-guide.md (monitoring)
- [ ] Set up Cloud Logging dashboards
- [ ] Test health check procedures (Section 6.1)
- [ ] Practice troubleshooting scenarios (Section 6.2)
- [ ] Document custom operational procedures

**Week 4 - Advanced:**
- [ ] Review portfolio orchestration (scripts/run_portfolio_swe.py)
- [ ] Review org storage architecture (000-docs/000-AT-ARCH-org-storage-architecture.md)
- [ ] Test portfolio audit runs
- [ ] Review upgrade path (Section 8.1)
- [ ] Practice disaster recovery procedures (Section 10.2)
- [ ] Schedule monthly maintenance tasks (Section 6.3)

---

## Appendix A: Quick Reference Commands

**Local Development:**
```bash
cd /home/jeremy/000-projects/iams/bobs-brain/

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Tests
pytest
pytest tests/unit/test_agentcard_json.py -v
pytest --cov=agents --cov-report=html

# Code quality
bash scripts/ci/check_nodrift.sh
flake8 agents/ service/
black agents/ service/
mypy agents/ --ignore-missing-imports

# ARV checks
python3 scripts/check_arv_minimum.py
python3 scripts/check_arv_agents.py
```

**GCP Operations:**
```bash
# Project setup
export PROJECT_ID=your-gcp-project
export LOCATION=us-central1
gcloud config set project ${PROJECT_ID}

# Infrastructure
cd infra/terraform
terraform init
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# Agent Engine
gcloud ai agent-engines list --region=${LOCATION}
gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION}

# Cloud Run
gcloud run services list --region=${LOCATION}
gcloud run logs read a2a-gateway --region=${LOCATION}

# Logging
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json
gcloud logging read "severity=ERROR" --limit 50 --format json

# Storage
gsutil ls gs://intent-org-knowledge-hub-dev/
gsutil du -s gs://intent-org-knowledge-hub-dev/
```

**GitHub Actions:**
```bash
# Manual workflow triggers
gh workflow run ci.yml
gh workflow run deploy-dev.yml --ref main
gh workflow run deploy-staging.yml --ref main --field skip_arv=false
gh workflow run portfolio-swe.yml --ref main --field repos=all --field mode=preview

# Check workflow status
gh workflow view ci.yml
gh run list --workflow=ci.yml --limit 5
gh run view ${RUN_ID}
```

---

## Appendix B: Key Documentation Files

**Essential Reading for Operations:**

1. **Architecture & Standards:**
   - README.md (1,027 lines - everything start)
   - 000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md (canonical spec)
   - 000-docs/6767-115-DR-STND-prompt-design-and-a2a-contracts-for-department-adk-iam.md (v0.10.0)

2. **Deployment:**
   - 000-docs/070-OD-RBOK-deployment-runbook.md (step-by-step)
   - 000-docs/068-OD-CONF-github-secrets-configuration.md (CI/CD auth)
   - 000-docs/069-OD-TELE-observability-telemetry-guide.md (monitoring)

3. **Org Storage & Portfolio:**
   - 000-docs/000-AT-ARCH-org-storage-architecture.md (GCS hub design)
   - 000-docs/6767-113-AA-REPT-live1-gcs-implementation.md (LIVE1 v0.9.0)
   - 000-docs/6767-110-AA-REPT-portfolio-orchestrator-implementation.md (PORT1-3)

4. **Porting & Templates:**
   - 000-docs/6767-105-DR-GUIDE-porting-iam-department-to-new-repo.md (how to port)
   - 000-docs/6767-106-DR-STND-iam-department-integration-checklist.md (checklist)
   - templates/iam-department/README.md (template structure)

---

## Appendix C: Contact & Support

**For Questions About:**

- **Architecture & Design:** Review 000-docs/6767-* files (canonical standards)
- **Hard Mode Rules:** See CLAUDE.md section 4 or README.md section "Hard Mode Explained"
- **Terraform Infrastructure:** Review infra/terraform/README.md
- **Agent Development:** See agents/bob/README.md or agent.py source
- **CI/CD Workflows:** Review .github/workflows/ci.yml source
- **Troubleshooting:** Section 6.2 of this document
- **Operational Procedures:** 000-docs/000-RB-OPS-adk-department-operations-runbook.md

**GitHub Issues:**
- File issues at: https://github.com/jeremylongshore/bobs-brain/issues
- Include: version, environment, reproduction steps, logs

**Documentation Updates:**
- Update this analysis as new versions release
- Archive old docs to 000-docs/archive/
- Keep CHANGELOG.md synchronized

---

## Summary

Bob's Brain is a **production-ready ADK agent department** with strict architectural guardrails (Hard Mode R1-R8) enforced via CI/CD. DevOps teams can operate the system independently by:

1. **Understanding the architecture** (multi-agent, Agent Engine, Cloud Run proxies)
2. **Maintaining the infrastructure** (Terraform, 3 environments, auto-scaling)
3. **Following deployment procedures** (CI/CD workflows, ARV gates, drift detection)
4. **Monitoring operations** (Cloud Logging, Cloud Trace, custom dashboards)
5. **Responding to incidents** (troubleshooting guide, disaster recovery procedures)

All operational knowledge is encoded in:
- This document (quick reference)
- README.md (product overview)
- 000-docs/6767-* files (canonical standards)
- Source code and comments
- Test suite (validates compliance)

**Start with:** README.md → CLAUDE.md → 000-docs/6767-DR-STND → operational runbooks → troubleshooting guide

**Version:** 0.10.0
**Last Updated:** 2025-11-21
**Status:** Ready for production deployment and operation
