# Canonical Standards Catalog – Bob's Brain Global Index

**Document Type:** Index / Reference (DR-INDEX)
**Status:** Active
**Purpose:** Global index and status catalog for all canonical standards, guides, and reference docs in bobs-brain
**Last Updated:** 2026-02-13

---

## I. Purpose

This document serves as the **master catalog** for all canonical documentation in the Bob's Brain repository.

**Naming Convention (v4.3):** All canonical standards now use `000-CC-ABCD-description.md` format, same as project-specific docs. The former `6767-` prefix has been retired from filenames (see `000-docs/000-DR-STND-document-filing-system-standard-v4.md`). Conceptual shorthand like "6767-LAZY pattern" remains valid in code.

**Scope:**
- Canonical docs (`000-*`) are considered **reference** material
- These docs are intended to be **cross-repo reusable** where applicable
- These docs have **higher stability requirements** than NNN-* implementation docs

**When to Use 000-* vs NNN-*:**
- **000-*** - Standards, guides, runbooks, architecture that should be stable and reusable
- **NNN-*** - Phase-specific work, AARs, plans, status reports tied to specific milestones

---

## II. Quick Start

**New to bobs-brain? Start here:**
1. **000-DR-INDEX-bobs-brain-standards-catalog.md** (this doc) - Global catalog of all canonical standards
2. **000-DR-INDEX-agent-engine-a2a-inline-deploy.md** - Agent Engine / A2A / Inline Deployment sub-index (if working on deployment/A2A topics)
3. **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)
4. **000-RB-OPS-adk-department-operations-runbook.md** - Day-to-day operations

**For Operators:**
- Start with **000-RB-OPS-adk-department-operations-runbook.md** (operations runbook)
- Then review **000-DR-INDEX-agent-engine-a2a-inline-deploy.md** (Agent Engine sub-index)
- Then drill into specific guides (Slack dev, Agent Engine dev, etc.)

**For Developers:**
- Start with **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** (understand Hard Mode)
- Then review **000-DR-INDEX-agent-engine-a2a-inline-deploy.md** (architecture overview)
- Then drill into implementation guides (lazy-loading pattern, inline deployment, etc.)

---

## III. Complete Canonical Standards Catalog

### Core Standards (Infrastructure & Compliance)

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md | DR-STND | adk-agent-engine-spec-and-hardmode-rules.md | Canonical (Cross-Repo) | Defines ADK + Agent Engine compliance and Hard Mode rules (R1-R8) for IAM Department |
| 000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md | DR-STND | inline-source-deployment-for-vertex-agent-engine.md | Active | Canonical pattern for deploying ADK agents to Agent Engine via inline source (not pickle) |
| 000-DR-STND-adk-lazy-loading-app-pattern.md | DR-STND | adk-lazy-loading-app-pattern.md | Active | Lazy-loading App pattern for all ADK agents (module-level `app` variable) |
| 000-DR-STND-arv-minimum-gate.md | DR-STND | arv-minimum-gate.md | Active | Agent Readiness Verification (ARV) minimum gate standard for deployment safety |
| 000-DR-STND-github-issue-creation-guardrails.md | DR-STND | github-issue-creation-guardrails.md | Active | Safety guardrails for GitHub issue creation (write operations disabled by default) |
| 000-DR-STND-document-filing-system-standard-v4.md | DR-STND | document-filing-system-standard-v4.md | Canonical | Universal standard for organizing project documentation with category-based classification v4.3 |
| 000-DR-STND-adk-cloud-run-tools-pattern.md | DR-STND | adk-cloud-run-tools-pattern.md | Active | Define how "tools live in Cloud Run" while staying 100% compliant with google-adk 1.18+ |
| 000-DR-STND-slack-gateway-deploy-pattern.md | DR-STND | slack-gateway-deploy-pattern.md | Active | Deployment pattern for Slack gateway service on Cloud Run |

### Agent Engine & Deployment

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-INDEX-agent-engine-a2a-inline-deploy.md | DR-INDEX | agent-engine-a2a-inline-deploy.md | Active | **Sub-index** for Agent Engine, A2A, and inline deployment topics (START HERE for deployment work) |
| 000-DR-GUIDE-agent-engine-dev-wiring-and-smoke-test.md | DR-GUIDE | agent-engine-dev-wiring-and-smoke-test.md | Complete (dev-only) | Guide for Agent Engine dev wiring and smoke test (Phase AE3) |
| 000-LS-SITR-ae-dev-wireup-complete.md | LS-SITR | ae-dev-wireup-complete.md | Complete (dev-only) | Status report: Agent Engine dev wiring complete (Slack → Cloud Run → Agent Engine) |

### A2A Protocol & AgentCards

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-STND-agentcards-and-a2a-contracts.md | DR-STND | agentcards-and-a2a-contracts.md | Active | AgentCard and A2A contract standard for ADK-based agent departments |
| 000-DR-STND-a2a-compliance-tck-inspector.md | DR-STND | a2a-compliance-tck-inspector.md | Active | A2A compliance tooling standard (a2a-inspector + a2a-tck) with phased adoption plan |
| 000-AA-REPT-a2a-inspector-integration-for-department-adk-iam.md | AA-REPT | a2a-inspector-integration-for-department-adk-iam.md | Active | AAR: a2a-inspector integration with two-layer validation strategy |

### Prompt Design & Agent Architecture

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-STND-prompt-design-a2a-contracts-iam-dept.md | DR-STND | prompt-design-a2a-contracts-iam-dept.md | Active | Canonical prompt design and A2A contract patterns for department adk iam |
| 000-DR-STND-prompt-design-and-agentcard-standard.md | DR-STND | prompt-design-and-agentcard-standard.md | Active | Contract-first prompt design standard with AgentCard integration |

### Operations & Deployment

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-RB-OPS-adk-department-operations-runbook.md | RB-OPS | adk-department-operations-runbook.md | Active | Daily operational procedures, monitoring, and troubleshooting for IAM department |
| 000-DR-STND-live-rag-and-agent-engine-rollout-plan.md | DR-STND | live-rag-and-agent-engine-rollout-plan.md | Active | Rollout strategy for enabling live Vertex AI Search (RAG) and Agent Engine features |

### Slack Integration

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-GUIDE-slack-dev-integration-operator-guide.md | DR-GUIDE | slack-dev-integration-operator-guide.md | Production-Ready | Step-by-step guide for Slack bot integration in dev/staging/prod |
| 000-LS-SITR-phase-c-slack-integration-audit.md | LS-SITR | phase-c-slack-integration-audit.md | In Progress | Slack integration audit - identified Agent Engine deployment blocker (fixed) |

### Storage & Knowledge Hub

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-AT-ARCH-org-storage-architecture.md | AT-ARCH | org-storage-architecture.md | Active | Org-wide knowledge hub storage architecture (LIVE1-GCS) - centralized GCS bucket |
| 000-OD-ARCH-datahub-storage-consolidation.md | OD-ARCH | datahub-storage-consolidation.md | Canonical | Datahub-intent consolidation - central knowledge hub for all agent systems (~4GB) |

### Template & Porting Guides

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-GUIDE-porting-iam-department-to-new-repo.md | DR-GUIDE | porting-iam-department-to-new-repo.md | Canonical Guide | Step-by-step guide for porting IAM department template to new product repos |
| 000-DR-STND-iam-department-template-scope-and-rules.md | DR-STND | iam-department-template-scope-and-rules.md | Reference | Scope and reusability boundaries for IAM department template |
| 000-DR-STND-iam-department-integration-checklist.md | DR-STND | iam-department-integration-checklist.md | Standard Checklist | Checklist for integrating IAM department into new repos (use with porting guide) |

### Indexes & Catalogs

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-INDEX-bobs-brain-standards-catalog.md | DR-INDEX | bobs-brain-standards-catalog.md | Active | **This document** - Global catalog of all canonical standards |

### User & Developer Guides

| ID | Type | Filename | Status | Summary |
|----|------|----------|--------|---------|
| 000-DR-GUIDE-iam-department-user-guide.md | DR-GUIDE | iam-department-user-guide.md | User Guide | How to use Bob and IAM department for software engineering tasks |
| 000-DR-ROADMAP-bobs-brain-you-are-here.md | DR-ROADMAP | bobs-brain-you-are-here.md | Active | Roadmap and "you are here" orientation for bobs-brain repo |

**Total Canonical Documents:** 28

---

## IV. Suggested Status Adjustments

### Potential Overlaps / Consolidations

**1. Prompt Design Standards (2 docs with potential overlap)**

**Files:**
- `000-DR-STND-prompt-design-a2a-contracts-iam-dept.md` (Active)
- `000-DR-STND-prompt-design-and-agentcard-standard.md` (Active)

**Analysis:** Two prompt design standards with potentially overlapping scope

**Recommendation:**
- ✅ **Keep both for now** - They may have different focus areas
- ⏸️ **Review for consolidation in future** - After Linux Foundation PR

**Action:** Review and clarify distinct purposes (deferred to future cleanup)

---

**2. Index Documents**

**Files:**
- `000-DR-INDEX-bobs-brain-standards-catalog.md` (This document - master index)
- `000-DR-INDEX-agent-engine-a2a-inline-deploy.md` (Sub-index for deployment topics)

**Analysis:** Two index documents with clear hierarchical relationship

**Recommendation:**
- ✅ **Keep both** - Master index + specialized sub-index is appropriate pattern

**Action:** None needed - working as designed

---

## V. How to Use the Canonical Standards

### Navigation Strategy

**Start at the Top:**
1. **000-DR-INDEX-bobs-brain-standards-catalog.md** (this doc) - Global catalog
2. **000-DR-INDEX-agent-engine-a2a-inline-deploy.md** - Agent Engine / A2A / Inline sub-index (if working on deployment topics)
3. Drill into specific standards/guides as needed

**By Audience:**

**For Operators:**
- **Primary:** `000-RB-OPS-adk-department-operations-runbook.md`
- **Slack:** `000-DR-GUIDE-slack-dev-integration-operator-guide.md`
- **Agent Engine:** `000-DR-GUIDE-agent-engine-dev-wiring-and-smoke-test.md`
- **Storage:** `000-AT-ARCH-org-storage-architecture.md`

**For Developers:**
- **Primary:** `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` (Hard Mode R1-R8)
- **Deployment:** `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
- **Agents:** `000-DR-STND-adk-lazy-loading-app-pattern.md`
- **A2A:** `000-DR-STND-agentcards-and-a2a-contracts.md`
- **Prompts:** `000-DR-STND-prompt-design-a2a-contracts-iam-dept.md`

**For Template Adopters:**
- **Porting Guide:** `000-DR-GUIDE-porting-iam-department-to-new-repo.md`
- **Integration Checklist:** `000-DR-STND-iam-department-integration-checklist.md`
- **Template Scope:** `000-DR-STND-iam-department-template-scope-and-rules.md`

**For End Users:**
- **User Guide:** `000-DR-GUIDE-iam-department-user-guide.md`
- **Roadmap:** `000-DR-ROADMAP-bobs-brain-you-are-here.md`

---

### Document Type Codes (000-CC-ABCD-*)

**Standard Type Codes:**
- **DR-STND** - Documentation/Reference Standard
- **DR-GUIDE** - Documentation/Reference Guide
- **DR-INDEX** - Documentation/Reference Index
- **DR-ROADMAP** - Documentation/Reference Roadmap
- **RB-OPS** - Runbook Operations
- **AA-REPT** - After-Action Report
- **LS-SITR** - Logs/Status SITREP
- **AT-ARCH** - Architecture/Technical
- **OD-ARCH** - Operations/Deployment Architecture

---

### Update Policy

**When to Update This Catalog:**
- ✅ Whenever a new 000-* canonical document is created
- ✅ Whenever a 000-* document status changes (Active → Superseded, Draft → Active)
- ✅ Quarterly review (next: 2026-06-01)

**How to Update:**
- Add new entry to appropriate section (III. Complete Catalog)
- Update summary/status if changed
- Update "Last Updated" date in header
- Commit with message: `docs(000-docs): update global catalog with <new-doc-name>`

---

## VI. Relationship to Other Indexes

**000-DR-INDEX-bobs-brain-standards-catalog.md (this doc):**
- **Scope:** All 000-* canonical docs across entire repo
- **Purpose:** Global catalog and navigation aid
- **Audience:** Everyone (developers, operators, template adopters, users)

**000-DR-INDEX-agent-engine-a2a-inline-deploy.md (sub-index):**
- **Scope:** Subset of 000-* docs related to Agent Engine, A2A, and inline deployment
- **Purpose:** Deep dive into deployment topics
- **Audience:** Developers and operators working on deployment/A2A features

**000-AA-AUDT-000-docs-inventory-and-gap-report.md (NNN-series inventory):**
- **Scope:** All NNN-CC-ABCD-* docs (001-133 range)
- **Purpose:** Gap analysis and historical record
- **Audience:** Developers tracking phase-specific work and AARs

**Hierarchy:**
```
000-DR-INDEX-bobs-brain-standards-catalog.md (global catalog - this doc)
  └─> 000-DR-INDEX-agent-engine-a2a-inline-deploy.md (sub-index)
      └─> Individual 000-* canonical standards/guides

000-AA-AUDT-000-docs-inventory-and-gap-report.md (NNN-series inventory)
  └─> Individual NNN-* phase docs/AARs
```

---

## VII. Summary

**Canonical Standards Highlights:**
- **28 canonical documents** covering standards, guides, runbooks, and architecture
- **2 index documents** for easy navigation (master + sub-index)
- **Multiple audiences served:** Developers, operators, template adopters, end users
- **Clear navigation paths** for each audience type

**Key Takeaways:**
1. Start with this master index for global orientation
2. Use the Agent Engine sub-index for deployment/A2A work
3. All 28 files now properly documented with summaries
4. Ready for Linux Foundation review

**Next Actions:**
1. ✅ All 28 canonical files documented in master index
2. ✅ Ready for Linux Foundation AI Card PR submission
3. ⏸️ Future: Quarterly review for new canonical docs (next: 2026-06-01)
4. ⏸️ Future: Consider consolidating overlapping prompt design standards

---

**Last Updated:** 2026-02-13
**Status:** Active (complete catalog of all 28 canonical files)
**Next Review:** 2026-06-01 (quarterly) or when 5+ new canonical docs added
