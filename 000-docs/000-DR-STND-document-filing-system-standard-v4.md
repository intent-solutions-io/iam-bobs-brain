# DOCUMENT FILING SYSTEM STANDARD v4.3

**Purpose:** Universal standard for organizing project documentation with category-based classification

**Last Updated:** 2026-02-13
**Status:** ✅ Production Standard
**Applies To:** All projects in `/home/jeremy/000-projects/` and cross-repo canonical standards

---

## WHAT CHANGED IN v4.3

**Key Updates:**
1. **Dropped `6767-` prefix from all filenames** - All canonical docs now use `000-` prefix, same as project-specific docs. The `6767-` prefix is retired from filenames entirely.
2. **Dropped topic prefixes** - Removed INLINE, LAZY, SLKAUD, SLKDEV, AECOMP, AEDEV, A2AINSP, ROADMAP prefixes from filenames. These were v3.0 workarounds that are no longer needed.
3. **Unified naming** - All docs in `000-docs/` follow exactly `NNN-CC-ABCD-description.ext` with no special-case prefixes.
4. **Conceptual shorthand preserved** - Pattern names like "6767-LAZY" and "6767 standard" remain as concept labels in code/comments, just not in filenames.

**Migration Impact:** All 28 `6767-*` files renamed to `000-*` prefix. See version history for v3.0 background.

---

## FORMAT SPECIFICATION

### Primary Format
```
NNN-CC-ABCD-short-description.ext
```

**Components:**
- **NNN** = Zero-padded sequence number (001-999) - enforces chronology
- **CC** = Two-letter category code (see Category Table)
- **ABCD** = Four-letter document type abbreviation (see Type Tables)
- **short-description** = 1-4 words, kebab-case, lowercase
- **ext** = File extension (.md, .pdf, .txt, etc.)

### Sub-Tasks Format
When a document has multiple related sub-documents:

**Option A - Letter Suffix:**
```
005-PM-TASK-api-endpoints.md
005a-PM-TASK-auth-endpoints.md
005b-PM-TASK-payment-endpoints.md
```

**Option B - Numeric Suffix:**
```
006-PM-RISK-security-audit.md
006-1-PM-RISK-encryption-review.md
006-2-PM-RISK-access-controls.md
```

---

## SPECIAL CASE: 6767 CANONICAL STANDARDS (SOP SERIES)

### Purpose of 6767 Series

The **canonical standards** (formerly "6767-series") represent **cross-repo reusable standards** (Standard Operating Procedures). These are global standards that can be copied and applied across:
- bobs-brain
- DiagnosticPro
- Hustle
- BrightStream
- Other Intent Solutions projects

**Key Distinction:** Canonical docs are NOT tied to a specific sprint, phase, or project implementation. They define universal patterns, architectures, and processes.

### Canonical Standards Filename Pattern (v4.3 Rule)

**Format:** Same as project-specific docs, using `000-` prefix:
```
000-CC-ABCD-short-description.ext
```

**Note:** Prior versions used a `6767-` prefix. As of v4.3, all canonical docs use `000-` prefix. The "6767" label survives only as a conceptual shorthand in code comments (e.g., "6767-LAZY pattern").

### Examples (CORRECT v4.3 Format)

```
✅ 000-DR-STND-document-filing-system-standard-v4.md
✅ 000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md
✅ 000-DR-STND-agentcards-and-a2a-contracts.md
✅ 000-DR-INDEX-bobs-brain-standards-catalog.md
✅ 000-RB-OPS-adk-department-operations-runbook.md
✅ 000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md
✅ 000-DR-STND-adk-lazy-loading-app-pattern.md
```

### Examples (INCORRECT - Pre-v4.3)

```
❌ 6767-DR-INDEX-bobs-brain-standards-catalog.md          (old 6767 prefix)
❌ 6767-INLINE-DR-STND-inline-source-deployment-...md     (old topic prefix)
❌ 6767-000-DR-INDEX-bobs-brain-standards-catalog.md      (old numbered prefix)
```

**Why Incorrect:** The `6767-` prefix and topic prefixes (INLINE, LAZY, etc.) are retired from filenames. All canonical docs use `000-` prefix.

### Document IDs vs Filenames

**Allowed:** Internal document IDs in headers for cross-referencing

**Example Header:**
```markdown
# Agent Engine, A2A, and Inline Deployment - Master Index

**Document Type:** Canonical Standard & Index (6767-DR-STND)
**Document ID:** 6767-120
**Status:** Active
```

**The Rule:**
- Document IDs (like "6767-000", "6767-120") **can exist in headers/content** for organizational purposes
- But the **filename itself** must NOT include these numeric IDs
- This distinguishes 6767 canonical docs from NNN-series project-specific docs

### Topic Prefixes (Retired in v4.3)

Prior to v4.3, some canonical docs used topic-specific prefixes (INLINE, LAZY, SLKDEV, etc.) between `6767-` and the category code. These have been dropped in v4.3 - the description portion of the filename captures the topic sufficiently.

**Conceptual shorthand** like "6767-LAZY pattern" is still used in code comments and docstrings as a pattern label. This is fine - it's the *filename prefix* that changed, not the concept name.

### Relationship to NNN-Series Docs

**Clear Distinction:**
- **6767 series** = Cross-repo canonical standards (reusable SOPs, patterns, architectures)
- **NNN series** = Project-specific docs (phases, AARs, plans, implementation details)

**Rule of Thumb:**
- **Use 6767** if the doc is a global SOP / cross-app standard
- **Use NNN** if the doc is app-specific, sprint-specific, or phase-specific

**Examples:**
- "ADK Agent Engine Hard Mode Rules" → 6767 (applies to all ADK departments)
- "Phase 4 ARV Gate Implementation AAR" → NNN (specific to bobs-brain Phase 4)

---

## CANONICAL STRUCTURE FOR APPS AND REPOS

### Global Canonical Docs (6767 Series)

**Location:** Typically in `000-docs/` or `/docs/` at repo root (or in a master standards repo like `prompts-intent-solutions`)

**Naming:** Always use the `6767-CC-ABCD-short-description.ext` pattern

**Purpose:** Represent reusable standards that can be applied across:
- bobs-brain (ADK agent department)
- DiagnosticPro (repair platform)
- Hustle (youth sports app)
- BrightStream (news platform)
- Other Intent Solutions projects

### Repo-Level / App-Level Docs (NNN Series)

**For Each Repo or App:**

**Option A - Repo Root:**
```
repo-root/
├── 000-docs/
│   ├── 001-AA-PLAN-phase-1-skeleton.md          # Project-specific
│   ├── 002-AA-REPT-phase-1-implementation.md    # Project-specific
│   ├── 000-DR-STND-adk-agent-engine-spec.md    # Canonical (if applicable)
│   └── ...
```

**Option B - Monorepo with App-Specific Docs:**
```
monorepo-root/
├── apps/
│   ├── hustle/
│   │   ├── 01-Docs/
│   │   │   ├── 001-PP-PROD-hustle-mvp-requirements.md
│   │   │   ├── 002-AT-ARCH-hustle-system-design.md
│   │   │   └── ...
│   │
│   ├── diagnosticpro/
│   │   ├── 01-Docs/
│   │   │   ├── 001-PP-PROD-diagnosticpro-platform-spec.md
│   │   │   ├── 002-AT-ARCH-diagnosticpro-architecture.md
│   │   │   └── ...
│   │
│   └── brightstream/
│       ├── 000-docs/
│       │   ├── 001-PP-ARCH-brightstream-platform-design.md
│       │   └── ...
```

**NNN Docs Represent:**
- Implementation history (phases, sprints)
- After-Action Reports (AARs)
- Runbooks specific to that app
- Meeting notes and decisions
- Status logs and progress tracking

**NOT Global Standards:** NNN docs are NOT canonical by default (use 6767 for that).

### Simple Rule-of-Thumb

| Scenario | Use |
|----------|-----|
| Global SOP / cross-app standard | `6767-CC-ABCD-description.ext` |
| App-specific, sprint-specific, phase-specific | `NNN-CC-ABCD-description.ext` |

**Examples:**
```
# Canonical filing standard (this doc):
000-DR-STND-document-filing-system-standard-v4.md

# Global Agent Engine standard:
000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md

# Hustle-specific AAR (in hustle's 01-Docs/):
027-AA-AACR-hustle-beta-launch-retro.md

# BrightStream Phase 1 plan (in brightstream's 000-docs/):
001-AA-PLAN-phase-1-infrastructure-setup.md
```

---

## CATEGORY CODES (2-LETTER)

| Code | Category | Description |
|------|----------|-------------|
| **PP** | Product & Planning | Requirements, roadmaps, business planning |
| **AT** | Architecture & Technical | Technical decisions, system design |
| **DC** | Development & Code | Code documentation, modules, components |
| **TQ** | Testing & Quality | Test plans, QA, bugs, security audits |
| **OD** | Operations & Deployment | DevOps, deployment, infrastructure |
| **LS** | Logs & Status | Status logs, work logs, progress tracking |
| **RA** | Reports & Analysis | Reports, analytics, research findings |
| **MC** | Meetings & Communication | Meeting notes, memos, presentations |
| **PM** | Project Management | Tasks, sprints, backlogs, risks |
| **DR** | Documentation & Reference | Guides, manuals, references, SOPs |
| **UC** | User & Customer | User docs, onboarding, training, feedback |
| **BL** | Business & Legal | Contracts, compliance, policies, legal |
| **RL** | Research & Learning | Research, experiments, POCs, proposals |
| **AA** | After Action & Review | Post-mortems, retrospectives, lessons |
| **WA** | Workflows & Automation | Workflow docs, n8n, automation, webhooks |
| **DD** | Data & Datasets | Data documentation, CSV, SQL, exports |
| **MS** | Miscellaneous | General, drafts, archives, work-in-progress |

---

## DOCUMENT TYPE ABBREVIATIONS (4-LETTER)

### PP - Product & Planning
| Code | Full Name | Usage |
|------|-----------|-------|
| **PROD** | Product Requirements Document | Core product requirements |
| **PLAN** | Plan/Planning Document | Strategic plans, project plans |
| **RMAP** | Roadmap | Product or project roadmaps |
| **BREQ** | Business Requirements Document | Business-level requirements |
| **FREQ** | Functional Requirements Document | Functional specifications |
| **SOWK** | Statement of Work | Project scope and deliverables |
| **KPIS** | Key Performance Indicators | Success metrics definition |
| **OKRS** | Objectives and Key Results | Goal-setting framework |

### AT - Architecture & Technical
| Code | Full Name | Usage |
|------|-----------|-------|
| **ADEC** | Architecture Decision Record | Technical decision documentation |
| **ARCH** | Technical Architecture Document | System architecture specs |
| **DSGN** | Design Document/Specification | Detailed design specs |
| **APIS** | API Documentation | API specifications |
| **SDKS** | SDK Documentation | Software development kit docs |
| **INTG** | Integration Documentation | Integration guides and specs |
| **DIAG** | Diagram/Visual Documentation | Architecture diagrams |

### DC - Development & Code
| Code | Full Name | Usage |
|------|-----------|-------|
| **DEVN** | Development Notes | Developer notes and annotations |
| **CODE** | Code Documentation | Code-level documentation |
| **LIBR** | Library Documentation | Library usage and APIs |
| **MODL** | Module Documentation | Module specifications |
| **COMP** | Component Documentation | Component specs and usage |
| **UTIL** | Helper/Utility Documentation | Utility function documentation |

### TQ - Testing & Quality
| Code | Full Name | Usage |
|------|-----------|-------|
| **TEST** | Test Plan/Strategy | Overall testing strategy |
| **CASE** | Test Case Documentation | Specific test cases |
| **QAPL** | Quality Assurance Plan | QA strategy and process |
| **BUGR** | Bug Report/Analysis | Bug documentation |
| **PERF** | Performance Testing | Performance test results |
| **SECU** | Security Audit/Testing | Security assessments |
| **PENT** | Penetration Test Results | Pentest findings |

### OD - Operations & Deployment
| Code | Full Name | Usage |
|------|-----------|-------|
| **OPNS** | Operations Documentation | Operational procedures |
| **DEPL** | Deployment Guide/Log | Deployment instructions |
| **INFR** | Infrastructure Documentation | Infrastructure specs |
| **CONF** | Configuration Documentation | Config file documentation |
| **ENVR** | Environment Setup | Environment configuration |
| **RELS** | Release Notes | Version release notes |
| **CHNG** | Change Log/Management | Change documentation |
| **INCD** | Incident Report | Incident documentation |
| **POST** | Post-Mortem/Incident Analysis | Incident analysis |

### LS - Logs & Status
| Code | Full Name | Usage |
|------|-----------|-------|
| **LOGS** | Status Log/Journal | General status logging |
| **WORK** | Work Log/Session Notes | Daily work logs |
| **PROG** | Progress Report | Progress documentation |
| **STAT** | Status Report/Update | Status updates |
| **CHKP** | Checkpoint/Milestone Log | Milestone tracking |

### RA - Reports & Analysis
| Code | Full Name | Usage |
|------|-----------|-------|
| **REPT** | General Report | Standard reports |
| **ANLY** | Analysis/Research Report | Analytical findings |
| **AUDT** | Audit Report | Audit results |
| **REVW** | Review Document | Review findings |
| **RCAS** | Root Cause Analysis | Problem analysis |
| **DATA** | Data Analysis | Data analysis reports |
| **METR** | Metrics Report | Metrics and KPIs |
| **BNCH** | Benchmark Results | Performance benchmarks |

### MC - Meetings & Communication
| Code | Full Name | Usage |
|------|-----------|-------|
| **MEET** | Meeting Notes/Minutes | Meeting documentation |
| **AGND** | Agenda | Meeting agendas |
| **ACTN** | Action Items | Action item tracking |
| **SUMM** | Summary/Executive Summary | High-level summaries |
| **MEMO** | Memo/Communication | Internal memos |
| **PRES** | Presentation | Presentation materials |
| **WKSP** | Workshop Notes | Workshop documentation |

### PM - Project Management
| Code | Full Name | Usage |
|------|-----------|-------|
| **TASK** | Task Breakdown/List | Task documentation |
| **BKLG** | Backlog | Product/sprint backlog |
| **SPRT** | Sprint Plan/Notes | Sprint planning docs |
| **RETR** | Retrospective | Sprint retrospectives |
| **STND** | Standup Notes | Daily standup logs |
| **RISK** | Risk Register/Assessment | Risk documentation |
| **ISSU** | Issue Tracker/Log | Issue tracking |

### DR - Documentation & Reference
| Code | Full Name | Usage |
|------|-----------|-------|
| **REFF** | Reference Material/Guide | Reference documentation |
| **GUID** | User Guide/Handbook | User guides |
| **MANL** | Manual | Operation manuals |
| **FAQS** | FAQ Document | Frequently asked questions |
| **GLOS** | Glossary | Term definitions |
| **SOPS** | Standard Operating Procedure | Procedural documentation |
| **TMPL** | Template | Document templates |
| **CHKL** | Checklist | Process checklists |
| **STND** | Standard | Standards and specifications |
| **INDEX** | Index/Catalog | Navigation and directory docs |

### UC - User & Customer
| Code | Full Name | Usage |
|------|-----------|-------|
| **USER** | User Documentation | End-user documentation |
| **ONBD** | Onboarding Guide | User onboarding materials |
| **TRNG** | Training Materials | Training documentation |
| **FDBK** | Feedback/User Feedback | User feedback logs |
| **SURV** | Survey Results | Survey data and analysis |
| **INTV** | Interview Notes/Transcripts | Interview documentation |
| **PERS** | Persona Documentation | User personas |

### BL - Business & Legal
| Code | Full Name | Usage |
|------|-----------|-------|
| **CNTR** | Contract/Agreement | Legal contracts |
| **NDAS** | Non-Disclosure Agreement | Confidentiality agreements |
| **LICN** | License Documentation | Licensing information |
| **CMPL** | Compliance Documentation | Compliance records |
| **POLI** | Policy Document | Company policies |
| **TERM** | Terms & Conditions | Terms documentation |
| **PRIV** | Privacy Documentation | Privacy policies |

### RL - Research & Learning
| Code | Full Name | Usage |
|------|-----------|-------|
| **RSRC** | Research Notes | Research documentation |
| **LERN** | Learning/Study Notes | Study materials |
| **EXPR** | Experiment/POC Documentation | Proof of concept docs |
| **PROP** | Proposal | Project proposals |
| **WHIT** | Whitepaper | Technical whitepapers |
| **CSES** | Case Study | Case study documentation |

### AA - After Action & Review
| Code | Full Name | Usage |
|------|-----------|-------|
| **AACR** | After Action Report | After-action reviews |
| **LESN** | Lessons Learned | Lessons documentation |
| **PMRT** | Post-Mortem/Incident Review | Incident post-mortems |

### WA - Workflows & Automation
| Code | Full Name | Usage |
|------|-----------|-------|
| **WFLW** | Workflow Documentation | Workflow specs |
| **N8NS** | n8n Workflow Documentation | n8n-specific workflows |
| **AUTO** | Automation Documentation | Automation scripts/docs |
| **HOOK** | Webhook Documentation | Webhook configuration |

### DD - Data & Datasets
| Code | Full Name | Usage |
|------|-----------|-------|
| **DSET** | Data Documentation | Dataset documentation |
| **CSVS** | CSV Dataset Documentation | CSV file documentation |
| **SQLS** | SQL/Database Documentation | Database documentation |
| **EXPT** | Data Export Documentation | Export specifications |

### MS - Miscellaneous
| Code | Full Name | Usage |
|------|-----------|-------|
| **MISC** | Miscellaneous/General | General documents |
| **DRFT** | Draft/Temporary | Draft documents |
| **ARCH** | Archive Notes | Archived materials |
| **OLDV** | Deprecated/Old Version | Deprecated docs |
| **WIPS** | Work in Progress | Work in progress docs |
| **INDX** | Index/Table of Contents | Index files |

---

## EXAMPLE CHRONOLOGY

### Project Documentation Structure
```
01-Docs/
├── 001-AT-ADEC-initial-architecture.md
├── 002-PP-PROD-core-features.md
├── 003-MC-MEET-kickoff-notes.md
├── 004-PP-PLAN-sprint-1-roadmap.pdf
├── 005-PM-TASK-api-endpoints.md
├── 005a-PM-TASK-auth-endpoints.md
├── 005b-PM-TASK-payment-endpoints.md
├── 006-PM-RISK-data-security.md
├── 007-AT-ADEC-database-choice.md
├── 008-MC-MEET-client-feedback.md
├── 009-AA-AACR-sprint-1-review.md
├── 010-LS-LOGS-error-analysis.txt
├── 011-TQ-TEST-integration-strategy.md
├── 012-OD-DEPL-production-guide.md
├── 013-UC-USER-onboarding-flow.md
├── 014-DR-GUID-api-reference.md
├── 015-RA-ANLY-user-metrics.xlsx
```

### Real-World Examples (bobs-brain)
```
000-docs/
├── 001-AA-PLAN-phase-1-skeleton.md
├── 002-AA-REPT-phase-1-implementation.md
├── 050-AT-ARCH-foreman-worker-department.md
├── 075-DR-STND-arv-minimum-gate.md
├── 100-OD-GUID-deployment-operator-runbook.md
├── 128-AA-REPT-phase-4-arv-gate-dev-deploy.md
├── 000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md
├── 000-DR-STND-document-filing-system-standard-v4.md
└── 000-RB-OPS-adk-department-operations-runbook.md
```

---

## BENEFITS OF THIS SYSTEM

### Enhanced Organization
- **Category visibility** - Immediately identify document type by category code
- **Improved sorting** - Documents naturally group by category, then chronology
- **Better searchability** - Search by category (PP, AT, etc.) or type (TASK, MEET)

### Scalability
- **Consistent 4-letter codes** - Uniform length for all document types
- **Clear hierarchy** - Category → Type → Description
- **Room for growth** - 17 categories × many types = extensive coverage

### Cross-Project Compatibility
- **Universal abbreviations** - Use across all projects (via 6767 series)
- **Standardized structure** - Team members recognize patterns
- **Easy onboarding** - New team members learn system quickly
- **Canonical standards** - 6767 docs provide cross-repo reusability

---

## MIGRATION FROM OLD SYSTEM

### Converting Existing Files

**Old Format:**
```
005-tsk-api-endpoints.md
006-rsk-security-audit.md
007-adr-database-choice.md
```

**New Format:**
```
005-PM-TASK-api-endpoints.md
006-PM-RISK-security-audit.md
007-AT-ADEC-database-choice.md
```

### Migration History

**v3.0 → v4.3 Migration (2026-02-13):**
All 28 `6767-*` files renamed to `000-*` prefix. Topic prefixes (INLINE, LAZY, etc.) dropped from filenames.

```
# Example renames:
6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md → 000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md
6767-INLINE-DR-STND-inline-source-deployment-*.md       → 000-DR-STND-inline-source-deployment-*.md
6767-LAZY-DR-STND-adk-lazy-loading-app-pattern.md       → 000-DR-STND-adk-lazy-loading-app-pattern.md
```

### Migration Script Pattern
```bash
# Example: Convert 3-letter to category + 4-letter
# Old: NNN-abc-description.ext
# New: NNN-CC-ABCD-description.ext

# tsk → PM-TASK
# rsk → PM-RISK
# adr → AT-ADEC
# prd → PP-PROD
# mtg → MC-MEET
```

---

## QUICK REFERENCE CARD

### Most Common Combinations

| Code | Document Type | Example |
|------|--------------|---------|
| PP-PROD | Product Requirements | 001-PP-PROD-feature-spec.md |
| AT-ADEC | Architecture Decision | 002-AT-ADEC-tech-stack.md |
| AT-ARCH | Architecture Document | 003-AT-ARCH-system-design.md |
| PM-TASK | Task Documentation | 004-PM-TASK-build-api.md |
| MC-MEET | Meeting Notes | 005-MC-MEET-sprint-planning.md |
| TQ-TEST | Test Plan | 006-TQ-TEST-integration-tests.md |
| OD-DEPL | Deployment Guide | 007-OD-DEPL-production.md |
| LS-WORK | Work Log | 008-LS-WORK-daily-log.md |
| RA-ANLY | Analysis Report | 009-RA-ANLY-user-data.md |
| DR-GUID | User Guide | 010-DR-GUID-user-manual.md |
| DR-STND | Standard/SOP | 011-DR-STND-code-review-process.md |
| AA-AACR | After-Action Report | 012-AA-AACR-sprint-retro.md |
| AA-LESN | Lessons Learned | 013-AA-LESN-deployment-lessons.md |

### Common Canonical Combinations

| Code | Document Type | Example |
|------|--------------|---------|
| 000-DR-STND | Canonical Standard | 000-DR-STND-document-filing-system-standard-v4.md |
| 000-DR-INDEX | Global Catalog/Index | 000-DR-INDEX-bobs-brain-standards-catalog.md |
| 000-RB-OPS | Runbook/Operations | 000-RB-OPS-adk-department-operations-runbook.md |
| 000-AT-ARCH | Architecture Standard | 000-AT-ARCH-org-storage-architecture.md |
| 000-DR-GUIDE | Cross-Repo Guide | 000-DR-GUIDE-porting-iam-department-to-new-repo.md |

---

## NAMING BEST PRACTICES

### DO's
✅ Use lowercase for description
✅ Use kebab-case (hyphens) for multi-word descriptions
✅ Keep descriptions 1-4 words maximum
✅ Use descriptive file extensions (.md, .pdf, .xlsx)
✅ Pad sequence numbers (001, 002, not 1, 2)
✅ Maintain chronological sequence
✅ Use 6767 prefix ONLY for cross-repo canonical standards
✅ Keep document IDs in headers but NOT in 6767 filenames

### DON'Ts
❌ Don't skip sequence numbers
❌ Don't use underscores or camelCase in descriptions
❌ Don't use special characters except hyphens
❌ Don't exceed 4 words in description
❌ Don't use non-standard category codes
❌ Don't omit category or type codes
❌ Don't use numeric IDs after 6767- in filenames (v3.0 rule)

---

## CATEGORY DECISION TREE

**Not sure which category? Use this guide:**

1. **Is it about product/business planning?** → PP
2. **Is it a technical/architecture decision?** → AT
3. **Is it code or development documentation?** → DC
4. **Is it about testing or quality?** → TQ
5. **Is it about deployment or operations?** → OD
6. **Is it a log or status update?** → LS
7. **Is it a report or analysis?** → RA
8. **Is it meeting notes or communication?** → MC
9. **Is it project management (tasks/risks)?** → PM
10. **Is it a reference guide or manual?** → DR
11. **Is it for end users or customers?** → UC
12. **Is it legal or business policy?** → BL
13. **Is it research or experimental?** → RL
14. **Is it a post-mortem or retrospective?** → AA
15. **Is it about workflows or automation?** → WA
16. **Is it about data or datasets?** → DD
17. **Doesn't fit anywhere?** → MS

---

## VERSION HISTORY

### v4.3 (2026-02-13)

**Major Changes:**
1. **Dropped `6767-` prefix from all filenames** - All 28 canonical docs renamed from `6767-*` to `000-*`
2. **Dropped topic prefixes** - INLINE, LAZY, SLKAUD, SLKDEV, AECOMP, AEDEV, A2AINSP, ROADMAP prefixes removed from filenames
3. **Unified naming** - Canonical docs now use same `000-CC-ABCD-description.ext` format as project-specific docs
4. **Preserved conceptual shorthand** - "6767-LAZY", "6767 standard" remain valid as concept labels in code

**Rationale:** Having two different prefix conventions (6767 vs NNN) created confusion. Since all docs live in the same `000-docs/` folder, using a single `000-` prefix is simpler and eliminates the special-case handling.

### v3.0 (2025-11-21)

**Changes:** Introduced `6767-CC-ABCD-description.ext` pattern for canonical docs. Banned numeric IDs in 6767 filenames. Added topic prefixes. (Superseded by v4.3)

### v2.0 (2025-10-16)

**Initial Production Standard:**
- Introduced category-based classification system
- Defined 17 category codes (PP, AT, DC, TQ, OD, LS, RA, MC, PM, DR, UC, BL, RL, AA, WA, DD, MS)
- Created comprehensive 4-letter document type abbreviations for each category
- Established NNN-CC-ABCD-description.ext format
- Provided examples, decision trees, and quick reference cards

**Status:** Baseline standard used across all `/home/jeremy/000-projects/` projects

---

**DOCUMENT FILING SYSTEM STANDARD v4.3**
*Category-based organization for professional project documentation with canonical cross-repo standards*

---

**Applies To:** All projects in `/home/jeremy/000-projects/` and canonical 6767 standards series
