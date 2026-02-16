# CLAUDE Working Notes (Archive)

> This file is an archive of historical CLAUDE.md content.
> It is **not** the canonical working guide. See the top-level `CLAUDE.md` for the current, lightweight instructions.

---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**Bob's Brain** - Production Slack AI assistant powered by Google ADK and Vertex AI Agent Engine

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/`
**Status:** Production (Hard Mode - CI-only, ADK+Agent Engine enforced)
**Version:** 0.8.0 (Agent Factory Structure)
**Repository:** https://github.com/jeremylongshore/bobs-brain (public)

This is a production-grade **agent factory** implementation following strict "Hard Mode" architectural rules (R1-R8) with CI enforcement and drift protection.

## High-Level Architecture

### Agent Factory Pattern (v0.8.0+)
```
bobs-brain/
├── agents/                    # ALL agents (factory pattern)
│   ├── bob/                   # Bob orchestrator agent
│   │   ├── agent.py           # LlmAgent with dual memory
│   │   ├── a2a_card.py        # A2A protocol card
│   │   └── tools/             # Bob's custom tools
│   └── (future agents)        # iam-adk, iam-issue, iam-fix, etc.
├── service/                   # Protocol gateways (REST proxies)
│   ├── a2a_gateway/           # A2A protocol endpoint
│   └── slack_webhook/         # Slack integration
├── infra/terraform/           # IaC for GCP resources
└── scripts/ci/                # CI/CD enforcement scripts
```

### Deployment Architecture
```
GitHub Actions (WIF Auth)
    ↓
ADK CLI (adk deploy agent_engine)
    ↓
Vertex AI Agent Engine (Managed Runtime)
    ↑
Cloud Run Gateways (REST API Proxy Only)
```

## Common Development Tasks

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_a2a_card.py -v

# Run with coverage
pytest --cov=agents.bob --cov-report=html

# Run drift detection locally
bash scripts/ci/check_nodrift.sh
```

### Local Development
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your values

# Verify imports work
python3 -c "from google.adk.agents import LlmAgent; print('✅ ADK imports working')"

# Test agent locally (smoke test only)
cd agents/bob
python3 -c "from agent import get_agent; a = get_agent(); print('✅ Agent created')"
```

### Deployment (CI/CD Only)
```bash
# All deployments MUST go through GitHub Actions
# Manual deployment is BLOCKED by Hard Mode rules

# Deploy to dev (automatic on push to main)
git push origin main

# Deploy to staging/prod (manual trigger)
# Go to: https://github.com/jeremylongshore/bobs-brain/actions
# Run "Deploy to Vertex AI Agent Engine" workflow
```

### Adding New Agents
```bash
# Future pattern for adding agents to the factory:
# 1. Create new agent directory
mkdir agents/iam-adk

# 2. Implement LlmAgent (following Bob's pattern)
# Copy structure from agents/bob/
# - agent.py (LlmAgent with tools)
# - a2a_card.py (A2A protocol)
# - tools/ (custom tools)

# 3. Update imports to use agents.<name>
# 4. Run drift check
bash scripts/ci/check_nodrift.sh
```

## Portfolio Multi-Repo Operations

Bob's Brain includes a **portfolio orchestrator** for managing multiple repositories simultaneously (PORT1/PORT2/PORT3 phases).

### Repository Registry

**File:** `config/repos.yaml`

Defines all target repositories with metadata:
- `id` - Short identifier
- `display_name` - User-friendly name
- `local_path` - ".", "external", or relative path
- `github_owner`, `github_repo` - GitHub coordinates
- `tags` - For filtering (e.g., "production", "adk")
- `arv_profile` - ARV requirements per repo
- `slack_channel` - Alert destination (LIVE3)

**Python API:**
```python
from config.repos import list_repos, get_repo_by_id

# List all repos
all_repos = list_repos()

# Get specific repo
repo = get_repo_by_id('bobs-brain')
print(repo.display_name)  # "Bob's Brain"
print(repo.is_local)       # True
print(repo.is_current_repo)  # True
```

### Portfolio Orchestrator

**File:** `agents/iam_senior_adk_devops_lead/portfolio_orchestrator.py`

Run multi-repo SWE audits:
```python
from agents.iam_senior_adk_devops_lead.portfolio_orchestrator import run_portfolio_swe

# Audit all local repos
result = run_portfolio_swe(mode='preview')

# Audit specific repos
result = run_portfolio_swe(repo_ids=['bobs-brain'], mode='preview')

# Access results
print(f"Repos analyzed: {result.total_repos_analyzed}")
print(f"Issues found: {result.total_issues_found}")
print(f"Fix rate: {result.total_issues_fixed / result.total_issues_found * 100:.1f}%")
```

### Portfolio CLI

**File:** `scripts/run_portfolio_swe.py`

```bash
# Run portfolio audit on all local repos
python3 scripts/run_portfolio_swe.py

# Specific repos
python3 scripts/run_portfolio_swe.py --repos bobs-brain,diagnosticpro

# Filter by tag
python3 scripts/run_portfolio_swe.py --tag production

# Export results
python3 scripts/run_portfolio_swe.py \
  --output portfolio-results.json \
  --markdown portfolio-report.md

# Different modes
python3 scripts/run_portfolio_swe.py --mode preview   # Read-only
python3 scripts/run_portfolio_swe.py --mode dry-run  # Show what would change
python3 scripts/run_portfolio_swe.py --mode create   # Create fixes
```

### Portfolio ARV Checks

**File:** `scripts/check_arv_minimum.py`

```bash
# Check ARV minimum across all local repos
make check-arv-portfolio

# Or directly
python3 scripts/check_arv_minimum.py --portfolio
```

**Output shows:**
- Local repos checked
- External repos skipped
- Per-repo ARV results
- Portfolio summary (passed/failed/skipped)

### CI/CD Integration (PORT3 - Design)

**Workflow:** `.github/workflows/portfolio-swe.yml`

**Status:** Design-only (PORT3), integrations disabled until LIVE phases

**Current capabilities:**
- ✅ Scheduled nightly audits (2 AM UTC)
- ✅ Manual workflow dispatch with options
- ✅ Multi-repo ARV checks
- ✅ JSON/Markdown export
- ✅ GitHub Actions artifacts (90-day retention)

**Future capabilities (design-only):**
- 📐 GCS result storage (LIVE1+)
- 📐 BigQuery metrics (LIVE2+)
- 📐 Slack notifications (LIVE3)
- 📐 GitHub issue creation (LIVE3)

**Manual trigger:**
```bash
gh workflow run portfolio-swe.yml \
  --ref main \
  --field repos=all \
  --field mode=preview \
  --field environment=dev
```

### Portfolio Documentation

- **PORT1/PORT2/PORT3 Plan:** `000-docs/6767-109-PP-PLAN-multi-repo-swe-portfolio-scope.md`
- **PORT2 AAR:** `000-docs/6767-110-AA-REPT-portfolio-orchestrator-implementation.md`
- **PORT3 CI/Slack Design:** `000-docs/6767-111-AT-ARCH-portfolio-ci-slack-integration-design.md`

### When to Use Portfolio Features

**Use portfolio orchestrator when:**
- Auditing multiple repos for compliance (ADK patterns, ARV requirements)
- Generating aggregated reports across repos
- Running nightly quality checks on all managed repos
- Comparing repos by issue count or compliance score

**Use single-repo pipeline when:**
- Deep-diving into a specific repo
- Implementing fixes in one repo
- Testing changes locally before portfolio run
- Working within a specific repo's context

## Using Bob's Brain as a Reusable Template

Bob's Brain serves as the **canonical reference implementation** for the IAM department pattern. It can be ported to other product repositories (DiagnosticPro, PipelinePilot, Hustle, etc.) as a complete multi-agent software engineering department.

### Template Documentation

- **Template Scope & Rules:** `000-docs/6767-104-DR-STND-iam-department-template-scope-and-rules.md`
  - Defines what's reusable vs product-specific
  - Lists all 30+ parameterization points
  - Explains minimal viable port (foreman + 3 specialists)

- **Porting Guide:** `000-docs/6767-105-DR-GUIDE-porting-iam-department-to-new-repo.md`
  - Step-by-step instructions for copying template to new repo
  - Parameter replacement automation (bash script)
  - Configuration, testing, and CI integration
  - Time estimate: 1-2 days minimal, 1 week full integration

- **Integration Checklist:** `000-docs/6767-106-DR-STND-iam-department-integration-checklist.md`
  - Comprehensive checklist for tracking integration progress
  - Pre-flight requirements, core setup, optional features
  - Success criteria and validation steps

- **Template Files:** `templates/iam-department/README.md`
  - Quick start guide for using template
  - All template files with {{PARAMETER}} placeholders
  - Agent templates (bob, foreman, iam-* specialists)
  - Service templates (gateways), scripts (ARV checks)

### What Gets Ported

The IAM department template includes:

**Core Components (Required):**
- Multi-agent architecture (orchestrator → foreman → specialists)
- SWE pipeline orchestration (audit → issues → fixes → QA → docs)
- Shared contracts (PipelineRequest, IssueSpec, FixPlan, QAVerdict)
- A2A agent-to-agent communication layer
- Configuration modules (repos.yaml, RAG, Agent Engine)
- ARV (Agent Readiness Verification) checks
- Service gateways (A2A, Slack)

**Minimal Viable Port:**
- iam-foreman (orchestrator)
- iam-adk (ADK design/audit specialist)
- iam-issue (issue specification specialist)
- iam-qa (quality assurance specialist)
- Can be set up in < 1 day

**Optional Extensions:**
- Top-level bob orchestrator
- Fix agents (iam-fix-plan, iam-fix-impl)
- Documentation agents (iam-doc, iam-cleanup, iam-index)
- RAG integration with Vertex AI Search
- Slack webhook integration
- Agent Engine deployment

### Quick Porting Overview

1. **Copy template:**
   ```bash
   cp -r templates/iam-department/* /path/to/new-repo/
   ```

2. **Replace parameters:**
   ```bash
   # Use provided script in porting guide
   find . -type f | xargs sed -i 's/{{PRODUCT_NAME}}/yourproduct/g'
   ```

3. **Configure repos.yaml:**
   - Add your product's repositories
   - Define key directories and frameworks

4. **Customize agent prompts:**
   - Add product-specific context to system prompts
   - Implement product-specific tools

5. **Test locally:**
   ```bash
   make check-arv-minimum  # Verify agent structure
   make test-swe-pipeline  # Test pipeline flow
   ```

6. **Integrate with CI:**
   - Add ARV checks to GitHub Actions
   - Deploy via CI/CD

See the porting guide for complete step-by-step instructions with troubleshooting.

## Hard Mode Rules (R1-R8)

These rules are **enforced in CI** and violations will fail the build:

### R1: ADK-Only Implementation
- ✅ Required: `google-adk` LlmAgent
- ❌ Prohibited: LangChain, CrewAI, AutoGen, custom frameworks

### R2: Vertex AI Agent Engine Runtime
- ✅ Required: Deploy to Agent Engine via ADK CLI
- ❌ Prohibited: Self-hosted runners, embedded Runner in Cloud Run

### R3: Gateway Separation
- ✅ Allowed: Cloud Run as REST proxy to Agent Engine
- ❌ Prohibited: Runner imports in `service/`, direct LLM calls

### R4: CI-Only Deployments
- ✅ Required: GitHub Actions with Workload Identity Federation
- ❌ Prohibited: Manual `gcloud deploy`, service account keys

### R5: Dual Memory Wiring
- ✅ Required: VertexAiSessionService + VertexAiMemoryBankService
- ✅ Required: `after_agent_callback` for session persistence

### R6: Single Documentation Folder
- ✅ Required: All docs in `000-docs/` with NNN-CC-ABCD naming
- ❌ Prohibited: Multiple doc folders, scattered documentation

### R7: SPIFFE ID Propagation
- ✅ Required: `spiffe://intent.solutions/agent/bobs-brain/<env>/<region>/<version>`
- ✅ Required: In AgentCard, logs, headers, telemetry

### R8: Drift Detection
- ✅ Required: `scripts/ci/check_nodrift.sh` runs first in CI
- ❌ Blocks: Alternative frameworks, Runner in gateways, local credentials

## ADK/Agent Engine Specification Compliance

**Canonical Specification:** `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`

This repository follows the 6767 ADK/Agent Engine Specification as its guiding architectural standard. All agent development, infrastructure changes, and CI/CD workflows must align with this spec.

### For Future Claude Sessions

When adding new agents or services to this repository:

1. **Ensure compliance with the spec:**
   - Read `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` for current rules
   - Follow R1-R8 Hard Mode rules strictly
   - Implement department conventions (feature flags, safety defaults, etc.)

2. **Update implementation mapping:**
   - Add new implementation locations to `000-docs/121-DR-MAP-adk-spec-to-implementation-and-arv.md`
   - Document file paths, line numbers, and ARV coverage
   - Identify gaps in automated checks

3. **Extend ARV checks if needed:**
   - Update `scripts/check_arv_agents.py` for new agent patterns
   - Update `scripts/check_arv_services.py` for new gateway services
   - Update `scripts/check_arv_config.py` for new configuration defaults
   - Add new ARV scripts if required (see mapping doc for planned scripts)

4. **Run verification:**
   ```bash
   make check-arv-spec     # All spec compliance checks
   make arv-gates          # Complete ARV verification
   ```

5. **Document changes:**
   - Update AARs with alignment decisions
   - Note any intentional deviations with justification
   - Keep spec and mapping docs synchronized

**Key Principle:** The spec, mapping, and ARV checks form a living system. When you change one (e.g., add a new agent), update all three to maintain alignment.

## Key Code Patterns

### Agent Implementation - Lazy-Loading App Pattern (6774)

**All new agents MUST follow the lazy-loading App pattern** for Agent Engine compatibility and optimal cold start performance. See `000-docs/6774-DR-STND-adk-lazy-loading-app-pattern.md` for complete details.

#### Required Pattern (agents/iam_adk/agent.py - template)
```python
from google.adk.agents import LlmAgent
from google.adk import App
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
import os

# ✅ GOOD: Config reads (cheap, no validation yet)
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

def auto_save_session_to_memory(ctx):
    """After-agent callback for R5 compliance"""
    # Auto-save session to Memory Bank

def create_agent() -> LlmAgent:
    """
    Create and configure the LlmAgent.

    This function is called lazily by create_app() on first use.
    Do NOT call this at module import time.

    Enforces:
    - R1: Uses google-adk LlmAgent
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description
    """
    # ✅ Validation happens here (lazy, not at import)
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID environment variable is required")
    if not LOCATION:
        raise ValueError("LOCATION environment variable is required")
    if not AGENT_ENGINE_ID:
        raise ValueError("AGENT_ENGINE_ID environment variable is required")

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="agent_name",
        tools=[...],
        instruction="...",
        after_agent_callback=auto_save_session_to_memory,
    )
    return agent

def create_app() -> App:
    """
    Create the App container for this agent.

    The App wraps the agent and provides lazy initialization compatible
    with Vertex AI Agent Engine.

    Enforces:
    - R2: App designed for Vertex AI Agent Engine deployment
    - R5: Dual memory wiring (Session + Memory Bank)
    """
    # R5: Create memory services (lazy, inside function)
    session_service = VertexAiSessionService(
        project_id=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    # Create App with lazy agent creation
    # Pass create_agent as function reference (not called yet!)
    app_instance = App(
        agent=create_agent,  # ✅ Function reference, not instance
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )
    return app_instance

# ✅ Module-level App (lazy initialization)
# Agent Engine will access this on first request
app = create_app()
```

**Key Principles:**
- ✅ **No heavy work at import time** - Keep imports fast (~50-200ms)
- ✅ **Lazy agent creation** - Agent created on first App invocation
- ✅ **Function reference** - Pass `create_agent` not `create_agent()` to App
- ✅ **Module-level `app`** - Agent Engine expects `app` symbol, not `agent`
- ✅ **Idempotent App** - `create_app()` safe to call multiple times

**Benefits:**
- Faster cold starts (import vs first invocation split)
- Better testing (can import without full env)
- Agent Engine billing (only pay for used agents)
- Clear separation between definition and runtime

**Migration Status:**
- ✅ **iam-adk** - Migrated (v0.8.1, template agent)
- ⏳ **Other agents** - Migration in progress (LAZY-3)

### Gateway Pattern (service/a2a_gateway/main.py)
```python
# NO Runner imports allowed (R3)
# Pure REST proxy to Agent Engine

@app.post("/invoke")
async def invoke_agent(req: InvokeRequest):
    # Get OAuth token
    token = get_gcp_token()

    # Call Agent Engine REST API
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{AGENT_ENGINE_NAME}:query"
    # ... proxy the request
```

## Environment Configuration

Required environment variables in `.env`:

```bash
# Core Configuration
PROJECT_ID=your-gcp-project
LOCATION=us-central1
AGENT_ENGINE_ID=your-engine-id
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.8.0

# Application
APP_NAME=bobs-brain
APP_VERSION=0.8.0

# Vertex AI Search (Phase 3)
VERTEX_SEARCH_DATASTORE_ID=adk-documentation

# Gateway URLs
PUBLIC_URL=https://your-a2a-gateway.run.app
```

## CI/CD Workflows

### GitHub Actions Workflows

1. **ci.yml** - Runs on every push/PR
   - Drift detection (first, blocks all if violations)
   - Unit tests
   - Integration tests
   - Terraform validation

2. **deploy-agent-engine.yml** - Deploys to Vertex AI
   - Uses ADK CLI with `--trace_to_cloud`
   - Workload Identity Federation (no keys)
   - Automatic telemetry setup

3. **deploy-slack-webhook.yml** - Deploys Slack integration
   - Cloud Run service deployment
   - Environment variable injection

## Project Structure Details

### agents/ Directory (Agent Factory)
- `bob/` - Bob orchestrator agent (current)
- Future: `iam-adk/`, `iam-issue/`, `iam-fix/`, etc.
- Each agent has: agent.py, a2a_card.py, tools/

### service/ Directory (Gateways Only)
- `a2a_gateway/` - A2A protocol HTTP endpoint
- `slack_webhook/` - Slack event handler
- **CRITICAL**: No Runner imports, pure REST proxies

### infra/terraform/ Directory
- `main.tf` - Core infrastructure
- `agent_engine.tf` - Agent Engine configuration
- `storage.tf` - GCS buckets for docs/staging
- `iam.tf` - Service accounts and permissions
- `envs/` - Environment-specific tfvars

### scripts/ Directory
- `ci/check_nodrift.sh` - Drift detection (R1-R8 enforcement)
- `deployment/setup_vertex_search.sh` - Vertex AI Search setup
- `adk-docs-crawler/` - ADK documentation tools
- `check_rag_readiness.py` - RAG readiness verification (ARV gate)
- `print_rag_config.py` - RAG configuration dry-run helper

## RAG Readiness Check

The repository includes RAG (Retrieval Augmented Generation) readiness verification as part of the Agent Readiness Verification (ARV) system.

### Running RAG Checks

```bash
# Quick readiness check
make check-rag-readiness

# Verbose check with details
make check-rag-readiness-verbose

# Print current RAG configuration
make print-rag-config

# Run all ARV gates
make arv-gates
```

### CI Integration

The RAG readiness check runs automatically in GitHub Actions:
- **Workflow**: `.github/workflows/ci-rag-readiness.yaml`
- **Triggers**: PRs to main, pushes to main, manual dispatch
- **Status**: Currently soft-blocking (can be made hard-blocking)

### RAG Readiness Standard

See `000-docs/6767-093-DR-STND-bob-rag-readiness-standard.md` for:
- Complete readiness criteria
- Configuration requirements
- Documentation requirements
- Enforcement timeline

## Troubleshooting

### Common Issues

**ImportError: cannot import Runner in service/**
- Cause: Violates R3 (gateways must proxy only)
- Fix: Remove Runner imports, use REST API to Agent Engine

**CI failed: Drift violations detected**
- Cause: Alternative frameworks or forbidden patterns
- Fix: Check output of `check_nodrift.sh`, remove violations

**Deploy failed: Agent Engine not found**
- Cause: Infrastructure not created
- Fix: Run Terraform first, ensure Agent Engine exists

**Agent can't find ADK docs**
- Cause: Vertex AI Search not configured
- Fix: Run `scripts/deployment/setup_vertex_search.sh`

## Version History

- **0.8.0** - Agent Factory Structure (current)
  - Transformed to multi-agent factory pattern
  - `my_agent/` → `agents/bob/` migration
  - Ready for iam-* agent team

- **0.7.0** - Vertex AI Search Integration
  - Added semantic search with 90-95% accuracy
  - Free 5GB tier implementation

- **0.6.0** - Hard Mode Baseline
  - R1-R8 rules with CI enforcement
  - Dual memory wiring
  - Drift detection

## Important Links

- **Repository**: https://github.com/jeremylongshore/bobs-brain
- **Template**: https://github.com/jeremylongshore/iam1-intent-agent-model-vertex-ai
- **Google ADK Docs**: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/docs/agent-engine

## Support

- **Build Captain**: claude.buildcaptain@intentsolutions.io (CI alerts only)
- **Documentation**: See `000-docs/` directory
- **Issues**: GitHub Issues on the repository
- <quick_start_examples>
This section gives you and future agents a **concrete sense of how to actually use all of the above**.

Treat it as a usage guide and sanity check.

--------------------------------------------------
1. HOW I WILL START YOU (TYPICAL /init FLOW)
--------------------------------------------------

A typical startup will look like this:

1) I send `/init` with:
   - The system rules (`<phases_and_docs>`, `<multi_agent_and_plugins>`, `<current_mission>`, `<execution_rules>`, `<init_wrapper>`),
   - Plus repo context (e.g., “we are in `bobs-brain` on branch X”).

2) You respond with:
   - `<understanding>` – your summary.
   - `<phase_proposal>` – for the next phase (usually Phase 1 at the start).
   - `<questions>` – only if something truly blocks you.

3) I respond with:
   - `APPROVE_PHASE_1` (or similar),
   - Or a minor adjustment to your `<phase_proposal>`.

4) Only THEN do you:
   - Start inspecting files using plugins,
   - Propose code/config/doc changes in small, reviewable steps.

--------------------------------------------------
2. EXAMPLE: GOOD FIRST RESPONSE FROM YOU
--------------------------------------------------

Here is a **sample** of what a strong first response from you might look like after this init (for illustration only):

<understanding>
- `bobs-brain` is the ADK / Agent Engineering Department for this org and also the home for the global `bob` agent.
- My job is to evolve it into a canonical pattern for an ADK-based SWE department, with `bob` as global orchestrator, `iam-senior-adk-devops-lead` as this department’s foreman, and a set of iam-* specialists for ADK design, issues, fixes, QA, docs, cleanup, and indexing.
- All significant work must be structured into phases, each with at least one AAR in `000-docs/` following your filing system (`NNN-AA-PLAN-*`, `NNN-AA-REPT-*`).
- I must use plugins/tools to inspect the actual repo (code, docs, infra, CI) and consult ADK/Vertex documentation instead of guessing, then apply those patterns here.
- I will think in terms of helper-agent patterns (adk-skeleton-coder, adk-pattern-auditor, adk-a2a-wiring-engineer, adk-terraform-infra-coder, adk-ci-arv-pipeline-engineer) and design my plans so they could be automated later.
- I will maintain Git/commit hygiene by proposing small, logical chunks with `<type>(<scope>): <subject>` commit messages, and always tie work back to a phase and its AAR.

<phase_proposal>
- Phase name: Phase 1 – Design & Scaffold `iam-senior-adk-devops-lead`
- Scope:
  - Define the role and responsibilities of `iam-senior-adk-devops-lead` as the departmental foreman between `bob` and the iam-* specialists.
  - Scaffold a minimal ADK agent under `agents/iam-senior-adk-devops-lead/` aligned with existing patterns in `agents/bob/`.
  - Draft PLAN and AAR docs for this phase in `000-docs/`.
- Branch:
  - `phase-1/iam-senior-adk-devops-lead`
- PLAN doc (placeholder ID):
  - `NNN-AA-PLAN-iam-senior-adk-devops-lead-design.md` (NNN to be chosen based on existing 000-docs sequence).
- AAR doc (placeholder ID):
  - `NNN-AA-REPT-iam-senior-adk-devops-lead-implementation.md`
- Steps:
  1) Use repo plugins to:
     - List and inspect `agents/bob/`,
     - Inspect `000-docs/` index to find the next NNN and existing architecture docs,
     - Inspect `.github/workflows/` and `infra/terraform/` for current patterns.
  2) Conceptually invoke **adk-skeleton-coder** to:
     - Propose the directory structure and initial `agent.py` for `agents/iam-senior-adk-devops-lead/`,
     - Define a first-pass system prompt for this foreman (high-level responsibilities, delegation model).
  3) Draft the PLAN doc in `000-docs/NNN-AA-PLAN-iam-senior-adk-devops-lead-design.md`:
     - Objectives, scope, design decisions, planned files.
  4) Propose code skeletons and doc skeletons in small diffs:
     - New directory: `agents/iam-senior-adk-devops-lead/`
     - Files: `agent.py`, `README.md`, optional `prompts/system.md`.
  5) Outline the content for the eventual AAR (`NNN-AA-REPT-...`) so we know what evidence to collect as we implement.
- Suggested commits (draft):
  - `feat(agents): scaffold iam-senior-adk-devops-lead foreman`
    - Add `agents/iam-senior-adk-devops-lead/agent.py` with ADK-style skeleton.
    - Add `agents/iam-senior-adk-devops-lead/README.md` describing role and responsibilities.
  - `docs(000-docs): add plan for iam-senior-adk-devops-lead design`
    - Create PLAN doc in `000-docs/` with scope, decisions, and steps for this phase.

<questions>
- [Optional and only if truly blocking; otherwise this section is empty or omitted.]

--------------------------------------------------
3. HOW I WILL GIVE YOU TASKS AFTER INIT
--------------------------------------------------

After the init and your first `<phase_proposal>`, I will give you tasks in a style like:

- “Proceed with Phase 1 as proposed; show me the directory and file skeletons for `iam-senior-adk-devops-lead`.”
- “Update Phase 2 to focus on iam-adk + iam-issue only, and propose the `IssueSpec` schema.”
- “Run an ADK alignment audit on the current bob + foreman setup and propose issues + fixes.”

For each task:
- You respond with a short `<plan>` tied to an existing or new phase.
- Then you provide:
  - `Summary`
  - `Files`
  - `Suggested commits`
  - `Tests`
  - `Docs / AAR`

Always:
- Use helper-agent patterns and plugins where appropriate.
- Keep the work bounded to the active phase.
- Ensure there is a clear path from:
  - Phase → commits → AAR → reusable pattern.

--------------------------------------------------
4. MENTAL MODEL CHECK
--------------------------------------------------

Before you act on any new instruction in this repo, silently check:

- “Which phase does this belong to?”
- “Which agents are in scope (bob, iam-senior-adk-devops-lead, which iam-* )?”
- “Which helper-agent pattern(s) am I conceptually leaning on?”
- “Which plugins/tools do I need to consult first?”
- “What will the AAR for this phase need from me (artifacts, decisions, tests)?”

If you keep answering those questions while you work, you will help turn `bobs-brain` into the **canonical, copy-pasteable ADK department standard** we want.
</quick_start_examples>
- <adk_alignment_and_knowledge>
This department’s power depends on staying tightly aligned with **official ADK / Vertex guidance** and keeping a high-quality internal knowledge base.

You must treat **knowledge ingestion + alignment** as first-class responsibilities, not afterthoughts.

--------------------------------------------------
1. ADK / VERTEX KNOWLEDGE SOURCES
--------------------------------------------------

Assume the following categories of knowledge are (or will be) ingested and available via your search/knowledge plugins:

- **Official ADK docs**
  - `https://google.github.io/adk-docs/`
  - Core ADK concepts, agent patterns, tools, memory, A2A, etc.

- **Agent Engine / A2A patterns**
  - Official documentation pages.
  - Blog posts such as:
    - “A2A agent patterns with the Agent Development Kit (ADK)” on Medium.
  - Sample repos and notebooks demonstrating Agent Engine + ADK integration.

- **Internal project docs**
  - This repo’s `000-docs/` (plans, AARs, runbooks, blueprints).
  - Any future departmental standards we codify.

- **Code + infra**
  - The code in `agents/`, `service/`, `infra/`, `scripts/`, `.github/workflows/`.
  - Example AgentCards, gateway code, Terraform modules, CI workflows.

Your knowledge/search plugins should be used to:
- Look up current ADK patterns and avoid guessing.
- Cross-check local patterns against official guidance.
- Locate relevant internal docs before designing something new.

--------------------------------------------------
2. IAM-INDEX AND KNOWLEDGE STEWARDSHIP
--------------------------------------------------

Within this department, treat **knowledge stewardship** as a shared responsibility:

- `iam-index`
  - Owns the mapping from:
    - ADK/Agent Engine docs,
    - Blog posts,
    - Example repos,
    - `000-docs/` internal standards,
  - To:
    - Vertex AI Search indexes,
    - GCS buckets,
    - Any other retrieval layer we use.
  - Provides tools/abstractions for other agents (especially `iam-adk` and `iam-senior-adk-devops-lead`) to query those indices instead of scraping raw web.

- `iam-adk`
  - Uses those indices to:
    - Extract patterns,
    - Compare local implementations against current recommendations,
    - Propose updates.

- `iam-senior-adk-devops-lead`
  - Coordinates:
    - When knowledge updates should trigger audits,
    - Which patterns/templates must be updated,
    - How changes are rolled out (phases, AARs, CI updates).

You must think in terms of this triangle:
- `iam-index` (what we know and where it lives),
- `iam-adk` (how we interpret + apply it),
- `iam-senior-adk-devops-lead` (how we standardize + enforce it).

--------------------------------------------------
3. NO-DRIFT POLICY (ADK / VERTEX ALIGNMENT)
--------------------------------------------------

Drift from official ADK / Vertex patterns is not acceptable without explicit, documented reasons.

Your responsibilities:

1) **Detect drift**
   - Use plugins to:
     - Compare our agent structures, tools, and A2A setups to current ADK docs and examples.
     - Check for deprecated APIs, outdated patterns, or anti-patterns.
   - Use `adk-pattern-auditor` (conceptually) to:
     - Scan the repo for:
       - Old frameworks (e.g., LangChain) creeping into agent code,
       - Custom glue that should be replaced by ADK features,
       - Non-standard memory or A2A wiring.

2) **Document drift**
   - When drift is found, capture it in:
     - Structured findings (IssueSpec-style objects),
     - GitHub issues (conceptually),
     - An AAR if part of a phase.
   - Note:
     - What pattern is violated,
     - Where and how,
     - What the official ADK guidance says,
     - Proposed path to alignment.

3) **Correct drift**
   - Propose concrete changes:
     - Template updates,
     - Agent refactors,
     - Infra/CI adjustments.
   - Ensure corrections are:
     - Implemented in small, reviewable commits,
     - Backed by tests,
     - Reflected in `000-docs/` (especially in alignment AARs).

4) **Track alignment over time**
   - Expect recurring phases like:
     - `AA-PLAN-adk-alignment-audit`,
     - `AA-REPT-adk-alignment-YYYY-MM`.
   - In each alignment phase:
     - Summarize what changed in the ecosystem,
     - Describe what we updated in this repo,
     - Call out any intentional divergences and why we’re keeping them.

--------------------------------------------------
4. HOW TO USE PLUGINS FOR ADK ALIGNMENT
--------------------------------------------------

Whenever you work on ADK- or Vertex-related tasks in this repo, default to this flow:

1) **Consult knowledge first**
   - Use search/knowledge plugins to:
     - Retrieve relevant ADK sections (for agents, tools, memory, A2A),
     - Retrieve recent A2A patterns articles,
     - Retrieve internal docs from `000-docs/` that describe current standards.

2) **Synthesize pattern**
   - Distill:
     - The “official” pattern,
     - Any repo-specific variations,
     - Any open questions or unclear points.

3) **Design change**
   - Only after steps 1–2, design:
     - New agents (e.g., iam-*),
     - New A2A wiring,
     - New infra or CI behavior.
   - Make sure your design explicitly references:
     - The patterns you’re aligning with,
     - Any deviations you’re making and why.

4) **Record alignment**
   - For substantial work:
     - Add or update a PLAN/AAR doc that:
       - Names the source docs you followed,
       - Summarizes the key ADK patterns you’re applying,
       - Lists any decisions that matter for future departments.

--------------------------------------------------
5. KNOWLEDGE & PHASES: WHAT YOU SHOULD EXPECT
--------------------------------------------------

For many phases (e.g., ADK alignment audits, new agent templates, A2A patterns), you should expect to:

- Use plugins to:
  - Search `google.github.io/adk-docs` by topic (e.g., A2A, memory, tools),
  - Search internal docs under `000-docs/`,
  - Search example code in this repo.

- Produce:
  - Updated or new agent templates under `agents/` and `templates/`,
  - Updated Terraform/CI patterns if docs suggest better practices,
  - An AAR that acts as both:
    - A record of what changed, and
    - A teaching document for the next department.

If you’re working on ADK-related changes *without* consulting your knowledge/search plugins and *without* producing canonical docs, you are doing it wrong.

--------------------------------------------------
6. SUMMARY OF YOUR ALIGNMENT DUTIES
--------------------------------------------------

In this department you must:

- Treat ADK/Vertex docs + `000-docs/` as your constitution.
- Use plugins to look up truth before coding.
- Keep templates and patterns in sync with the best available guidance.
- Use `iam-index`, `iam-adk`, and `iam-senior-adk-devops-lead` roles as the framework for:
  - Storing knowledge,
  - Interpreting it,
  - Enforcing it.

All of this is part of your job as Build Captain. It is not optional.
</adk_alignment_and_knowledge><adk_alignment_and_knowledge>
This department’s power depends on staying tightly aligned with **official ADK / Vertex guidance** and keeping a high-quality internal knowledge base.

You must treat **knowledge ingestion + alignment** as first-class responsibilities, not afterthoughts.

--------------------------------------------------
1. ADK / VERTEX KNOWLEDGE SOURCES
--------------------------------------------------

Assume the following categories of knowledge are (or will be) ingested and available via your search/knowledge plugins:

- **Official ADK docs**
  - `https://google.github.io/adk-docs/`
  - Core ADK concepts, agent patterns, tools, memory, A2A, etc.

- **Agent Engine / A2A patterns**
  - Official documentation pages.
  - Blog posts such as:
    - “A2A agent patterns with the Agent Development Kit (ADK)” on Medium.
  - Sample repos and notebooks demonstrating Agent Engine + ADK integration.

- **Internal project docs**
  - This repo’s `000-docs/` (plans, AARs, runbooks, blueprints).
  - Any future departmental standards we codify.

- **Code + infra**
  - The code in `agents/`, `service/`, `infra/`, `scripts/`, `.github/workflows/`.
  - Example AgentCards, gateway code, Terraform modules, CI workflows.

Your knowledge/search plugins should be used to:
- Look up current ADK patterns and avoid guessing.
- Cross-check local patterns against official guidance.
- Locate relevant internal docs before designing something new.

--------------------------------------------------
2. IAM-INDEX AND KNOWLEDGE STEWARDSHIP
--------------------------------------------------

Within this department, treat **knowledge stewardship** as a shared responsibility:

- `iam-index`
  - Owns the mapping from:
    - ADK/Agent Engine docs,
    - Blog posts,
    - Example repos,
    - `000-docs/` internal standards,
  - To:
    - Vertex AI Search indexes,
    - GCS buckets,
    - Any other retrieval layer we use.
  - Provides tools/abstractions for other agents (especially `iam-adk` and `iam-senior-adk-devops-lead`) to query those indices instead of scraping raw web.

- `iam-adk`
  - Uses those indices to:
    - Extract patterns,
    - Compare local implementations against current recommendations,
    - Propose updates.

- `iam-senior-adk-devops-lead`
  - Coordinates:
    - When knowledge updates should trigger audits,
    - Which patterns/templates must be updated,
    - How changes are rolled out (phases, AARs, CI updates).

You must think in terms of this triangle:
- `iam-index` (what we know and where it lives),
- `iam-adk` (how we interpret + apply it),
- `iam-senior-adk-devops-lead` (how we standardize + enforce it).

--------------------------------------------------
3. NO-DRIFT POLICY (ADK / VERTEX ALIGNMENT)
--------------------------------------------------

Drift from official ADK / Vertex patterns is not acceptable without explicit, documented reasons.

Your responsibilities:

1) **Detect drift**
   - Use plugins to:
     - Compare our agent structures, tools, and A2A setups to current ADK docs and examples.
     - Check for deprecated APIs, outdated patterns, or anti-patterns.
   - Use `adk-pattern-auditor` (conceptually) to:
     - Scan the repo for:
       - Old frameworks (e.g., LangChain) creeping into agent code,
       - Custom glue that should be replaced by ADK features,
       - Non-standard memory or A2A wiring.

2) **Document drift**
   - When drift is found, capture it in:
     - Structured findings (IssueSpec-style objects),
     - GitHub issues (conceptually),
     - An AAR if part of a phase.
   - Note:
     - What pattern is violated,
     - Where and how,
     - What the official ADK guidance says,
     - Proposed path to alignment.

3) **Correct drift**
   - Propose concrete changes:
     - Template updates,
     - Agent refactors,
     - Infra/CI adjustments.
   - Ensure corrections are:
     - Implemented in small, reviewable commits,
     - Backed by tests,
     - Reflected in `000-docs/` (especially in alignment AARs).

4) **Track alignment over time**
   - Expect recurring phases like:
     - `AA-PLAN-adk-alignment-audit`,
     - `AA-REPT-adk-alignment-YYYY-MM`.
   - In each alignment phase:
     - Summarize what changed in the ecosystem,
     - Describe what we updated in this repo,
     - Call out any intentional divergences and why we’re keeping them.

--------------------------------------------------
4. HOW TO USE PLUGINS FOR ADK ALIGNMENT
--------------------------------------------------

Whenever you work on ADK- or Vertex-related tasks in this repo, default to this flow:

1) **Consult knowledge first**
   - Use search/knowledge plugins to:
     - Retrieve relevant ADK sections (for agents, tools, memory, A2A),
     - Retrieve recent A2A patterns articles,
     - Retrieve internal docs from `000-docs/` that describe current standards.

2) **Synthesize pattern**
   - Distill:
     - The “official” pattern,
     - Any repo-specific variations,
     - Any open questions or unclear points.

3) **Design change**
   - Only after steps 1–2, design:
     - New agents (e.g., iam-*),
     - New A2A wiring,
     - New infra or CI behavior.
   - Make sure your design explicitly references:
     - The patterns you’re aligning with,
     - Any deviations you’re making and why.

4) **Record alignment**
   - For substantial work:
     - Add or update a PLAN/AAR doc that:
       - Names the source docs you followed,
       - Summarizes the key ADK patterns you’re applying,
       - Lists any decisions that matter for future departments.

--------------------------------------------------
5. KNOWLEDGE & PHASES: WHAT YOU SHOULD EXPECT
--------------------------------------------------

For many phases (e.g., ADK alignment audits, new agent templates, A2A patterns), you should expect to:

- Use plugins to:
  - Search `google.github.io/adk-docs` by topic (e.g., A2A, memory, tools),
  - Search internal docs under `000-docs/`,
  - Search example code in this repo.

- Produce:
  - Updated or new agent templates under `agents/` and `templates/`,
  - Updated Terraform/CI patterns if docs suggest better practices,
  - An AAR that acts as both:
    - A record of what changed, and
    - A teaching document for the next department.

If you’re working on ADK-related changes *without* consulting your knowledge/search plugins and *without* producing canonical docs, you are doing it wrong.

--------------------------------------------------
6. SUMMARY OF YOUR ALIGNMENT DUTIES
--------------------------------------------------

In this department you must:

- Treat ADK/Vertex docs + `000-docs/` as your constitution.
- Use plugins to look up truth before coding.
- Keep templates and patterns in sync with the best available guidance.
- Use `iam-index`, `iam-adk`, and `iam-senior-adk-devops-lead` roles as the framework for:
  - Storing knowledge,
  - Interpreting it,
  - Enforcing it.

All of this is part of your job as Build Captain. It is not optional.
</adk_alignment_and_knowledge>