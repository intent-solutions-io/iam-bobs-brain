# CLAUDE.md – How to Work With Claude in bobs-brain

## 1. Purpose of This File

This is the **live** guide for Claude Code when working in the `bobs-brain` repository. It provides essential context, patterns, and house rules to help AI assistants work effectively with this ADK-based agent department.

**For deeper context:** See `000-docs/claude-working-notes-archive.md` for historical notes and detailed background.

---

## 📋 TL;DR for DevOps (Quick Reference)

**Current Status (v0.14.0):**
- **Version**: v0.14.0 – Documentation Excellence & Community Contributions
- **Phase**: Phase 26 Complete - Repository Cleanup & Release
- **Deployment**: Infrastructure ready, Terraform + GitHub Actions for all deployments (R4 compliance)
- **Community**: Linux Foundation AI Card PR #7, A2A Samples PR #419 (production patterns shared)

**Key Documents:**
- **6767 Global Catalog**: `000-docs/6767-000-DR-INDEX-bobs-brain-standards-catalog.md` (START HERE for all 6767 standards)
- **Agent Engine Sub-Index**: `000-docs/6767-120-DR-STND-agent-engine-a2a-and-inline-deploy-index.md` (for deployment/A2A topics)
- **Hard Mode Rules**: `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` (R1-R8)
- **Inline Deployment**: `000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
- **DevOps Playbook**: `000-docs/120-AA-AUDT-appaudit-devops-playbook.md`

**Deployment Pattern:**
- ✅ **Production**: Inline source deployment (source code → Agent Engine, no serialization)
- ⛔ **Legacy**: Serialized/pickle deployment (deprecated, do not use)

**Key Scripts:**
- `make check-all` - Run all quality checks (drift detection, tests, ARV)
- `make check-inline-deploy-ready` - ARV checks for Agent Engine deployment
- `make deploy-inline-dry-run` - Validate deployment config without deploying
- `make smoke-bob-agent-engine-dev` - Post-deployment health check (requires deployed agent)

**A2A / AgentCard Plan:**
- Foreman + workers architecture (iam-senior-adk-devops-lead → iam-*)
- AgentCards in `.well-known/agent-card.json` for all agents
- Validation via `tests/unit/test_agentcard_json.py` and a2a-inspector (planned)
- **A2A compliance (a2a-inspector + a2a-tck) scaffolded; see 6767-121 for details**
- See: `000-docs/6767-DR-STND-agentcards-and-a2a-contracts.md`
- See: `000-docs/6767-121-DR-STND-a2a-compliance-tck-and-inspector.md`

**Slack Bob Deployment (Phase 24 - R4 Compliant):**
- ✅ **Deploy via Terraform only**: `.github/workflows/terraform-prod.yml`
- ⛔ **NEVER use**: `.github/workflows/deploy-slack-webhook.yml` (deprecated - R4 violation)
- ⛔ **NEVER run**: `gcloud run services update slack-webhook` (manual deploys violate R4)
- 📖 **Operator Guide**: `000-docs/164-AA-REPT-phase-24-slack-bob-ci-deploy-and-restore.md`

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

## 3. How to Talk to Claude About This Repo

### Example Prompts

**For agents/department work:**
- "Design the iam-adk specialist agent following Bob's patterns"
- "Audit agent.py files for ADK compliance against Hard Mode rules"
- "Propose A2A wiring between iam-foreman and iam-issue"

**For infrastructure:**
- "Update Terraform to add Agent Engine configuration for iam-adk"
- "Design CI workflow for multi-agent ARV (Agent Readiness Verification)"

**For CI/CD:**
- "Add drift detection checks for new iam-* agents"
- "Implement ARV gates in GitHub Actions"

### Key Expectations

When working in this repo, Claude should:

1. **Respect repo layout** - Don't invent new folders without permission
2. **Consult `000-docs/`** - Check existing standards before creating new patterns
3. **Use plugins/tools first** - Search ADK docs and repo patterns before guessing
4. **Propose small changes** - Break work into reviewable commits
5. **Follow phases** - Structure work into phases with PLAN and AAR docs
6. **Think in agents** - Consider which department agent (bob, foreman, specialist) owns the work

---

## 4. Expectations & House Rules

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

**See:** `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` for complete spec.

### Coding Style

**Python (agents/):**
- Follow lazy-loading App pattern (see 6767-LAZY standard)
- Use `google-adk` imports exclusively
- Implement `after_agent_callback` for R5 compliance
- Module-level `app`, not `agent`

**Terraform (infra/):**
- Use modules over copy-pasted resources
- Keep env configs in `envs/dev`, `envs/prod`
- Name resources consistently with existing patterns

**CI Workflows:**
- Reuse job patterns from existing `.github/workflows/`
- Group checks logically (lint, test, build, deploy, ARV)
- Keep workflows focused (avoid mega-workflows)

### Documentation Standards

**Document Filing System v3.0:**
- Format: `NNN-CC-ABCD-description.md` (project-specific) or `6767-CC-ABCD-description.md` (canonical standards)
- Categories: PP (Planning), AT (Architecture), AA (After-Action Reports), DR (Documentation/Reference)
- All docs in `000-docs/` - NO scattered documentation
- See: `000-docs/6767-DR-STND-document-filing-system-standard-v3.md` for complete rules

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

---

## 5. Where to Find the Deep Details

**All detailed documentation lives in `000-docs/`** - DON'T overcrowd this file.

### Key SOP Documents (6767-series)

All **6767-prefixed docs act as Standard Operating Procedures (SOPs)** - these are canonical standards:

- **6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)
- **6767-LAZY-DR-STND-adk-lazy-loading-app-pattern.md** - Lazy-loading App pattern
- **6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md** - Inline source deployment
- **6767-115-DR-STND-prompt-design-and-a2a-contracts-for-department-adk-iam.md** - Prompt design contracts

### Other Key References

- **127-DR-STND-agent-engine-entrypoints.md** - Canonical entrypoints for inline deployment
- **126-AA-AUDT-appaudit-devops-playbook.md** - Complete DevOps onboarding (15k words)
- **claude-working-notes-archive.md** - Historical verbose content

### How to Find What You Need

```bash
# List all SOPs (6767-series)
ls 000-docs/6767*.md

# List all standards
ls 000-docs/*-DR-STND-*.md

# Search for keyword
grep -r "inline source" 000-docs/

# Find doc by number
ls 000-docs/127-*
```

**Rule**: When you need detailed info, **search `000-docs/` first** - don't bloat CLAUDE.md.

---

## 6. Changelog / Maintenance

**Last Update:** 2025-12-05

**Recent Changes:**
- **Phase 26 (v0.14.0)**: Repository cleanup, branch archival tooling, and release
  - Created `scripts/maintenance/cleanup_branches.sh` for safe branch archival
  - Added `000-docs/ARCHIVED_BRANCHES.md` branch management index
  - Updated version to v0.14.0 with comprehensive CHANGELOG
  - Validated canonical scaffold alignment (single docs root, clear separation)
- **Community Contributions**: Linux Foundation AI Card PR #7, A2A Samples PR #419
- **Documentation**: Added docs 179-182 (CTO strategy, A2A implementation, Phase 26 planning/AAR)
- Previous: Phase 25 (Slack Bob Hardening), three-tier architecture documentation

**Maintenance Policy:**
- **DON'T overcrowd CLAUDE.md** - it's a pointer doc, not a knowledge base
- All detailed docs go in `000-docs/` following NNN-CC-ABCD naming
- 6767-series docs = SOPs (Standard Operating Procedures)
- CLAUDE.md should remain concise (target ~15k chars)
  - Exception: Section 2 (Architecture) is worth the space to prevent confusion
- When adding new standards, update Section 5 with pointer, not full content

---

## Quick Reference Commands

```bash
# Navigate to repo
cd /home/jeremy/000-projects/iams/bobs-brain/

# Run tests
pytest
pytest tests/unit/test_a2a_card.py -v

# Check compliance
bash scripts/ci/check_nodrift.sh
make check-arv-minimum

# Local development
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# View documentation
ls 000-docs/
cat 000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md
```

---

**For complete historical context, patterns, and examples:** See `000-docs/claude-working-notes-archive.md`
