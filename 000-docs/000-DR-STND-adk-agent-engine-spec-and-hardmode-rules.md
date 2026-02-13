# ADK + Agent Engine Specification and Hard Mode Rules

**Document ID:** 000-DR-STND-adk-agent-engine-spec-and-hardmode-rules
**Phase:** SPEC-ALIGN-ARV-EXPANSION (S1)
**Status:** Canonical Standard (Cross-Repo)
**Created:** 2025-11-20
**Purpose:** Define the canonical specification for ADK + Agent Engine compliance and Hard Mode architectural rules that apply to this department and all future ADK-based departments.

---

## I. Executive Summary

This document establishes the **canonical specification** for what "ADK + Agent Engine compliant" and "Hard Mode" mean for the IAM Department and all future departments derived from this template.

**Key Audiences:**
- **Build Captains**: Understand architectural non-negotiables
- **Department Creators**: Know what must be preserved when porting
- **ARV Engineers**: Know what to check and enforce
- **Future Claude Sessions**: Have a single source of truth

**Core Principles:**
1. **ADK First**: All agents built with Google ADK primitives, not alternative frameworks
2. **Agent Engine Runtime**: Agents deployed to Vertex AI Agent Engine, not self-hosted
3. **Gateway Separation**: Cloud Run services are REST proxies only, never run Runners
4. **Safety by Default**: Feature flags off, DRY_RUN on, CI-only deployments
5. **Single Source of Truth**: One docs root, one agent directory, one config system
6. **Template Ready**: Everything parameterizable for reuse across products

---

## II. ADK Agent Expectations

### A. Agent Construction

**REQUIRED:**

1. **ADK LlmAgent**: All agents MUST be constructed using `google.adk.agents.LlmAgent`
   ```python
   from google.adk.agents import LlmAgent

   agent = LlmAgent(
       model="gemini-2.0-flash-exp",
       name="agent_name",
       instruction="...",
       tools=[...]
   )
   ```

2. **ADK Tools**: All tools MUST use ADK's tool system:
   - Built-in tools from `google.adk.tools`
   - Custom tools wrapped as `FunctionTool`
   - NO raw HTTP calls to models in agent code
   - NO custom tool frameworks (no LangChain tools, no hand-rolled decorators)

3. **Agent Factory Pattern**: Each agent MUST:
   - Live in `agents/<agent-name>/agent.py`
   - Export a `get_agent()` factory function
   - Export a `root_agent` for ADK CLI deployment
   - Be independently testable

4. **Tool Registration**: Tools MUST be:
   - Registered via the agent's `tools=[]` parameter
   - Documented with proper docstrings (ADK introspects these)
   - Type-hinted (ADK generates schemas from type hints)

**PROHIBITED:**
- ❌ LangChain agents, CrewAI, AutoGen, or custom orchestration frameworks
- ❌ Direct `gemini.generate_content()` calls bypassing ADK
- ❌ Hand-rolled agent loops instead of ADK's Runner
- ❌ Mixing multiple agent frameworks in the same department

**RATIONALE:**
- ADK provides standardized patterns for Agent Engine deployment
- Agent Engine can only host ADK-compatible agents
- Template reusability requires consistent agent construction

### B. Memory Patterns

**REQUIRED (R5 - Dual Memory Wiring):**

1. **Session Service**: Use `VertexAiSessionService` for conversation state
   ```python
   from google.adk.sessions import VertexAiSessionService

   session_service = VertexAiSessionService(
       project_id=PROJECT_ID,
       location=LOCATION
   )
   ```

2. **Memory Bank Service**: Use `VertexAiMemoryBankService` for long-term knowledge
   ```python
   from google.adk.memory import VertexAiMemoryBankService

   memory_bank = VertexAiMemoryBankService(
       project_id=PROJECT_ID,
       location=LOCATION,
       memory_bank_id=MEMORY_BANK_ID
   )
   ```

3. **Session Persistence**: Use `after_agent_callback` for automatic session saving
   ```python
   def auto_save_session_to_memory(ctx):
       """After-agent callback for R5 compliance"""
       # Auto-save session to Memory Bank

   agent = LlmAgent(
       ...,
       after_agent_callback=auto_save_session_to_memory
   )
   ```

**OPTIONAL ALTERNATIVES:**
- Vertex AI Search for semantic retrieval (complements, doesn't replace)
- Cloud SQL/Firestore for structured state (use case specific)
- Custom memory adapters IF they wrap ADK's memory interface

**PROHIBITED:**
- ❌ Custom memory systems that bypass ADK's memory interface
- ❌ Session state stored in global variables or singletons
- ❌ Direct database access for conversation history without ADK integration

### C. Agent-to-Agent (A2A) Communication

**REQUIRED:**

1. **A2A Protocol**: Use standardized A2A contracts
   ```python
   @dataclass
   class A2AAgentCall:
       task: str
       context: Dict[str, Any]
       agent_name: str
       session_id: Optional[str]
       correlation_id: str

   @dataclass
   class A2AAgentResult:
       success: bool
       result: Any
       error: Optional[str]
       agent_name: str
       correlation_id: str
   ```

2. **Adapter Pattern**: Use unified adapter for local/engine routing
   - `call_agent_local()` for dev/test
   - `call_agent_engine()` for Agent Engine deployment
   - Environment-based routing, not hard-coded

3. **SPIFFE ID Propagation (R7)**: All A2A calls MUST include:
   ```
   spiffe://intent.solutions/agent/<product>/<env>/<region>/<version>
   ```

**PROHIBITED:**
- ❌ Direct HTTP calls between agents without A2A protocol
- ❌ Custom RPC systems (gRPC, etc.) instead of A2A
- ❌ Agent-to-agent calls that bypass correlation IDs

---

## III. Agent Engine Expectations

### A. Deployment Model

**REQUIRED (R2):**

1. **Agent Engine Deployment**: All production agents MUST be deployed to Vertex AI Agent Engine via ADK CLI
   ```bash
   adk deploy agent_engine \
     --agent_engine_id=<engine-id> \
     --project=<project> \
     --location=<region> \
     --trace_to_cloud
   ```

2. **CI-Only Deployment (R4)**: Deployments MUST go through GitHub Actions with Workload Identity Federation
   - NO manual `gcloud deploy` commands
   - NO service account key files
   - NO local deployment to production/staging

3. **ReasoningEngine Resources**: Agents are deployed as Vertex AI ReasoningEngine resources
   - Managed by Agent Engine
   - Auto-scaling and health monitoring
   - Built-in telemetry

**PROHIBITED:**
- ❌ Self-hosted ADK Runners on VMs or Cloud Run
- ❌ Embedded Runners in application code
- ❌ Manual deployments bypassing CI
- ❌ Service account keys committed to repo

**RATIONALE:**
- Agent Engine provides managed runtime with observability
- CI-only deployments ensure reproducibility and audit trails
- WIF authentication is more secure than service account keys

### B. Gateway Separation

**REQUIRED (R3):**

1. **Cloud Run as Gateway Only**: Services in `service/` directory MUST:
   - Act as REST API proxies to Agent Engine
   - NOT import `google.adk.Runner`
   - NOT run agent loops locally
   - Use OAuth2 tokens to call Agent Engine REST API

2. **Clear Separation**:
   ```
   [Slack/Web] → [Cloud Run Gateway] → [Agent Engine] → [ADK Agent]
        HTTP           REST API           Managed           LlmAgent
   ```

3. **Gateway Responsibilities**:
   - Protocol translation (Slack events → Agent Engine requests)
   - Authentication/authorization
   - Rate limiting and throttling
   - Metrics and logging

**PROHIBITED:**
- ❌ Importing `Runner` in `service/` modules
- ❌ Direct Gemini API calls in gateway code
- ❌ Running agent orchestration in Cloud Run
- ❌ Mixing gateway and agent logic

**RATIONALE:**
- Gateway separation enables independent scaling
- Agent Engine provides specialized runtime for agents
- Clear boundaries simplify debugging and monitoring

---

## IV. Hard Mode Rules (R1-R8)

These rules are **enforced in CI** and violations will fail the build.

### R1: ADK-Only Implementation

**Description:** All agents MUST be built with ADK primitives.

**Required:**
- ✅ `google.adk.agents.LlmAgent`
- ✅ ADK tool system (FunctionTool, built-ins)
- ✅ ADK memory interfaces

**Prohibited:**
- ❌ LangChain, CrewAI, AutoGen, custom frameworks
- ❌ Direct model API calls bypassing ADK
- ❌ Custom agent orchestration loops

**Enforcement:**
- `scripts/check_arv_agents.py`
- Scans for prohibited imports
- Validates agent construction patterns

**Why This Matters:**
- Agent Engine only hosts ADK agents
- Template reusability requires consistent patterns
- Mixing frameworks creates maintenance burden

### R2: Vertex AI Agent Engine Runtime

**Description:** Agents MUST be deployed to Agent Engine, not self-hosted.

**Required:**
- ✅ Deploy via ADK CLI: `adk deploy agent_engine`
- ✅ Agent Engine IDs in config
- ✅ ReasoningEngine resources

**Prohibited:**
- ❌ Self-hosted Runners on VMs/Cloud Run
- ❌ Embedded Runners in application code
- ❌ Custom agent hosting infrastructure

**Enforcement:**
- `scripts/check_arv_services.py`
- Detects Runner imports in `service/`
- CI job validates deployment target

**Why This Matters:**
- Agent Engine provides managed runtime
- Auto-scaling and observability built-in
- Simplified ops (no custom infra to maintain)

### R3: Gateway Separation

**Description:** Cloud Run services are REST proxies only, never run Runners.

**Required:**
- ✅ Cloud Run as HTTP gateway
- ✅ REST API calls to Agent Engine
- ✅ OAuth2 token authentication

**Prohibited:**
- ❌ Runner imports in `service/`
- ❌ Direct LLM calls in gateways
- ❌ Agent orchestration in Cloud Run

**Enforcement:**
- `scripts/check_arv_services.py`
- Scans `service/` for Runner imports
- Validates no agent construction in gateways

**Why This Matters:**
- Clear separation of concerns
- Independent scaling (gateways vs agents)
- Easier debugging and monitoring

### R4: CI-Only Deployments

**Description:** All deployments MUST go through GitHub Actions with WIF.

**Required:**
- ✅ GitHub Actions workflows
- ✅ Workload Identity Federation auth
- ✅ No manual `gcloud` commands for prod/staging

**Prohibited:**
- ❌ Manual `gcloud deploy`
- ❌ Service account key files
- ❌ Local deployments to production

**Enforcement:**
- CI workflow structure checks
- No `.json` key files in repo
- Deployment logs auditable

**Why This Matters:**
- Reproducible deployments
- Audit trail for compliance
- Security (no long-lived keys)

### R5: Dual Memory Wiring

**Description:** Agents use VertexAiSessionService + VertexAiMemoryBankService.

**Required:**
- ✅ `VertexAiSessionService` for conversations
- ✅ `VertexAiMemoryBankService` for long-term knowledge
- ✅ `after_agent_callback` for session persistence

**Prohibited:**
- ❌ Custom memory systems bypassing ADK
- ❌ Global variable state
- ❌ Unmanaged conversation history

**Enforcement:**
- Code review (hard to automate fully)
- ARV checks validate session config
- Integration tests verify persistence

**Why This Matters:**
- ADK memory patterns are proven
- Agent Engine optimizes for ADK memory
- Consistent UX across products

### R6: Single Documentation Folder

**Description:** All docs in `000-docs/` with NNN-CC-ABCD naming.

**Required:**
- ✅ All docs in `000-docs/`
- ✅ NNN-CC-ABCD naming convention
- ✅ 6767 prefix for canonical standards

**Prohibited:**
- ❌ Multiple doc folders
- ❌ Scattered documentation
- ❌ Random file naming

**Enforcement:**
- `scripts/check_arv_docs.py`
- Validates naming convention
- Ensures no duplicate 6767 IDs

**Why This Matters:**
- Single source of truth
- Easy to find docs
- Template extraction is straightforward

### R7: SPIFFE ID Propagation

**Description:** Immutable agent identity in all telemetry and logs.

**Required:**
- ✅ SPIFFE ID format: `spiffe://intent.solutions/agent/<product>/<env>/<region>/<version>`
- ✅ In AgentCard metadata
- ✅ In structured logs
- ✅ In A2A calls

**Prohibited:**
- ❌ Missing SPIFFE IDs
- ❌ Mutable agent identifiers
- ❌ Generic agent names without environment

**Enforcement:**
- ARV checks validate SPIFFE format
- Log samples inspected in CI
- AgentCard schema validation

**Why This Matters:**
- Distributed tracing across agents
- Security (identity-based access)
- Observability and debugging

### R8: Drift Detection

**Description:** ARV checks run FIRST in CI and block on violations.

**Required:**
- ✅ `scripts/ci/check_nodrift.sh` runs first
- ✅ Blocks on alternative frameworks
- ✅ Blocks on Runner in gateways
- ✅ Blocks on local credentials

**Prohibited:**
- ❌ Drift from ADK/Agent Engine patterns
- ❌ Custom frameworks sneaking in
- ❌ Hard-coded credentials

**Enforcement:**
- CI job order (drift first, then lint/test)
- Fails fast on violations
- Clear error messages

**Why This Matters:**
- Prevents architectural erosion
- Keeps template clean and reusable
- Maintains CI as source of truth

---

## V. Department-Wide Conventions

### A. File Layout

**REQUIRED STRUCTURE:**
```
bobs-brain/
├── agents/                     # ALL agents (factory pattern)
│   ├── bob/                    # Orchestrator agent
│   ├── iam-senior-adk-devops-lead/  # Foreman agent
│   ├── iam-adk/                # ADK design specialist
│   ├── iam-issue/              # Issue specification specialist
│   ├── iam-fix-plan/           # Fix plan specialist
│   ├── iam-fix-impl/           # Fix implementation specialist
│   ├── iam-qa/                 # QA specialist
│   ├── iam-doc/                # Documentation specialist
│   ├── iam-cleanup/            # Cleanup specialist
│   ├── iam-index/              # Knowledge indexing specialist
│   ├── config/                 # Centralized configuration
│   ├── shared_contracts.py     # Shared dataclasses
│   └── utils/                  # Shared utilities
│
├── service/                    # Protocol gateways (REST proxies only)
│   ├── a2a_gateway/            # A2A HTTP endpoint
│   └── slack_webhook/          # Slack integration
│
├── infra/terraform/            # Infrastructure as Code
│   ├── main.tf                 # Core infrastructure
│   ├── agent_engine.tf         # Agent Engine resources
│   ├── envs/                   # Environment configs
│   └── modules/                # Reusable modules
│
├── scripts/                    # Automation and checks
│   ├── ci/                     # CI-related scripts
│   └── deployment/             # Deployment utilities
│
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
├── 000-docs/                   # SINGLE docs root
│   ├── 6767-*.md               # Canonical standards (cross-repo)
│   └── NNN-*.md                # Repo-local docs
│
└── archive/                    # Deprecated code (not deleted)
```

**PROHIBITED:**
- ❌ Multiple agent directories (no `my_agent/`, `legacy_agents/`, etc.)
- ❌ Multiple doc folders (no `docs/`, `documentation/`, etc.)
- ❌ Scattered configuration (all config in `agents/config/`)

### B. Naming Conventions

**Agent Names:**
- **Orchestrator**: `bob` (or product-specific name)
- **Foreman**: `iam-senior-adk-devops-lead` (or `iam-foreman`)
- **Specialists**: `iam-<role>` (e.g., `iam-adk`, `iam-issue`, `iam-qa`)

**Config Modules:**
- `agents/config/<feature>.py` (e.g., `github_features.py`, `repos.py`)
- Centralized, not scattered

**Documentation:**
- Canonical standards: `000-CC-ABCD-description.md`
- Repo-local: `NNN-CC-ABCD-description.md`
- Where:
  - `NNN` = Sequential number (001-999)
  - `CC` = Category code (PP, AT, DR, etc.)
  - `ABCD` = Document type (PLAN, REPT, STND, etc.)

**Environment Variables:**
- Feature flags: `<FEATURE>_ENABLED` (e.g., `GITHUB_ISSUE_CREATION_ENABLED`)
- Modes: `<FEATURE>_DRY_RUN` (e.g., `GITHUB_ISSUES_DRY_RUN`)
- Lists: `<FEATURE>_ALLOWED_<ENTITY>` (e.g., `GITHUB_ISSUE_CREATION_ALLOWED_REPOS`)

### C. Feature Flag Defaults

**SAFETY FIRST:**
- New external integrations default **DISABLED**
- Dry-run modes default **ENABLED**
- Destructive operations default **OFF**

**Examples:**
```bash
# GitHub Issues
GITHUB_ISSUE_CREATION_ENABLED=false      # Must opt-in
GITHUB_ISSUES_DRY_RUN=true               # Safe by default

# Slack Notifications
SLACK_NOTIFICATIONS_ENABLED=false        # Must opt-in
SLACK_BOB_ENABLED=false                  # Must opt-in

# Org Storage
ORG_STORAGE_WRITE_ENABLED=false          # Must opt-in
```

**RATIONALE:**
- Prevents accidental spam/noise in production
- Forces conscious decision to enable
- Makes dev/test environments safe by default

### D. 6767 Canonical Standards

**What Gets 6767 Prefix:**
- ✅ Architectural patterns (agent structure, A2A, memory)
- ✅ Department-wide standards (ARV, config, deployment)
- ✅ Cross-repo templates (porting guide, integration checklist)
- ✅ Operational runbooks (deployment, troubleshooting)

**What Stays Repo-Local (No 6767):**
- ❌ Product-specific architecture
- ❌ One-off phase plans
- ❌ Status reports and SITREPs
- ❌ Meeting notes and AARs

**RATIONALE:**
- 6767 docs are meant to be copied to other repos
- Non-6767 docs are bobs-brain-specific
- Clear separation aids template extraction

---

## VI. Implementation Mapping

**IMPORTANT:** For concrete mappings from this specification to actual code, ARV scripts, and test coverage, see:

**→ `000-docs/121-DR-MAP-adk-spec-to-implementation-and-arv.md`**

That mapping document provides:
- **Implementation Locations**: Where each rule lives in the repo (agents/, service/, infra/, etc.)
- **ARV Check Scripts**: Which scripts enforce each rule (existing and planned)
- **Test Coverage**: Which tests validate each rule (existing and planned)
- **Status Summary**: Coverage overview and gap analysis
- **Priority Guidance**: What to implement first in S3

**Quick Reference - Key Implementation Files:**

| Rule | Implementation Location | ARV Script | Status |
|------|------------------------|------------|--------|
| R1: ADK-Only | `agents/*/agent.py` | `check_arv_agents.py` (TODO) | ⚠️ Partial |
| R2: Agent Engine | `infra/terraform/agent_engine.tf` | `check_arv_engine_flags.py` | ✅ |
| R3: Gateway Sep | `service/*/main.py` | `check_arv_services.py` (TODO) | ⚠️ Partial |
| R4: CI-Only | `.github/workflows/` | Manual review (WIF enforces) | ✅ |
| R5: Dual Memory | `agents/bob/agent.py` | `check_arv_memory.py` (TODO) | ⚠️ |
| R6: Single Docs | `000-docs/` | `check_arv_docs.py` (TODO) | ✅ |
| R7: SPIFFE ID | `agents/bob/a2a_card.py` | `check_arv_spiffe.py` (TODO) | ⚠️ Partial |
| R8: Drift Check | `scripts/ci/check_nodrift.sh` | ✅ Active | ✅ |

**Note:** See full mapping doc for detailed evidence, what to check, and priority guidance.

---

## VII. Template Readiness Notes

### A. What Must Be Preserved When Porting

**CRITICAL (Do Not Change):**
1. **Agent Factory Structure**: `agents/` directory with agent subdirectories
2. **Hard Mode Rules (R1-R8)**: All rules apply to new repos
3. **ADK/Agent Engine Patterns**: Agent construction, memory wiring, A2A protocol
4. **CI-Only Deployment**: GitHub Actions with WIF
5. **Single Docs Root**: `000-docs/` with naming convention
6. **Feature Flag Safety**: External integrations default OFF

**ADAPTABLE (Change Per Product):**
1. **Orchestrator Name**: `bob` → `<product>_orchestrator`
2. **Agent Tools**: Product-specific tools registered per agent
3. **System Prompts**: Tailored to product domain and tasks
4. **Config Values**: Project IDs, Agent Engine IDs, bucket names
5. **Service Gateways**: Product-specific integration endpoints

### B. Parameterization Points

**Infrastructure:**
- `PROJECT_ID`: GCP project identifier
- `AGENT_ENGINE_ID`: Vertex AI Agent Engine resource ID
- `LOCATION`: GCP region (e.g., `us-central1`)
- `ORG_STORAGE_BUCKET`: GCS bucket for org-wide knowledge

**Agents:**
- `ORCHESTRATOR_NAME`: Name of primary orchestrator agent
- `FOREMAN_NAME`: Name of departmental foreman
- `SPECIALIST_ROLES`: List of `iam-*` specialist agent roles

**Integration:**
- `SLACK_APP_ID`: Slack app identifier (if applicable)
- `GITHUB_OWNER`: GitHub org/username for issue creation

**See:** `000-docs/000-DR-STND-iam-department-template-scope-and-rules.md` for full parameterization guide (30+ points).

---

## VIII. Compliance and Enforcement

### A. How Compliance Is Verified

**Automated Checks (CI):**
1. **Drift Detection (R8)**: `scripts/ci/check_nodrift.sh` runs FIRST
2. **ARV Agents**: `scripts/check_arv_agents.py` validates agent structure
3. **ARV Services**: `scripts/check_arv_services.py` validates gateway separation
4. **ARV Docs**: `scripts/check_arv_docs.py` validates doc naming and structure
5. **ARV Config**: `scripts/check_arv_config.py` validates feature flag defaults

**Manual Reviews:**
- Memory wiring patterns (R5) - code review
- SPIFFE ID usage (R7) - log samples
- A2A protocol usage - integration tests
- System prompt quality - human review

**CI Workflow Order:**
```
1. check_nodrift.sh (R8: blocks everything if fails)
2. ARV checks (R1-R7: blocks downstream if fails)
3. Lint, unit tests, integration tests
4. Deployment (only if all checks pass)
```

### B. What Happens on Violation

**Drift Violations (R8):**
- CI fails immediately with clear error message
- PR cannot merge until fixed
- No automatic bypass mechanism

**ARV Violations (R1-R7):**
- CI fails with rule ID and location
- Specific guidance on how to fix
- Warnings (e.g., missing tests) don't block, errors do

**Deployment Violations:**
- Manual deployments to prod/staging blocked by WIF
- CI workflows require approval for prod deployments
- All deployments logged and auditable

---

## IX. Future Evolution

### A. How to Update This Spec

**When ADK/Agent Engine Changes:**
1. Update this 6767 spec doc with new patterns
2. Update `121-DR-MAP-*` with new implementation locations
3. Update ARV scripts to enforce new rules
4. Add tests for new rules
5. Document in AAR or SITREP

**When Adding New Rules:**
1. Propose rule in RFC or phase plan
2. Update this spec with new rule (e.g., R9)
3. Implement ARV check if possible
4. Update mapping doc
5. Roll out via staged deployment

### B. Versioning

**This Spec:**
- **Version 1.0**: Initial spec (SPEC-ALIGN-ARV-EXPANSION S1)
- **Version 1.1**: (Planned) Add R9-R10 for multi-cloud patterns
- **Version 2.0**: (Planned) ADK 2.0 migration

**Backwards Compatibility:**
- Repos on older spec versions can opt-in to new rules
- Breaking changes require major version bump
- Migration guides provided for breaking changes

---

## X. Related Documentation

**6767 Canonical Standards:**
- `000-DR-STND-iam-department-template-scope-and-rules.md` - Template scope and parameterization
- `000-DR-STND-arv-minimum-gate.md` - ARV baseline requirements
- `000-DR-GUIDE-porting-iam-department-to-new-repo.md` - Step-by-step porting guide

**Repo-Local Implementation:**
- `121-DR-MAP-adk-spec-to-implementation-and-arv.md` - (To be created in S2)
- `122-LS-SITR-adk-spec-alignment-and-arv-expansion.md` - (To be created in S4)

**External References:**
- Google ADK Documentation: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- Vertex AI Agent Engine: https://cloud.google.com/vertex-ai/docs/agent-engine
- SPIFFE Specification: https://spiffe.io/docs/latest/spiffe-about/

---

## XI. Summary: The Contract

**What This Spec Guarantees:**
1. **Portability**: Departments built to this spec work across products
2. **Enforceability**: CI can verify most rules automatically
3. **Clarity**: No ambiguity about what "compliant" means
4. **Evolvability**: Clear process for updating as ADK/Agent Engine evolve

**What You Must Do:**
1. **New Agents**: Build with ADK, deploy to Agent Engine, follow naming
2. **New Gateways**: REST proxy only, no Runner imports
3. **New Features**: Feature flag OFF by default, dry-run ON
4. **New Docs**: `000-docs/` with proper naming, 6767 for cross-repo
5. **New ARV Checks**: Update mapping doc, implement check script

**What You Get:**
1. **Predictable Behavior**: Agents work the same way everywhere
2. **Template Reuse**: Copy department to new repos with confidence
3. **CI Safety Net**: Drift caught early, not in production
4. **Operational Simplicity**: Fewer surprises, fewer ops burdens

---

**Last Updated:** 2025-11-20
**Phase:** SPEC-ALIGN-ARV-EXPANSION (S1)
**Status:** Active (Version 1.0)
**Next Review:** When ADK 2.0 is released or after 6 months
