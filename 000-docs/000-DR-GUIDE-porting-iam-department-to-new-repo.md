# Porting Guide: IAM Department to New Repository

**Document ID:** 000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE
**Title:** Porting the IAM Department Template to New Repositories
**Phase:** T2 (Porting & Integration)
**Status:** Canonical Guide
**Created:** 2025-11-20
**Purpose:** Step-by-step guide for installing the ADK-based IAM department pattern from bobs-brain into a new product repository.

---

## I. Executive Summary

This guide walks you through the process of **porting the IAM department template** from `bobs-brain` to a new product repository (e.g., DiagnosticPro, PipelinePilot, Hustle).

**Time Estimate:** 1-2 days for minimal viable port, 1 week for full integration

**Prerequisites:**
- Target repo has basic Python/ADK setup
- Access to GCP project for target product
- (Optional) Slack workspace for integration
- (Optional) GitHub repo write access for issue creation

**What You'll Build:**
- Multi-agent IAM department for your product
- SWE pipeline orchestration (audit → issues → fixes → QA → docs)
- (Optional) RAG integration with your product's knowledge
- (Optional) Slack integration
- (Optional) Agent Engine deployment

---

## II. Pre-Flight Checklist

Before starting the port, verify your target repository has:

### Required:
- [ ] Python 3.11+ environment
- [ ] Git repository (GitHub, GitLab, etc.)
- [ ] Basic directory structure (`src/` or equivalent)
- [ ] Test framework (pytest recommended)
- [ ] CI/CD pipeline (GitHub Actions, GitLab CI, etc.)

### Recommended:
- [ ] Documentation folder (`docs/` or `000-docs/`)
- [ ] Makefile or task runner
- [ ] Virtual environment management (venv, poetry, etc.)
- [ ] Code formatting (black, ruff, etc.)

### Optional (Can Add Later):
- [ ] Terraform/IaC setup
- [ ] GCP project configured
- [ ] Slack workspace
- [ ] Agent Engine access

---

## III. Porting Process Overview

### High-Level Steps:
1. **Copy template** → Target repo
2. **Replace parameters** → Product-specific values
3. **Configure repos** → repos.yaml
4. **Customize agents** → System prompts + tools
5. **Wire RAG** (optional) → Knowledge sources
6. **Test locally** → Synthetic repo test
7. **Integrate CI** → ARV checks
8. **Deploy** (optional) → Slack/Agent Engine

---

## IV. Step-by-Step Porting Instructions

### Step 1: Copy Template Files

**From bobs-brain:**
```bash
cd /path/to/bobs-brain
```

**To target repo:**
```bash
# Copy entire template directory
cp -r templates/iam-department/* /path/to/target-repo/

# OR copy selectively (minimal viable port):
mkdir -p /path/to/target-repo/agents
cp -r templates/iam-department/agents/iam-foreman /path/to/target-repo/agents/
cp -r templates/iam-department/agents/iam-adk /path/to/target-repo/agents/
cp -r templates/iam-department/agents/iam-issue /path/to/target-repo/agents/
cp -r templates/iam-department/agents/iam-qa /path/to/target-repo/agents/
cp -r templates/iam-department/agents/shared_contracts /path/to/target-repo/agents/
cp -r templates/iam-department/agents/a2a /path/to/target-repo/agents/
cp -r templates/iam-department/agents/config /path/to/target-repo/agents/
```

### Step 2: Parameter Replacement

**Create a parameter mapping file:**
```bash
cd /path/to/target-repo

# Create replacement script
cat > replace_params.sh << 'EOF'
#!/bin/bash
# Parameter replacement for IAM department template

# Core parameters
PRODUCT_NAME="diagnosticpro"                    # Your product name (lowercase, no spaces)
PRODUCT_DISPLAY_NAME="DiagnosticPro"            # Display name (can have caps/spaces)
PROJECT_ID="diagnosticpro-prod"                 # GCP project ID
LOCATION="us-central1"                          # GCP region
REPO_OWNER="jeremylongshore"                    # GitHub owner
REPO_NAME="diagnostic-platform"                 # GitHub repo name
ORCHESTRATOR_AGENT_NAME="diagnosticbot"         # Top agent name (or keep "bob")
FOREMAN_AGENT_NAME="iam-senior-lead"            # Foreman name (or keep long name)

# Find and replace in all template files
find . -type f \( -name "*.template" -o -name "*.py" -o -name "*.md" -o -name "*.yaml" \) | while read file; do
  sed -i "s/{{PRODUCT_NAME}}/$PRODUCT_NAME/g" "$file"
  sed -i "s/{{PRODUCT_DISPLAY_NAME}}/$PRODUCT_DISPLAY_NAME/g" "$file"
  sed -i "s/{{PROJECT_ID}}/$PROJECT_ID/g" "$file"
  sed -i "s/{{LOCATION}}/$LOCATION/g" "$file"
  sed -i "s/{{REPO_OWNER}}/$REPO_OWNER/g" "$file"
  sed -i "s/{{REPO_NAME}}/$REPO_NAME/g" "$file"
  sed -i "s/{{ORCHESTRATOR_AGENT_NAME}}/$ORCHESTRATOR_AGENT_NAME/g" "$file"
  sed -i "s/{{FOREMAN_AGENT_NAME}}/$FOREMAN_AGENT_NAME/g" "$file"
done

echo "✅ Parameter replacement complete!"
EOF

chmod +x replace_params.sh
./replace_params.sh
```

**Remove .template extensions:**
```bash
find . -type f -name "*.template" | while read f; do
  mv "$f" "${f%.template}"
done
```

### Step 3: Configure repos.yaml

**Edit `agents/config/repos.yaml`:**
```yaml
repositories:
  - name: "diagnosticpro"
    full_name: "jeremylongshore/diagnostic-platform"
    url: "https://github.com/jeremylongshore/diagnostic-platform"
    primary: true
    description: "DiagnosticPro main repository"
    primary_language: "Python"
    frameworks:
      - "Google ADK"
      - "FastAPI"
    key_directories:
      agents: "agents/"
      service: "service/"
      scripts: "scripts/"
      tests: "tests/"
      docs: "docs/"  # Or "000-docs/" if using that convention
```

### Step 4: Customize Agent System Prompts

**For each agent, edit system prompts to reflect your product domain:**

**Example: `agents/iam-adk/system-prompt.md`**
```markdown
# DiagnosticPro ADK Design Specialist

You are an ADK/Vertex AI design specialist for **DiagnosticPro**.

## Your Product Domain: DiagnosticPro

DiagnosticPro is a repair and diagnostic platform that:
- [Add product-specific context]
- [Add domain knowledge]
- [Add key technical details]

## When Auditing DiagnosticPro Code

Look for:
- ADK compliance (use LlmAgent, proper tools, dual memory)
- DiagnosticPro-specific best practices
- Integration patterns with diagnostic APIs
- [Add product-specific concerns]
```

**Repeat for:**
- `agents/iam-issue/system-prompt.md`
- `agents/iam-qa/system-prompt.md`
- `agents/iam-foreman/system-prompt.md`
- (Other agents as needed)

### Step 5: Implement Product-Specific Tools

**Create tools for your product's specific needs:**

**Example: `agents/tools/diagnosticpro_tools.py`**
```python
"""
DiagnosticPro-specific tools for IAM department agents.
"""

from google.adk.tools import Tool

class DiagnosticTool(Tool):
    """Query DiagnosticPro diagnostic database."""

    def run(self, query: str) -> str:
        # Implement your product-specific logic
        pass

# Register with agent profiles
# See agents/tools/profiles.py for pattern
```

### Step 6: Create Synthetic Test Repo (Optional but Recommended)

**For testing the SWE pipeline:**
```bash
mkdir -p tests/data/synthetic_repo/diagnosticpro

# Create minimal test structure
cat > tests/data/synthetic_repo/diagnosticpro/sample.py << 'EOF'
"""
Sample DiagnosticPro code for testing IAM department.
"""

# INTENTIONAL ISSUE: Missing proper error handling
def process_diagnostic(data):
    result = data['diagnostic_id']  # Could raise KeyError
    return result
EOF
```

### Step 7: Run Local Tests

**Test the SWE pipeline locally:**
```bash
# Ensure PYTHONPATH includes repo root
export PYTHONPATH=/path/to/target-repo:$PYTHONPATH

# Run pipeline test
python -m pytest tests/test_swe_pipeline.py -v

# Or run CLI demo
python scripts/run_swe_pipeline_once.py \
  --repo-path tests/data/synthetic_repo/diagnosticpro \
  --task "Audit for ADK compliance" \
  --mode preview
```

**Expected output:**
```
✅ Pipeline executed successfully
📊 Results:
  - Issues found: 3
  - Fixes proposed: 0 (preview mode)
  - Duration: 45.2s
```

### Step 8: Run ARV Checks

**IMPORTANT:** Every IAM department MUST define an ARV (Agent Readiness Verification) checklist and runner.
See `117-AA-REPT-iam-department-arv-implementation.md` in bobs-brain for the reference implementation.

**Run comprehensive ARV check:**
```bash
# Add to Makefile (copy from templates/iam-department/Makefile.snippet)
make arv-department
```

**Expected output:**
```
======================================================================
ARV – IAM/ADK Department Readiness Verification
======================================================================
Environment: DEV

[CONFIG]
  ✅ config-basic – PASSED
[TESTS]
  ✅ tests-unit – PASSED
  ✅ tests-swe-pipeline – PASSED
[ENGINE]
  ✅ engine-flags-safety – PASSED
  ✅ arv-minimum-requirements – PASSED

RESULT: PASSED (4/4 required checks passed)
======================================================================
```

**Individual checks** (for debugging):
```bash
make check-arv-minimum        # Structure only
make check-config             # Config only
make check-rag-readiness      # RAG only (if enabled)
```

### Step 9: Integrate with CI

**Add to `.github/workflows/ci.yml` (or equivalent):**
```yaml
jobs:
  arv-department:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run ARV Department Check (ARV-DEPT)
        run: make arv-department
        env:
          DEPLOYMENT_ENV: dev
```

**Note:** This replaces individual ARV checks with a comprehensive readiness gate. See `117-AA-REPT-iam-department-arv-implementation.md` for details.

---

## V. Optional Integrations

### Option A: RAG Integration

**If your product has knowledge sources to query:**

1. **Create Vertex AI Search datastore:**
   ```bash
   # (GCP Console or gcloud command)
   ```

2. **Configure RAG:**
   ```python
   # agents/config/rag_config.py
   VERTEX_SEARCH_DATASTORE_ID = "diagnosticpro-knowledge"
   KNOWLEDGE_HUB_BUCKET = "diagnosticpro-knowledge-hub"
   KNOWLEDGE_HUB_PREFIX = "diagnosticpro/"
   ```

3. **Test RAG:**
   ```bash
   make check-rag-readiness
   ```

### Option B: Slack Integration

**If you want Slack-triggered pipelines:**

1. **Create Slack app** (slack.api/apps)
2. **Configure webhook:**
   ```python
   # service/slack_webhook/main.py
   SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
   SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
   ```

3. **Deploy webhook to Cloud Run:**

   > ⚠️ **DEPRECATED (R4 Violation):** Manual `gcloud run deploy` commands are banned in Hard Mode.
   > ✅ **Use instead:** Terraform + GitHub Actions (see `000-DR-STND-slack-gateway-deploy-pattern.md`)

   ```bash
   # ❌ DEPRECATED - DO NOT USE (R4 Violation)
   gcloud run deploy diagnosticpro-slack-webhook \
     --source service/slack_webhook \
     --region us-central1

   # ✅ CORRECT: Use Terraform module (see infra/terraform/modules/slack_bob_gateway/)
   # Deploy via GitHub Actions workflow: .github/workflows/deploy-slack-gateway-dev.yml
   ```

4. **Configure Slack Events API** to point to Cloud Run URL

### Option C: Agent Engine Deployment

**If you want to deploy agents to Vertex AI Agent Engine:**

1. **Configure Agent Engine IDs:**
   ```python
   # agents/config/agent_engine_config.py
   PROD_CONFIG: Dict[str, AgentEngineConfig] = {
       "diagnosticbot": AgentEngineConfig(
           reasoning_engine_id="projects/diagnosticpro-prod/locations/us-central1/reasoningEngines/...",
           ...
       ),
   }
   ```

2. **Deploy via ADK CLI:**
   ```bash
   cd agents/diagnosticbot
   adk deploy agent_engine --trace_to_cloud
   ```

3. **Test via Agent Engine REST API or gateway**

---

## VI. Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'agents'`

**Solution:**
```bash
# Ensure PYTHONPATH set correctly
export PYTHONPATH=/path/to/target-repo:$PYTHONPATH

# Or add to pytest.ini:
# [pytest]
# pythonpath = .
```

**Issue:** ARV checks fail - missing agent.py

**Solution:**
```bash
# Ensure each iam-* agent has:
agents/iam-adk/agent.py
agents/iam-issue/agent.py
agents/iam-qa/agent.py

# If missing, create minimal agent.py:
cp templates/iam-department/agents/iam-adk/agent.py.template agents/iam-adk/agent.py
# Then remove .template extension and customize
```

**Issue:** Pipeline runs but produces no results

**Solution:**
- Check repos.yaml is configured
- Verify repo_hint matches a configured repository
- Check agent system prompts are customized for your product
- Run with `--mode preview` first to see analysis without artifacts

**Issue:** RAG config errors

**Solution:**
```bash
# Verify environment variables:
echo $VERTEX_SEARCH_DATASTORE_ID

# Run readiness check:
make check-rag-readiness
```

---

## VII. Minimal Viable Port Checklist

To get a working IAM department in < 1 day:

### Absolutely Required:
- [ ] Copy foreman + 3 specialists (adk, issue, qa)
- [ ] Replace core parameters (product name, repo)
- [ ] Configure repos.yaml
- [ ] Create synthetic test repo
- [ ] Run `make test-swe-pipeline` successfully
- [ ] Run `make check-arv-minimum` successfully

### Highly Recommended:
- [ ] Customize agent system prompts for product domain
- [ ] Implement 1-2 product-specific tools
- [ ] Integrate ARV checks into CI

### Can Add Later:
- [ ] Top-level orchestrator (bob/diagnosticbot)
- [ ] Fix agents (iam-fix-plan, iam-fix-impl)
- [ ] Doc/cleanup/index agents
- [ ] RAG integration
- [ ] Slack integration
- [ ] Agent Engine deployment

---

## VIII. Post-Port Validation

After porting, validate everything works:

### 1. Local Testing
```bash
# ARV checks
make arv-gates

# Pipeline test
make test-swe-pipeline

# CLI demo
make run-swe-pipeline-demo
```

### 2. CI Integration
```bash
# Push to GitHub and verify CI passes
git push origin feature/iam-department-port

# Check GitHub Actions/CI logs
```

### 3. Manual Pipeline Run
```bash
# Run real analysis on your codebase
python scripts/run_swe_pipeline_once.py \
  --repo-path . \
  --task "Audit main API module for ADK compliance" \
  --mode preview
```

### 4. Review Results
- Check `PipelineResult` output
- Verify `IssueSpec` objects are sensible
- Confirm QA verdicts are accurate

---

## IX. Next Steps After Successful Port

### Phase 1: Stabilization (Week 1)
- Run pipeline on multiple modules
- Fix any agent configuration issues
- Tune system prompts based on results
- Add product-specific tools as needed

### Phase 2: Integration (Week 2)
- Enable RAG (if applicable)
- Set up Slack integration (if desired)
- Configure GitHub issue creation
- Train team on usage

### Phase 3: Scale (Week 3+)
- Deploy to Agent Engine (optional)
- Add fix agents (iam-fix-*)
- Add doc/cleanup agents
- Integrate with team workflows

---

## X. Support & Resources

### Documentation
- **Template Scope:** `000-docs/000-DR-STND-iam-department-template-scope-and-rules-DR-STND-iam-department-template-scope-and-rules.md`
- **Integration Checklist:** `000-docs/000-DR-STND-iam-department-integration-checklist-DR-STND-iam-department-integration-checklist.md`
- **Ops Runbook:** `000-docs/000-RB-OPS-adk-department-operations-runbook-RB-OPS-adk-department-operations-runbook.md`
- **Usage Guide:** `000-docs/000-DR-GUIDE-iam-department-user-guide-DR-GUIDE-how-to-use-bob-and-iam-department-for-swe.md`

### Reference Implementation
- **Source:** bobs-brain repository
- **Location:** `https://github.com/jeremylongshore/bobs-brain`
- **Agents:** `agents/bob`, `agents/iam-*`
- **Tests:** `tests/test_swe_pipeline.py`

### Troubleshooting
1. Check bobs-brain reference implementation
2. Review agent system prompts
3. Verify repos.yaml configuration
4. Run ARV checks for diagnostic info
5. Check logs for detailed error messages

---

## XI. Success Criteria

Your port is successful when:

1. **ARV checks pass:**
   ```bash
   make arv-gates
   # ✅ All ARV gates passed
   ```

2. **Pipeline runs successfully:**
   ```bash
   make test-swe-pipeline
   # ✅ All tests passed
   ```

3. **Real analysis produces sensible results:**
   - Issues found are relevant
   - Issue specs are well-formed
   - QA verdicts are accurate

4. **CI integration works:**
   - GitHub Actions/CI passes
   - ARV checks block bad commits

5. **Team can use it:**
   - Slack commands work (if enabled)
   - CLI tool is intuitive
   - Results are actionable

---

**Document Status:** Canonical Guide
**Template Version:** 1.0.0
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
**Last Updated:** 2025-11-20

**Related Docs:**
- 000-DR-STND-iam-department-template-scope-and-rules-DR-STND-iam-department-template-scope-and-rules.md (scope)
- 000-DR-STND-iam-department-integration-checklist-DR-STND-iam-department-integration-checklist.md (checklist)
- templates/iam-department/README.md (template README)
- **118-DR-STND-cicd-pipeline-for-iam-department.md** (CI/CD pipeline standard - CICD-DEPT)
- **119-RB-OPS-deployment-operator-runbook.md** (deployment operations - CICD-DEPT)
