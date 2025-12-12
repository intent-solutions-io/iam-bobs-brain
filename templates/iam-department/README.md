# IAM Department Template

**Version:** 1.1.0
**Source:** bobs-brain reference implementation
**Purpose:** Reusable ADK-based multi-agent software engineering department template

---

## Quick Start

### Option A: Automated Installation (Recommended)

Use the installation script for guided setup:

```bash
# From bobs-brain repo root
cd templates/iam-department
./install.sh /path/to/target/repo
```

The script will:
1. Prompt for all required parameters
2. Copy template files to target
3. Replace placeholders automatically
4. Provide next steps

After installation, validate:
```bash
./validate.sh /path/to/target/repo
```

### Option B: Manual Installation

#### 1. Copy Template to New Repo
```bash
cp -r templates/iam-department/* /path/to/new-repo/
```

#### 2. Replace Parameters

**Required Parameters** (must replace these):
```bash
{{PRODUCT_NAME}}              # e.g., "diagnosticpro", "pipelinepilot"
{{PRODUCT_DISPLAY_NAME}}       # e.g., "DiagnosticPro", "Pipeline Pilot"
{{PROJECT_ID}}                 # GCP project ID
{{LOCATION}}                   # GCP region (e.g., "us-central1")
{{REPO_OWNER}}                 # GitHub owner (e.g., "jeremylongshore")
{{REPO_NAME}}                  # GitHub repo name
{{ORCHESTRATOR_AGENT_NAME}}    # Top-level agent name (e.g., "bob", "diagnosticbot")
{{FOREMAN_AGENT_NAME}}         # Foreman name (e.g., "iam-senior-lead")
```

**Search/Replace Example:**
```bash
# In new repo root
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yaml" \) | \
  xargs sed -i 's/{{PRODUCT_NAME}}/diagnosticpro/g'
```

#### 3. Remove .template Extensions
```bash
find . -type f -name "*.template" | \
  while read f; do mv "$f" "${f%.template}"; done
```

#### 4. Customize Product-Specific Logic
- Update agent system prompts for your product domain
- Implement product-specific tools
- Configure `repos.yaml` with your repositories
- Update RAG config with your knowledge sources

#### 5. Validate
```bash
make check-arv-minimum
make test-swe-pipeline
```

---

## What's Included

### Agents
- **bob/** - Orchestrator agent template
- **iam-foreman/** - Department foreman template
- **iam-adk/** - ADK/Vertex design specialist
- **iam-issue/** - Issue specification specialist
- **iam-fix-plan/** - Fix planning specialist
- **iam-fix-impl/** - Fix implementation specialist
- **iam-qa/** - Quality assurance specialist
- **iam-doc/** - Documentation specialist
- **iam-cleanup/** - Code cleanup specialist
- **iam-index/** - Knowledge indexing specialist

### Core Infrastructure
- **shared_contracts/** - Pipeline contracts (PipelineRequest, IssueSpec, etc.)
- **a2a/** - Agent-to-Agent protocol contracts and adapter
- **tools/** - Tool layer patterns (RAG, GitHub, repos)
- **config/** - Configuration modules (RAG, agent engine, features, repos)
- **utils/** - Logging and utilities

### Services
- **service/a2a_gateway/** - A2A HTTP gateway template
- **service/slack_webhook/** - Slack integration template

### Scripts
- **scripts/** - ARV checks, pipeline runners, config printers

### Documentation
- **docs-templates/** - 6767-style doc templates for architecture, standards, guides

---

## Minimal Viable Port

To get started quickly, you need:

1. **3-4 agents:**
   - Foreman (orchestrator)
   - iam-adk (design/audit)
   - iam-issue (issue specs)
   - iam-qa (quality checks)

2. **Core contracts:**
   - PipelineRequest / PipelineResult
   - IssueSpec
   - QAVerdict

3. **A2A layer:**
   - Contracts + adapter (local mode)

4. **Pipeline orchestrator:**
   - Basic audit → issues → QA flow

5. **Tests:**
   - Synthetic repo test harness

6. **ARV check:**
   - check_arv_minimum.py

**Optional (phase in later):**
- Top-level orchestrator (bob)
- Fix agents (plan/impl)
- Doc/cleanup/index agents
- RAG integration
- Slack integration
- GitHub issue creation
- Agent Engine deployment

---

## Parameter Reference

### Core Parameters
| Parameter | Example | Required |
|-----------|---------|----------|
| {{PRODUCT_NAME}} | `bobs-brain` | Yes |
| {{PROJECT_ID}} | `bobs-brain-prod` | Yes |
| {{LOCATION}} | `us-central1` | Yes |
| {{REPO_OWNER}} | `jeremylongshore` | Yes |
| {{REPO_NAME}} | `bobs-brain` | Yes |

### Agent Parameters
| Parameter | Example | Required |
|-----------|---------|----------|
| {{ORCHESTRATOR_AGENT_NAME}} | `bob` | Yes |
| {{FOREMAN_AGENT_NAME}} | `iam-senior-adk-devops-lead` | Yes |

### Slack Parameters (if using Slack integration)
| Parameter | Example | Required |
|-----------|---------|----------|
| {{SLACK_BOT_TOKEN}} | `xoxb-...` | Yes* |
| {{SLACK_SIGNING_SECRET}} | `abc123...` | Yes* |
| {{SLACK_BOT_USER_ID}} | `U07NRCYJX8A` | Yes* |

*Only required if using Slack integration

### Agent Engine Parameters (if using Agent Engine)
| Parameter | Example | Required |
|-----------|---------|----------|
| {{AGENT_ENGINE_ID_BOB}} | `5828234061910376448` | Yes* |
| {{AGENT_ENGINE_ID_FOREMAN}} | `123456789...` | Yes* |

*Only required if deploying to Agent Engine

### RAG Parameters (if using RAG)
| Parameter | Example | Required |
|-----------|---------|----------|
| {{VERTEX_SEARCH_DATASTORE}} | `adk-documentation` | Yes* |
| {{KNOWLEDGE_HUB_BUCKET}} | `intent-adk-knowledge-hub` | Yes* |
| {{KNOWLEDGE_HUB_PREFIX}} | `bobs-brain/` | Yes* |

*Only required if using RAG

---

## Directory Structure

```
templates/iam-department/
├── README.md                          # This file
├── agents/                            # Agent templates
│   ├── bob/                           # Orchestrator template
│   │   ├── agent.py.template
│   │   └── system-prompt.md.template
│   ├── iam-foreman/                   # Foreman template
│   │   ├── orchestrator.py.template
│   │   └── system-prompt.md.template
│   ├── iam-adk/                       # Specialist template (example)
│   │   ├── agent.py.template
│   │   └── system-prompt.md.template
│   ├── (other iam-* agents...)
│   ├── shared_contracts/              # Pipeline contracts
│   │   └── __init__.py.template
│   ├── a2a/                           # A2A protocol
│   │   ├── contracts.py.template
│   │   └── adapter.py.template
│   ├── tools/                         # Tool patterns
│   │   ├── vertex_search.py.template
│   │   ├── github_tools.py.template
│   │   └── repo_tools.py.template
│   ├── config/                        # Configuration
│   │   ├── rag_config.py.template
│   │   ├── agent_engine_config.py.template
│   │   ├── features.py.template
│   │   └── repos.yaml.template
│   └── utils/                         # Utilities
│       └── logging.py.template
├── service/                           # Gateway services
│   ├── a2a_gateway/
│   │   └── main.py.template
│   └── slack_webhook/
│       └── main.py.template
├── scripts/                           # Scripts
│   ├── check_rag_readiness.py.template
│   ├── check_arv_minimum.py.template
│   └── run_swe_pipeline_once.py.template
├── docs-templates/                    # Documentation templates
│   ├── 6767-XXX-AT-ARCH-department.md.template
│   ├── 6767-XXX-DR-STND-rag.md.template
│   └── 6767-XXX-DR-STND-arv.md.template
└── Makefile.snippet                   # Makefile targets to add
```

---

## Usage Notes

### Agent System Prompts
Each agent's `system-prompt.md.template` contains:
- Role description
- Responsibilities
- Tool access patterns
- Example interactions

**Customize these** for your product domain while maintaining the role structure.

### Tools Layer
Tool templates provide patterns for:
- **RAG:** Vertex AI Search integration
- **GitHub:** Read-only repository operations
- **Repos:** Repository introspection

**Implement product-specific tools** following these patterns.

### Pipeline Modes
The foreman orchestrator supports three modes:
- **preview** - Analyze only, no artifacts
- **dry-run** - Generate artifacts, no GitHub interaction
- **create** - Full pipeline with GitHub issue creation

Start with `preview` mode for safety.

### ARV Checks
ARV (Agent Readiness Verification) checks ensure:
- Agent structure is correct (agent.py, system prompts)
- RAG configuration is valid
- Feature flags are safe
- Tests pass

Run `make arv-gates` before deployment.

---

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'agents'`
**Fix:** Ensure you're running from repo root and PYTHONPATH is set

**Issue:** ARV checks fail with missing agent.py
**Fix:** Check agent directory structure, ensure all iam-* agents have agent.py

**Issue:** RAG config errors
**Fix:** Verify VERTEX_SEARCH_DATASTORE_ID environment variable is set

**Issue:** Pipeline runs but produces no results
**Fix:** Check repos.yaml is configured with your repositories

---

## Next Steps After Porting

1. **Test Locally:**
   ```bash
   make test-swe-pipeline
   ```

2. **Configure RAG (optional):**
   - Set up Vertex AI Search datastore
   - Configure knowledge sources
   - Run `make check-rag-readiness`

3. **Enable Slack (optional):**
   - Create Slack app
   - Configure webhook URL
   - Test with Slack commands

4. **Deploy to Agent Engine (optional):**
   - Deploy agents via ADK CLI
   - Configure gateway services
   - Enable feature flags gradually

---

## Support

For questions or issues:
1. Check bobs-brain reference implementation
2. Review porting guide: `000-docs/6767-105-DR-GUIDE-porting-iam-department-to-new-repo.md`
3. Review scope doc: `000-docs/6767-104-DR-STND-iam-department-template-scope-and-rules.md`

---

**Template Version:** 1.0.0
**Last Updated:** 2025-11-20
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
