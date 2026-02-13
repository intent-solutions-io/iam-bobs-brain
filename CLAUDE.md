# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Task Tracking (Beads / bd)

- Use `bd` for ALL tasks/issues (no markdown TODO lists).
- Start of session: `bd ready`
- Create work: `bd create "Title" -p 1 --description "Context + acceptance criteria"`
- Update status: `bd update <id> --status in_progress`
- Finish: `bd close <id> --reason "Done"`
- End of session: `bd sync` (flush/import/export + git sync)
- Manual testing safety:
  - Prefer `BEADS_DIR` to isolate a workspace if needed. (`BEADS_DB` exists but is deprecated.)

### Beads Upgrades
- After upgrading `bd`, run: `bd info --whats-new`
- If `bd info` warns about hooks, run: `bd hooks install`

---

## 1. Purpose of This File

This is the **live** guide for Claude Code when working in the `bobs-brain` repository. It provides essential context, patterns, and house rules to help AI assistants work effectively with this ADK-based agent department.

**For deeper context:** See `000-docs/claude-working-notes-archive.md` for historical notes and detailed background.

---

## 📋 TL;DR for DevOps (Quick Reference)

**Current Status (v2.0.0 - Vision Alignment GA):**
- **Version**: v2.0.0 – Enterprise Controls + ADK Compliance Department
- **Phase**: Vision Alignment Complete (Phases D, E, F, G)
- **Deployment**: Infrastructure ready, Terraform + GitHub Actions for all deployments (R4 compliance)
- **New in v2.0.0**: Canonical agent IDs, enterprise controls, Mission Spec v1

**Key Documents:**
- **Standards Catalog**: `000-docs/000-DR-INDEX-bobs-brain-standards-catalog.md` (START HERE for all canonical standards)
- **Hard Mode Rules**: `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` (R1-R8)
- **Agent Identity**: `000-docs/252-DR-STND-agent-identity-standard.md` (canonical IDs)
- **Enterprise Controls**: `000-docs/253-DR-STND-mandates-budgets-approvals.md` (mandates, risk tiers)
- **Policy Gates**: `000-docs/254-DR-STND-policy-gates-risk-tiers.md` (R0-R4 enforcement)
- **Evidence Bundles**: `000-docs/255-DR-STND-evidence-bundles-and-audit-export.md` (audit trails)
- **Mission Spec v1**: `000-docs/257-DR-STND-mission-spec-v1.md` (workflow-as-code)
- **DevOps Playbook**: `000-docs/120-AA-AUDT-appaudit-devops-playbook.md`

**Deployment Pattern:**
- ✅ **Production**: Inline source deployment (source code → Agent Engine, no serialization)
- ⛔ **Legacy**: Serialized/pickle deployment (deprecated, do not use)

**Agent Architecture (Canonical IDs):**
- **bob**: User interface (Slack integration)
- **iam-orchestrator**: Foreman/scheduler (alias: iam-senior-adk-devops-lead)
- **iam-compliance**: ADK standards checking (alias: iam-adk)
- **iam-triage**: Issue decomposition (alias: iam-issue)
- **iam-planner**: Fix planning (alias: iam-fix-plan)
- **iam-engineer**: Implementation (alias: iam-fix-impl)
- **iam-qa**: Testing/verification
- **iam-docs**: Documentation (alias: iam-doc)
- **iam-hygiene**: Repo cleanup (alias: iam-cleanup)
- **iam-index**: Search/catalog
- AgentCards in `.well-known/agent-card.json` for all agents
- See: `000-docs/252-DR-STND-agent-identity-standard.md`

**Slack Bob Deployment (Phase 24 - R4 Compliant):**
- ✅ **Deploy via Terraform only**: `.github/workflows/terraform-prod.yml`
- ⛔ **NEVER use**: `.github/workflows/deploy-slack-webhook.yml` (deprecated - R4 violation)
- ⛔ **NEVER run**: `gcloud run services update slack-webhook` (manual deploys violate R4)
- 📖 **Operator Guide**: `000-docs/164-AA-REPT-phase-24-slack-bob-ci-deploy-and-restore.md`

---

## 🚀 Quick Commands (Development Workflow)

### Setup & Testing
```bash
# Initial setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all quality checks (lint + test)
make ci

# Run specific checks
bash scripts/ci/check_nodrift.sh  # Drift detection (R8)
pytest tests/unit/ -v             # Unit tests only
pytest tests/integration/ -v      # Integration tests only
pytest tests/unit/test_agentcard_json.py -v  # Single test file
pytest -k "test_agent" -v         # Run tests matching pattern

# Run single test with verbose output
pytest tests/unit/test_<name>.py::test_function_name -vvs

# Run tests by marker
pytest -m unit -v                # Unit tests only (marker-based)
pytest -m integration -v         # Integration tests (may need GCP)
pytest -m "not slow" -v          # Skip slow tests

# Multi-version testing with nox
nox -s tests-3.12                # Test on Python 3.12
nox -s lint                      # Lint checks via nox
nox -s coverage                  # Coverage via nox
nox --list                       # List all nox sessions

# Smoke tests
make smoke-agents                 # Test lazy-loading App pattern (6767-LAZY)
make smoke-bob-agent-engine-dev   # Test deployed agent
```

### Deployment
```bash
# Dry-run validation (safe, no deployment)
make deploy-inline-dry-run

# ARV checks before deployment
make check-inline-deploy-ready AGENT_NAME=bob ENV=dev

# CI/CD deployment (recommended)
git push origin main  # Triggers GitHub Actions

# View deployment status
gh run list --workflow=agent-engine-inline-deploy.yml
```

### Make Targets Quick Reference
```bash
make help                         # Show all available targets

# Quality Checks (run before commits)
make ci                           # Lint + tests (pre-commit gate)
make lint                         # Flake8 linting
make format                       # Format with black
make format-check                 # Check formatting (no changes)

# Testing
make test                         # All tests (pytest tests/)
make test-coverage                # Tests with HTML coverage report
make test-swe-pipeline            # SWE pipeline tests only
make check-a2a-contracts          # Validate AgentCard JSON files
make smoke-agents                 # Test lazy-loading pattern (6767-LAZY)

# ARV Gates (Agent Readiness Verification)
make arv-gates                    # All ARV gates (RAG + minimum + engine + spec)
make arv-department               # Comprehensive ARV for IAM department
make check-inline-deploy-ready    # Deployment readiness check
make check-arv-minimum            # ARV minimum requirements only

# Deployment (CI/CD preferred - R4)
make deploy-inline-dry-run        # Validate deployment (safe, no changes)
make slack-dev-smoke              # Test Slack webhook

# Development Utilities
make setup                        # Complete dev environment setup
make clean                        # Clean pycache, coverage, logs
make safe-commit                  # lint + format-check + test before commit
```

---

## 2. Repo Context & Architecture

**Bob's Brain** is a production-grade **ADK agent department** built on Google's Agent Development Kit (ADK) and Vertex AI Agent Engine. It serves as:

- The canonical reference implementation for multi-agent SWE (Software Engineering) departments
- A Slack AI assistant powered by ADK agents
- A reusable template for other product repositories

### Three-Tier Agent Architecture

**CRITICAL:** bobs-brain uses a strict hierarchy - understand this before making changes:

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: User Interface (Conversational)                    │
│                                                             │
│  User (via Slack)                                           │
│       ↓                                                     │
│  Bob - Conversational LLM Agent                             │
│  • Uses Gemini to respond like Claude/GPT/Gemini           │
│  • Friendly, helpful, answers questions naturally           │
│  • Has ADK documentation search tools                       │
│  • Delegates complex work to foreman via A2A               │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Orchestration Layer (Workflow Coordination)        │
│                                                             │
│  iam-senior-adk-devops-lead (Foreman)                       │
│  • Orchestrates workflow across specialists                 │
│  • NEVER executes specialist work itself                    │
│  • Delegation patterns: single, sequential, parallel        │
│  • Returns structured JSON to Bob                           │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Execution Layer (Strict Function Workers)          │
│                                                             │
│  iam-* Specialists (8 agents)                               │
│  • iam-adk: ADK compliance checking                         │
│  • iam-issue: GitHub issue creation                         │
│  • iam-fix-plan: Fix planning                               │
│  • iam-fix-impl: Fix implementation                         │
│  • iam-qa: Testing and validation                           │
│  • iam-doc: Documentation                                   │
│  • iam-cleanup: Repository hygiene                          │
│  • iam-index: Knowledge indexing                            │
│                                                             │
│  Each specialist:                                           │
│  • Has STRICT input/output JSON schemas (in AgentCard)      │
│  • Is deterministic (no planning loops, no self-reflection) │
│  • Uses tools to execute (never generates without tools)    │
│  • Returns structured results matching skill output schema  │
└─────────────────────────────────────────────────────────────┘
```

### Agent Directory Layout

```
agents/
├── bob/                          # Tier 1: User-facing conversational agent
│   ├── agent.py                  # LlmAgent with dual memory (R5)
│   ├── .well-known/
│   │   └── agent-card.json       # A2A contract
│   └── tools/                    # Bob-specific tools (Vertex Search)
│
├── iam_senior_adk_devops_lead/   # Tier 2: Foreman/orchestrator
│   ├── agent.py                  # Workflow coordination
│   └── orchestrator.py           # SWE pipeline logic
│
├── iam_adk/                      # Tier 3: ADK compliance specialist
├── iam_issue/                    # Tier 3: GitHub issue creator
├── iam_fix_plan/                 # Tier 3: Fix planner
├── iam_fix_impl/                 # Tier 3: Fix implementer
├── iam_qa/                       # Tier 3: QA validator
├── iam_doc/                      # Tier 3: Documentation writer
├── iam_cleanup/                  # Tier 3: Repo cleanup
└── iam_index/                    # Tier 3: Knowledge indexing

shared_tools/                     # Shared tool implementations
shared_contracts/                 # JSON schemas for agent communication

service/                          # Cloud Run gateway proxies (R3: no Runner here)
├── slack_webhook/                # Slack events → Agent Engine REST API
├── a2a_gateway/                  # A2A protocol HTTP endpoint
└── github_webhook/               # GitHub events handler

missions/                         # Mission Spec YAML files (declarative workflows)
```

**Key Pattern (6767-LAZY):**
- Each agent has `agent.py` with:
  - `create_agent()` - Lazy agent instantiation
  - `create_app()` - Wraps in App for Agent Engine
  - Module-level `app` (NOT `agent`)
- No import-time validation or heavy work
- See: `000-docs/000-DR-STND-adk-lazy-loading-app-pattern.md`

### Key Architectural Rules

**User Interaction:**
- ✅ Users ONLY talk to Bob (via Slack)
- ❌ Users NEVER call foreman or specialists directly
- ✅ Bob presents specialist results in friendly, conversational way

**Bob's Role (Conversational LLM):**
- Responds naturally to user questions (like Claude/GPT/Gemini)
- Searches ADK documentation when needed
- Delegates complex SWE work to foreman via A2A
- Maintains conversational context within sessions

**Foreman's Role (Orchestrator):**
- Receives structured requests from Bob
- Plans workflows (single specialist, sequential, parallel)
- Calls specialists with strict JSON payloads (matching their AgentCard skills)
- Validates specialist outputs
- Aggregates results and returns to Bob

**Specialists' Role (Function Workers):**
- Accept strict JSON inputs (defined in `.well-known/agent-card.json`)
- Execute using domain-specific tools
- Return strict JSON outputs (matching output schemas)
- NO conversational behavior - deterministic function execution only

**Example Flow:**
```
User: "Check if iam-adk agent is ADK compliant"
  ↓
Bob: [Understands intent, delegates to foreman]
  ↓ A2A call
Foreman: [Plans workflow, calls iam-adk specialist]
  ↓ A2A call with strict JSON
iam-adk: {
  "target": "agents/iam_adk",
  "focus_rules": ["R1", "R2", "R5"]
}
  ↓ Returns strict JSON
iam-adk: {
  "compliance_status": "COMPLIANT",
  "violations": [],
  "risk_level": "LOW"
}
  ↓ Returns to foreman
Foreman: [Validates, aggregates, returns to Bob]
  ↓ Returns to Bob
Bob: "Good news! iam-adk is fully compliant with ADK Hard Mode rules."
  ↓
User: [Sees friendly response]
```

**Architecture Pattern:** Agent Factory with strict "Hard Mode" rules (R1-R8) enforced via CI/CD.

---

## 3. Expectations & House Rules

**Before making changes:**
1. Consult `000-docs/` for existing standards before creating new patterns
2. Search ADK docs and repo patterns before guessing
3. Think in agents - which department agent (bob, foreman, specialist) owns the work?
4. Don't invent new folders without permission

### Architecture Standards

**Hard Mode Rules (R1-R8)** - CI-enforced, cannot be violated:
- R1: ADK-Only (no LangChain, CrewAI, custom frameworks)
- R2: Vertex AI Agent Engine runtime (no self-hosted runners)
- R3: Gateway separation (Cloud Run proxies only, no Runner in service/)
- R4: CI-only deployments (GitHub Actions with WIF, no manual gcloud)
- R5: Dual memory wiring (VertexAiSessionService + VertexAiMemoryBankService)
- R6: Single doc folder (all docs in `000-docs/` with NNN-CC-ABCD naming)
- R7: SPIFFE ID propagation (in AgentCard, logs, headers)
- R8: Drift detection (runs first in CI, blocks violations)

**See:** `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` for complete spec.

### ⛔ Common Anti-Patterns (DO NOT DO)

**R1 Violations (Agent Implementation):**
```python
# ❌ WRONG - No LangChain mixing
from langchain import ...

# ❌ WRONG - No CrewAI mixing
from crewai import ...

# ✅ CORRECT - ADK only
from google.adk.agents import LlmAgent
```

**R3 Violations (Gateway Separation):**
```python
# ❌ WRONG - No Runner in service/ gateways
from google.adk import Runner  # In service/slack_webhook/ or service/a2a_gateway/

# ✅ CORRECT - Use httpx to call Agent Engine REST API
import httpx
response = await client.post(f"{AGENT_ENGINE_URL}/query", json=request)
```

**R4 Violations (CI-Only Deployments):**
```bash
# ❌ WRONG - Manual deploys forbidden
gcloud run services update slack-webhook ...
terraform apply  # From local machine for prod

# ✅ CORRECT - CI/CD only
git push origin main  # Triggers GitHub Actions
```

**R6 Violations (Single Docs Folder):**
```bash
# ❌ WRONG - No scattered docs
mkdir docs/
touch wiki/architecture.md
touch agents/bob/README.md

# ✅ CORRECT - All docs in 000-docs/
touch 000-docs/185-AT-ARCH-bob-architecture.md
```

**6767-LAZY Violations:**
```python
# ❌ WRONG - No eager instantiation at module level
agent = LlmAgent(...)  # Runs at import time

# ❌ WRONG - Heavy validation at import time
assert PROJECT_ID, "PROJECT_ID required"  # Blocks imports

# ✅ CORRECT - Lazy-loading pattern
def create_agent() -> LlmAgent:
    """Lazy agent creation (called on-demand)"""
    # Validate here, not at import time
    return LlmAgent(...)

app = create_app()  # Module-level app, not agent
```

### Coding Style

**Python (agents/):**
- Follow lazy-loading App pattern (see 6767-LAZY standard)
- Use `google-adk` imports exclusively
- Implement `after_agent_callback` for R5 compliance
- Module-level `app`, not `agent`

**Creating New Agents:**
```python
# agents/iam_new/agent.py - REQUIRED STRUCTURE
from google.adk.agents import LlmAgent
from google.adk.apps import App

# 1. Config reads (cheap, no validation)
PROJECT_ID = os.getenv("PROJECT_ID")

# 2. Lazy agent creation
def create_agent() -> LlmAgent:
    """Called on-demand, not at import."""
    return LlmAgent(name="iam-new", model="gemini-2.0-flash", ...)

# 3. Lazy app creation
def create_app() -> App:
    return App(agent=create_agent())

# 4. Module-level app (NOT agent)
app = create_app()
```
Each agent also needs:
- `agents/iam_new/.well-known/agent-card.json` (A2A contract)
- Entry in `agents/__init__.py` if using shared imports

**Terraform (infra/):**
- Use modules over copy-pasted resources
- Keep env configs in `envs/dev`, `envs/prod`
- Name resources consistently with existing patterns

**CI Workflows:**
- Reuse job patterns from existing `.github/workflows/`
- Group checks logically (lint, test, build, deploy, ARV)
- Keep workflows focused (avoid mega-workflows)

### Test Infrastructure

**Pytest markers** (use with `-m` flag):
- `unit` - Fast tests, no external dependencies
- `integration` - May require GCP/Agent Engine
- `slack` - Requires Slack webhook
- `slow` - Tests taking >5 seconds
- `mcp` - MCP server tests
- `arv` - Agent Readiness Verification tests

**Conftest skip markers** (auto-applied):
- `requires_adk` - Skips if `google-adk` not installed
- `requires_apihub` - Skips if `google-cloud-apihub` not installed

**Drift detection** (`scripts/ci/check_nodrift.sh`):
- Runs first in CI, blocks on any R1/R3/R4 violations
- Scans for LangChain/CrewAI/AutoGen imports (R1)
- Scans for Runner imports in `service/` (R3)
- Scans for manual deploy commands (R4)

### Documentation Standards

**Document Filing System v3.0:**
- Format: `NNN-CC-ABCD-description.md` (project-specific) or `000-CC-ABCD-description.md` (canonical standards)
- Categories: PP (Planning), AT (Architecture), AA (After-Action Reports), DR (Documentation/Reference)
- All docs in `000-docs/` - NO scattered documentation
- See: `000-docs/000-DR-STND-document-filing-system-standard-v4.md` for complete rules

**Key Doc Types:**
- **PLAN** (`NNN-AA-PLAN-*.md`) - Phase planning before work starts
- **REPT** (`NNN-AA-REPT-*.md`) - After-Action Report after phase completes
- **STND** (`NNN-DR-STND-*.md`) - Standards and specifications
- **ARCH** (`NNN-AT-ARCH-*.md`) - Architecture designs

### Phases & AARs

**All significant work** must be structured into phases:

1. **Phase Planning**
   - Create `NNN-AA-PLAN-phase-name.md` in `000-docs/`
   - Define scope, steps, decisions, expected artifacts

2. **Implementation**
   - Work in small, reviewable commits
   - Reference phase name in commit messages

3. **AAR (After-Action Report)**
   - Create `NNN-AA-REPT-phase-name.md` when complete
   - Document what was built, decisions made, lessons learned

**Example Phase Flow:**
```
Phase 1: Design iam-adk specialist
├── 001-AA-PLAN-iam-adk-design.md (planning)
├── [implementation commits]
└── 002-AA-REPT-iam-adk-implementation.md (AAR)
```

### Commit Messages

Use conventional commits format:
```
<type>(<scope>): <subject>

<optional body>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`

**Examples:**
- `feat(agents): scaffold iam-adk specialist agent`
- `docs(000-docs): add plan for iam-adk design phase`
- `ci(workflows): add ARV checks for agent readiness`

### Git Workflow Protocol

**NEVER commit directly to main.** Always use feature branches:

```bash
# 1. Start from clean main
git checkout main && git pull

# 2. Create feature branch FIRST
git checkout -b feature/my-feature-name

# 3. Make commits on feature branch
git add <files...> && git commit -m "feat(scope): description"

# 4. Push and create PR
git push -u origin feature/my-feature-name
gh pr create --title "feat: description" --body "..."

# 5. After PR merged, clean up
git checkout main && git pull
git branch -d feature/my-feature-name
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code restructuring
- `test/` - Adding or improving tests
- `ci/` - CI/CD changes
- `chore/` - Maintenance tasks

**Protected Branch:** `main` is protected - all changes via PR only.

---

## 4. Documentation Navigation

### Start Here (By Role)

**Developers (Building Agents):**
1. **[Master Index](000-docs/000-DR-INDEX-bobs-brain-standards-catalog.md)** - Complete map of all standards
2. **[Hard Mode Rules](000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md)** - R1-R8 architecture rules
3. **[Lazy-Loading Pattern](000-docs/000-DR-STND-adk-lazy-loading-app-pattern.md)** - Agent implementation pattern

**Operators (Deploying/Running):**
1. **[DevOps Playbook](000-docs/120-AA-AUDT-appaudit-devops-playbook.md)** - Complete operational guide
2. **[Inline Deployment](000-docs/000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md)** - Deployment guide
3. **[Operations Runbook](000-docs/000-RB-OPS-adk-department-operations-runbook.md)** - Day-to-day operations

**Template Adopters (Porting to New Repos):**
1. **[Porting Guide](000-docs/000-DR-GUIDE-porting-iam-department-to-new-repo.md)** - Step-by-step instructions
2. **[Integration Checklist](000-docs/000-DR-STND-iam-department-integration-checklist.md)** - Complete checklist
3. **[Template Standards](000-docs/000-DR-STND-iam-department-template-scope-and-rules.md)** - Customization rules

### Key SOP Documents (Canonical Standards)

All **000-prefixed canonical docs act as Standard Operating Procedures (SOPs)**:

- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)
- **000-DR-STND-adk-lazy-loading-app-pattern.md** - Lazy-loading App pattern (6767-LAZY)
- **000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md** - Inline source deployment
- **000-DR-STND-prompt-design-a2a-contracts-iam-dept.md** - Prompt design contracts

### Other Key References

- **127-DR-STND-agent-engine-entrypoints.md** - Canonical entrypoints for inline deployment
- **120-AA-AUDT-appaudit-devops-playbook.md** - Complete DevOps onboarding (15k words)
- **claude-working-notes-archive.md** - Historical verbose content

### Quick Lookups

```bash
# Find all canonical standards
ls 000-docs/000-*.md

# List all standards
ls 000-docs/*-DR-STND-*.md

# Search for topic
grep -r "inline source" 000-docs/

# Find doc by number
ls 000-docs/127-*
```

**Rule**: When you need detailed info, **search `000-docs/` first** - don't bloat CLAUDE.md.

---

## 5. Changelog / Maintenance

**Last Update:** 2026-02-13

**Recent Changes:**
- **Doc-Filing v4.3 Migration**: All 28 `6767-*` canonical docs renamed to `000-*` prefix
- **Identity Alignment**: README/CLAUDE.md updated to reflect ADK compliance focus (not "general-purpose orchestrator")
- **Vision Alignment GA (v2.0.0)**: Enterprise controls + ADK compliance department
  - **Phase D**: Canonical agent identity system with backwards-compatible aliases
  - **Phase E**: Enterprise controls (risk tiers R0-R4, policy gates, evidence bundles)
  - **Phase F**: Mission Spec v1 (declarative workflow-as-code)
  - **Phase G**: GA finalization, docs 252-257, 260 (AAR)
  - 103 new unit tests (303 total)
- **New Standards**: 252 (Agent Identity), 253 (Mandates), 254 (Policy Gates), 255 (Evidence), 257 (Mission Spec)
- Previous: Phase 26 (v0.14.0) - Repository cleanup, branch archival

**Maintenance Policy:**
- **DON'T overcrowd CLAUDE.md** - it's a pointer doc, not a knowledge base
- All detailed docs go in `000-docs/` following NNN-CC-ABCD or 000-CC-ABCD naming
- Canonical docs (000-* prefix) = SOPs (Standard Operating Procedures)
- CLAUDE.md should remain concise (target ~15k chars)
  - Exception: Section 2 (Architecture) is worth the space to prevent confusion
- When adding new standards, update Section 5 with pointer, not full content

---

**For complete historical context, patterns, and examples:** See `000-docs/claude-working-notes-archive.md`
