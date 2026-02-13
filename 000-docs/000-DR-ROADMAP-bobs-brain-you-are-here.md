# Bob's Brain – You Are Here

**Doc Type:** Roadmap / Orientation
**Scope:** `bobs-brain` repo (Bob + ADK/IAM department)
**Audience:** Future Jeremy, collaborators, and new engineers

---

## 1. Purpose of This Repo

This repo is the **reference implementation** of how Intent Solutions builds:

- A primary orchestrator agent (**Bob**)
- A specialist ADK/Vertex team (**IAM department**)
- A clean set of standards (6767 docs, ARV, Hard Mode rules)
- A deployment path to **Vertex AI Agent Engine** with Cloud Run gateways

Later, this structure will become the first "single-team starter template" for:

- `intent-agent-model-jvp-base`
- And any future "department repos" (DiagnosticPro, PipelinePilot, etc.)

---

## 2. Current Architecture (High Level)

**Agents:**

- `bob` – global orchestrator (user-facing)
- `iam-senior-adk-devops-lead` – foreman for ADK/Vertex work
- `iam-*` specialists:
  - `iam-adk` (ADK compliance / patterns)
  - `iam-issue` (GitHub issue specs + creation)
  - `iam-fix-plan` (solution design)
  - `iam-fix-impl` (implementation)
  - `iam-qa` (testing / validation)
  - `iam-doc` (docs & runbooks)
  - `iam-cleanup` (tech debt & refactors)
  - `iam-index` (knowledge indexing & org storage)

**Key supporting pieces:**

- `agents/config/*` – feature flags, org storage, Agent Engine IDs, etc.
- `service/*` – Cloud Run services (Slack webhook, a2a gateway)
- `infra/terraform` – infra definition (to be expanded to manage Agent Engine)
- `scripts/*` – checks, portfolio audits, smoke tests
- `000-docs/` – all documentation
  - 6767-prefixed = **canonical cross-repo standards**
  - Normal numeric = repo-local guides, AARs, SITREPs

---

## 3. What's Done vs In Flight

### Done (High Confidence)

- Repo structure cleaned (agents/service/scripts/archive/000-docs)
- IAM department implemented (Bob + foreman + specialists)
- 6767 doc convention implemented and corrected
- Org-wide GCS storage pattern (LIVE1) designed and implemented
- Portfolio audit flows (multi-repo SWE audits) implemented
- Slack notifications plumbing (LIVE3A) implemented but **flagged OFF by default**
- ARV / Hard Mode design for:
  - ADK-only agents
  - Single docs root
  - No local runner in Cloud Run gateways
  - Config/feature flag safety
- **AE-DEV-WIREUP (✅ COMPLETE)**
  Wired Bob + IAM into Vertex AI Agent Engine via a2a gateway:
  - Centralized Agent Engine config module
  - a2a HTTP gateway (Cloud Run) with clean JSON contract
  - Dev-only smoke tests + comprehensive documentation

### In Flight / Planned

- **Slack "re-attach"**
  - Ensure Slack app points at the new Cloud Run webhook/gateway
  - End-to-end tests: Slack → gateway → Agent Engine → Bob → Slack

- **LIVE3B/C** – GitHub issue creation + full integration docs
  - iam-issue wired to create real GitHub issues (with DRY-RUN safety)
  - Live3 docs, operator runbook, and config sanity checks

- **Template Extraction**
  - Lift this IAM department into `intent-agent-model-jvp-base` as the canonical "one department / one team" starter kit

---

## 4. Where This Is Going

Near-term goals:

1. **Bob reachable in dev via Slack (and optionally Discord/Web UI)**
2. **IAM department able to audit other repos** using:
   - Repo cloning/inspection
   - Org GCS data
   - Vertex AI Search (RAG)
3. **One-click-ish pattern** to:
   - Spin up a new "department repo"
   - Port in the IAM team
   - Wire it to Agent Engine and org storage

Long-term:

- `bobs-brain` and `intent-agent-model-jvp-base` become the **standard pattern** for:
  - Vertex AI ADK agent teams
  - Multi-agent departments you can replicate across your entire portfolio

---

## 5. How to Read the 6767 Docs

- `6767-xxx-DR-STND-*`
  Cross-repo standards (naming, ARV rules, department design, etc.)

- `6767-xxx-DR-GUIDE-*`
  Cross-repo how-to guides (porting departments, using Bob + IAM, etc.)

- `6767-xxx-AA-REPT-*` / `6767-xxx-PM-*`
  Canonical AARs and postmortems that define how **all** future repos should behave.

If future you is ever lost, read:

1. This roadmap
2. The top-level `README.md`
3. `000-DR-STND-iam-department-template-scope-and-rules.md` (or equivalent)
4. The latest SITREP doc

---

## 6. Front Doors to Bob: Platform Strategy

### Primary: Slack (Work Context)

**Slack Free vs Pro:**
- **Free plan:** $0, 90-day message history, limited integrations
- **Pro plan:** ~$7.25-8.75/user/month, unlimited history, full integrations

**Recommendation:** Start on Slack Free
- Bob's memory lives in Vertex/GCS/logs, not Slack history
- 90-day limit is human convenience, not a blocker
- Upgrade to Pro only if you need:
  - Long-term searchable human chat history
  - More collaborators using Slack broadly
  - Heavy workflow/integration usage

**Pros:**
- Strong work context (threads, channels, permissions)
- Clean app model + good security
- Easy to lock down (less spam)
- Natural home for dev/ops assistant

**Cons:**
- Paid tiers add up per user
- Free plan history limit
- Heavier than simple chat options

### Secondary: Discord (Community/Lab Front Door)

**Cost:** Free with unlimited message history

**Pros:**
- Great for public/semi-public community
- Free with multiple channels
- Users already expect bots
- Good gateway & REST APIs

**Cons:**
- More "noisy" without moderation
- Less "work mode," more "community mode"
- Another thing to maintain

### Tertiary: Web Dashboard (Control Panel)

**What it is:** Small web UI talking to a2a gateway

**Shows:**
- Conversation with Bob
- Agent runs / audit status
- Links to relevant docs

**Pros:**
- Fully under your control
- Easy to add admin tools
- Good demo surface

**Cons:**
- Must build and maintain
- Doesn't replace chat for quick Q&A

### Skip for Now

**WhatsApp:**
- 2025 policy updates restrict general-purpose AI chatbots
- Per-message billing complexity
- Not worth the headache

**Telegram:**
- Good for "phone only" experience
- Skip unless you want broader public access
- Not as integrated with dev workflow

---

## 7. Consolidated TODO List

### A. Roadmap & Standards ✅ (DONE)
- ✅ Add "You Are Here" roadmap doc (this document)
- ✅ Ensure all 6767- docs are cross-repo standards
- [ ] Add "Spec vs Implementation" checklist doc mapping ADK/Agent Engine expectations

### B. Agent Engine & Gateways ✅ (DONE)
- ✅ AE-DEV-WIREUP complete
  - ✅ Central agents/config/agent_engine.py module
  - ✅ a2a gateway service implemented & tested
  - ✅ make agent-engine-dev-smoke command working
  - ✅ ARV check for dev smoke test

### C. Slack: Get Bob Actually Talking (NEXT)
- [ ] Audit current Slack app config
  - [ ] Verify Request URL points to Cloud Run webhook/gateway
  - [ ] Verify app installed in workspace & channel
  - [ ] Verify env vars in Slack webhook service:
    - SLACK_SIGNING_SECRET
    - SLACK_BOT_TOKEN
    - Channel IDs / config
- [ ] Implement integration test:
  - [ ] Take fake Slack event payload
  - [ ] Send to Slack webhook endpoint
  - [ ] Ensure reaches Agent Engine & returns Bob reply
- [ ] Manual test: @Bob in dev Slack channel

### D. LIVE3 Completion (Notifications & Issues)
- [ ] LIVE3B – GitHub issues:
  - [ ] Implement DRY-RUN mode for GitHub issue creation
  - [ ] Wire iam-issue into portfolio audits
  - [ ] Add tests & config flags
- [ ] LIVE3C – Integration/docs:
  - [ ] Write LIVE3 architecture doc
  - [ ] Add operator runbook (safe enable Slack/GitHub)
  - [ ] Add config sanity-check script (make validate-config)

### E. Frontend Expansion
- [ ] Decide Slack plan:
  - [ ] Start on Slack Free
  - [ ] Revisit Pro if need unlimited history
- [ ] Decide on second front door:
  - [ ] If community-facing: Discord server + bot
  - [ ] If internal only: Web dashboard
- [ ] Design minimal dashboard:
  - [ ] List recent runs/audits
  - [ ] Trigger audits & view results
  - [ ] Simple chat panel with Bob (optional)

### F. Template (JVP Base)
- [ ] Once Bob + IAM + LIVE3 + AE-DEV stable:
  - [ ] Copy cleaned department to intent-agent-model-jvp-base
  - [ ] Strip bobs-brain-specific wording
  - [ ] Add "How to instantiate new department" doc
  - [ ] Tag as official Intent Solutions agent template

---

## 8. Next Immediate Steps

**Priority 1: Slack End-to-End**
1. Fix Slack → Bob connection
2. Prove you can @Bob and get responses
3. Document the working flow

**Priority 2: LIVE3 Polish**
1. Finish GitHub issue creation
2. Write operator runbook
3. Make it production-safe

**Priority 3: Template Extraction**
1. Clean up for reusability
2. Extract to JVP base
3. Document instantiation process

---

## 9. Development Phases (Suggested)

### Phase 1: Agent Engine Dev Wiring ✅ (COMPLETE)
- Central config for Agent Engine IDs
- a2a gateway service in Cloud Run
- Dev smoke script validation

### Phase 2: Slack → Bob End-to-End (CURRENT)
- Fix Slack app configuration
- Wire to current Cloud Run URL
- Integration test: Slack event → webhook → gateway → Agent Engine → response
- Manual test: @Bob responds in Slack

### Phase 3: LIVE3B/C – Make IAM Department Operational
- GitHub issue creation with DRY-RUN
- Portfolio sweeps → Slack notification → optional GitHub issue
- Operator/runbook docs for toggle features

### Phase 4: Template Extraction & JVP Base
- Copy cleaned structure to intent-agent-model-jvp-base
- Strip repo-specific bits
- "First department starter kit"

### Phase 5: Multi-Frontends
- Add second frontend (Discord or web dashboard)
- Same a2a gateway contract
- Multiple front doors, one brain

---

## 10. Key Files by Purpose

### Configuration
- `agents/config/agent_engine.py` - Agent Engine IDs, paths, URLs
- `agents/config/features.py` - Feature flags (LIVE1-3, RAG, etc.)
- `agents/config/inventory.py` - All environment variables
- `agents/config/notifications.py` - Slack config
- `agents/config/github_features.py` - GitHub config

### Services (Cloud Run)
- `service/a2a_gateway/main.py` - A2A protocol gateway
- `service/a2a_gateway/agent_engine_client.py` - Agent Engine client
- `service/slack_webhook/` - Slack event handler

### Scripts & Tools
- `scripts/run_agent_engine_dev_smoke.py` - Dev smoke test
- `scripts/check_config_all.py` - Config validation
- `scripts/run_arv_department.py` - ARV checks
- `Makefile` - Common commands

### Documentation
- `000-docs/6770-DR-ROADMAP-bobs-brain-you-are-here.md` - This roadmap
- `000-docs/6768-DR-GUIDE-agent-engine-dev-wiring-and-smoke-test.md` - AE-DEV guide
- `000-docs/6769-LS-SITR-ae-dev-wireup-complete.md` - AE-DEV SITREP
- `000-docs/6767-*` - Cross-repo standards

---

_Last Updated: 2025-11-20_
_Status: AE-DEV-WIREUP complete, Slack integration next_
_Next: Get Bob talking via Slack end-to-end_
