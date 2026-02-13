# 170-PP-PLAN: CTO Roadmap – Canonical IAM Department Template

**Document Type:** Strategic Planning (PP-PLAN)
**Phase:** Post-Consolidation → Production-Ready Template
**Created:** 2025-11-29
**Status:** Active Roadmap
**Author:** Build Captain (CTO-level analysis)

---

## Executive Summary

**Mission:** Transform `bobs-brain` from a prototype ADK agent department into the **canonical IAM (Intent Agent Management) department template** that can be replicated across product repositories.

**Current State (v0.10.0):**
- ✅ 11 agents with A2A v0.3.0 compliance
- ✅ CI/CD hardened with drift detection (R8)
- ✅ Service accounts cleaned (8→5)
- ✅ Infrastructure ready (Terraform + Agent Engine)
- ❌ NOT deployed to Agent Engine yet
- ❌ Slack gateway NOT hardened (manual deploy risk)
- ❌ NO observability (logging, metrics, alerts)
- ❌ NOT reusable as template

**Target State ("I Can Sleep and Delegate"):**
- ✅ Bob conversational via Slack (Gemini-powered LLM experience)
- ✅ Bob can orchestrate IAM agents for testing/fixes
- ✅ System deployed to Agent Engine (dev → prod)
- ✅ Observable and recoverable (dashboards, alerts, runbooks)
- ✅ Template-ready (any team can clone and adapt)
- ✅ Zero orphaned accounts or manual deploys

**Success Bar:**
> "I can sleep and delegate" - The system works with minimal ADK/Vertex expertise, is observable, recoverable, and repeatable for new departments.

---

## Strategic Vision

### What Bob Is

**Bob is a conversational LLM-powered agent orchestrator:**

1. **User-facing Personality** (via Slack)
   - Uses Gemini to respond like any LLM (Claude/GPT/Gemini chat experience)
   - Maintains conversational context within sessions
   - Delegates complex work to specialized IAM agents

2. **IAM Department Foreman**
   - Routes ADK compliance → `iam-adk`
   - Routes issues → `iam-issue`
   - Routes fixes → `iam-fix-plan` → `iam-fix-impl`
   - Routes validation → `iam-qa`
   - Routes docs → `iam-docs`

3. **A2A Orchestrator**
   - Calls agents via Agent-to-Agent protocol (AgentCards + A2A v0.3.0)
   - Maintains audit trail (SPIFFE ID propagation, structured logs)
   - Enforces quality gates (ARV, drift detection)

### What Canonical Template Means

**bobs-brain becomes reusable infrastructure for ANY agent department:**

```
bobs-brain/                          # Canonical template
├── agents/                          # Generic structure
│   ├── bob/                         # Orchestrator (reusable)
│   ├── iam_senior_adk_devops_lead/  # Foreman (reusable)
│   └── iam_*/                       # Specialists (IAM-specific)
│
├── infra/terraform/                 # Reusable modules
│   ├── modules/agent_engine/        # Generic Agent Engine setup
│   └── envs/dev/                    # Environment configs
│
├── service/                         # Reusable gateway pattern
│   ├── slack_gateway/               # Terraform-only deploys
│   └── a2a_gateway/                 # A2A HTTP endpoints
│
├── .github/workflows/               # Reusable CI/CD
│   ├── ci.yml                       # Quality gates (ARV, drift, tests)
│   └── deploy-*.yml                 # Environment deploys
│
└── 000-docs/6767-*.md               # SOPs for replication
```

**Other teams can:**
- Clone `bobs-brain`
- Replace `iam_*` agents with domain-specific specialists (e.g., `finance_*`, `ops_*`)
- Keep: bob orchestrator, CI/CD, Terraform modules, gateway patterns
- Customize: agent prompts, tools, domain logic

---

## Phased Roadmap

### Phase 25: Slack Bob Hardening (Lock Gateway Pattern)

**Goal:** Kill all legacy deploy paths and harden Slack gateway to Terraform+CI only.

**Scope:**
1. **Remove Manual Deploy Paths**
   - Delete `deploy.sh` scripts (if any exist)
   - Remove `gcloud run deploy` examples from docs
   - Audit `000-docs/` for manual deploy references

2. **Strengthen CI Guardrails**
   - Add `deploy-slack-gateway-dev.yml` workflow (Terraform-only)
   - Add `deploy-slack-gateway-prod.yml` workflow (manual approval gate)
   - Enforce WIF-only authentication (no service account keys)

3. **Documentation Updates**
   - Update `126-AA-AUDT-appaudit-devops-playbook.md` (remove manual steps)
   - Add `6767-122-DR-STND-slack-gateway-deploy-pattern.md` (Terraform+CI canonical pattern)
   - Update README.md (remove quickstart deploy shortcuts)

4. **ARV Integration**
   - Add `make check-slack-gateway-config` (validates Terraform vars)
   - Integrate Slack gateway validation into `ci.yml`

**Deliverables:**
- ✅ No manual deploy paths exist
- ✅ CI workflow for Slack gateway (dev + prod)
- ✅ Documentation reflects Terraform-first pattern
- ✅ ARV checks Slack gateway config

**Duration:** 1-2 days
**Branch:** `feature/phase-25-slack-hardening`
**AAR:** `171-AA-REPT-phase-25-slack-hardening.md`

---

### Phase 26: Agent Engine Dev Deployment (Bob Goes Live)

**Goal:** Deploy bob + foreman to dev Agent Engine, smoke test, integrate with dev Slack.

**Scope:**

#### 26.1: Agent Engine Deployment
1. **Deploy to Dev Agent Engine**
   - Use `scripts/deploy_inline_source.py` for bob + iam-senior-adk-devops-lead
   - Configure Memory Bank (optional: custom topics or defaults)
   - Verify SPIFFE ID propagation in logs

2. **Smoke Tests**
   - Run `make smoke-bob-agent-engine-dev` (health check)
   - Test A2A call from bob → iam-foreman
   - Verify session persistence (short-term memory)
   - Test Memory Bank (if configured)

3. **Dev Slack Integration**
   - Point dev Slack workspace to Agent Engine endpoint (not Cloud Run)
   - Test conversational flow (user → Slack → Agent Engine → bob → Gemini response)
   - Test IAM delegation (user asks for fix → bob → iam-foreman → iam-fix)

#### 26.2: Memory Bank Configuration (Decision Point)
**Option A: Use Defaults (Fast Path)**
- Deploy without custom `context_spec.memory_bank_config`
- Memory Bank works but uses generic topics
- Pro: Faster to production
- Con: Not optimized for IAM domain

**Option B: Configure Custom Memory (Optimal Path)**
- Add `context_spec.memory_bank_config` to `deploy_inline_source.py`
- Define custom topics: `iam_compliance_history`, `iam_agent_capabilities`, `user_preferences`
- Add few-shot examples for memory extraction
- Pro: Better memory relevance for IAM work
- Con: Requires 1-2 extra days for tuning

**Recommendation:** Start with Option A (defaults), iterate to Option B in Phase 27 if needed.

#### 26.3: Dev Environment Validation
- ✅ Bob responds conversationally via dev Slack
- ✅ Bob delegates to IAM agents (smoke test one A2A call)
- ✅ Logs show SPIFFE ID propagation
- ✅ No errors in Agent Engine logs

**Deliverables:**
- ✅ bob + iam-foreman deployed to dev Agent Engine
- ✅ Dev Slack → Agent Engine integration working
- ✅ Smoke tests passing
- ✅ Logs observable in Cloud Logging

**Duration:** 2-3 days
**Branch:** `feature/phase-26-agent-engine-dev`
**AAR:** `172-AA-REPT-phase-26-agent-engine-dev-deployment.md`

---

### Phase 27: Observability & ARV Hard Gate (Production Readiness)

**Goal:** Make bobs-brain observable, monitored, and enforce ARV as a hard gate for production deploys.

**Scope:**

#### 27.1: Cloud Monitoring Setup
1. **Dashboards**
   - Agent Engine API calls (latency, errors, throughput)
   - Slack gateway metrics (request volume, 4xx/5xx errors)
   - A2A call success rates (bob → foreman → specialists)
   - Memory Bank usage (if configured)

2. **Alerts**
   - Agent Engine 5xx errors > 5% over 5 minutes
   - Slack gateway downtime > 1 minute
   - A2A call failures > 10% over 10 minutes
   - Service account permission errors

3. **Structured Logs**
   - Enforce JSON logs in all agents (`logger.info({"event": "...", "spiffe_id": "..."})`)
   - Add trace IDs for A2A call chains
   - Log ARV validation results

#### 27.2: ARV Hard Gate Integration
1. **CI Enforcement**
   - Make `arv-department` job BLOCK deploys if it fails (currently informational)
   - Add `arv-agent-engine-readiness` job (checks Agent Engine config)
   - Require ARV pass for `deploy-dev.yml` and `deploy-prod.yml`

2. **ARV Checks**
   - All agents have valid AgentCards (schema + 6767 compliance)
   - All agents have tests passing
   - Drift detection clean
   - Terraform validate passes
   - Documentation complete (no [TBD] placeholders)

3. **Golden Path Evals (Minimal Set)**
   - Eval 1: Bob responds to "hello" (conversation works)
   - Eval 2: Bob delegates to iam-foreman (A2A works)
   - Eval 3: Bob+foreman completes simple fix (end-to-end pipeline)

#### 27.3: Runbooks
- Create `000-docs/6767-123-DR-RUNB-incident-response-playbook.md`
  - What to do if Agent Engine is down
  - What to do if Slack gateway is down
  - What to do if A2A calls fail
  - How to rollback a bad deployment

**Deliverables:**
- ✅ Cloud Monitoring dashboards for all components
- ✅ Alerts configured with notification channels
- ✅ ARV hard gate in CI (blocks bad deploys)
- ✅ Minimal golden path evals passing
- ✅ Incident response runbook

**Duration:** 3-4 days
**Branch:** `feature/phase-27-observability-arv`
**AAR:** `173-AA-REPT-phase-27-observability-and-arv.md`

---

### Phase 28: Prod Deployment (First Production Users)

**Goal:** Deploy to production Agent Engine and production Slack workspace.

**Scope:**

1. **Production Deployment**
   - Deploy bob + iam-foreman to prod Agent Engine (using `deploy-prod.yml` workflow)
   - Point production Slack workspace to prod Agent Engine endpoint
   - Verify ARV hard gate passes (blocking gate)

2. **Production Smoke Tests**
   - Run `make smoke-bob-agent-engine-prod` (health check)
   - Test conversational flow in prod Slack
   - Test A2A delegation (bob → iam-foreman)
   - Monitor dashboards for 24 hours

3. **Production Validation**
   - ✅ No errors in first 100 messages
   - ✅ A2A success rate > 95%
   - ✅ Latency < 5s for conversational responses
   - ✅ Latency < 30s for IAM delegations

4. **Production Runbook Test**
   - Simulate Agent Engine failure (kill agent, verify recovery)
   - Simulate Slack gateway failure (redeploy via CI)
   - Verify alerts fire correctly

**Deliverables:**
- ✅ bob + iam-foreman in production Agent Engine
- ✅ Production Slack workspace connected
- ✅ First 100 production messages successful
- ✅ Dashboards and alerts validated under load

**Duration:** 2-3 days
**Branch:** `feature/phase-28-prod-deployment`
**AAR:** `174-AA-REPT-phase-28-prod-deployment.md`

---

### Phase 29: Template Extraction & Canonization

**Goal:** Extract reusable patterns into canonical template that other teams can clone.

**Scope:**

#### 29.1: Canonize 6767 Standards
1. **Review All 6767-series Docs**
   - Ensure all hard mode rules (R1-R8) are documented
   - Ensure all deployment patterns (inline source, Terraform-first, WIF-only) are SOPs
   - Remove bobs-brain-specific examples, replace with `{{PLACEHOLDERS}}`

2. **Create Template-Ready Versions**
   - `6767-200-DR-TMPL-agent-department-quickstart.md` (how to clone bobs-brain for new department)
   - `6767-201-DR-TMPL-agent-skeleton.md` (how to create new specialist agent)
   - `6767-202-DR-TMPL-ci-cd-setup.md` (how to configure CI/CD for new repo)

#### 29.2: JVP Alignment (If Applicable)
- If JVP (Jumpstart Vertical Program) or base template exists:
  - Align bobs-brain structure with JVP patterns
  - Submit bobs-brain as canonical IAM department reference
  - Document divergences (if any) with justification

#### 29.3: Onboarding Documentation
- Create `000-docs/6767-203-DR-ONBD-new-team-onboarding.md`
  - Step-by-step guide for new team cloning bobs-brain
  - Prerequisites (GCP project, Terraform, GitHub Actions)
  - Customization checklist (rename agents, update prompts, configure domain logic)
  - First deployment walkthrough

#### 29.4: Template Testing
- **Test 1:** Clone bobs-brain to new repo `example-finance-brain`
- **Test 2:** Replace `iam_*` agents with `finance_*` agents (mock implementation)
- **Test 3:** Deploy to dev Agent Engine (verify template works end-to-end)
- **Test 4:** Document gaps found during cloning (improve template)

**Deliverables:**
- ✅ All 6767-series docs reviewed and template-ready
- ✅ Template quickstart guide (`6767-200`)
- ✅ Onboarding documentation (`6767-203`)
- ✅ Template validated via clone test (example-finance-brain)

**Duration:** 4-5 days
**Branch:** `feature/phase-29-template-extraction`
**AAR:** `175-AA-REPT-phase-29-template-canonization.md`

---

### Phase 30+: Continuous Improvement

**Ongoing Work:**
- **Memory Bank Optimization** (if using defaults initially)
  - Add custom topics for IAM domain
  - Add few-shot examples for better memory extraction
  - Tune TTL and embedding models

- **IAM Agent Expansion**
  - Add `iam-security` (security scanning specialist)
  - Add `iam-performance` (performance optimization specialist)
  - Add `iam-cost` (cost optimization specialist)

- **Multi-Repo Adoption**
  - Deploy template to 3+ product repos
  - Gather feedback from other teams
  - Iterate on template based on real-world usage

- **Advanced A2A Patterns**
  - Implement parallel A2A calls (bob → multiple specialists simultaneously)
  - Add A2A circuit breakers (fail fast if agent unreachable)
  - Add A2A retry logic (exponential backoff)

---

## Success Metrics

### "I Can Sleep and Delegate" Bar

**Operational Excellence:**
- ✅ System runs for 7 days with zero manual intervention
- ✅ No orphaned service accounts or manual deploys
- ✅ All deploys via CI/CD (Terraform+GitHub Actions)
- ✅ Dashboards show green for all components
- ✅ Alerts configured and tested (no silent failures)

**Recoverability:**
- ✅ Incident response runbook exists and tested
- ✅ Any component failure can be recovered in < 15 minutes
- ✅ Rollback procedure documented and tested

**Repeatability:**
- ✅ New team can clone bobs-brain and deploy in < 1 day
- ✅ Onboarding documentation complete (no tribal knowledge)
- ✅ Template validated via real clone test

**User Experience:**
- ✅ Bob responds conversationally like any LLM (via Slack)
- ✅ Bob delegates to IAM agents for complex work
- ✅ Latency < 5s for conversation, < 30s for IAM tasks
- ✅ Success rate > 95% for A2A calls

---

## Risk Mitigation

### Risk 1: Agent Engine Deployment Complexity
**Mitigation:**
- Start with dev environment (Phase 26)
- Extensive smoke tests before prod (Phase 28)
- Runbooks for common failures (Phase 27)

### Risk 2: Memory Bank Configuration Gaps
**Mitigation:**
- Use defaults initially (Phase 26)
- Iterate to custom config if needed (Phase 30+)
- Document Memory Bank usage patterns in AAR

### Risk 3: Template Adoption Friction
**Mitigation:**
- Validate template via real clone test (Phase 29)
- Gather feedback from first 3 adopter teams
- Iterate based on real-world usage

### Risk 4: Observability Gaps
**Mitigation:**
- Build dashboards and alerts BEFORE prod deploy (Phase 27)
- Test incident response procedures (Phase 28)
- Monitor for 7 days before declaring "done"

---

## Decision Points

### Decision 1: Memory Bank Configuration (Phase 26)
**Question:** Use defaults or configure custom topics?
**Options:**
- **A:** Use defaults (fast path, iterate later)
- **B:** Configure custom (optimal, takes 1-2 extra days)

**Recommendation:** Start with A, revisit in Phase 30+ if memory quality is poor.

### Decision 2: Prod Deploy Timeline (Phase 28)
**Question:** Deploy to prod after Phase 27 or wait longer?
**Criteria for GO:**
- ✅ Dev environment stable for 7+ days
- ✅ ARV hard gate passing
- ✅ Dashboards and alerts validated
- ✅ Runbook tested in dev

**Recommendation:** Don't rush prod. Wait for 7-day stability window.

### Decision 3: Template Scope (Phase 29)
**Question:** What's included in canonical template?
**Must Include:**
- bob orchestrator (reusable)
- Terraform modules (Agent Engine + gateways)
- CI/CD workflows (ARV + deploy)
- 6767-series SOPs

**Domain-Specific (NOT in template):**
- iam-* agents (these are IAM-specific, not generic)
- IAM-specific prompts and tools

**Recommendation:** Template is infrastructure + orchestration. Domain logic is replaceable.

---

## Appendix A: Phase Dependencies

```
Phase 25: Slack Hardening
    ↓
Phase 26: Agent Engine Dev Deploy
    ↓
Phase 27: Observability & ARV
    ↓
Phase 28: Prod Deploy
    ↓
Phase 29: Template Extraction
    ↓
Phase 30+: Continuous Improvement
```

**Critical Path:** Cannot deploy to prod (Phase 28) without observability (Phase 27).

---

## Appendix B: Effort Estimates

| Phase | Duration | Complexity | Blocking Risks |
|-------|----------|------------|----------------|
| 25: Slack Hardening | 1-2 days | Low | None (safe cleanup) |
| 26: Agent Engine Dev | 2-3 days | Medium | Agent Engine config gaps |
| 27: Observability | 3-4 days | High | Metrics integration complexity |
| 28: Prod Deploy | 2-3 days | Medium | Prod stability unknowns |
| 29: Template Extract | 4-5 days | Medium | Template validation takes time |
| **Total** | **12-17 days** | - | - |

**Assumptions:**
- One developer working full-time
- No major Agent Engine API changes during phases
- GCP access available for dev/prod deploys

---

## Appendix C: Key Documents

**This Roadmap:**
- `170-PP-PLAN-cto-roadmap-canonical-iam-template.md` (this document)

**Phase AARs (to be created):**
- `171-AA-REPT-phase-25-slack-hardening.md`
- `172-AA-REPT-phase-26-agent-engine-dev-deployment.md`
- `173-AA-REPT-phase-27-observability-and-arv.md`
- `174-AA-REPT-phase-28-prod-deployment.md`
- `175-AA-REPT-phase-29-template-canonization.md`

**SOPs (existing + to be created):**
- `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` (R1-R8)
- `000-DR-STND-adk-lazy-loading-app-pattern.md`
- `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
- `6767-122-DR-STND-slack-gateway-deploy-pattern.md` (to be created in Phase 25)
- `6767-123-DR-RUNB-incident-response-playbook.md` (to be created in Phase 27)
- `6767-200-DR-TMPL-agent-department-quickstart.md` (to be created in Phase 29)

---

## Document Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-29 | Initial roadmap created | Build Captain |

---

**Next Action:** Review this roadmap, approve phases 25-29, then execute Phase 25 (Slack Hardening).

**Question for User:** Start with Phase 25 immediately, or need adjustments to roadmap first?
