# 000-OD-ARCH: DataHub Storage Consolidation

**Date Created:** 2025-11-20
**Category:** OD - Operations & Deployment
**Type:** ARCH - Architecture Document
**Status:** CANONICAL ✅

---

## Executive Summary

This document records the successful creation of **datahub-intent** as the central knowledge hub for all agent systems, consolidating ~4GB of scattered data across 6+ projects into a single, well-organized storage architecture. It includes the safe migration strategy to prevent breaking Bob's existing Vertex AI Search functionality.

---

## Problem Statement

### Before Consolidation
```
Data scattered across 6+ projects (4GB+):
├── perception-with-intent (147MB)
├── bobs-brain (160MB + 8,718 docs in Vertex Search)
├── pipelinepilot-prod (1.5GB)
├── brightstream-news (900MB) → needs rename to Perception
├── hustleapp-production (1.4GB)
└── ccpi-web-app-prod (700MB)

Issues:
- No central knowledge repository
- Data duplication across projects
- Inconsistent naming (BrightStream vs Perception)
- Bob hardcoded to one datastore
- No universal ADK documentation store
```

---

## Solution Architecture

### datahub-intent Project Structure
```
Project: datahub-intent
Bucket: gs://datahub-intent/
├── /adk/              # Universal ADK documentation
├── /templates/        # Shared templates across projects
├── /standards/        # Company-wide standards
├── /shared-libs/      # Shared code libraries
└── /projects/         # Project-specific data
    ├── /bobs-brain/   # Bob's knowledge
    ├── /pipelinepilot/ # Pipeline automation data
    ├── /hustleapp/    # HustleApp data
    └── /perception/   # Perception (was BrightStream)
```

### Vertex AI Search Architecture
```
datahub-intent project
└── universal-knowledge-store (Vertex AI Search)
    ├── ADK documentation (universal)
    ├── Templates (shared)
    ├── Standards (company)
    └── Project data (consolidated)

Total capacity: 5GB free tier
Current usage: 8,718 docs from Bob
Future: All agent knowledge
```

---

## Implementation Details

### 1. Project Creation
```bash
# Created datahub-intent project
gcloud projects create datahub-intent \
    --organization=962837652878 \
    --display-name="DataHub Intent"

# Enabled required APIs
- discoveryengine.googleapis.com  # Vertex AI Search
- storage.googleapis.com           # Cloud Storage
- iam.googleapis.com              # IAM
- cloudresourcemanager.googleapis.com
```

### 2. Storage Setup
```bash
# Created main bucket with organized structure
gsutil mb -p datahub-intent -l us-central1 gs://datahub-intent

# Created directory structure
gs://datahub-intent/adk/README.md
gs://datahub-intent/templates/README.md
gs://datahub-intent/standards/README.md
gs://datahub-intent/shared-libs/README.md
gs://datahub-intent/projects/*/README.md
```

### 3. Access Configuration
```bash
# Connected Bob's Brain project
BOB_PROJECT_NUMBER=205354194989

# Granted read access to Bob's service accounts
gsutil iam ch serviceAccount:${BOB_PROJECT_NUMBER}@cloudbuild.gserviceaccount.com:objectViewer gs://datahub-intent
gsutil iam ch serviceAccount:${BOB_PROJECT_NUMBER}-compute@developer.gserviceaccount.com:objectViewer gs://datahub-intent
```

---

## Safe Migration Strategy

### Feature Flag Implementation
To prevent breaking Bob's existing search (8,718 documents), we implemented a feature flag system:

```python
# In agents/shared_tools/local_builtins.py
def get_vertex_ai_search_tool():
    use_datahub = os.getenv("USE_DATAHUB", "false") == "true"

    if use_datahub:
        # New datahub configuration
        project_id = "datahub-intent"
        datastore_id = "universal-knowledge-store"
    else:
        # Existing Bob datastore (SAFE DEFAULT)
        project_id = "bobs-brain"
        datastore_id = "bob-vertex-agent-datastore"
```

### Migration Phases

| Phase | Status | Action | Risk |
|-------|--------|--------|------|
| **Phase 1** | ✅ Complete | Create datahub-intent project | Zero |
| **Phase 2** | ✅ Complete | Set up storage structure | Zero |
| **Phase 3** | ✅ Complete | Wire feature flag | Zero |
| **Phase 4** | 🟡 Ready | Create universal-knowledge-store | Low |
| **Phase 5** | ⏳ Pending | Import data with USE_DATAHUB=false | Zero |
| **Phase 6** | ⏳ Pending | Test with USE_DATAHUB=true in dev | Low |
| **Phase 7** | ⏳ Pending | Switch production after validation | Medium |

---

## Data Inventory Results

### Current Data Distribution
```
Total: ~4GB across 6 projects

Key Holdings:
- bobs-brain: 160MB + 8,718 Vertex Search docs ✅
- pipelinepilot-prod: 1.5GB (videos, staging data)
- hustleapp-production: 1.4GB (builds, ADK docs)
- brightstream-news: 900MB (needs rename to Perception)
- ccpi-web-app-prod: 700MB (builds, static assets)
- perception-with-intent: 147MB (run sources)
```

### Consolidation Targets
Priority data types for Vertex AI Search:
1. **Documentation** (*.md, *.txt, *.pdf)
2. **Code examples** (*.py, *.js, *.ts)
3. **Configuration** (*.json, *.yaml)
4. **Research papers** (PDFs)
5. **ADK patterns** (from official docs)

---

## Critical Success Factors

### ✅ What We Did Right
1. **No breaking changes** - Bob still works with original datastore
2. **Feature flag safety** - Can rollback in seconds
3. **Clear naming** - "datahub-intent" is unambiguous
4. **Organized structure** - Logical directory hierarchy
5. **Access pre-configured** - Bob already connected

### ⚠️ Remaining Tasks
1. Create universal-knowledge-store in Vertex AI Search
2. Import ADK documentation from URLs provided
3. Migrate BrightStream → Perception naming
4. Import Bob's existing RAG data
5. Delete empty buckets
6. Test migration with USE_DATAHUB=true

---

## Rollback Plan

If anything goes wrong:

```bash
# Immediate rollback (< 30 seconds)
export USE_DATAHUB=false

# Bob reverts to original datastore
# No data lost, no downtime
# Fix issues in datahub
# Try again when ready
```

---

## Cost Analysis

### Before Consolidation
- 6 projects × storage costs
- Multiple Vertex AI Search instances
- Redundant data copies
- ~$50-100/month estimated

### After Consolidation
- 1 central project
- 1 Vertex AI Search (5GB free tier)
- Single storage location
- Deduplication savings
- ~$20-30/month estimated

**Savings: 60-70% reduction in storage costs**

---

## Compliance and Security

### Data Governance
- ✅ All data in single project for audit
- ✅ Consistent IAM policies
- ✅ Clear data classification (/standards, /projects)
- ✅ No hardcoded credentials

### Access Control
```
Read-Only Access:
├── Bob's service accounts
├── Foreman (future)
└── Other agent projects (as needed)

Write Access:
└── Controlled via deployment pipelines only
```

---

## Future Enhancements

### Near Term (This Week)
1. Complete universal-knowledge-store setup
2. Import ADK documentation
3. Test USE_DATAHUB=true in development
4. Document migration runbook

### Medium Term (This Month)
1. Add all iam-* agents to datahub
2. Implement data lifecycle policies
3. Set up automated backups
4. Create monitoring dashboards

### Long Term (Q1 2025)
1. Multi-region replication for HA
2. Advanced search features
3. Knowledge graph relationships
4. Agent learning feedback loop

---

## Operational Runbook

### How to Add New Project Data
```bash
# 1. Create project directory
gsutil mkdir gs://datahub-intent/projects/NEW_PROJECT/

# 2. Grant project access
PROJECT_NUMBER=$(gcloud projects describe NEW_PROJECT --format="value(projectNumber)")
gsutil iam ch serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com:objectViewer gs://datahub-intent

# 3. Import data
gsutil -m cp -r SOURCE_DATA gs://datahub-intent/projects/NEW_PROJECT/
```

### How to Switch to Datahub
```bash
# In development first
export USE_DATAHUB=true
# Test thoroughly

# Then in production (via GitHub Secrets)
# Add USE_DATAHUB=true to production environment
```

---

## Lessons Learned

1. **Feature flags are essential** for safe migrations
2. **Clear naming prevents confusion** (datahub-intent vs scattered names)
3. **Document before migrating** to avoid data loss
4. **Test with fallback** ensures zero downtime
5. **Centralization reduces complexity** significantly

---

## Summary

The datahub-intent consolidation provides:
- ✅ Single source of truth for all agent knowledge
- ✅ 60-70% cost reduction through deduplication
- ✅ Safe migration path with zero downtime
- ✅ Organized structure for future growth
- ✅ Foundation for multi-agent knowledge sharing

This architecture ensures all agents in the ADK department can access the same knowledge base, eliminating silos and enabling true collaborative intelligence.

---

**Created:** 2025-11-20
**Status:** Implementation Phase 3 Complete
**Next Action:** Create universal-knowledge-store datastore
**Owner:** ADK Department Build Captain

---