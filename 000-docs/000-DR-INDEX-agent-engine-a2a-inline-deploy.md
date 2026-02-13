# Agent Engine, A2A, and Inline Deployment - Master Index

**Document Type:** Canonical Standard & Index (000-DR-INDEX)
**Status:** Active
**Applies To:** All ADK agent departments (starting with department adk iam)
**Purpose:** Master reference linking all Agent Engine, A2A, and inline deployment standards
**Last Updated:** 2026-02-13

---

## I. Purpose and Scope

This document serves as the **master index** for the Bob's Brain Agent Engine / A2A architecture. It provides:

1. **Quick reference** to all related standards and implementation docs
2. **High-level overview** of how we use Agent Engine inline deployment
3. **A2A / AgentCard usage patterns** for our foreman + worker model
4. **External citations** for all upstream specifications and tools

**Target Audience:**
- New developers onboarding to the repo
- Operators deploying agents to Agent Engine
- Reviewers validating compliance with our standards

**What This Document Is NOT:**
- A tutorial (see linked guides for step-by-step instructions)
- A complete specification (see linked 6767 standards for details)
- Implementation code (see repo code for actual agents)

**Note on 6767 Naming:** This doc uses document ID "6767-120" in its header but follows pre-v3.0 naming conventions in its filename. See `000-docs/000-DR-STND-document-filing-system-standard-v4.md` for current 6767 naming rules.

### Relationship to 6767-000 Global Catalog

**This document (6767-120) is a SUB-INDEX** within the larger 6767 documentation series.

**Navigation Hierarchy:**
- **6767-000** = Global catalog of ALL 6767-* standards, guides, and reference docs
- **6767-120** (this doc) = Sub-index focused on Agent Engine, A2A, and inline deployment topics
- **Individual 6767-*** = Specific standards, guides, and implementation docs

**When to Use Each:**
- **Start with the standards catalog** (`000-DR-INDEX-bobs-brain-standards-catalog.md`) for global orientation across all topics
- **Drill into this index** when working specifically on Agent Engine deployment or A2A protocol topics
- **Jump to specific 000-*** docs when you know exactly what you need

**Cross-References:**
- See `000-docs/000-DR-INDEX-bobs-brain-standards-catalog.md` for complete catalog
- See Section V below for links to all Agent Engine / A2A / inline deployment standards

---

## II. Agent Engine Topology & Inline Source Deployment

### What is Vertex AI Agent Engine?

**Vertex AI Agent Engine** is Google Cloud's managed runtime for ADK-based agents. Key characteristics:

- **Serverless**: No infrastructure to manage
- **Auto-scaling**: Handles traffic spikes automatically
- **Integrated**: Native Vertex AI Search, Memory Bank, Tool execution
- **Secure**: Workload Identity, IAM-based access control

### Inline Source Deployment Pattern

**Inline source deployment** is our standard deployment method (as of v0.10.0). It replaces the legacy serialized/pickle deployment pattern.

**How It Works:**
1. **Source code** is deployed directly from Git (no intermediate serialization)
2. **Agent Engine** packages source as tarball and executes Python modules on-demand
3. **Entrypoint pattern**: Module/object pair (e.g., `agents.bob.agent.app`)
4. **CI-friendly**: No GCS bucket required, works in GitHub Actions

**Benefits:**
- ✅ Simpler CI/CD (no serialization step)
- ✅ Better debugging (source matches runtime)
- ✅ Version control (Git SHA → deployed code)
- ✅ No GCS bucket dependencies

**Official Resources:**
- **Discussion**: https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935
- **Vertex AI Agent Engine Docs**: https://cloud.google.com/vertex-ai/docs/agent-engine

**Our Implementation:**
- See: `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
- Scripts: `agents/agent_engine/deploy_inline_source.py`
- ARV checks: `scripts/check_inline_deploy_ready.py`
- Workflow: `.github/workflows/agent-engine-inline-dev-deploy.yml`

---

## III. A2A (Agent-to-Agent) Protocol & AgentCards

### What is the A2A Protocol?

**A2A (Agent-to-Agent)** is an open protocol for machine-readable agent capabilities and task delegation.

**Key Concepts:**
- **AgentCard**: JSON manifest describing agent identity, skills, authentication
- **Skills**: Structured capabilities with strict input/output schemas (JSON Schema)
- **Task Envelope**: Standard format for delegating work between agents
- **Inspector**: Validation tool for AgentCard compliance

**Official A2A Resources:**
- **A2A Protocol Specification**: https://a2a-protocol.org/
- **A2A Inspector Tool**: https://github.com/a2aproject/a2a-inspector
- **A2A Inspector Web UI**: https://a2aprotocol.ai/a2a-inspector

### Our A2A Usage Pattern

**Current Implementation (v0.10.0):**
- AgentCards for **internal agent contracts** (foreman → workers)
- JSON-based skill definitions in `.well-known/agent-card.json`
- Contract references ($comment fields) linking to Python dataclasses
- Validation via unit tests (`tests/unit/test_agentcard_json.py`)

**Future Expansion:**
- External A2A network integration (beyond this repo)
- Runtime validation with a2a-inspector in CI
- A2A gateway for external agent discovery

**Our Implementation:**
- See: `000-DR-STND-agentcards-and-a2a-contracts.md`
- See: `000-DR-STND-prompt-design-a2a-contracts-iam-dept.md`
- Integration: `000-AA-REPT-a2a-inspector-integration-for-department-adk-iam.md`

### A2A Compliance Tooling

**Purpose:** Validate A2A protocol compliance using official tools

**Tools:**
- **a2a-inspector** (Interactive) - Manual debugging and validation of AgentCards and A2A endpoints
- **a2a-tck** (Automated) - Technology Compatibility Kit for formal A2A spec compliance testing

**Current Status (v0.10.0):**
- Documentation and local scripts in place (Phase A)
- CI workflow scaffolded (disabled by default, manual trigger only)
- No live A2A endpoints yet (agents not deployed to Agent Engine)

**Usage:**
- Local a2a-inspector validation: See `scripts/run_a2a_inspector_local.md`
- Local a2a-tck testing: Run `./scripts/run_a2a_tck_local.sh` (requires `A2A_TCK_SUT_URL`)
- CI scaffold: `.github/workflows/a2a-compliance.yml` (workflow_dispatch only)

**Full Standard:**
- See: `000-DR-STND-a2a-compliance-tck-inspector.md`

---

## IV. Department Architecture: Foreman + Workers

### Overview

Bob's Brain implements a **multi-agent department** pattern with clear hierarchy:

```
Bob (Global Orchestrator)
  └─> iam-senior-adk-devops-lead (Foreman)
        ├─> iam-adk (ADK/Vertex specialist)
        ├─> iam-issue (Issue creation specialist)
        ├─> iam-fix-plan (Fix planning specialist)
        ├─> iam-fix-impl (Fix implementation specialist)
        ├─> iam-qa (Quality assurance specialist)
        └─> ... (other specialists)
```

**Key Principles:**
1. **Foreman orchestrates** - Routes work, aggregates results, manages pipeline
2. **Workers execute** - Focused specialists with single responsibilities
3. **AgentCards define contracts** - Machine-readable skill interfaces
4. **A2A envelopes for tasks** - Structured PipelineRequest → PipelineResult messages

### Agent Identity & IAM Patterns

**SPIFFE ID Format:**
```
spiffe://intent.solutions/agent/bobs-brain/<env>/<region>/<version>
```

**Example:**
```
spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0
```

**IAM & Authentication:**
- Workload Identity Federation (WIF) for GitHub Actions → GCP
- Service accounts per environment (dev/staging/prod)
- No long-lived credentials in code or Git

**Our Implementation:**
- See: `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` (R7: SPIFFE ID)
- See: `.env.example` for configuration patterns

---

## V. Complete Reference Map

### Core Standards (Canonical Docs)

| Document ID | Topic | Description |
|------------|-------|-------------|
| `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` | ADK/Agent Engine spec | Hard Mode rules (R1-R8), compliance requirements |
| `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md` | Inline deployment | Source code deployment pattern, ARV gates, CI workflow |
| `000-DR-STND-agentcards-and-a2a-contracts.md` | AgentCards & A2A | Contract structure, skill patterns, validation |
| `000-DR-STND-a2a-compliance-tck-inspector.md` | A2A compliance | a2a-inspector (interactive), a2a-tck (automated) validation |
| `000-DR-STND-prompt-design-a2a-contracts-iam-dept.md` | Prompt design | 5-part system prompt template, contract-first philosophy |
| `000-DR-STND-arv-minimum-gate.md` | ARV baseline | Agent Readiness Verification minimum requirements |
| `000-DR-STND-adk-lazy-loading-app-pattern.md` | Lazy-loading pattern | Module-level `app` variable pattern |

### Integration & Operations

| Document ID | Topic | Description |
|------------|-------|-------------|
| `000-AA-REPT-a2a-inspector-integration-for-department-adk-iam.md` | a2a-inspector | Runtime AgentCard validation |
| `000-RB-OPS-adk-department-operations-runbook.md` | Operations | Day-to-day operations guide |
| `000-DR-GUIDE-porting-iam-department-to-new-repo.md` | Porting guide | How to copy department to new repo |

### Implementation AARs (Phase Documentation)

| Document ID | Phase | Description |
|------------|-------|-------------|
| `128-AA-REPT-phase-4-arv-gate-dev-deploy.md` | Phase 4 | ARV gate implementation |
| `130-AA-REPT-phase-5-first-dev-deploy-and-smoke-test.md` | Phase 5-6 | First dev deployment + smoke testing |

---

## VI. External References & Citations

### Google Cloud Platform

**Vertex AI / ADK:**
- Google ADK Documentation: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- Vertex AI Agent Engine: https://cloud.google.com/vertex-ai/docs/agent-engine
- Agent Engine Inline Deployment Discussion: https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935

**Identity & Security:**
- SPIFFE Specification: https://spiffe.io/docs/latest/spiffe-about/
- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation

### A2A Protocol

**Official A2A Resources:**
- A2A Protocol Specification: https://a2a-protocol.org/
- A2A Inspector Tool (GitHub): https://github.com/a2aproject/a2a-inspector
- A2A Inspector Web UI: https://a2aprotocol.ai/a2a-inspector

### Tools & CI

**GitHub Actions:**
- Workflow Syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- Manual Triggers (workflow_dispatch): https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch

---

## VII. Quick Start Paths

### For New Developers

1. **Read Architecture**: `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`
2. **Understand Deployment**: `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
3. **Learn A2A Contracts**: `000-DR-STND-agentcards-and-a2a-contracts.md`
4. **See Operations**: `000-RB-OPS-adk-department-operations-runbook.md`

### For Operators (Deployment)

1. **ARV Baseline**: `000-DR-STND-arv-minimum-gate.md`
2. **Inline Deployment**: `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md` (Phase 6 runbook)
3. **Smoke Testing**: `000-docs/130-AA-REPT-phase-5-first-dev-deploy-and-smoke-test.md`
4. **Operations Runbook**: `000-RB-OPS-adk-department-operations-runbook.md`

### For Template Adopters (Copying to New Repo)

1. **Porting Guide**: `000-DR-GUIDE-porting-iam-department-to-new-repo.md`
2. **Template Scope**: `000-DR-STND-iam-department-template-scope-and-rules.md`
3. **Integration Checklist**: `000-DR-STND-iam-department-integration-checklist.md`

---

## VIII. Change Log

**v1.0 (2025-11-21):**
- Initial creation as master index for v0.10.0
- Links Agent Engine inline deployment, A2A/AgentCards, department architecture
- Provides external citations for all upstream specs and tools
- Maps to all related 6767 canonical standards

---

## IX. Future Expansion

**Planned Additions (Post v0.10.0):**
- [ ] External A2A network integration patterns
- [ ] Multi-region Agent Engine deployment
- [ ] Blue/Green deployment strategies for agent updates
- [ ] Production observability patterns (logging, tracing, metrics)
- [ ] Cost optimization strategies for Agent Engine
- [ ] Agent versioning and backward compatibility

**Feedback & Updates:**
- This index will be updated as new 6767 standards are created
- External resource links will be validated quarterly
- Major architecture changes will trigger index updates

---

**End of Document**
