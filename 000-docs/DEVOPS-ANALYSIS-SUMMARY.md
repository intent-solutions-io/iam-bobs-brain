# Bob's Brain - DevOps Analysis Summary
**Created:** 2025-11-21
**Analysis Type:** Comprehensive DevOps onboarding study
**Repository:** https://github.com/jeremylongshore/bobs-brain
**Version Analyzed:** 0.10.0

---

## What This Repository Is

**Bob's Brain** is a **production-grade AI agent department** built on Google's Agent Development Kit (ADK) and Vertex AI Agent Engine. It serves as:

- A **reusable template** for multi-agent software engineering teams
- A **Slack AI assistant** powered by 8+ specialist agents
- A **compliance auditor** focused on ADK/Vertex pattern alignment
- A **portfolio orchestrator** for org-wide multi-repo analysis

**Key Characteristic:** Hard Mode rules (R1-R8) enforced via CI/CD to prevent architectural decay

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Technology Stack** | Python 3.12+, Google ADK, Vertex AI Agent Engine, Cloud Run |
| **Agents** | 1 orchestrator (bob) + 8 specialists (iam-*) |
| **Infrastructure** | Terraform (IaC), 3 environments (dev/staging/prod) |
| **Deployment** | CI/CD via GitHub Actions, Workload Identity Federation |
| **Runtime** | Managed Vertex AI Agent Engine (no self-hosted runners) |
| **Gateways** | Cloud Run proxies (A2A protocol + Slack webhooks) |
| **Storage** | GCS org-wide knowledge hub (LIVE1 v0.9.0+) |
| **Testing** | Pytest (40+ tests), 100% A2A contract validation |
| **Monitoring** | Cloud Logging, Cloud Trace, Cloud Monitoring |
| **Memory** | Dual: VertexAiSessionService + VertexAiMemoryBankService |
| **Security** | Workload Identity (WIF), SPIFFE IDs, Secret Manager |

---

## Directory Structure

```
bobs-brain/
├── agents/                          # Agent implementations
│   ├── bob/                         # Global orchestrator
│   ├── iam-senior-adk-devops-lead/  # Foreman (dept coordinator)
│   ├── iam_adk/                     # Specialist: ADK patterns
│   ├── iam_issue/                   # Specialist: Issue detection
│   ├── iam_fix_plan/                # Specialist: Fix planning
│   ├── iam_fix_impl/                # Specialist: Fix implementation
│   ├── iam_qa/                      # Specialist: QA validation
│   ├── iam_doc/                     # Specialist: Documentation
│   ├── iam_cleanup/                 # Specialist: Code cleanup
│   ├── iam_index/                   # Specialist: Knowledge curation
│   ├── shared_contracts.py          # A2A protocol contracts
│   └── shared_tools/                # Common tool implementations
│
├── service/                         # HTTP gateways (proxies)
│   ├── a2a_gateway/                 # A2A protocol endpoint
│   └── slack_webhook/               # Slack events handler
│
├── infra/terraform/                 # Infrastructure as Code
│   ├── main.tf                      # Core config
│   ├── variables.tf                 # Input variables
│   ├── iam.tf                       # Service accounts
│   ├── agent_engine.tf              # Agent Engine resources
│   ├── cloud_run.tf                 # Gateway services
│   ├── storage.tf                   # GCS buckets
│   ├── knowledge_hub.tf             # Org storage (LIVE1)
│   └── envs/                        # Environment configs
│       ├── dev.tfvars
│       ├── staging.tfvars
│       └── prod.tfvars
│
├── .github/workflows/               # CI/CD pipelines
│   ├── ci.yml                       # Tests, lint, build
│   ├── deploy-dev.yml               # Deploy to dev
│   ├── deploy-staging.yml           # Deploy to staging
│   ├── deploy-prod.yml              # Deploy to prod
│   ├── portfolio-swe.yml            # Portfolio audits
│   └── release.yml                  # Release workflow
│
├── scripts/                         # Operational scripts
│   ├── ci/
│   │   └── check_nodrift.sh         # Drift detection (R8)
│   ├── check_arv_*.py               # Agent readiness verification
│   ├── run_portfolio_swe.py          # Portfolio orchestrator
│   ├── run_*_smoke.py               # Smoke test scripts
│   └── check_org_storage_readiness.py # GCS validation
│
├── tests/                           # Test suite
│   ├── unit/
│   │   ├── test_agentcard_json.py   # 18 A2A contract tests (v0.10.0)
│   │   ├── test_storage_*.py        # 36 GCS tests
│   │   └── test_*.py                # Other unit tests
│   └── integration/                 # Integration tests
│
├── 000-docs/                        # All documentation (1,684 files)
│   ├── 6767-DR-STND-*.md            # Canonical standards
│   ├── 6767-OD-RBOK-*.md            # Operational runbooks
│   ├── 6767-AT-ARCH-*.md            # Architecture guides
│   ├── 6767-AA-REPT-*.md            # After-Action Reports
│   ├── 6767-AA-PLAN-*.md            # Phase plans
│   └── ...                          # 100+ docs
│
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container image
├── Makefile                         # Development commands (26KB)
├── .env.example                     # Configuration template
├── CHANGELOG.md                     # Version history
├── README.md                        # Main documentation (1,027 lines)
├── CLAUDE.md                        # AI working guide (209 lines)
├── VERSION                          # Version file
└── LICENSE                          # MIT License
```

---

## Key Deployment Architecture

```
Slack App
    ↓
slack_webhook (Cloud Run, R3 proxy)
    ↓
a2a_gateway (Cloud Run, R3 proxy)
    ↓
Agent Engine (Managed Runtime, R2)
    ├── bob (orchestrator)
    └── iam-* (specialists)
    ↓
Memory Services:
├── VertexAiSessionService (R5)
└── VertexAiMemoryBankService (R5)

GCS Org Storage (Optional - LIVE1):
└── gs://intent-org-knowledge-hub-{env}/
```

---

## Hard Mode Rules (R1-R8)

| Rule | Constraint | Enforcement |
|------|-----------|------------|
| **R1** | ADK-only (no LangChain/CrewAI) | Drift detection blocks |
| **R2** | Vertex AI Agent Engine runtime | Terraform enforces |
| **R3** | Cloud Run proxies only (no Runner) | Code + drift checks |
| **R4** | CI-only deployments (WIF auth) | GitHub Actions enforced |
| **R5** | Dual memory wiring required | Code inspection tests |
| **R6** | Single docs folder (000-docs/) | File structure validation |
| **R7** | SPIFFE ID propagation | Environment validation |
| **R8** | Drift detection first in CI | Job ordering enforces |

---

## Critical Information for DevOps

### Initial Setup (Day 1)
```bash
# 1. Clone & prepare
git clone https://github.com/jeremylongshore/bobs-brain.git
cd bobs-brain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Validate locally
bash scripts/ci/check_nodrift.sh  # Must pass
pytest                             # Run tests

# 3. Prepare GCP project
export PROJECT_ID=your-project
gcloud config set project ${PROJECT_ID}

# 4. Deploy infrastructure
cd infra/terraform
terraform apply -var-file=envs/dev.tfvars

# 5. Configure GitHub secrets (WIF)
# See: 000-docs/6767-OD-CONF-github-secrets-configuration.md
```

### Daily Operations
```bash
# Health check (5 min)
gcloud ai agent-engines list --region=us-central1
gcloud run services list --region=us-central1
gsutil ls gs://intent-org-knowledge-hub-dev/

# Error monitoring
gcloud logging read "severity=ERROR" --limit 50 --format json

# Portfolio audit
python3 scripts/run_portfolio_swe.py --repos all
```

### Common Issues & Fixes

**Drift Detection Fails:**
- R1: Remove LangChain/CrewAI imports → ADK only
- R3: Remove Runner imports from service/ → REST API only
- R4: No credentials in code → Use Secret Manager + WIF

**Agent Not Responding:**
- Check Agent Engine state: `gcloud ai agent-engines describe`
- Verify memory wiring in agent code
- Check Cloud Run gateway health
- Review logs: `gcloud logging read`

**GCS Org Storage Not Writing:**
- Enable flag: `export ORG_STORAGE_WRITE_ENABLED=true`
- Verify bucket exists: `gsutil ls gs://intent-org-knowledge-hub-{env}/`
- Check service account permissions: `gcloud projects get-iam-policy`

---

## Operational Responsibilities

### What You Need to Handle
- [ ] Terraform state management & backups
- [ ] GCP project & billing administration
- [ ] Cloud Run service scaling & monitoring
- [ ] Cloud Logging dashboards & alerts
- [ ] Disaster recovery & incident response
- [ ] Dependency updates & security patching
- [ ] Cost optimization (CUDs, auto-scaling)
- [ ] GitHub Actions secret rotation
- [ ] Slack integration credentials management

### What's Automated
- ✅ Drift detection (R8) - blocks bad code
- ✅ CI/CD pipeline (tests, build, deploy)
- ✅ Agent Engine deployment (adk CLI)
- ✅ Cloud Run auto-scaling
- ✅ Logging & tracing (built-in)
- ✅ Portfolio orchestration
- ✅ GCS lifecycle policies (auto-delete old data)

---

## Performance & Scaling

### Resource Allocation

**Agent Engine:**
- Dev: n1-standard-2, 2 replicas ($70/month)
- Staging: n1-standard-4, 3 replicas ($140/month)
- Prod: n1-standard-4, 5 replicas ($233/month)

**Cloud Run Gateways:**
- A2A Gateway: 0-10 instances
- Slack Webhook: 0-10 instances
- Cost: ~$60/month per gateway pair

**GCS Org Storage:**
- Storage: $0.02/GB/month
- Typical usage: $5-20/month

**Total Monthly Cost: ~$300-400 (prod all-in)**

### Auto-Scaling Strategy
```
Agent Engine:
- Min replicas: 1 (prod) or 0 (dev)
- Max replicas: 5 (prod), 2 (dev)
- Target CPU: 70%
- Scale-up time: 2-3 minutes
- Cold start: 30-60 seconds

Cloud Run Gateways:
- Min instances: 0 (serverless)
- Max instances: 10-15
- Scale-up time: <1 second (warm instances cached)
```

---

## Testing & Validation

### Test Coverage
- **Unit Tests:** 40+ tests covering agents, contracts, storage
- **Integration Tests:** 20+ tests for agent-to-agent communication
- **A2A Validation:** 18 tests validating AgentCards (v0.10.0)
- **Smoke Tests:** 5+ smoke test scripts for post-deployment

### Quality Gates (CI/CD)
1. **Drift Check** (R8) - Must pass first
2. **ARV Verification** - Agent readiness gates
3. **Tests** - Pytest suite
4. **Lint** - Flake8, Black, Mypy
5. **Security** - Bandit, Safety
6. **Terraform** - Plan validation
7. **Build** - Docker image creation

### How to Run Tests Locally
```bash
# All tests
pytest

# Specific suite
pytest tests/unit/test_agentcard_json.py -v

# With coverage
pytest --cov=agents --cov-report=html

# Drift detection
bash scripts/ci/check_nodrift.sh

# ARV gates
python3 scripts/check_arv_minimum.py
```

---

## Configuration & Environment Variables

### Required Configuration
```bash
# GCP Project (required)
PROJECT_ID=your-gcp-project
LOCATION=us-central1

# Deployment (required)
DEPLOYMENT_ENV=dev|staging|prod
APP_NAME=bobs-brain
APP_VERSION=0.10.0

# Agent Engine (required)
AGENT_ENGINE_ID=your-engine-id
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0

# Gateway URLs (required)
PUBLIC_URL=https://a2a-gateway-dev.run.app
SLACK_WEBHOOK_URL=https://slack-webhook-dev.run.app
```

### Feature Flags (Optional)
```bash
# Org Storage (LIVE1)
ORG_STORAGE_WRITE_ENABLED=false
ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev

# RAG/Vertex Search (LIVE2)
LIVE_RAG_BOB_ENABLED=false
VERTEX_SEARCH_DATASTORE_ID_DEV=adk-documentation-dev

# Slack Integration
SLACK_BOB_ENABLED=false
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

---

## Monitoring & Alerting

### Key Metrics
- Agent Engine throughput (requests/sec)
- Response latency (P50/P95/P99)
- Error rate (%)
- Cloud Run instance count & scaling events
- GCS write latency
- Portfolio audit duration

### Recommended Alerts
```
CRITICAL:
- Agent Engine unavailable (no responses)
- Cloud Run error rate > 5%
- GCS write failures

WARNING:
- Latency P95 > 10 seconds
- Error rate > 1%
- Scaling hitting max replicas
- Portfolio audit > 30 minutes
```

### Logging
```bash
# Recent errors
gcloud logging read "severity=ERROR" --limit 50 --format json

# Agent execution logs
gcloud logging read "agent_id=bob" --limit 100

# Gateway access logs
gcloud logging read "resource.type=cloud_run_revision" --limit 100

# Custom dashboard
# Create in Cloud Monitoring console for persistent view
```

---

## Maintenance & Upgrades

### Monthly Tasks
- [ ] Update dependencies: `pip install --upgrade google-adk google-cloud-*`
- [ ] Run full test suite: `pytest --cov=agents`
- [ ] Review logs for errors/warnings
- [ ] GCS cleanup (auto-handled by lifecycle policies)
- [ ] Terraform state backup

### Quarterly Tasks
- [ ] Security audit: `bandit -r agents/ service/`
- [ ] Dependency vulnerability scan: `safety check`
- [ ] Review & optimize GCP costs
- [ ] Rotate Slack credentials (if applicable)
- [ ] Update documentation

### Version Upgrades
- Current: **v0.10.0** (contract-first prompts, AgentCard validation)
- Previous: v0.9.0 (org storage LIVE1, portfolio orchestration)
- Upgrade path: Read CHANGELOG.md, apply migrations, test in dev/staging first

---

## Documentation & Resources

### Essential Files (START HERE)
1. **README.md** (1,027 lines) - Complete product overview
2. **CLAUDE.md** (209 lines) - Architecture & rules
3. **CHANGELOG.md** (1,000+ lines) - Version history

### Operational Documents (6767-series = canonical)
- `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Architecture standard
- `6767-OD-RBOK-deployment-runbook.md` - Step-by-step deployment
- `6767-OD-TELE-observability-telemetry-guide.md` - Monitoring setup
- `6767-OD-CONF-github-secrets-configuration.md` - CI/CD auth
- `6767-112-AT-ARCH-org-storage-architecture.md` - GCS design
- `000-RB-OPS-adk-department-operations-runbook.md` - Daily ops

### File Locations
- Configuration: `/home/jeremy/000-projects/iams/bobs-brain/`
- Infrastructure: `infra/terraform/`
- Agents: `agents/`
- Services: `service/`
- Tests: `tests/`
- Docs: `000-docs/` (1,684 files)
- Scripts: `scripts/`

---

## Next Steps for DevOps Teams

**Immediate (This Week):**
1. Read README.md thoroughly
2. Review CLAUDE.md & Hard Mode rules
3. Set up local development environment
4. Run drift detection & tests
5. Review Terraform configuration

**Short-Term (This Month):**
1. Provision GCP project & enable APIs
2. Configure Workload Identity Federation
3. Deploy to dev environment
4. Set up Cloud Logging dashboards
5. Test deployment workflows

**Medium-Term (This Quarter):**
1. Deploy to staging & production
2. Configure monitoring & alerting
3. Document custom operational procedures
4. Run portfolio audits
5. Establish backup & DR procedures

---

## Key Contacts & Resources

**Documentation:**
- Main: https://github.com/jeremylongshore/bobs-brain
- Issues: https://github.com/jeremylongshore/bobs-brain/issues
- Docs: `/home/jeremy/000-projects/iams/bobs-brain/000-docs/`

**Related Projects:**
- Foundation Template: https://github.com/jeremylongshore/iam1-intent-agent-model-vertex-ai
- Google ADK: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- Vertex AI Agent Engine: https://cloud.google.com/vertex-ai/docs/agent-engine

---

## Document Information

**Analysis Version:** 1.0
**Repository Version Analyzed:** 0.10.0
**Analysis Date:** 2025-11-21
**Analysis Type:** Comprehensive DevOps onboarding
**Status:** Complete & ready for operations team handoff

**Created in:** `/home/jeremy/000-projects/iams/bobs-brain/claudes-docs/`

**Related Analysis Document:**
- Full Analysis: `DEVOPS-ONBOARDING-ANALYSIS.md` (11 parts, comprehensive reference)
- This Summary: `DEVOPS-ANALYSIS-SUMMARY.md` (quick reference)

**See Also:**
- README.md - Product overview
- CLAUDE.md - Architecture & rules
- 000-docs/6767-* - Canonical standards
