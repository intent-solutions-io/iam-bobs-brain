# IAM Department Integration Checklist

**Document ID:** 000-DR-STND-iam-department-integration-checklist-DR-STND
**Title:** IAM Department Cross-Repo Integration Checklist
**Phase:** T2 (Porting & Integration)
**Status:** Standard Checklist
**Created:** 2025-11-20
**Purpose:** Concise checklist for teams porting the IAM department template to ensure nothing is missed.

---

## Quick Reference

Use this checklist alongside the porting guide (`000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md`) to track your integration progress.

**Estimated Time:** 1-2 days minimal, 1 week full integration

---

## PRE-FLIGHT (Before You Start)

### Target Repository Ready
- [ ] Python 3.11+ installed and configured
- [ ] Git repository initialized
- [ ] Virtual environment setup (venv/poetry)
- [ ] Test framework available (pytest recommended)
- [ ] CI/CD pipeline exists (GitHub Actions, etc.)
- [ ] Documentation folder exists or can be created

### Access & Permissions
- [ ] GitHub repository access (read/write)
- [ ] (Optional) GCP project access
- [ ] (Optional) Slack workspace admin
- [ ] (Optional) Vertex AI Agent Engine access

---

## CORE SETUP (Required for All Ports)

### 1. Template Copy
- [ ] Copied `templates/iam-department/` to target repo
- [ ] Directory structure matches template layout
- [ ] All `.template` files present

### 2. Parameter Replacement
- [ ] Defined product name (lowercase, no spaces)
- [ ] Defined product display name
- [ ] Defined GCP project ID
- [ ] Defined GCP location/region
- [ ] Defined GitHub repo owner/name
- [ ] Defined agent names (orchestrator, foreman)
- [ ] Ran global search/replace on all parameters
- [ ] Removed `.template` extensions from all files

### 3. Repository Configuration
- [ ] Edited `agents/config/repos.yaml`
- [ ] Added primary repository entry
- [ ] Configured repository metadata (language, frameworks)
- [ ] Defined key directories
- [ ] Added any additional repositories (if applicable)

### 4. Agent Customization
- [ ] Reviewed all agent system prompts
- [ ] Customized prompts for product domain
- [ ] Added product-specific context to prompts
- [ ] Verified agent responsibilities match product needs

### 5. Local Testing
- [ ] Created synthetic test repo (optional but recommended)
- [ ] Set PYTHONPATH correctly
- [ ] Ran `pytest tests/test_swe_pipeline.py -v`
- [ ] Tests passed successfully
- [ ] CLI demo script works (`run_swe_pipeline_once.py`)

### 6. ARV Checks
- [ ] Added ARV check scripts to `scripts/`
- [ ] Added Makefile targets (or equivalent)
- [ ] Ran `make check-arv-minimum`
- [ ] ARV checks passed
- [ ] Fixed any agent structure issues

### 7. CI Integration
- [ ] Added ARV check job to CI workflow
- [ ] Added SWE pipeline test job to CI
- [ ] Pushed to CI and verified success
- [ ] CI blocks on ARV failures

---

## AGENTS & TOOLS (Required Specialists)

### Minimal Viable Department
- [ ] iam-foreman (orchestrator) configured
- [ ] iam-adk (design/audit) configured
- [ ] iam-issue (issue specs) configured
- [ ] iam-qa (quality checks) configured

### Optional (Add as Needed)
- [ ] Top-level orchestrator (bob/productbot) configured
- [ ] iam-fix-plan (fix design) configured
- [ ] iam-fix-impl (fix implementation) configured
- [ ] iam-doc (documentation) configured
- [ ] iam-cleanup (code cleanup) configured
- [ ] iam-index (knowledge indexing) configured

### Product-Specific Tools
- [ ] Identified product-specific tool needs
- [ ] Created tool implementations in `agents/tools/`
- [ ] Registered tools with agent profiles
- [ ] Tested tools independently

---

## SHARED CONTRACTS

- [ ] `PipelineRequest` / `PipelineResult` imported
- [ ] `IssueSpec` contract available
- [ ] `FixPlan` contract available (if using fix agents)
- [ ] `QAVerdict` contract available
- [ ] (Optional) Added product-specific contract fields

---

## A2A LAYER

- [ ] `A2AAgentCall` / `A2AAgentResult` contracts present
- [ ] A2A adapter (`agents/a2a/adapter.py`) configured
- [ ] `call_agent_local` function working
- [ ] (Optional) `call_agent_engine` configured for Agent Engine
- [ ] Correlation IDs propagated through pipeline

---

## CONFIGURATION MODULES

### Core Config
- [ ] `repos.yaml` configured (see #3 above)
- [ ] Environment detection working (`dev`/`staging`/`prod`)

### RAG Config (Optional)
- [ ] `rag_config.py` configured (if using RAG)
- [ ] `VERTEX_SEARCH_DATASTORE_ID` set
- [ ] `KNOWLEDGE_HUB_BUCKET` set
- [ ] `KNOWLEDGE_HUB_PREFIX` set
- [ ] Ran `make check-rag-readiness`
- [ ] RAG checks passed

### Agent Engine Config (Optional)
- [ ] `agent_engine_config.py` configured (if using Agent Engine)
- [ ] Reasoning engine IDs defined per environment
- [ ] SPIFFE IDs configured
- [ ] Ran `make print-agent-engine-config`
- [ ] Config validated

### Feature Flags (Optional)
- [ ] `features.py` configured (if using feature flags)
- [ ] All flags default to False
- [ ] Flag names match product needs
- [ ] Ran `make check-arv-engine-flags`
- [ ] Flag checks passed

---

## SERVICE GATEWAYS (Optional)

### A2A Gateway
- [ ] `service/a2a_gateway/main.py` configured
- [ ] AgentCard endpoint (`/.well-known/agent.json`) works
- [ ] `/query` endpoint works
- [ ] `/a2a/run` endpoint works (if using A2A protocol)
- [ ] Deployed to Cloud Run (optional)
- [ ] Health check endpoint working

### Slack Webhook
- [ ] `service/slack_webhook/main.py` configured
- [ ] Slack bot created (slack.api/apps)
- [ ] `SLACK_BOT_TOKEN` configured
- [ ] `SLACK_SIGNING_SECRET` configured
- [ ] Bot user ID configured
- [ ] Event subscriptions configured
- [ ] Deployed to Cloud Run (optional)
- [ ] Slack commands trigger pipeline

---

## SCRIPTS & UTILITIES

### ARV Checks
- [ ] `check_rag_readiness.py` present and working
- [ ] `check_arv_minimum.py` present and working
- [ ] `check_arv_engine_flags.py` present (if using flags)
- [ ] All checks pass locally

### Pipeline Runners
- [ ] `run_swe_pipeline_once.py` present
- [ ] CLI demo works with synthetic repo
- [ ] Can run on real codebase
- [ ] Results are sensible

### Config Printers
- [ ] `print_rag_config.py` present (if using RAG)
- [ ] `print_agent_engine_config.py` present (if using Engine)
- [ ] Config validation works

---

## TESTING & VALIDATION

### Unit Tests
- [ ] `tests/test_swe_pipeline.py` present
- [ ] Tests pass with synthetic repo
- [ ] Tests cover main pipeline flow
- [ ] (Optional) Added product-specific tests

### Integration Tests
- [ ] Pipeline runs on real codebase
- [ ] Issues found are relevant
- [ ] Issue specs are well-formed
- [ ] QA verdicts are accurate
- [ ] No false positives/negatives

### Smoke Tests
- [ ] Pipeline completes without errors
- [ ] All agents respond
- [ ] Contracts are honored
- [ ] Correlation IDs work
- [ ] Logging is comprehensive

---

## CI/CD INTEGRATION

### GitHub Actions (or equivalent)
- [ ] ARV check job added to workflow
- [ ] ARV checks block on failure
- [ ] SWE pipeline test job added
- [ ] Tests run on every push/PR
- [ ] CI status badge in README (optional)

### Build Pipeline
- [ ] Dependencies installed in CI
- [ ] Python version matches local (3.11+)
- [ ] Tests run in CI environment
- [ ] CI completes in < 10 minutes

---

## DOCUMENTATION

### Required Docs
- [ ] Updated README with IAM department overview
- [ ] Added setup/installation instructions
- [ ] Documented available agents and their roles
- [ ] Documented how to run pipeline (CLI + Slack)
- [ ] Added troubleshooting section

### Optional Docs
- [ ] Product-specific agent guide
- [ ] Architecture diagram showing agents
- [ ] Example workflows/use cases
- [ ] Video demo or screenshots

---

## OBSERVABILITY & MONITORING

### Logging
- [ ] Correlation IDs in all log messages
- [ ] Structured logging format (JSON recommended)
- [ ] Log levels appropriate (INFO/DEBUG/ERROR)
- [ ] Logs include agent names and steps
- [ ] Can trace pipeline runs end-to-end

### Error Handling
- [ ] Pipeline failures are caught gracefully
- [ ] Errors are logged with context
- [ ] Users receive actionable error messages
- [ ] Retry logic where appropriate

### (Optional) Monitoring
- [ ] Cloud Logging/Monitoring configured
- [ ] Alerts for pipeline failures
- [ ] Dashboards for pipeline metrics
- [ ] Performance tracking

---

## SECURITY & COMPLIANCE

### Secrets Management
- [ ] No secrets in code/config
- [ ] Secrets loaded from environment variables
- [ ] (GCP) Secrets stored in Secret Manager
- [ ] (CI) Secrets configured in CI system

### Access Control
- [ ] GitHub tokens have minimal required permissions
- [ ] Service accounts have minimal IAM roles
- [ ] Bot tokens are restricted to necessary scopes

### Code Quality
- [ ] ARV checks enforce structure
- [ ] Linting configured (black, ruff, etc.)
- [ ] Type hints used where appropriate
- [ ] Security scanning in CI (optional)

---

## OPTIONAL FEATURES

### RAG Integration
- [ ] Vertex AI Search datastore created
- [ ] Knowledge sources indexed
- [ ] RAG config validated
- [ ] Agents query RAG successfully
- [ ] Results improve with RAG enabled

### Slack Integration
- [ ] Slack app created and configured
- [ ] Bot invited to channels
- [ ] Commands tested in Slack
- [ ] Pipeline triggered from Slack
- [ ] Results posted back to Slack

### Agent Engine Deployment
- [ ] Agents deployed to Agent Engine
- [ ] Reasoning engine IDs configured
- [ ] Agent Engine REST API tested
- [ ] Gateways proxy to Engine
- [ ] Feature flags control routing

### GitHub Issue Creation
- [ ] GitHub token has repo write access
- [ ] Issue creation tested in dry-run mode
- [ ] Issue templates configured (optional)
- [ ] Labels/assignees configured
- [ ] Issue creation tested in create mode

---

## POST-PORT VALIDATION

### Smoke Test Checklist
- [ ] Run `make arv-gates` → All pass
- [ ] Run `make test-swe-pipeline` → All pass
- [ ] Run CLI demo → Produces results
- [ ] Run on real codebase → Finds issues
- [ ] Push to GitHub → CI passes

### Quality Checklist
- [ ] Issues found are relevant to product
- [ ] Issue descriptions are clear and actionable
- [ ] QA verdicts are accurate
- [ ] No excessive false positives
- [ ] Performance is acceptable (< 5min for typical audit)

### Team Readiness
- [ ] Team trained on how to use IAM department
- [ ] Documentation reviewed and approved
- [ ] Workflow integrated with team processes
- [ ] Feedback loop established

---

## MAINTENANCE & UPDATES

### Ongoing Tasks
- [ ] Monitor for template updates from bobs-brain
- [ ] Sync agent improvements from reference implementation
- [ ] Update system prompts as product evolves
- [ ] Add new agents as needs arise
- [ ] Review and update tests regularly

### Template Version Tracking
- [ ] Document which template version was ported
- [ ] Track local customizations
- [ ] Plan for template upgrades
- [ ] Document breaking changes

---

## TROUBLESHOOTING REFERENCE

### If ARV Checks Fail
1. Check agent directory structure (agent.py present?)
2. Verify system prompts exist
3. Check shared_contracts imports
4. Review error messages in detail
5. Compare to bobs-brain reference implementation

### If Tests Fail
1. Verify PYTHONPATH is set correctly
2. Check synthetic repo exists
3. Review repos.yaml configuration
4. Check agent system prompts
5. Run with `-vvs` for detailed output

### If Pipeline Produces No Results
1. Verify repos.yaml is configured
2. Check repo_hint matches configured repo
3. Verify agents are responding (check logs)
4. Try with `--mode preview` first
5. Check tool implementations

### If CI Fails
1. Review CI logs for specific errors
2. Verify dependencies installed correctly
3. Check Python version matches local
4. Verify ARV checks run before tests
5. Check secrets/env vars configured

---

## SUCCESS CRITERIA

Your integration is complete when:

✅ **All checklist items above are checked**
✅ **ARV checks pass:** `make arv-gates`
✅ **Tests pass:** `make test-swe-pipeline`
✅ **CI passes:** GitHub Actions/CI green
✅ **Pipeline produces useful results on real code**
✅ **Team can use it:** Documentation clear, workflow integrated

---

## NEXT STEPS

After completing this checklist:

1. **Stabilize** (Week 1)
   - Run pipeline on multiple modules
   - Fine-tune agent prompts
   - Add product-specific tools

2. **Integrate** (Week 2)
   - Enable optional features (RAG, Slack, etc.)
   - Train team on usage
   - Establish workflows

3. **Scale** (Week 3+)
   - Add more agents as needed
   - Deploy to Agent Engine (optional)
   - Integrate with other systems

---

**Document Status:** Standard Checklist
**Template Version:** 1.0.0
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
**Last Updated:** 2025-11-20

**Related Docs:**
- 000-DR-STND-iam-department-template-scope-and-rules-DR-STND-iam-department-template-scope-and-rules.md (scope)
- 000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md (detailed guide)
- templates/iam-department/README.md (template README)
