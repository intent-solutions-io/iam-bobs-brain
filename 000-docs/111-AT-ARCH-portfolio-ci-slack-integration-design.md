# 111-AT-ARCH-portfolio-ci-slack-integration-design.md

**Date Created:** 2025-11-20
**Category:** AT - Architecture & Technical
**Type:** ARCH - Architecture
**Status:** DESIGN (PORT3)
**Phase:** PORT3 (CI Integration + Slack Design)

---

## Executive Summary

This document defines the **CI/CD integration architecture** for portfolio-wide SWE audits in Bob's Brain, including GitHub Actions workflows, Slack notification designs, and GitHub issue automation patterns.

**Critical:** This is a **DESIGN-ONLY** document for PORT3. Actual integrations will be enabled in LIVE phases (LIVE1/LIVE2/LIVE3).

**Key Components:**
- ✅ GitHub Actions workflow (`.github/workflows/portfolio-swe.yml`) - IMPLEMENTED
- 📐 Slack message shapes - DESIGNED
- 📐 GitHub issue templates - DESIGNED
- 📐 GCS result storage patterns - DESIGNED
- ⏸️ All integrations DISABLED until LIVE phases

---

## Architecture Overview

### Integration Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                  │
│              (portfolio-swe.yml - PORT3)                   │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ Scheduled/Manual              │ On Completion
             │ Trigger                       │
             ▼                                ▼
┌────────────────────────┐      ┌──────────────────────────────┐
│  Portfolio CLI         │      │   Notification Layer         │
│  (run_portfolio_swe)   │      │   (LIVE3 - Design Only)      │
│                        │      │                              │
│  - ARV checks          │      │  - Slack webhooks            │
│  - Multi-repo audit    │      │  - GitHub issues             │
│  - JSON/MD export      │      │  - Email alerts (future)     │
└────────────┬───────────┘      └──────────────────────────────┘
             │
             │ Results
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
│                  (LIVE1+ - Design Only)                     │
│                                                             │
│  - GCS Buckets (results, reports, history)                 │
│  - BigQuery (metrics, trends)                              │
│  - Cloud Logging (audit trail)                             │
└─────────────────────────────────────────────────────────────┘
```

### Phase Progression

| Phase | Scope | Integration Status |
|-------|-------|-------------------|
| **PORT3** (Current) | Design CI/Slack patterns | All disabled (local-only) |
| **LIVE1** | Enable Vertex AI Search | GCS storage enabled |
| **LIVE2** | Enable Agent Engine calls | WIF auth, Cloud Run gateways |
| **LIVE3** | Enable Slack + GitHub issues | Full automation enabled |

---

## GitHub Actions Workflow

### Workflow File: `.github/workflows/portfolio-swe.yml`

**Location:** `.github/workflows/portfolio-swe.yml`
**Status:** IMPLEMENTED ✅
**Integration Status:** Local-only (PORT3)

#### Triggers

1. **Scheduled (Nightly)**
   - Cron: `0 2 * * *` (2 AM UTC daily)
   - Runs on all local repos by default
   - Mode: `preview` (read-only)

2. **Manual (Workflow Dispatch)**
   - Inputs:
     - `repos` (string, default: "all") - Repo IDs to audit
     - `mode` (choice: preview/dry-run/create) - Pipeline mode
     - `tag` (string, optional) - Filter by repo tag
     - `environment` (choice: dev/staging/prod) - Target environment

#### Job: `portfolio-audit`

**Runs on:** `ubuntu-latest`
**Environment:** Input-driven or 'dev'

**Steps:**

1. **Checkout code** - `actions/checkout@v4`
2. **Set up Python 3.12** - `actions/setup-python@v5`
3. **Install dependencies** - `pip install -r requirements.txt`
4. **Run ARV portfolio check** - `make check-arv-portfolio`
5. **Run portfolio SWE audit** - `python3 scripts/run_portfolio_swe.py`
6. **Upload JSON results** - Artifact: `portfolio-results-json` (90 days)
7. **Upload Markdown report** - Artifact: `portfolio-report-md` (90 days)
8. **Generate summary** - GitHub Actions summary page
9. **Fail if threshold exceeded** - Exit 1 if > 10 issues found

#### Disabled Steps (LIVE Phases)

**LIVE1+: GCS Upload**
```yaml
# - name: Upload results to GCS
#   run: |
#     gsutil cp portfolio-results.json gs://$BUCKET/results/$RUN_ID/results.json
#     gsutil cp portfolio-report.md gs://$BUCKET/results/$RUN_ID/report.md
```

**LIVE3: Slack Notification**
```yaml
# - name: Send Slack notification
#   run: |
#     curl -X POST -H 'Content-type: application/json' \
#       --data @slack-message.json \
#       "$SLACK_WEBHOOK_URL"
```

**LIVE3: GitHub Issue Creation**
```yaml
# - name: Create GitHub issues
#   run: |
#     jq -r '.repos[] | ... | @json' portfolio-results.json | while read issue; do
#       gh issue create --title "..." --body "..." --label "..."
#     done
```

---

## Slack Integration Design

### Message Types

#### 1. Portfolio Audit Complete (Primary)

**Trigger:** On workflow completion (success or failure)
**Channel:** `#bobs-brain-portfolio` (or repo-specific channels)
**Frequency:** After each nightly audit + manual runs

**Message Shape:**
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📊 Portfolio SWE Audit Complete",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Environment:*\ndev"
        },
        {
          "type": "mrkdwn",
          "text": "*Run ID:*\nc98cc8f2-bc2d"
        },
        {
          "type": "mrkdwn",
          "text": "*Duration:*\n0.33s"
        },
        {
          "type": "mrkdwn",
          "text": "*Timestamp:*\n2025-11-20 03:52 UTC"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Repos Analyzed:*\n✅ 1"
        },
        {
          "type": "mrkdwn",
          "text": "*Repos Skipped:*\n⏭️ 4"
        },
        {
          "type": "mrkdwn",
          "text": "*Repos Errored:*\n❌ 0"
        },
        {
          "type": "mrkdwn",
          "text": "*Total Issues:*\n🔍 3"
        }
      ]
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Issues Fixed:*\n✅ 2"
        },
        {
          "type": "mrkdwn",
          "text": "*Fix Rate:*\n📈 66.7%"
        },
        {
          "type": "mrkdwn",
          "text": "*Critical Issues:*\n🚨 0"
        },
        {
          "type": "mrkdwn",
          "text": "*High Issues:*\n⚠️ 0"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Top Repos by Issue Count:*\n1️⃣ bobs-brain (3 issues)\n2️⃣ diagnosticpro (0 issues - skipped)\n3️⃣ pipelinepilot (0 issues - skipped)"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Issues by Severity:*\n• Medium: 1\n• Low: 2"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Issues by Type:*\n• adk_violation: 2\n• missing_doc: 1"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View GitHub Run",
            "emoji": true
          },
          "url": "https://github.com/jeremylongshore/bobs-brain/actions/runs/123456",
          "action_id": "view_run"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "Download JSON",
            "emoji": true
          },
          "url": "https://github.com/jeremylongshore/bobs-brain/actions/runs/123456/artifacts/456789",
          "action_id": "download_json"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "Download Report",
            "emoji": true
          },
          "url": "https://github.com/jeremylongshore/bobs-brain/actions/runs/123456/artifacts/456790",
          "action_id": "download_report"
        }
      ]
    }
  ]
}
```

#### 2. Critical Issue Alert (High-Priority)

**Trigger:** When critical/high severity issues detected
**Channel:** `#bobs-brain-alerts` (high-priority channel)
**Frequency:** Immediate (within workflow)

**Message Shape:**
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚨 Critical Portfolio Issues Detected",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Portfolio audit found critical/high severity issues requiring immediate attention.*"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Repository:*\nbobs-brain"
        },
        {
          "type": "mrkdwn",
          "text": "*Severity:*\n🚨 CRITICAL"
        },
        {
          "type": "mrkdwn",
          "text": "*Issue Count:*\n3"
        },
        {
          "type": "mrkdwn",
          "text": "*Environment:*\nproduction"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Issue Summary:*\n• Security vulnerability in agent.py\n• Missing ARV compliance checks\n• Drift from ADK patterns detected"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View Full Report",
            "emoji": true
          },
          "url": "https://github.com/jeremylongshore/bobs-brain/actions/runs/123456",
          "style": "danger",
          "action_id": "view_report"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "Create Fix Plan",
            "emoji": true
          },
          "url": "https://github.com/jeremylongshore/bobs-brain/issues/new?template=fix-plan.md",
          "action_id": "create_fix"
        }
      ]
    }
  ]
}
```

#### 3. Weekly Trend Summary (Aggregate)

**Trigger:** Weekly scheduled job (Sundays, 10 AM UTC)
**Channel:** `#bobs-brain-portfolio`
**Frequency:** Weekly

**Message Shape:**
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📈 Weekly Portfolio Trends",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Portfolio health summary for week of Nov 13-20, 2025*"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Total Audits:*\n7 runs"
        },
        {
          "type": "mrkdwn",
          "text": "*Avg Issues/Run:*\n4.2"
        },
        {
          "type": "mrkdwn",
          "text": "*Avg Fix Rate:*\n72.5%"
        },
        {
          "type": "mrkdwn",
          "text": "*Trend:*\n📉 -12% issues"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Repos Analyzed:*\n• bobs-brain: 7 audits, 3.2 avg issues\n• diagnosticpro: 0 audits (external)\n• pipelinepilot: 0 audits (external)"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Top Issue Types:*\n1. adk_violation (14 occurrences)\n2. missing_doc (8 occurrences)\n3. test_coverage (5 occurrences)"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View Dashboard",
            "emoji": true
          },
          "url": "https://console.cloud.google.com/...",
          "action_id": "view_dashboard"
        }
      ]
    }
  ]
}
```

### Slack Webhook Configuration

**Environment Variables:**
```bash
# LIVE3 - Slack integration
SLACK_WEBHOOK_URL_PORTFOLIO=https://hooks.slack.com/services/T.../B.../...
SLACK_WEBHOOK_URL_ALERTS=https://hooks.slack.com/services/T.../B.../...
SLACK_BOT_TOKEN=xoxb-...  # For interactive features (future)
```

**GitHub Secrets:**
- `SLACK_WEBHOOK_URL` - Primary portfolio channel
- `SLACK_ALERT_WEBHOOK_URL` - High-priority alerts channel

**Channel Mapping:**
```yaml
# Repo-specific channels (from repos.yaml)
bobs-brain:
  slack_channel: "#bobs-brain-portfolio"
diagnosticpro:
  slack_channel: "#diagnosticpro-alerts"
pipelinepilot:
  slack_channel: "#pipelinepilot-ops"
```

---

## GitHub Issue Automation

### Issue Templates

#### Template 1: Portfolio Audit Finding

**File:** `.github/ISSUE_TEMPLATE/portfolio-finding.md`
**Status:** DESIGN (LIVE3)

```markdown
---
name: Portfolio Audit Finding
about: Automated issue from portfolio SWE audit
title: '[{{repo_id}}] {{issue_title}}'
labels: portfolio-audit, {{severity}}, automated
assignees: ''
---

## Portfolio Audit Finding

**Generated by:** Portfolio SWE Audit
**Run ID:** {{portfolio_run_id}}
**Timestamp:** {{timestamp}}
**Repository:** {{repo_id}} ({{display_name}})

---

### Issue Details

**Severity:** {{severity}}
**Type:** {{issue_type}}
**Location:** {{file_path}}:{{line_number}}

### Description

{{issue_description}}

### Recommendation

{{fix_suggestion}}

### Context

- **Total Issues Found:** {{total_issues}}
- **Portfolio Fix Rate:** {{fix_rate}}%
- **Similar Issues:** {{similar_count}} other repos

---

### Automated Actions

- [ ] iam-senior-adk-devops-lead to triage
- [ ] iam-adk to analyze ADK compliance
- [ ] iam-fix-plan to create fix plan
- [ ] iam-fix-impl to implement fix
- [ ] iam-qa to validate fix

---

**Links:**
- [Full Portfolio Report](https://github.com/jeremylongshore/bobs-brain/actions/runs/{{run_id}})
- [JSON Results](https://github.com/jeremylongshore/bobs-brain/actions/runs/{{run_id}}/artifacts/{{artifact_id}})
```

### Issue Creation Logic

**Criteria for Automated Issue Creation (LIVE3):**

1. **Severity Threshold:**
   - CRITICAL: Always create issue
   - HIGH: Create if not duplicate
   - MEDIUM: Create if recurring (>3 audits)
   - LOW: Aggregate into weekly summary

2. **Duplicate Detection:**
   - Check existing issues by title pattern
   - Search for `[{{repo_id}}] {{issue_title}}`
   - If found: Add comment with new occurrence
   - If not found: Create new issue

3. **Label Strategy:**
   - `portfolio-audit` (all automated issues)
   - `{{severity}}` (critical/high/medium/low)
   - `automated` (machine-generated)
   - `{{issue_type}}` (adk_violation, missing_doc, etc.)
   - `{{repo_id}}` (source repository)

4. **Assignment:**
   - CRITICAL/HIGH: Assign to `@iam-senior-adk-devops-lead` (human proxy)
   - MEDIUM: Add to project board, no assignment
   - LOW: No auto-assignment

### GitHub API Integration

**Required Permissions:**
```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write  # For future PR automation
```

**Example API Call (LIVE3):**
```bash
gh issue create \
  --title "[bobs-brain] ADK pattern violation in agent.py" \
  --body "$(cat issue-template.md)" \
  --label "portfolio-audit,high,automated,adk_violation,bobs-brain" \
  --assignee "iam-senior-adk-devops-lead"
```

---

## Storage Layer Design

### GCS Bucket Structure (LIVE1+)

**Bucket:** `gs://bobs-brain-portfolio-results/`
**Lifecycle:** 90-day retention for detailed results, indefinite for summaries

```
gs://bobs-brain-portfolio-results/
├── results/
│   ├── 2025-11-20/
│   │   ├── c98cc8f2-bc2d-4db1-aa7d-9d21e0ce92a9/
│   │   │   ├── portfolio-results.json
│   │   │   ├── portfolio-report.md
│   │   │   └── per-repo/
│   │   │       ├── bobs-brain.json
│   │   │       ├── diagnosticpro.json (skipped)
│   │   │       └── pipelinepilot.json (skipped)
│   │   └── summary.json (daily aggregate)
│   └── 2025-11-19/
│       └── ...
├── trends/
│   ├── weekly/
│   │   ├── 2025-W47.json
│   │   └── 2025-W46.json
│   ├── monthly/
│   │   ├── 2025-11.json
│   │   └── 2025-10.json
│   └── annual/
│       └── 2025.json
└── exports/
    ├── bigquery/  # For BigQuery imports
    └── dashboards/  # For dashboard data
```

### BigQuery Schema (LIVE2+)

**Dataset:** `bobs_brain_analytics`

#### Table: `portfolio_audit_runs`
```sql
CREATE TABLE `bobs_brain_analytics.portfolio_audit_runs` (
  portfolio_run_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  duration_seconds FLOAT64,
  environment STRING,  -- dev/staging/prod
  triggered_by STRING,  -- schedule/manual/pr

  total_repos_analyzed INT64,
  total_repos_skipped INT64,
  total_repos_errored INT64,
  total_issues_found INT64,
  total_issues_fixed INT64,
  fix_rate FLOAT64,

  repo_ids ARRAY<STRING>,
  tags ARRAY<STRING>,

  github_run_id STRING,
  github_run_url STRING
) PARTITION BY DATE(timestamp);
```

#### Table: `portfolio_issues`
```sql
CREATE TABLE `bobs_brain_analytics.portfolio_issues` (
  issue_id STRING NOT NULL,
  portfolio_run_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,

  repo_id STRING NOT NULL,
  repo_display_name STRING,

  severity STRING,  -- critical/high/medium/low
  issue_type STRING,  -- adk_violation/missing_doc/test_coverage/etc
  title STRING,
  description STRING,
  file_path STRING,
  line_number INT64,

  fixed BOOLEAN,
  fix_suggestion STRING,

  github_issue_url STRING,  -- If issue created
  slack_message_ts STRING   -- If notified
) PARTITION BY DATE(timestamp);
```

### Upload Pattern (LIVE1+)

**Workflow Step:**
```yaml
- name: Upload results to GCS
  env:
    BUCKET: ${{ secrets.PORTFOLIO_RESULTS_BUCKET }}
    RUN_ID: ${{ github.run_id }}
  run: |
    # Extract portfolio run ID from results
    PORTFOLIO_RUN_ID=$(jq -r '.portfolio_run_id' portfolio-results.json)
    DATE=$(date +%Y-%m-%d)

    # Create directory structure
    gsutil -m cp portfolio-results.json \
      "gs://$BUCKET/results/$DATE/$PORTFOLIO_RUN_ID/portfolio-results.json"

    gsutil -m cp portfolio-report.md \
      "gs://$BUCKET/results/$DATE/$PORTFOLIO_RUN_ID/portfolio-report.md"

    # Upload per-repo results (future enhancement)
    # for repo in $(jq -r '.repos[].repo_id' portfolio-results.json); do
    #   jq ".repos[] | select(.repo_id == \"$repo\")" portfolio-results.json > "$repo.json"
    #   gsutil cp "$repo.json" "gs://$BUCKET/results/$DATE/$PORTFOLIO_RUN_ID/per-repo/$repo.json"
    # done

    # Create daily summary
    jq '{
      date: "'"$DATE"'",
      portfolio_run_id: .portfolio_run_id,
      summary: .summary
    }' portfolio-results.json > daily-summary.json

    gsutil cp daily-summary.json "gs://$BUCKET/results/$DATE/summary.json"
```

---

## Security & Permissions

### Workload Identity Federation (WIF)

**Required for:** LIVE1+ (GCS uploads, BigQuery writes)

**Configuration:**
```yaml
permissions:
  contents: read
  id-token: write  # For WIF authentication
  issues: write    # For issue creation (LIVE3)
```

**Authentication Step:**
```yaml
- name: Authenticate to GCP (Workload Identity Federation)
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
```

### Required GitHub Secrets

| Secret | Purpose | Phase |
|--------|---------|-------|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF authentication | LIVE1+ |
| `GCP_SERVICE_ACCOUNT` | Service account email | LIVE1+ |
| `PROJECT_ID` | GCP project ID | LIVE1+ |
| `PORTFOLIO_RESULTS_BUCKET` | GCS bucket name | LIVE1+ |
| `SLACK_WEBHOOK_URL` | Slack notifications | LIVE3 |
| `SLACK_ALERT_WEBHOOK_URL` | High-priority alerts | LIVE3 |

### IAM Roles Required

**Service Account Permissions:**
- `roles/storage.objectCreator` (GCS uploads)
- `roles/bigquery.dataEditor` (BigQuery writes)
- `roles/logging.logWriter` (Audit logs)

**GitHub Actions Role Bindings:**
```terraform
resource "google_service_account_iam_member" "github_actions_wif" {
  service_account_id = google_service_account.portfolio_auditor.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${var.workload_identity_pool_id}/attribute.repository/${var.github_repo}"
}
```

---

## Testing Strategy

### PORT3 Testing (Design Phase)

**Scope:** Validate workflow structure without live integrations

**Tests:**
1. **Workflow Syntax Validation:**
   ```bash
   yamllint .github/workflows/portfolio-swe.yml
   actionlint .github/workflows/portfolio-swe.yml
   ```

2. **Local Dry-Run:**
   ```bash
   # Simulate workflow steps locally
   python3 scripts/run_portfolio_swe.py --repos bobs-brain --mode preview \
     --output /tmp/portfolio-results.json --markdown /tmp/portfolio-report.md

   # Verify outputs
   test -f /tmp/portfolio-results.json
   test -f /tmp/portfolio-report.md
   jq '.summary.total_repos_analyzed' /tmp/portfolio-results.json
   ```

3. **Manual Workflow Trigger:**
   ```bash
   # Trigger workflow via GitHub CLI
   gh workflow run portfolio-swe.yml \
     --ref main \
     --field repos=bobs-brain \
     --field mode=preview \
     --field environment=dev

   # Watch run
   gh run watch
   ```

### LIVE1 Testing (GCS Integration)

**Scope:** Validate storage layer

**Tests:**
1. **GCS Upload Validation:**
   ```bash
   # Run workflow and verify uploads
   gsutil ls gs://bobs-brain-portfolio-results/results/$(date +%Y-%m-%d)/

   # Verify file structure
   gsutil cat gs://.../portfolio-results.json | jq '.summary'
   ```

2. **BigQuery Import:**
   ```bash
   # Load results into BigQuery
   bq load --source_format=NEWLINE_DELIMITED_JSON \
     bobs_brain_analytics.portfolio_audit_runs \
     gs://.../portfolio-results.json

   # Query results
   bq query --use_legacy_sql=false \
     'SELECT portfolio_run_id, total_issues_found FROM bobs_brain_analytics.portfolio_audit_runs ORDER BY timestamp DESC LIMIT 10'
   ```

### LIVE3 Testing (Full Integration)

**Scope:** Validate Slack + GitHub issues

**Tests:**
1. **Slack Message Validation:**
   ```bash
   # Test webhook with sample payload
   curl -X POST -H 'Content-type: application/json' \
     --data @test-slack-message.json \
     "$SLACK_WEBHOOK_URL"
   ```

2. **GitHub Issue Creation:**
   ```bash
   # Test issue creation with sample data
   gh issue create \
     --title "[TEST] Portfolio audit finding" \
     --body "Test issue from integration testing" \
     --label "portfolio-audit,test,automated"

   # Verify and close
   gh issue list --label "portfolio-audit,test"
   gh issue close <issue-number>
   ```

3. **End-to-End Workflow:**
   ```bash
   # Run full workflow in staging environment
   gh workflow run portfolio-swe.yml \
     --ref main \
     --field repos=bobs-brain \
     --field mode=preview \
     --field environment=staging

   # Verify:
   # - Workflow completes successfully
   # - GCS files uploaded
   # - Slack message received
   # - No GitHub issues created (mode=preview)
   ```

---

## Rollout Plan

### Phase Timeline

| Phase | Timeframe | Deliverables |
|-------|-----------|--------------|
| **PORT3** (Current) | Week 1 | Workflow + design docs (this document) ✅ |
| **LIVE1** | Week 2-3 | Enable GCS storage, BigQuery integration |
| **LIVE2** | Week 4-5 | Enable Vertex AI Search, Agent Engine calls |
| **LIVE3** | Week 6+ | Enable Slack notifications, GitHub issues |

### Rollout Checklist

**PORT3 (Complete) ✅**
- [x] GitHub Actions workflow created
- [x] Slack message shapes designed
- [x] GitHub issue templates designed
- [x] Storage layer architecture defined
- [x] Design document created (this doc)
- [x] All integrations commented out / disabled

**LIVE1 (Pending)**
- [ ] Create GCS bucket `bobs-brain-portfolio-results`
- [ ] Set up WIF authentication
- [ ] Configure GitHub secrets (GCP_*, PROJECT_ID, BUCKET)
- [ ] Uncomment GCS upload steps in workflow
- [ ] Test GCS uploads in staging
- [ ] Set up BigQuery dataset and tables
- [ ] Configure lifecycle policies (90-day retention)
- [ ] Validate storage layer in production

**LIVE2 (Pending)**
- [ ] Enable Vertex AI Search in portfolio CLI
- [ ] Enable Agent Engine calls (if needed)
- [ ] Update WIF permissions for Vertex AI
- [ ] Test with real ADK docs retrieval
- [ ] Validate multi-repo Agent Engine integration

**LIVE3 (Pending)**
- [ ] Set up Slack workspace and channels
- [ ] Create Slack app and webhooks
- [ ] Configure GitHub secrets (SLACK_*)
- [ ] Uncomment Slack notification steps
- [ ] Test Slack messages in staging channel
- [ ] Set up GitHub issue templates
- [ ] Uncomment issue creation steps
- [ ] Test issue creation in staging repo
- [ ] Configure duplicate detection logic
- [ ] Enable weekly trend summaries
- [ ] Full end-to-end testing in production

---

## Monitoring & Alerting

### Workflow Monitoring (LIVE1+)

**Metrics to Track:**
- Workflow success/failure rate
- Average run duration
- Issue detection rate (issues per repo)
- Fix rate trends over time
- GCS upload failures
- BigQuery load errors

**GitHub Actions Built-in:**
- Workflow run history
- Artifact retention
- Step-level timing
- Failure notifications (built-in)

### Cloud Monitoring (LIVE2+)

**Dashboards:**
1. **Portfolio Health Dashboard**
   - Total repos tracked
   - Local vs external repos
   - Issues by severity (time series)
   - Fix rate trends
   - Top repos by issue count

2. **Integration Health Dashboard**
   - GCS upload success rate
   - BigQuery load latency
   - Slack notification delivery
   - GitHub issue creation rate

**Alerts:**
1. **Critical Issue Alert**
   - Trigger: Critical/high severity issues detected
   - Notification: Slack + email
   - Escalation: After 2 hours if not acknowledged

2. **Workflow Failure Alert**
   - Trigger: Portfolio workflow fails
   - Notification: Slack + email
   - Escalation: After 1 failure

3. **Trend Degradation Alert**
   - Trigger: Fix rate drops below 50% for 7 days
   - Notification: Slack weekly summary
   - Escalation: Manual review required

---

## Related Documentation

### PORT Series
- `109-PP-PLAN-multi-repo-swe-portfolio-scope.md` - PORT1/PORT2/PORT3 plan
- `110-AA-REPT-portfolio-orchestrator-implementation.md` - PORT2 AAR
- `111-AT-ARCH-portfolio-ci-slack-integration-design.md` - This document (PORT3)

### Operational Standards
- `094-AT-ARCH-iam-swe-pipeline-orchestration.md` - Single-repo pipeline
- `096-DR-STND-repo-registry-and-target-selection.md` - Registry standard
- `000-DR-STND-arv-minimum-gate.md` - ARV minimum gate

---

## Conclusion

This design document provides a comprehensive blueprint for CI/CD integration and Slack notifications for portfolio-wide SWE audits in Bob's Brain.

**Key Achievements:**
- 🎯 GitHub Actions workflow implemented and tested (PORT3)
- 📐 Slack message shapes designed for all scenarios
- 📐 GitHub issue templates and automation logic defined
- 📐 Storage layer architecture (GCS + BigQuery) designed
- 📐 Security and permissions model defined
- 📐 Testing strategy and rollout plan established

**Status:** PORT3 DESIGN COMPLETE ✅
**Next Phase:** LIVE1 (GCS Integration)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-20
**Status:** Design Complete (PORT3)
**Owner:** iam-senior-adk-devops-lead
**Phase:** PORT3 → LIVE1

---

**Timestamp:** 2025-11-20T05:00:00Z
