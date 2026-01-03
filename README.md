# 🤖 Bob's Brain

<div align="center">

[![Version](https://img.shields.io/badge/version-1.1.0-green.svg)](CHANGELOG.md)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://cloud.google.com/vertex-ai/docs/agent-development-kit)
[![Agent Engine](https://img.shields.io/badge/Vertex%20AI-Agent%20Engine-4285F4.svg)](https://cloud.google.com/vertex-ai/docs/agent-engine)
[![License: ELv2](https://img.shields.io/badge/License-ELv2-blue.svg)](LICENSE)

**Specialist AI team for auditing and fixing Google Vertex/ADK design systems.**

Bob's Brain orchestrates expert agents that ensure your codebase follows Google's ADK and Vertex AI patterns. Built with Google ADK, Vertex AI Agent Engine, A2A protocol, Session Cache + Memory Bank. Hard Mode architecture enforces drift-free development.

[Quick Start](#-quick-start) • [What It Does](#-what-bob-does) • [Hard Mode Rules](#%EF%B8%8F-hard-mode-explained) • [Use as Template](#-use-as-template)

</div>

---

## 👋 What is Bob's Brain?

Bob's Brain is a **Slack AI assistant with a specialist team focused on auditing and constructing fixes for Google Vertex/ADK design systems.** This isn't a general-purpose coding assistant – it's a precision tool that ensures your agents, infrastructure, and architecture align with Google's ADK and Vertex AI recommended patterns.

**Key Focus:** Audit Google Vertex/ADK design compliance → Detect drift → Construct fixes → Maintain alignment

### Bob's Multi-Department Architecture

Bob is the **global orchestrator** that coordinates multiple specialist departments. This repo contains Bob's **first specialist team** – the **iam-* department** (Intent Agent Model) – focused exclusively on ADK/Vertex compliance:

```
┌─────────────────────────────────────────────────────────┐
│  Bob (Global Orchestrator)                              │
│  • Slack interface                                      │
│  • Routes requests to specialist departments            │
└─────────────────────────┬───────────────────────────────┘
                          │
       ┌──────────────────┴────────────────────┐
       │                                       │
       ▼                                       ▼
┌──────────────────────┐            ┌──────────────────────┐
│ iam-* Department     │            │ Future Departments   │
│ (THIS REPO)          │            │ (Coming Soon)        │
│                      │            │                      │
│ Focus: ADK/Vertex    │            │ • Data pipeline team │
│ compliance audits    │            │ • Security team      │
│ and fixes            │            │ • Performance team   │
└──────────────────────┘            └──────────────────────┘
```

**This repo = Bob's first specialist department, not Bob's entire brain.**

### Why This Team Exists

Building with Google ADK and Vertex AI requires strict architectural patterns. Most teams drift over time:

- ❌ Mix LangChain with ADK code
- ❌ Self-host runners instead of using Agent Engine
- ❌ Scatter docs across wikis and random files
- ❌ Skip memory wiring or do it incorrectly
- ❌ Violate Google's recommended patterns

**This team prevents that drift.** It audits your repos, detects violations, constructs fixes, and keeps you aligned with Google's ADK/Vertex standards.

### What Makes It "Hard Mode"

We enforce 8 architectural rules (R1-R8) that prevent the usual agent chaos:

- ✅ **ADK-only** - No mixing LangChain, CrewAI, or other frameworks
- ✅ **Managed runtime** - Vertex AI Agent Engine, not self-hosted containers
- ✅ **CI-enforced** - Automated checks block bad patterns before they merge
- ✅ **Memory that works** - Dual Session + Memory Bank for real continuity
- ✅ **Clean separation** - Cloud Run proxies, not franken-servers with embedded agents
- ✅ **One docs folder** - All docs in `000-docs/`, no scattered README files
- ✅ **Immutable identity** - SPIFFE IDs everywhere for clean tracing
- ✅ **Drift detection** - CI fails if you try to sneak in forbidden imports

**Tl;dr:** Production-grade multi-agent system with enforced architectural standards and compliance automation.

---

## 🎯 What This Team Does

The **iam-* department** is a specialist team focused exclusively on **Google Vertex/ADK design system compliance**:

### Core Capabilities (ADK/Vertex Focused)

**🔍 ADK/Vertex Compliance Audits**
- Scans repos for ADK import violations (no LangChain, CrewAI mixing)
- Detects drift from Google's recommended Agent Engine patterns
- Validates memory wiring (Session + Memory Bank)
- Checks A2A protocol implementation
- Ensures SPIFFE identity propagation
- Verifies gateway separation (no Runner in Cloud Run)

**🛠️ Automated ADK/Vertex Fixes**
- Constructs fix plans for ADK pattern violations
- Generates PRs to align with Vertex AI recommended architecture
- Refactors code to follow Google's ADK patterns
- Runs QA checks against ADK/Vertex standards

**📋 Portfolio-Wide ADK Compliance**
- Audits multiple repos for ADK/Vertex compliance simultaneously
- Aggregates ADK pattern violations across your org
- Tracks compliance scores and fix rates
- Stores audit results in centralized GCS buckets

**📝 ADK/Vertex Documentation**
- Writes AARs for all ADK pattern fixes
- Generates architecture docs showing Vertex AI alignment
- Documents ADK-specific patterns and decisions
- Maintains searchable knowledge of ADK/Vertex patterns

**💬 Slack Integration**
- Answers questions about ADK/Vertex patterns
- Sends alerts for ADK compliance failures
- Helps teams understand Google's recommended architectures

### The iam-* Specialist Team (ADK/Vertex Compliance)

This department has 8 specialist agents, each focused on a specific aspect of ADK/Vertex compliance:

```
┌─────────────┐
│     Bob     │  ← Global orchestrator (routes ADK/Vertex requests here)
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│ iam-senior-adk-devops-lead (Foreman)                    │
│ • Coordinates ADK/Vertex compliance audits              │
│ • Delegates to specialist agents                        │
└──────┬───────────────────────────────────────────────────┘
       │
       ├─→ iam-adk         (ADK/Vertex pattern expert)
       │                   Knows Google's recommended patterns
       │
       ├─→ iam-issue       (ADK violation detector)
       │                   Scans for drift from Google patterns
       │
       ├─→ iam-fix-plan    (ADK fix strategy planner)
       │                   Designs fixes to align with Vertex AI
       │
       ├─→ iam-fix-impl    (ADK fix implementer)
       │                   Refactors code to Google standards
       │
       ├─→ iam-qa          (ADK compliance QA)
       │                   Validates fixes against Google patterns
       │
       ├─→ iam-docs        (ADK/Vertex documentation)
       │                   Documents alignment decisions
       │
       ├─→ iam-cleanup     (ADK codebase cleanup)
       │                   Removes deprecated ADK patterns
       │
       └─→ iam-index       (ADK knowledge curator)
                           Maintains ADK/Vertex pattern library
```

**Important:** This team ONLY handles ADK/Vertex compliance work. General software engineering, data pipelines, security audits, etc. are handled by Bob's other departments (coming soon).

---

## 🏗️ Architecture

### How It Works

**For end users (Slack):**
```
You in Slack
   ↓
Slack webhook (Cloud Run)
   ↓
Vertex AI Agent Engine ← Bob's Brain (ADK agent)
   ↓
Dual Memory (Session + Memory Bank)
```

**For portfolio audits (CLI):**
```
python3 scripts/run_portfolio_swe.py
   ↓
Portfolio Orchestrator
   ↓
iam-senior-adk-devops-lead (foreman)
   ↓
iam-* specialist agents
   ↓
GCS Knowledge Hub (results storage)
```

### Directory Structure

```
bobs-brain/
├── agents/
│   └── bob/              # Main agent (LlmAgent + tools)
│       ├── agent.py      # Core agent logic
│       ├── a2a_card.py   # Agent-to-Agent protocol
│       └── tools/        # Custom tools
│
├── service/              # HTTP gateways (proxies only!)
│   ├── a2a_gateway/      # A2A protocol endpoint
│   └── slack_webhook/    # Slack event handler
│
├── infra/terraform/      # All infrastructure as code
├── .github/workflows/    # CI/CD (drift check first!)
├── 000-docs/             # All documentation (AARs, guides)
├── tests/                # Unit & integration tests
└── scripts/              # Deployment & maintenance tools
```

**Key principle:** Cloud Run services are **proxies only**. They forward requests to Agent Engine via REST. No `Runner` imports allowed in gateways.

---

## ⚡️ Hard Mode Explained

"Hard Mode" means we enforce strict rules that keep this agent system maintainable as it scales. This repository follows the **[6767 ADK/Agent Engine Specification](000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md)** as its guiding architectural standard. Here's what that looks like:

### The 8 Rules (R1-R8)

Every rule is **enforced in CI**. Violations fail the build automatically.

#### R1: Agent Implementation
- ✅ Use `google-adk` LlmAgent
- ❌ No LangChain, CrewAI, AutoGen, or custom frameworks

**Why:** Mixing frameworks creates integration nightmares. Pick one, stick with it.

#### R2: Deployed Runtime
- ✅ Deploy to Vertex AI Agent Engine
- ❌ No self-hosted runners or Cloud Run with embedded Runner

**Why:** Let Google manage the runtime. Focus on agent logic, not infrastructure.

#### R3: Gateway Separation
- ✅ Cloud Run as HTTP proxy to Agent Engine
- ❌ No `Runner` imports in gateway code

**Why:** Clean separation means gateways can restart without touching agents.

#### R4: CI-Only Deployments
- ✅ All deploys via GitHub Actions + Workload Identity Federation
- ❌ No manual `gcloud deploy` or service account keys

**Why:** Reproducible deployments. No "works on my machine" excuses.

#### R5: Dual Memory Wiring
- ✅ VertexAiSessionService + VertexAiMemoryBankService
- ✅ `after_agent_callback` to persist sessions

**Why:** Actual conversation continuity, not just storing embeddings.

#### R6: Single Docs Folder
- ✅ All docs in `000-docs/` with `NNN-CC-ABCD-name.md` format
- ❌ No scattered docs, multiple doc folders, or random READMEs

**Why:** Predictable structure. Easy to find things. Easy to copy to new repos.

#### R7: SPIFFE Identity
- ✅ `spiffe://intent.solutions/agent/bobs-brain/<env>/<region>/<version>`
- ✅ Propagated in AgentCard, logs, HTTP headers

**Why:** Immutable identity makes tracing and security audits straightforward.

#### R8: Drift Detection
- ✅ `scripts/ci/check_nodrift.sh` runs first in CI
- ❌ Blocks alternative frameworks, Runner in gateways, local creds

**Why:** Prevent architectural decay before it gets committed.

### Enforcement

The drift check script (`scripts/ci/check_nodrift.sh`) runs **before** anything else in CI:

```yaml
# .github/workflows/ci.yml
jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check for drift violations
        run: bash scripts/ci/check_nodrift.sh
        # Fails build if violations found
```

If drift check fails, the entire pipeline stops. No tests run. No deployment happens. Fix the violations first.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud account with Vertex AI enabled
- (Optional) Slack workspace for integration
- (Optional) GitHub account for CI/CD

### 1. Clone & Setup

```bash
# Get the code
git clone https://github.com/intent-solutions-io/bobs-brain.git
cd bobs-brain

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Edit .env with your GCP project details
```

### 2. Verify Everything Works

```bash
# Check all imports are valid
python3 -c "
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from a2a.types import AgentCard
print('✅ All ADK imports working')
"

# Run drift detection locally
bash scripts/ci/check_nodrift.sh
```

### 3. Deploy (CI Recommended)

**Option A: Via GitHub Actions (Recommended)**
```bash
# Push to main triggers automatic deployment
git add .
git commit -m "feat: your feature description"
git push origin main

# GitHub Actions handles:
# 1. Drift detection
# 2. Tests
# 3. Docker build
# 4. Deploy to Agent Engine
# 5. Deploy gateways
```

**Option B: Manual (Local Testing Only)**
```bash
# This is for local development only
# Production deployments MUST go through CI
cd agents/bob
python3 -c "from agent import get_agent; a = get_agent(); print('✅ Agent created')"
```

### 4. Run Portfolio Audits

```bash
# Audit all local repos
python3 scripts/run_portfolio_swe.py

# Audit specific repos
python3 scripts/run_portfolio_swe.py --repos bobs-brain,diagnosticpro

# Export results
python3 scripts/run_portfolio_swe.py --output audit.json --markdown report.md
```

**That's it.** You've got a working AI agent that can audit code, fix issues, and generate docs.

---

## 📦 Portfolio Multi-Repo Audits

One of Bob's superpowers: **auditing multiple repos at once** and giving you org-wide metrics.

### How It Works

1. Define your repos in `config/repos.yaml`:

```yaml
repos:
  - id: bobs-brain
    display_name: "Bob's Brain"
    local_path: "."
    tags: ["adk", "agents", "production"]
    slack_channel: "#bobs-brain-alerts"

  - id: diagnosticpro
    display_name: "DiagnosticPro"
    local_path: "external"  # Not checked out locally (skipped gracefully)
    tags: ["production", "firebase"]
```

2. Run the portfolio orchestrator:

```bash
python3 scripts/run_portfolio_swe.py
```

3. Get aggregated results:

```json
{
  "portfolio_run_id": "c98cc8f2-...",
  "timestamp": "2025-11-20T03:52:34Z",
  "summary": {
    "total_repos_analyzed": 5,
    "total_issues_found": 42,
    "total_issues_fixed": 30,
    "fix_rate": 71.4
  },
  "issues_by_severity": {
    "high": 5,
    "medium": 20,
    "low": 17
  },
  "repos": [...]
}
```

### CLI Options

```bash
# Basic usage
python3 scripts/run_portfolio_swe.py

# Specific repos only
python3 scripts/run_portfolio_swe.py --repos bobs-brain,diagnosticpro

# Filter by tags
python3 scripts/run_portfolio_swe.py --tag production

# Different modes
python3 scripts/run_portfolio_swe.py --mode preview   # Read-only analysis
python3 scripts/run_portfolio_swe.py --mode dry-run   # Show what would change
python3 scripts/run_portfolio_swe.py --mode create    # Actually fix issues

# Export results
python3 scripts/run_portfolio_swe.py --output results.json --markdown report.md
```

### Automated CI/CD Integration

The portfolio audit runs nightly via GitHub Actions:

```bash
# Manual trigger
gh workflow run portfolio-swe.yml \
  --ref main \
  --field repos=all \
  --field mode=preview
```

**Features:**
- ✅ Multi-repo ARV checks
- ✅ Automated audits (nightly at 2 AM UTC)
- ✅ JSON/Markdown export
- ✅ GCS storage for historical results (v0.9.0+)
- 📐 Slack notifications (coming soon)
- 📐 GitHub issue creation (coming soon)

**Roadmap:**
- **LIVE1-GCS (v0.9.0):** ✅ Complete - GCS org-wide storage
- **LIVE-BQ (Future):** BigQuery analytics integration
- **LIVE2 (Planned):** Vertex AI Search RAG + Agent Engine calls (dev-only)
- **LIVE3 (Planned):** Slack notifications + GitHub issue creation

---

## 🗄️ Org-Wide Storage

**New in v0.9.0** - All your portfolio audit results stored in one place for easy querying and analytics.

### What It Does

- **Centralized GCS bucket** for all audit results
- **Lifecycle management** (90-day retention for per-repo details)
- **Graceful fallback** (writes never crash your pipeline)
- **Environment-aware** (separate buckets for dev/staging/prod)

### GCS Bucket Structure

```
gs://intent-org-knowledge-hub-{env}/
├── portfolio/runs/{run_id}/summary.json        # Portfolio-level summary
├── portfolio/runs/{run_id}/per-repo/*.json     # Per-repo details
├── swe/agents/{agent}/runs/{run_id}.json       # Single-repo runs (future)
├── docs/                                        # Org docs (future)
└── vertex-search/                               # RAG snapshots (LIVE2+)
```

### Setup

**1. Enable in Terraform:**
```hcl
# infra/terraform/envs/dev.tfvars
org_storage_enabled     = true
org_storage_bucket_name = "intent-org-knowledge-hub-dev"
```

**2. Check readiness:**
```bash
python3 scripts/check_org_storage_readiness.py
python3 scripts/check_org_storage_readiness.py --write-test
```

**3. Enable writes:**
```bash
export ORG_STORAGE_WRITE_ENABLED=true
export ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev
```

**4. Run audit:**
```bash
python3 scripts/run_portfolio_swe.py
# Results automatically written to GCS
```

### Key Features

- ✅ **Opt-in by default** - Nothing writes unless you explicitly enable it
- ✅ **Graceful errors** - If GCS fails, pipeline continues (just logs error)
- ✅ **Fully tested** - 36 tests with 100% pass rate
- ✅ **IAM-secured** - Service account-based access control

**Documentation:**
- [Org Storage Architecture](000-docs/6767-AT-ARCH-org-storage-architecture.md)
<!-- - [LIVE1-GCS Implementation AAR](000-docs/6767-113-AA-REPT-live1-gcs-implementation.md) (FILE NOT FOUND) -->

---

## 🎨 Use as Template

Bob's Brain isn't just a product – it's a **complete multi-agent template** you can copy to your own repos.

### What You Get

When you port Bob's Brain to your product (DiagnosticPro, PipelinePilot, etc.):

- ✅ **Multi-agent architecture** - bob → foreman → iam-* specialists
- ✅ **SWE pipeline** - audit → issues → fixes → QA → docs
- ✅ **Shared contracts** - JSON schemas for all agent interactions
- ✅ **A2A communication** - Agent-to-Agent protocol wiring
- ✅ **ARV checks** - Agent Readiness Verification for CI
- ✅ **Gateway services** - A2A and Slack endpoints
- ✅ **Terraform infrastructure** - Agent Engine, Cloud Run, IAM
- ✅ **CI/CD workflows** - Drift check, tests, deploy
- ✅ **Documentation system** - 000-docs/ with [filing standards v3.0](000-docs/6767-DR-STND-document-filing-system-standard-v3.md)

### Time to Port

- **Basic setup:** 1-2 days
- **Full integration:** 1 week
- **Production-ready:** 2 weeks (with proper testing)

### Porting Guides

Start here:
1. [Porting Guide](000-docs/6767-DR-GUIDE-porting-iam-department-to-new-repo.md) - Step-by-step instructions
2. [Integration Checklist](000-docs/6767-DR-STND-iam-department-integration-checklist.md) - Don't miss anything
3. [Template Scope](000-docs/6767-DR-STND-iam-department-template-scope-and-rules.md) - What to customize
4. [Template Files](templates/iam-department/README.md) - Reusable components

### Original Template

Bob's Brain is built on top of:
- [iam1-intent-agent-model-vertex-ai](https://github.com/jeremylongshore/iam1-intent-agent-model-vertex-ai)

That's the foundational Hard Mode architecture. Bob extends it into a full multi-agent department.

---

## 🚀 Deployment to Vertex AI Agent Engine

Bob deploys to **Vertex AI Agent Engine** using ADK CLI with full CI/CD automation.

### Deployment Architecture

```
GitHub Actions (WIF)
    ↓
ADK CLI (adk deploy agent_engine)
    ↓
Vertex AI Agent Engine ← Managed runtime
    ↑
Cloud Run Gateways (A2A + Slack) ← HTTP proxies only
```

### Prerequisites

Before deploying:
- ✅ GCP project with Vertex AI enabled
- ✅ GitHub secrets configured (WIF provider, service account)
- ✅ Terraform infrastructure applied (`infra/terraform/`)
- ✅ Staging bucket created (`gs://<project-id>-adk-staging`)

### CI/CD Deployment (Recommended)

```bash
# Push to main triggers automatic deployment
git push origin main

# GitHub Actions automatically:
# 1. Runs drift detection (blocks if violations)
# 2. Runs tests
# 3. Authenticates via WIF (no keys!)
# 4. Builds Docker container
# 5. Deploys to Agent Engine
# 6. Deploys Cloud Run gateways
```

### Terraform Infrastructure Deployment (R4-Compliant)

**All infrastructure (including Slack gateway) is deployed via Terraform only:**

```bash
# ⚠️ NEVER use manual gcloud commands for Slack Bob
# ❌ WRONG: gcloud run services update slack-webhook ...
# ✅ CORRECT: Use Terraform + GitHub Actions

# Deploy via GitHub Actions (RECOMMENDED):
# 1. Update Terraform code in infra/terraform/
# 2. Create PR → terraform plan runs automatically
# 3. Merge PR to main
# 4. Trigger workflow: .github/workflows/terraform-prod.yml
#    - Set apply=true for production deployment
```

**Local Terraform Testing (Validation Only):**
```bash
# Validate Terraform changes locally (no apply)
cd infra/terraform
terraform init -backend-config="bucket=bobs-brain-terraform-state"
terraform validate
terraform plan -var-file=envs/prod.tfvars

# ⚠️ NEVER run terraform apply locally for production
# Always use GitHub Actions for actual deployments
```

**Important:** R4 enforces **CI-only deployments**. Manual `gcloud` or local `terraform apply` commands create deployment drift and violate Hard Mode rules.

---

## 💬 Slack Integration

Bob communicates via Slack through an **R3-compliant Cloud Run gateway** that proxies to Agent Engine.

### Architecture

```
Slack Events API
    ↓
Cloud Run: slack-webhook (R3 gateway - HTTP proxy only)
    ├─ Verifies Slack signature
    ├─ Transforms to Agent Engine format
    └─ POST /reasoningEngines/{id}:query
        ↓
Vertex AI Agent Engine: Bob
    ├─ ADK agent (google-adk)
    ├─ Dual Memory (Session + Memory Bank)
    └─ Returns response
        ↓
Cloud Run: slack-webhook
    └─ Formats response for Slack
```

### Deployment (R4-Compliant)

**✅ Correct Method:**
```bash
# Use Terraform + GitHub Actions workflow
# Workflow: .github/workflows/terraform-prod.yml
# Module: infra/terraform/modules/slack_bob_gateway/
```

**❌ DEPRECATED - DO NOT USE (R4 Violations):**
```bash
# ⛔ THESE COMMANDS ARE BANNED - R4 HARD MODE VIOLATION
# Manual deployments create drift and violate CI-only deployment rules

# NEVER USE THESE:
gcloud run services update slack-webhook ...  # R4 VIOLATION - Use Terraform
gcloud run deploy slack-webhook --source .    # R4 VIOLATION - Use Terraform

# ⚠️  Using these commands will:
# - Create configuration drift (dev != prod)
# - Bypass CI quality gates (drift detection, ARV, tests)
# - Leave orphaned resources (service accounts, secrets)
# - Violate audit trail requirements
# - Block future Terraform deploys (state mismatch)

# ✅ CORRECT METHOD: See above - Use Terraform + GitHub Actions workflow
```

**Configuration:**
- Secrets: Stored in Secret Manager (`slack-bot-token`, `slack-signing-secret`)
- Feature Flag: `slack_bob_enabled = true` in `envs/prod.tfvars`
- Environment: `SLACK_BOB_ENABLED=true` set by Terraform module

**Operator Guide:** See `000-docs/164-AA-REPT-phase-24-slack-bob-ci-deploy-and-restore.md` for complete deployment instructions.

---

## 📚 Documentation

All docs live in `000-docs/` following the `NNN-CC-ABCD-name.md` format.

### 🎯 Start Here (New to the Repo?)

**For Developers:**
1. **[Master Index](000-docs/6767-DR-INDEX-bobs-brain-standards-catalog.md)** - Complete reference map for Agent Engine/A2A/Inline Deployment
2. **[ADK/Agent Engine Spec](000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md)** - Hard Mode rules (R1-R8) and architecture
3. **[CLAUDE.md](CLAUDE.md)** - How Claude Code works with this repo

**For Operators:**
1. **[DevOps Playbook](000-docs/120-AA-AUDT-appaudit-devops-playbook.md)** - Complete operator guide from /appaudit analysis
2. **[Operations Runbook](000-docs/6767-RB-OPS-adk-department-operations-runbook.md)** - Day-to-day operations
3. **[Inline Deployment Standard](000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md)** - Agent Engine deployment guide

**For Template Adopters:**
1. **[Porting Guide](000-docs/6767-DR-GUIDE-porting-iam-department-to-new-repo.md)** - Copy department to new repo
2. **[Integration Checklist](000-docs/6767-DR-STND-iam-department-integration-checklist.md)** - Don't miss anything
3. **[Template Standards](000-docs/6767-DR-STND-iam-department-template-scope-and-rules.md)** - Customization rules

### Key Standards (6767 Canonical Docs)

**Agent Engine & Deployment (v0.10.0):**
- **[Master Index](000-docs/6767-DR-INDEX-bobs-brain-standards-catalog.md)** - Complete reference map (START HERE)
- [ADK/Agent Engine Spec](000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md) - Hard Mode rules (R1-R8)
- [Inline Source Deployment](000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md) - Deploy pattern, ARV gates
- [ARV Minimum Gate](000-docs/6767-DR-STND-arv-minimum-gate.md) - Agent Readiness Verification baseline
- [Lazy-Loading App Pattern](000-docs/6767-LAZY-DR-STND-adk-lazy-loading-app-pattern.md) - Module-level app pattern

**A2A Protocol & AgentCards (v0.10.0):**
- [AgentCards & A2A Contracts](000-docs/6767-DR-STND-agentcards-and-a2a-contracts.md) - Contract structure, skill patterns
- [Prompt Design & A2A](000-docs/6767-DR-STND-prompt-design-a2a-contracts-iam-dept.md) - 5-part template, contract-first
- [a2a-inspector Integration](000-docs/6767-A2AINSP-AA-REPT-a2a-inspector-integration-for-department-adk-iam.md) - Runtime validation

**Portfolio & Org Storage (v0.9.0):**
<!-- - [Portfolio Scope](000-docs/6767-109-PP-PLAN-multi-repo-swe-portfolio-scope.md) - PORT1/PORT2/PORT3 plan (FILE NOT FOUND) -->
<!-- - [Portfolio Orchestrator AAR](000-docs/6767-110-AA-REPT-portfolio-orchestrator-implementation.md) - Implementation (FILE NOT FOUND) -->
- [Org Storage Architecture](000-docs/6767-AT-ARCH-org-storage-architecture.md) - GCS hub design
<!-- - [LIVE1-GCS AAR](000-docs/6767-113-AA-REPT-live1-gcs-implementation.md) - v0.9.0 implementation (FILE NOT FOUND) -->

**IAM Department Templates:**
- [Operations Runbook](000-docs/6767-RB-OPS-adk-department-operations-runbook.md) - Day-to-day operations
- [Porting Guide](000-docs/6767-DR-GUIDE-porting-iam-department-to-new-repo.md) - Step-by-step instructions
- [Integration Checklist](000-docs/6767-DR-STND-iam-department-integration-checklist.md) - Complete checklist
- [Template Standards](000-docs/6767-DR-STND-iam-department-template-scope-and-rules.md) - Scope and customization
<!-- - [User Guide](000-docs/6767-DR-GUIDE-how-to-use-bob-and-iam-department-for-swe.md) - How to use this department (FILE NOT FOUND) -->

### Document Filing System

Format: `NNN-CC-ABCD-description.md`

- **NNN:** Sequential number (001-999)
- **CC:** Category (PP, AT, TQ, OD, LS, RA, MC, PM, DR, UC, BL, RL, AA, WA, DD, MS)
- **ABCD:** Document type (ARCH, REPT, ALIG, CRIT, CONF, etc.)
- **description:** 1-4 words in kebab-case

**Example:** `6767-AT-ARCH-org-storage-architecture.md`

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=agents.bob --cov-report=html

# Verbose output
pytest -v
```

### Test Coverage

- ✅ Agent initialization and tool registration
- ✅ A2A protocol and AgentCard generation
- ✅ Portfolio orchestrator (36 tests for org storage)
- ✅ Storage config and GCS writer
- ✅ Memory wiring (Session + Memory Bank)

---

## 🛠️ Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature
```

### 2. Make Changes

- Edit agent logic in `agents/bob/`
- Edit gateway code in `service/` (proxies only, no Runner!)
- Add tests in `tests/`
- Update docs in `000-docs/`

### 3. Run Local Checks

```bash
# Drift detection
bash scripts/ci/check_nodrift.sh

# Tests
pytest

# Linting
flake8 agents/bob/ service/
black --check agents/bob/ service/
mypy agents/bob/ service/
```

### 4. Commit & Push

```bash
git add .
git commit -m "feat(scope): description

Details about the change

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"
git push origin feature/your-feature
```

### 5. Create Pull Request

CI will automatically:
- Run drift detection
- Run tests
- Deploy to staging (if PR is to main)

---

## 🔧 Configuration

### Environment Variables

Required in `.env`:

```bash
# GCP Core
PROJECT_ID=your-gcp-project
LOCATION=us-central1
AGENT_ENGINE_ID=your-engine-id
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0

# Application
APP_NAME=bobs-brain
APP_VERSION=0.10.0

# Org Storage (v0.10.0+)
ORG_STORAGE_WRITE_ENABLED=true
ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev

# Vertex AI Search
VERTEX_SEARCH_DATASTORE_ID=adk-documentation

# Gateway URLs
PUBLIC_URL=https://your-a2a-gateway.run.app
```

See [.env.example](.env.example) for full template.

### Slack Integration (Dev)

Talk to Bob via @mentions in Slack (dev environment only):

```bash
# Enable Slack bot
SLACK_BOB_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
A2A_GATEWAY_URL=https://a2a-gateway-xxx.run.app  # Preferred routing
```

**Quick Start:**
1. Get credentials from [Slack API Apps](https://api.slack.com/apps) → bobs_brain (`A099YKLCM1N`)
2. Set env vars in `.env` or GitHub Secrets
3. Deploy: `gh workflow run deploy-slack-webhook.yml`
4. Test: `make slack-dev-smoke`
5. Mention in Slack: `@bobs_brain Hello!`

<!-- **Full Guide:** See [000-docs/6772-DR-GUIDE-slack-dev-integration-operator-guide.md](000-docs/6772-DR-GUIDE-slack-dev-integration-operator-guide.md) (FILE NOT FOUND) -->

### Terraform Variables

In `infra/terraform/envs/{env}.tfvars`:

```hcl
project_id = "your-gcp-project"
location   = "us-central1"

# Org Storage
org_storage_enabled     = true
org_storage_bucket_name = "intent-org-knowledge-hub-dev"

# Agent Engine
agent_engine_id   = "bobs-brain-dev"
agent_runtime_sa  = "bob-agent-dev@your-project.iam.gserviceaccount.com"
```

---

## 🚨 Troubleshooting

### Drift Detection Failed

**Symptom:** CI fails with "Drift violations detected"

**Fix:**
```bash
# Run locally to see violations
bash scripts/ci/check_nodrift.sh

# Common issues:
# 1. Imported Runner in service/ → Remove it, use REST API
# 2. Found LangChain/CrewAI → Remove alternative frameworks
# 3. Service account keys in repo → Remove, use WIF
```

### Agent Can't Find ADK Docs

**Symptom:** Agent says "I don't have information about that ADK pattern"

**Fix:**
```bash
# Set up Vertex AI Search
bash scripts/deployment/setup_vertex_search.sh

# Check datastore exists
export VERTEX_SEARCH_DATASTORE_ID=adk-documentation
```

### Org Storage Not Writing

**Symptom:** Portfolio audit runs but no GCS files appear

**Fix:**
```bash
# Check readiness
python3 scripts/check_org_storage_readiness.py --write-test

# Common issues:
# 1. ORG_STORAGE_WRITE_ENABLED not set → export ORG_STORAGE_WRITE_ENABLED=true
# 2. Bucket doesn't exist → Apply Terraform with org_storage_enabled=true
# 3. No IAM permissions → Add service account to org_storage_writer_service_accounts
```

### Deploy Failed: Agent Engine Not Found

**Symptom:** `adk deploy` fails with "Agent Engine not found"

**Fix:**
```bash
# Create infrastructure first
cd infra/terraform
terraform init
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# Verify engine exists
gcloud ai agent-engines list --region=us-central1
```

---

## 📊 Project Status

**Current Version:** v1.1.0 – Google Multi-Agent Patterns Rollout

**What's New in v1.1.0:**
- ✅ **Sequential Pipeline** - SequentialAgent with state passing via `output_key`
- ✅ **Parallel Fan-Out** - ParallelAgent with unique output_keys per agent
- ✅ **Quality Gates** - LoopAgent with Generator-Critic iteration
- ✅ **Human-in-the-Loop** - Callbacks with RiskLevel classification (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ **Pattern Templates** - 8 reusable templates in `templates/` directory

**Pattern Coverage:** 7 of 8 patterns from [Google's multi-agent patterns guide](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)

**Community:**
- Featured in [Agent Starter Pack community showcase (PR #580)](https://github.com/GoogleCloudPlatform/agent-starter-pack/pull/580)

**Deployment Status:**
- ✅ **Agent Engine**: Inline source deployment with ARV gates
- ✅ **A2A / AgentCard**: Foreman + workers with validation
- ✅ **CI/CD**: Drift detection, tests, Terraform-only deploys (R4 compliant)
- ✅ **Slack Integration**: R3-compliant gateway via Terraform

**Metrics:**
- 9 agent implementations
- 8 reusable pattern templates
- 17 test files (unit + integration)
- CI passes: lint, drift detection, ARV gates
- 8 enforced Hard Mode rules (R1-R8)

---

## 🔧 What Was Wrong and What We Fixed (v0.7.0)

Before Hard Mode, Bob's Brain had typical agent repo problems:

**Problems:**
- ❌ Mixed frameworks (ADK + LangChain + custom code)
- ❌ Self-hosted runners (containers that sometimes crashed)
- ❌ Manual deployments (inconsistent environments)
- ❌ Scattered docs (README, wiki, notion, random .md files)
- ❌ No drift detection (architectural decay over time)

**Solutions (Hard Mode):**
- ✅ R1-R8 rules enforced in CI
- ✅ Vertex AI Agent Engine (let Google manage runtime)
- ✅ GitHub Actions with WIF (reproducible deploys)
- ✅ Single `000-docs/` folder with filing system
- ✅ Automated drift checks block violations

**Result:** Agent system that's maintainable, scalable, and actually works in production.

---

## 🤝 Contributing

We welcome contributions! Here's how:

### Reporting Issues

- Use GitHub Issues
- Include drift check output if relevant
- Provide minimal reproduction steps

### Pull Requests

1. Fork the repository
2. Create feature branch (`feature/your-feature`)
3. Follow Hard Mode rules (R1-R8)
4. Add tests for new functionality
5. Update docs in `000-docs/`
6. Ensure drift check passes
7. Submit PR with clear description

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/bobs-brain.git
cd bobs-brain

# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run checks
bash scripts/ci/check_nodrift.sh
pytest
```

---

## 📄 License

[Elastic License 2.0 (ELv2)](LICENSE) - See LICENSE file for details.

You're free to:
- Use this for internal purposes
- Modify and learn from it
- Use as a template for your own agents

Restrictions: Cannot provide as a managed service to third parties.

---

## 🔗 Resources

**This Project:**
- [GitHub Repository](https://github.com/intent-solutions-io/bobs-brain)
- [Release Notes](https://github.com/intent-solutions-io/bobs-brain/releases)
- [Documentation](000-docs/)
- [Project Site](https://bobs-brain.web.app)

**Google ADK & Vertex:**
- [ADK Documentation](https://cloud.google.com/vertex-ai/docs/agent-development-kit)
- [Agent Engine Docs](https://cloud.google.com/vertex-ai/docs/agent-engine)
- [Vertex AI Platform](https://cloud.google.com/vertex-ai)

**Related Technologies:**
- [A2A Protocol](https://github.com/google/adk-python) - Agent-to-Agent communication
- [SPIFFE](https://spiffe.io/) - Immutable identity framework
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) - Keyless auth

---

<div align="center">

**Built with ❤️ using Google ADK**

[⭐ Star us on GitHub](https://github.com/intent-solutions-io/bobs-brain) • [📖 Read the docs](000-docs/) • [🌐 Project Site](https://bobs-brain.web.app)

</div>
