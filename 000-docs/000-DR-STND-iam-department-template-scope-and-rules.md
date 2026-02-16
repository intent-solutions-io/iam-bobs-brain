# IAM Department Template - Scope and Parameterization Rules

**Document ID:** 000-DR-STND-iam-department-template-scope-and-rules
**Title:** IAM Department Template Scope and Parameterization Rules
**Phase:** T1 (Template Extraction)
**Status:** Reference Standard
**Created:** 2025-11-20
**Purpose:** Define what components of the bobs-brain ADK/IAM department are reusable template material vs product-specific, and establish parameterization rules for porting to other repos.

---

## I. Executive Summary

This document defines the **scope and reusability boundaries** for the IAM Department template extracted from `bobs-brain`. The template enables other product repos (DiagnosticPro, PipelinePilot, Hustle, etc.) to adopt the same ADK-based multi-agent software engineering department pattern with minimal friction.

**Key Outcomes:**
- Clear separation of template (reusable) vs product-specific (bobs-brain-only) components
- Explicit parameterization rules for adapting the template to new repos
- Foundation for the `templates/iam-department/` extraction

---

## II. Template Material vs Product-Specific

### A. TEMPLATE MATERIAL (Reusable Across All Repos)

These components form the core IAM department pattern and should be extracted into `templates/iam-department/`:

#### 1. Agent Directory Layout
```
agents/
├── bob/                          # Orchestrator agent (rename per product)
│   ├── agent.py                  # LlmAgent with tools
│   ├── system-prompt.md          # Orchestrator instructions
│   └── tools/                    # Product-agnostic tool patterns
├── iam-foreman/                  # Foreman pattern (currently iam-senior-adk-devops-lead)
│   ├── orchestrator.py           # SWE pipeline orchestrator
│   └── system-prompt.md          # Foreman instructions
├── iam-adk/                      # ADK/Vertex design specialist
├── iam-issue/                    # Issue specification specialist
├── iam-fix-plan/                 # Fix plan design specialist
├── iam-fix-impl/                 # Fix implementation specialist
├── iam-qa/                       # Quality assurance specialist
├── iam-doc/                      # Documentation specialist
├── iam-cleanup/                  # Code cleanup specialist
└── iam-index/                    # Knowledge indexing specialist
```

**Template-eligible patterns:**
- Agent role definitions and responsibilities
- System prompt structures (with product-specific placeholders)
- Tool registration patterns
- Memory configuration (Session + Memory Bank)
- A2A integration patterns

#### 2. Shared Contracts
```
agents/shared_contracts.py
```

**Template-eligible:**
- `PipelineRequest` / `PipelineResult` dataclasses
- `IssueSpec` contract (GitHub issue draft)
- `FixPlan` contract (fix planning)
- `QAVerdict` contract (quality checks)
- `RepoContext` contract (repository metadata)

**Parameterization:** Product-specific fields may be added, but core shape should remain

#### 3. A2A Layer
```
agents/a2a/
├── contracts.py                  # A2AAgentCall / A2AAgentResult
└── adapter.py                    # call_agent_local / call_agent_engine
```

**Template-eligible:**
- A2A protocol shapes
- Adapter pattern (local vs engine routing)
- Correlation ID propagation
- SPIFFE ID patterns

**Parameterization:** Agent names, engine IDs, environment detection

#### 4. SWE Pipeline Orchestrator
```
agents/iam-foreman/orchestrator.py
```

**Template-eligible patterns:**
- Pipeline orchestration flow (audit → issues → plans → fixes → QA → doc)
- Agent coordination via A2A
- Pipeline modes (preview / dry-run / create)
- Guardrails (issue limit, dry-run enforcement)
- Result aggregation

**NOT template-eligible:**
- Product-specific tools called during pipeline
- Repo-specific validation logic

#### 5. Tools Layer Patterns
```
agents/tools/
├── vertex_search.py              # RAG tool factory pattern
├── github_tools.py               # GitHub read-only operations pattern
└── repo_tools.py                 # Repository introspection pattern
```

**Template-eligible:**
- Tool factory patterns
- Profile system (agent → tool mapping)
- Vertex AI Search integration pattern
- GitHub read-only client pattern

**Parameterization:**
- `{{PROJECT_ID}}`, `{{LOCATION}}`, `{{DATASTORE_ID}}`
- Repository owner/name
- GitHub token configuration

#### 6. Configuration Modules
```
agents/config/
├── rag_config.py                 # RAG configuration pattern
├── agent_engine_config.py        # Agent Engine ID mapping
├── features.py                   # Feature flags pattern
└── repos.yaml                    # Repository registry pattern
```

**Template-eligible:**
- Config module structures
- Environment detection patterns
- Feature flag patterns
- RAG configuration shape

**Parameterization:** All specific IDs, names, URLs, bucket paths

#### 7. Gateway Services Patterns
```
service/
├── a2a_gateway/                  # A2A HTTP gateway pattern
│   └── main.py                   # FastAPI A2A protocol handler
└── slack_webhook/                # Slack integration pattern
    └── main.py                   # Slack event handler → SWE pipeline
```

**Template-eligible:**
- Gateway architecture (Cloud Run proxy pattern)
- A2A protocol endpoint shapes
- Slack event handling patterns
- Pipeline trigger integration

**Parameterization:**
- Agent Engine URLs
- Slack bot tokens, signing secrets
- Channel IDs, command names

#### 8. Scripts & Tooling
```
scripts/
├── check_rag_readiness.py        # ARV gate for RAG config
├── check_arv_minimum.py          # ARV gate for agent structure
├── check_arv_engine_flags.py     # ARV gate for feature flags
├── print_rag_config.py           # Config validation
├── print_agent_engine_config.py  # Engine ID validation
└── run_swe_pipeline_once.py      # CLI pipeline runner
```

**Template-eligible:**
- ARV check patterns (structure, RAG, flags)
- Config printer patterns
- CLI runner patterns

**Parameterization:** Agent names, config paths

#### 9. Makefile Targets
```makefile
check-rag-readiness
check-arv-minimum
check-arv-engine-flags
arv-gates
test-swe-pipeline
run-swe-pipeline-demo
```

**Template-eligible:** All targets and their patterns

#### 10. Documentation Templates
```
000-docs/
├── 000-AT-ARCH-department-architecture.md.template
├── 000-DR-STND-rag-config-pattern.md.template
├── 000-DR-STND-github-integration.md.template
├── 000-DR-STND-a2a-protocol.md.template
├── 000-DR-STND-slack-triggers.md.template
├── 000-DR-STND-arv-minimum.md.template
└── 000-AA-REPT-deployment-aar.md.template
```

**Template-eligible:** Doc structures, section headings, pattern descriptions

**Parameterization:** Product names, repo URLs, agent names

---

### B. PRODUCT-SPECIFIC (Bobs-Brain Only - NOT Template Material)

These components are **specific to bobs-brain** and should NOT be extracted as-is:

#### 1. Specific Repository Information
- **Repo names:** `jeremylongshore/bobs-brain`
- **Repo IDs:** Specific GitHub repo IDs in `repos.yaml`
- **Branch strategies:** Main/develop/feature patterns specific to this repo

#### 2. Agent Engine Deployment IDs
- **Specific reasoning engine IDs:**
  - Bob current: `5828234061910376448`
  - Bob next-gen: `BOB_PROD_NEXT_GEN_PLACEHOLDER`
  - Foreman IDs per environment
- **SPIFFE IDs:** `spiffe://intent.solutions/agent/bobs-brain/...`

#### 3. Slack Configuration
- **Bot tokens:** Specific to bobs-brain Slack app
- **Channel IDs:** `#bobs-brain-alerts`, etc.
- **Command names:** `/bob-audit`, `/bob-pipeline`
- **User IDs:** `<@U07NRCYJX8A>` (Bob's Slack user ID)

#### 4. Knowledge Hub Specifics
- **GCS bucket:** `intent-adk-knowledge-hub`
- **Prefix patterns:** `bobs-brain/`, `shared/adk/`
- **Datastore IDs:** `adk-documentation` (Vertex AI Search)

#### 5. Project/Environment IDs
- **Project ID:** `bobs-brain-prod` (or dev/staging variants)
- **Location:** `us-central1`
- **Service account emails**
- **Cloud Run service URLs**

#### 6. Branding & Names
- **Product name:** "Bob's Brain"
- **Agent names:** "Bob", "iam-senior-adk-devops-lead"
- **Description strings:** "AI assistant for..."
- **Version numbers:** `0.8.0`, `0.9.0`

#### 7. Product-Specific Tools
- **Bobs-brain-specific tools:**
  - Tools that query bobs-brain-only APIs
  - Tools that reference bobs-brain documentation
  - Tools tied to specific bobs-brain workflows

---

## III. Parameterization Rules

### A. Required Parameters (Must Be Replaced)

When porting the IAM department template to a new repo, these parameters **MUST** be replaced:

| Parameter | Example (bobs-brain) | Description |
|-----------|---------------------|-------------|
| `{{PRODUCT_NAME}}` | `bobs-brain` | Product/repo short name |
| `{{PRODUCT_DISPLAY_NAME}}` | `Bob's Brain` | Human-readable product name |
| `{{PROJECT_ID}}` | `bobs-brain-prod` | GCP project ID |
| `{{LOCATION}}` | `us-central1` | GCP region |
| `{{REPO_OWNER}}` | `jeremylongshore` | GitHub organization/user |
| `{{REPO_NAME}}` | `bobs-brain` | GitHub repository name |
| `{{REPO_FULL_NAME}}` | `jeremylongshore/bobs-brain` | Full GitHub repo path |
| `{{ORCHESTRATOR_AGENT_NAME}}` | `bob` | Top-level orchestrator name |
| `{{FOREMAN_AGENT_NAME}}` | `iam-senior-adk-devops-lead` | Department foreman name |
| `{{SLACK_BOT_TOKEN}}` | `xoxb-...` | Slack OAuth token |
| `{{SLACK_SIGNING_SECRET}}` | `abc123...` | Slack app signing secret |
| `{{SLACK_BOT_USER_ID}}` | `U07NRCYJX8A` | Slack bot user ID |
| `{{AGENT_ENGINE_ID_BOB}}` | `5828234061910376448` | Agent Engine reasoning engine ID |
| `{{AGENT_ENGINE_ID_FOREMAN}}` | `FOREMAN_PROD_PLACEHOLDER` | Foreman engine ID |
| `{{SPIFFE_ID_PREFIX}}` | `spiffe://intent.solutions/agent/bobs-brain` | SPIFFE ID base |
| `{{KNOWLEDGE_HUB_BUCKET}}` | `intent-adk-knowledge-hub` | GCS bucket for docs |
| `{{KNOWLEDGE_HUB_PREFIX}}` | `bobs-brain/` | Bucket prefix for product |
| `{{VERTEX_SEARCH_DATASTORE}}` | `adk-documentation` | Vertex AI Search datastore |
| `{{A2A_GATEWAY_URL}}` | `https://a2a-gateway-...run.app` | A2A gateway Cloud Run URL |
| `{{SLACK_WEBHOOK_URL}}` | `https://slack-webhook-...run.app` | Slack webhook URL |

### B. Optional Parameters (Can Be Customized)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `{{VERSION}}` | `0.1.0` | Initial version for new repo |
| `{{DEFAULT_ENV}}` | `dev` | Default environment |
| `{{PIPELINE_ISSUE_LIMIT}}` | `20` | Max issues per pipeline run |
| `{{PIPELINE_DEFAULT_MODE}}` | `preview` | Default pipeline mode |
| `{{RAG_ENABLED_DEFAULT}}` | `false` | Default RAG enablement |
| `{{LOG_LEVEL}}` | `INFO` | Logging level |

### C. Structural Parameters (Directory Names)

| Parameter | Example | Notes |
|-----------|---------|-------|
| `{{DOCS_DIR}}` | `000-docs` | Can vary by repo |
| `{{AGENTS_DIR}}` | `agents` | Standard |
| `{{SERVICE_DIR}}` | `service` | Standard |
| `{{SCRIPTS_DIR}}` | `scripts` | Standard |
| `{{INFRA_DIR}}` | `infra/terraform` | Can vary |

---

## IV. Components That Can Be Copied As-Is

These components require **minimal or no changes** when porting:

### 1. Core Contracts (agents/shared_contracts.py)
- `PipelineRequest`
- `PipelineResult`
- `IssueSpec`
- `FixPlan`
- `QAVerdict`

**Why:** Generic data shapes, no product-specific logic

### 2. A2A Protocol (agents/a2a/contracts.py)
- `A2AAgentCall`
- `A2AAgentResult`

**Why:** Standard protocol, product-agnostic

### 3. Pipeline Orchestration Pattern
- Overall flow: audit → issues → fixes → QA → doc
- Mode switching (preview/dry-run/create)
- Guardrails and limits

**Why:** Universal SWE pipeline pattern

### 4. ARV Check Patterns
- Structure checks (agent.py, system prompts)
- RAG configuration validation
- Feature flag safety checks

**Why:** Standard validation patterns

### 5. Logging Helpers (agents/utils/logging.py)
- Correlation ID helpers
- Pipeline/agent/GitHub logging functions

**Why:** Generic logging utilities

---

## V. Minimal Viable Port

To establish a **minimal viable IAM department** in a new repo, you need:

### Required Components:
1. **Foreman + 3 specialists:**
   - Foreman (orchestrator)
   - iam-adk (design/audit)
   - iam-issue (issue specs)
   - iam-qa (quality checks)

2. **Shared contracts:**
   - `PipelineRequest` / `PipelineResult`
   - `IssueSpec`
   - `QAVerdict`

3. **A2A layer:**
   - Contracts + adapter (local mode)

4. **Pipeline orchestrator:**
   - Basic audit → issues → QA flow

5. **Tests:**
   - `test_swe_pipeline.py` (with synthetic repo)

6. **ARV minimum check:**
   - `check_arv_minimum.py`

### Optional (Can Be Phased In):
- Bob orchestrator (top-level)
- iam-fix-* agents (plan/impl)
- iam-doc, iam-cleanup, iam-index
- RAG integration
- Slack integration
- GitHub issue creation
- Agent Engine deployment
- Cloud Run gateways

---

## VI. Parameterization Process

### Step 1: Copy Template
```bash
cp -r templates/iam-department/ /path/to/new-repo/
```

### Step 2: Global Search/Replace
```bash
# In new repo root
find . -type f -name "*.py" -o -name "*.md" -o -name "*.yaml" | \
  xargs sed -i 's/{{PRODUCT_NAME}}/diagnosticpro/g'

# Repeat for all required parameters
```

### Step 3: Remove .template Extensions
```bash
find . -type f -name "*.template" | \
  while read f; do mv "$f" "${f%.template}"; done
```

### Step 4: Customize Product-Specific
- Update tool implementations for product's APIs/data
- Customize agent system prompts for product domain
- Configure repos.yaml with product's repositories

### Step 5: Validate
```bash
make check-arv-minimum
make test-swe-pipeline
```

---

## VII. Template Maintenance Rules

### A. Keeping Template in Sync

As `bobs-brain` evolves:

1. **When to update template:**
   - New agent role added
   - Contract shapes change
   - Pipeline flow improves
   - ARV checks enhanced
   - Tool patterns improved

2. **How to update:**
   - Extract changes to template files
   - Update parameterization rules
   - Version the template
   - Document breaking changes

### B. Versioning

Template versions should follow:
```
templates/iam-department/VERSION
```

Example: `1.0.0` (initial), `1.1.0` (new agents), `2.0.0` (breaking changes)

### C. Documentation Updates

When template changes:
1. Update `000-DR-GUIDE-porting-iam-department-to-new-repo.md` (porting guide)
2. Update `templates/iam-department/README.md`
3. Add migration notes for existing ports

---

## VIII. Quality Standards for Template Files

All `.template` files must:

1. **Use consistent placeholders:**
   - `{{UPPERCASE_WITH_UNDERSCORES}}`
   - Never hardcode bobs-brain-specific values

2. **Include inline comments:**
   ```python
   # TEMPLATE: Replace with your product's project ID
   PROJECT_ID = "{{PROJECT_ID}}"
   ```

3. **Provide examples:**
   ```python
   # Example: bobs-brain → "bobs-brain"
   # Example: DiagnosticPro → "diagnosticpro"
   PRODUCT_NAME = "{{PRODUCT_NAME}}"
   ```

4. **Have README sections:**
   Each template directory/file should have a README explaining:
   - Purpose
   - Required parameters
   - Optional customizations
   - Examples

---

## IX. Anti-Patterns to Avoid

### DON'T:
1. ❌ Hardcode bobs-brain references in templates
2. ❌ Include actual credentials/tokens
3. ❌ Copy product-specific tool implementations as templates
4. ❌ Include bobs-brain-specific GitHub repo IDs
5. ❌ Reference bobs-brain Slack channels/users
6. ❌ Use actual Agent Engine IDs as examples

### DO:
1. ✅ Use clear, obvious placeholders
2. ✅ Provide both parameter name and example
3. ✅ Include validation in ARV checks
4. ✅ Document all required vs optional parameters
5. ✅ Test templates with fresh clone + search/replace

---

## X. Success Criteria

The IAM department template is successful if:

1. **New repo can port in < 1 day:**
   - Copy template
   - Replace parameters
   - Pass ARV checks
   - Run synthetic pipeline test

2. **Minimal changes needed:**
   - < 10% of template files require custom logic
   - Most changes are search/replace

3. **Clear boundaries:**
   - Template vs product-specific is obvious
   - No ambiguity about what to customize

4. **Maintenance is straightforward:**
   - Improvements in bobs-brain → template updates clear
   - Breaking changes documented

---

## XI. Next Steps

1. **Phase T1, Task 2:** Create `templates/iam-department/` skeleton with all template files
2. **Phase T1, Task 3:** Write `templates/iam-department/README.md` usage guide
3. **Phase T2:** Create porting guide and integration checklist docs
4. **Phase T3:** Create ops/runbooks for day-to-day use

---

**Document Status:** Reference Standard
**Template Version:** 1.0.0
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
**Related Docs:**
- 000-DR-GUIDE-porting-iam-department-to-new-repo.md (next)
- 000-DR-STND-iam-department-integration-checklist.md
- templates/iam-department/README.md
