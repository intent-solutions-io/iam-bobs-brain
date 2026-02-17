# Org-Wide Knowledge Hub Storage Architecture (LIVE1-GCS)

**Document Number:** 000-AT-ARCH-org-storage-architecture
**Status:** Active
**Phase:** LIVE1-GCS
**Created:** 2025-11-20
**Last Updated:** 2025-11-20

---

## Overview

The **Org-Wide Knowledge Hub** is a centralized GCS bucket for storing SWE audit results, portfolio analyses, and knowledge artifacts across all repos and products in the organization.

**Key Goals:**
- Single source of truth for portfolio-level audit data
- Shared knowledge base across all agent departments
- Foundation for future analytics (BigQuery integration in LIVE-BQ)
- Opt-in by default with feature flags

---

## Architecture

### Bucket Structure

```
gs://intent-org-knowledge-hub-{env}/
├── portfolio/
│   └── runs/
│       └── {run_id}/
│           ├── summary.json              # Portfolio-level summary
│           └── per-repo/
│               ├── {repo_id}.json        # Per-repo details
│               └── ...
│
├── swe/
│   └── agents/
│       └── {agent_name}/
│           └── runs/
│               └── {run_id}.json         # Single-repo SWE runs (future)
│
├── docs/                                 # Org-wide docs (future)
│
└── vertex-search/                        # RAG snapshots (LIVE2+)
```

### Lifecycle Rules

- **Per-repo details:** 90-day retention (keeps recent audit history)
- **Portfolio summaries:** Retained indefinitely
- **Future:** May add archival policies for older data

---

## Components

### 1. Terraform Infrastructure (`infra/terraform/storage.tf`)

**Bucket Resource:**
```hcl
resource "google_storage_bucket" "org_knowledge_hub" {
  count         = var.org_storage_enabled ? 1 : 0
  name          = var.org_storage_bucket_name
  location      = var.org_storage_location
  force_destroy = false

  uniform_bucket_level_access = true
  versioning { enabled = true }

  lifecycle_rule {
    condition {
      age            = 90
      matches_prefix = ["portfolio/runs/*/per-repo/"]
    }
    action { type = "Delete" }
  }
}
```

**IAM Bindings:**
- Bob's agent runtime SA: `roles/storage.objectAdmin`
- Future repos can be added via `org_storage_writer_service_accounts`

**Feature Flags:**
- `org_storage_enabled` (default: false) - Create bucket
- `org_storage_bucket_name` - Bucket name
- `org_storage_location` (default: "US") - GCS location

### 2. Python Configuration (`agents/config/storage.py`)

**Config Helpers:**
```python
get_org_storage_bucket() -> Optional[str]
is_org_storage_write_enabled() -> bool
make_portfolio_run_summary_path(run_id: str) -> str
make_portfolio_run_repo_path(run_id: str, repo_id: str) -> str
make_swe_agent_run_path(agent_name: str, run_id: str) -> str  # Future
```

**Environment Variables:**
- `ORG_STORAGE_BUCKET` - Bucket name
- `ORG_STORAGE_WRITE_ENABLED` - Must be "true" to write

### 3. GCS Writer (`agents/iam_senior_adk_devops_lead/storage_writer.py`)

**Main Function:**
```python
write_portfolio_result_to_gcs(result: PortfolioResult, *, env: str) -> None
```

**Behavior:**
- Checks: GCS library availability, feature flag, bucket name
- Writes: summary.json + per-repo/{repo_id}.json for completed repos
- Error Handling: Logs errors but does NOT crash portfolio pipeline
- Authentication: Uses Application Default Credentials (ADC)

**JSON Structure (summary.json):**
```json
{
  "portfolio_run_id": "uuid",
  "timestamp": "ISO-8601",
  "environment": "dev|staging|prod",
  "duration_seconds": 123.45,
  "summary": {
    "total_repos_analyzed": 10,
    "total_repos_skipped": 1,
    "total_repos_errored": 0,
    "total_issues_found": 42,
    "total_issues_fixed": 30,
    "fix_rate": 71.4
  },
  "issues_by_severity": { "high": 5, "medium": 20, ... },
  "issues_by_type": { "security": 10, "quality": 32 },
  "repos_by_issue_count": [...],
  "repos_by_compliance_score": [...],
  "repos": [...]
}
```

### 4. Integration Point (`portfolio_orchestrator.py`)

**After pipeline completes:**
```python
# Step 5: Write to org-wide knowledge hub (LIVE1-GCS)
if is_org_storage_write_enabled() and get_org_storage_bucket():
    print("WRITING TO ORG KNOWLEDGE HUB")
    write_portfolio_result_to_gcs(portfolio_result, env=env)
else:
    print("Org storage write disabled")
```

**Logging:**
- Enabled: Shows bucket name, run ID, success message
- Disabled: Info message with enable instructions
- Enabled but bucket not set: Warning message

---

## Usage

### Setup (One-time)

1. **Enable in Terraform:**
   ```bash
   # Edit infra/terraform/envs/dev.tfvars
   org_storage_enabled     = true
   org_storage_bucket_name = "intent-org-knowledge-hub-dev"

   # Apply Terraform (via CI/CD)
   ```

2. **Check Readiness:**
   ```bash
   python3 scripts/check_org_storage_readiness.py
   python3 scripts/check_org_storage_readiness.py --write-test
   ```

3. **Enable Writes (Runtime):**
   ```bash
   export ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev
   export ORG_STORAGE_WRITE_ENABLED=true
   ```

### Running Portfolio Audits with Org Storage

```bash
# Set environment variables
export ORG_STORAGE_BUCKET=intent-org-knowledge-hub-dev
export ORG_STORAGE_WRITE_ENABLED=true

# Run portfolio audit
python3 scripts/run_portfolio_swe.py

# Check written files
gsutil ls gs://intent-org-knowledge-hub-dev/portfolio/runs/
```

### Disabling Org Storage

```bash
# Unset or set to false
unset ORG_STORAGE_WRITE_ENABLED
# OR
export ORG_STORAGE_WRITE_ENABLED=false

# Pipeline will skip GCS writes silently
```

---

## Security

### Authentication
- Uses Application Default Credentials (ADC)
- In production: Service account from Agent Engine
- In development: `gcloud auth application-default login`

### IAM Roles
- **Writer SAs:** `roles/storage.objectAdmin`
- **Reader SAs (future):** `roles/storage.objectViewer`

### Data Protection
- Versioning enabled for audit trail
- Uniform bucket-level access (no object-level ACLs)
- Per-environment buckets (dev/staging/prod isolation)

---

## BigQuery Integration (Future - LIVE-BQ)

**Design-only in this phase. No actual BigQuery writers.**

**Planned Approach:**
1. GCS → BigQuery Data Transfer
2. Tables: `portfolio_swe_runs`, `swe_issues`, `swe_fixes`
3. Config: `ORG_AUDIT_BIGQUERY_ENABLED`, `ORG_AUDIT_DATASET`
4. Query interface for analytics and dashboards

---

## Troubleshooting

### No writes happening

**Check:**
```bash
python3 scripts/check_org_storage_readiness.py
```

**Common causes:**
- `ORG_STORAGE_WRITE_ENABLED` not set to "true"
- `ORG_STORAGE_BUCKET` not set
- google-cloud-storage not installed
- Service account lacks permissions

### Permission denied

**Check IAM:**
```bash
gcloud storage buckets get-iam-policy gs://intent-org-knowledge-hub-dev
```

**Ensure service account has:**
- `roles/storage.objectAdmin` on the bucket

### Writes failing but pipeline continues

**This is expected behavior.** Org storage write failures:
- Are logged with full context
- Do NOT crash the portfolio pipeline
- Allow pipeline to complete successfully

---

## Migration Path for Other Repos

**When integrating org storage in a new repo:**

1. Copy `agents/config/storage.py` → new repo
2. Copy `agents/{agent}/storage_writer.py` → adapt for your agent
3. Add Terraform variable section (see `infra/terraform/variables.tf`)
4. Wire writer into your orchestrator after results computed
5. Add tests (see `tests/unit/test_storage_*.py`)
6. Update repo SA in `org_storage_writer_service_accounts` list

**See:** `000-docs/000-DR-STND-iam-department-integration-checklist.md` for full checklist

---

## References

- **Terraform:** `infra/terraform/storage.tf`, `infra/terraform/variables.tf`
- **Python Config:** `agents/config/storage.py`
- **Writer:** `agents/iam_senior_adk_devops_lead/storage_writer.py`
- **Integration:** `agents/iam_senior_adk_devops_lead/portfolio_orchestrator.py`
- **Tests:** `tests/unit/test_storage_config.py`, `tests/unit/test_storage_writer.py`
- **Readiness Script:** `scripts/check_org_storage_readiness.py`
- **AAR:** `000-docs/113-AA-REPT-live1-gcs-implementation.md`

---

**Last Updated:** 2025-11-20
**Next Review:** After LIVE-BQ phase
