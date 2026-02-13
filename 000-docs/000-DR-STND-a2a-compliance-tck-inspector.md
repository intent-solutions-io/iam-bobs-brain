# A2A Compliance Tooling - a2a-inspector and a2a-tck

**Document Type:** Canonical Standard (6767-DR-STND)
**Document ID:** 6767-121
**Status:** Active
**Applies To:** All ADK agent departments using A2A protocol
**Purpose:** Define A2A compliance validation approach using a2a-inspector and a2a-tck
**Last Updated:** 2025-11-21

---

## I. Purpose and Scope

This document defines how we use **A2A compliance tooling** in the Bob's Brain repository to validate our AgentCard implementations and A2A protocol compliance.

**Key Tools:**
- **a2a-inspector** - Interactive debugger and playground for A2A protocol validation
- **a2a-tck** - Technology Compatibility Kit for formal A2A specification compliance testing

**Target Audience:**
- Developers implementing A2A agents and AgentCards
- Operators validating A2A compliance before deployment
- QA engineers running compliance checks in CI/CD

**What This Document Covers:**
- Difference between a2a-inspector and a2a-tck
- How we use each tool in the bobs-brain / department adk iam context
- Phased adoption plan (docs → local → CI)
- External references to official A2A specifications and tools

---

## II. Tool Comparison: a2a-inspector vs a2a-tck

### a2a-inspector (Interactive Debugger)

**Purpose:** Manual, interactive validation and debugging of A2A protocol implementations

**Key Features:**
- Real-time inspection of AgentCard JSON schemas
- Interactive testing of A2A endpoints (task submission, status checks, session management)
- Visual debugging of agent-to-agent communication flows
- Support for both local development and remote endpoints

**Use Cases in bobs-brain:**
- Validating AgentCard JSON files before committing (`agents/*/. well-known/agent-card.json`)
- Testing foreman → worker delegation flows (iam-senior-adk-devops-lead → iam-*)
- Debugging A2A protocol issues during development
- One-time verification of A2A compliance before deployment

**Invocation:** Manual / developer-initiated (not automated)

**Output:** Interactive web UI or CLI output for human review

---

### a2a-tck (Technology Compatibility Kit)

**Purpose:** Automated, formal compliance testing against the A2A specification

**Key Features:**
- Comprehensive test suite covering mandatory and optional A2A spec requirements
- Automated validation of A2A endpoints (authentication, authorization, task lifecycle)
- Compliance reporting (pass/fail per spec section)
- Designed for CI/CD integration

**Use Cases in bobs-brain:**
- Automated compliance checks in CI/CD pipelines (future)
- Regression testing for A2A protocol changes
- Pre-deployment validation gates (ARV checks)
- Formal compliance certification for A2A protocol adherence

**Invocation:** Automated / CI-triggered (or manual via script)

**Output:** Machine-readable compliance report (JSON) + human-readable summary

---

## III. How We Use These Tools in bobs-brain

### Department adk iam Context

**Our A2A Architecture:**
- **Foreman:** `iam-senior-adk-devops-lead` (departmental orchestrator)
- **Workers:** `iam-adk`, `iam-issue`, `iam-fix-plan`, `iam-fix-impl`, `iam-qa`, `iam-doc`, `iam-cleanup`, `iam-index`
- **Protocol:** A2A for foreman → worker task delegation
- **AgentCards:** JSON manifests in `.well-known/agent-card.json` for each agent

### a2a-inspector Usage

**When to Use:**
- Before committing new/updated AgentCard JSON files
- When debugging A2A delegation issues (foreman → worker)
- During development of new A2A skills or contracts
- For one-time validation before deployment to Agent Engine

**How to Use:**
1. Clone a2a-inspector repository locally
2. Point it at local dev service or deployed A2A endpoint
3. Interactively test AgentCard schemas and A2A flows
4. Fix issues discovered during inspection
5. Re-validate until compliant

**Documentation:** See `scripts/run_a2a_inspector_local.md` for detailed instructions

---

### a2a-tck Usage

**When to Use:**
- Automated compliance checks in CI/CD (future, after deployment)
- Pre-deployment ARV (Agent Readiness Verification) gates
- Regression testing after A2A protocol changes
- Formal compliance certification

**How to Use:**
1. Set `A2A_TCK_SUT_URL` environment variable to A2A endpoint under test
2. Run `./run_tck.py --sut-url "$A2A_TCK_SUT_URL" --category mandatory --compliance-report report.json`
3. Review compliance report for pass/fail status per spec section
4. Fix violations and re-run until fully compliant

**Documentation:** See `scripts/run_a2a_tck_local.sh` for example invocation

---

## IV. Phased Adoption Plan

### Phase A: Documentation + Local Scripts (Current Phase)

**Goal:** Establish A2A compliance standards and prepare tooling scaffolding

**Deliverables:**
- ✅ This 6767-121 standard document
- ✅ Local helper scripts (`scripts/run_a2a_inspector_local.md`, `scripts/run_a2a_tck_local.sh`)
- ✅ CI workflow scaffold (`.github/workflows/a2a-compliance.yml`) - disabled by default
- ✅ Cross-references from master index (6767-120)

**Status:** IN PROGRESS (this phase)

**Constraints:**
- No live A2A endpoints yet (agents not deployed to Agent Engine)
- No automated TCK runs in CI (manual trigger only)
- Documentation and scaffolding only

---

### Phase B: Optional Local Manual Testing (Future)

**Goal:** Enable developers to manually validate A2A compliance locally

**Deliverables:**
- Local dev environment with A2A endpoints running (e.g., dev Agent Engine deployment or local mock)
- Manual a2a-inspector validation workflow documented
- Manual a2a-tck runs against local endpoints
- Developer documentation for troubleshooting A2A issues

**Status:** PLANNED (after Phase 6 dev deployment to Agent Engine)

**Prerequisites:**
- At least one agent deployed to Agent Engine dev environment
- A2A endpoints accessible for testing
- `A2A_TCK_SUT_URL` configured for dev environment

---

### Phase C: CI Integration (ARV Gates) (Future)

**Goal:** Automate A2A compliance checks as part of CI/CD and ARV gates

**Deliverables:**
- Automated a2a-tck runs in GitHub Actions (gated by environment variables)
- ARV check integration (`make check-arv-a2a` or similar)
- Compliance reporting in CI (pass/fail per A2A spec section)
- Automatic blocking of deployments on A2A compliance failures

**Status:** PLANNED (after agents deployed and Phase B validated)

**Prerequisites:**
- Agents deployed to Agent Engine (dev, staging, prod)
- A2A endpoints stable and accessible from CI
- Approval for automated TCK runs in CI (may require rate limiting, test budgets, etc.)

---

## V. Current Status (v0.10.0-preview)

**What's in Place:**
- ✅ This 6767-121 standard document defining A2A compliance approach
- ✅ Local helper scripts for future a2a-inspector and a2a-tck usage
- ✅ CI workflow scaffold (disabled by default, no live runs yet)
- ✅ Cross-references from master index and DevOps TL;DR

**What's NOT in Place Yet:**
- ❌ Live A2A endpoints (agents not deployed to Agent Engine)
- ❌ Automated a2a-tck runs in CI (scaffold only)
- ❌ a2a-inspector integration (documentation only)
- ❌ ARV gates for A2A compliance (planned for Phase C)

**Next Steps:**
- Complete Phase 6 dev deployment to Agent Engine
- Manually validate A2A endpoints with a2a-inspector (Phase B)
- Enable automated a2a-tck runs in CI (Phase C)

---

## VI. Compliance Expectations

### Mandatory A2A Spec Requirements

All agents in the department adk iam must comply with:
- **AgentCard Schema:** Valid JSON following a2a-protocol.org schema
- **SPIFFE ID Format:** `spiffe://intent.solutions/agent/bobs-brain/<env>/<region>/<version>`
- **Authentication:** Support for configured authentication methods (API keys, OAuth, etc.)
- **Authorization:** Proper scope validation for task submission
- **Task Lifecycle:** Correct status transitions (pending → running → completed/failed)
- **Session Management:** Stateful or stateless session handling per AgentCard declaration

### Optional A2A Spec Requirements

Agents may optionally support:
- **Advanced Skill Definitions:** Complex input/output schemas beyond basic string/JSON
- **Multi-Agent Orchestration:** Delegation to other agents via A2A protocol
- **External A2A Network Discovery:** Publishing AgentCards to public registries

### Compliance Validation

**a2a-inspector Validation:**
- Manual review of AgentCard JSON schemas
- Interactive testing of A2A endpoints (if deployed)
- Visual inspection of agent-to-agent flows

**a2a-tck Validation:**
- Automated test suite against live A2A endpoints
- Pass/fail per A2A spec section (mandatory vs optional)
- Compliance report generated for audit purposes

---

## VII. Integration with Existing Standards

**Related 6767 Standards:**
- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - ADK/Agent Engine spec (R1-R8 rules)
- **000-DR-STND-agentcards-and-a2a-contracts.md** - AgentCard and A2A contracts standard
- **000-DR-STND-prompt-design-a2a-contracts-iam-dept.md** - Prompt design with A2A
- **000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md** - Inline deployment (includes A2A endpoints)

**Workflow Integration:**
- AgentCard JSON files validated by unit tests (`tests/unit/test_agentcard_json.py`)
- a2a-inspector provides additional manual validation layer (future)
- a2a-tck provides automated compliance checks in CI (future)
- ARV gates ensure A2A compliance before deployment (future)

---

## VIII. References / External Links

### Official A2A Protocol Resources

**A2A Protocol Specification:**
- **URL:** https://a2a-protocol.org/latest/specification/
- **Purpose:** Canonical A2A protocol specification (mandatory and optional requirements)
- **Sections:** Authentication, authorization, task lifecycle, session management, AgentCard schema

**A2A Definitions:**
- **URL:** https://a2a-protocol.org/latest/definitions/
- **Purpose:** Terminology and data model definitions for A2A protocol
- **Key Terms:** Agent, Task, Session, Skill, AgentCard, SPIFFE ID

**a2a-inspector (Interactive Debugger):**
- **GitHub:** https://github.com/a2aproject/a2a-inspector
- **Purpose:** Manual, interactive validation and debugging of A2A protocol implementations
- **Documentation:** See repository README for installation and usage

**a2a-tck (Technology Compatibility Kit):**
- **GitHub:** https://github.com/a2aproject/a2a-tck
- **Purpose:** Automated compliance test suite for A2A specification
- **Documentation:** See repository README for test categories and invocation

---

### Google Cloud Platform / ADK Resources

**Google ADK Documentation:**
- **URL:** https://cloud.google.com/vertex-ai/docs/agent-development-kit
- **Purpose:** Official ADK framework documentation for building LLM agents
- **Relevant Sections:** Agent construction, tool registration, memory configuration

**Vertex AI Agent Engine:**
- **URL:** https://cloud.google.com/vertex-ai/docs/agent-engine
- **Purpose:** Managed runtime for deploying ADK agents
- **Relevant Sections:** Inline source deployment, A2A endpoint configuration, monitoring

**Agent Engine Inline Deployment Discussion:**
- **URL:** https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935
- **Purpose:** Community discussion on inline source deployment patterns
- **Key Topics:** Source package structure, entrypoint configuration, dependency management

**SPIFFE Specification:**
- **URL:** https://spiffe.io/docs/latest/spiffe-about/
- **Purpose:** Secure Production Identity Framework for Everyone (identity standard)
- **Relevant Sections:** SPIFFE ID format, trust domains, workload identity

---

### Internal bobs-brain Documentation

**Related Standards:**
- `000-docs/000-DR-INDEX-agent-engine-a2a-inline-deploy.md` - Master index
- `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - ADK spec (R1-R8)
- `000-docs/000-DR-STND-agentcards-and-a2a-contracts.md` - AgentCard contracts
- `000-docs/000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md` - Inline deployment

**Local Helper Scripts:**
- `scripts/run_a2a_inspector_local.md` - a2a-inspector usage guide
- `scripts/run_a2a_tck_local.sh` - a2a-tck invocation script

**CI Workflows:**
- `.github/workflows/a2a-compliance.yml` - A2A compliance scaffold (manual trigger only)

---

## IX. Compliance Citation Requirement

**Policy:** All future 6767 documents that reference upstream standards MUST include explicit external citations.

**Rationale:**
- Transparency: Readers can verify our interpretation against official specs
- Auditability: Clear provenance for compliance claims
- Maintainability: Easy to update when upstream specs change
- Credibility: External validation of our architecture decisions

**Required Citations:**
- Official specification URLs (e.g., https://a2a-protocol.org/latest/specification/)
- Tool/library GitHub repositories (e.g., https://github.com/a2aproject/a2a-tck)
- Vendor documentation (e.g., https://cloud.google.com/vertex-ai/docs/agent-engine)

**Examples:**
- ✅ GOOD: "Per A2A Protocol Specification (https://a2a-protocol.org/latest/specification/), all agents must support..."
- ❌ BAD: "Per the A2A protocol, all agents must support..." (no citation)

---

## X. Summary

**This Standard Defines:**
- Difference between a2a-inspector (interactive) and a2a-tck (automated)
- How we use each tool in the bobs-brain / department adk iam context
- Phased adoption plan (A: docs + scripts → B: local manual → C: CI automation)
- External citations to official A2A specs, tools, and ADK documentation

**Current Phase:** Phase A (Documentation + Local Scripts)

**Next Milestones:**
- Phase B: Manual local validation after dev deployment to Agent Engine
- Phase C: Automated CI integration with ARV gates

**Key Takeaway:** We are preparing for A2A compliance validation, but not yet running automated checks against live endpoints. This is spec alignment work only.

---

**Last Updated:** 2025-11-21
**Status:** Active
**Next Review:** After Phase 6 dev deployment to Agent Engine (when A2A endpoints are available for testing)
