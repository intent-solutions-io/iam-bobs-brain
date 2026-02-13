# CI/CD Pipeline Standard for IAM Department

**Document Number:** 118-DR-STND-cicd-pipeline-for-iam-department
**Status:** Active
**Date:** 2025-11-20
**Phase:** CICD-DEPT
**Author:** Build Captain (Claude)

---

## Executive Summary

This document defines the **canonical CI/CD pipeline pattern** for IAM/ADK departments using GitHub Actions, Vertex AI Agent Engine, and Workload Identity Federation. This pattern is **copy-pasteable to any new IAM department repo**.

**Key Components:**
- **ci.yml** - Checks-only workflow (drift, ARV, tests, security)
- **deploy-dev.yml** - Dev deployment with ARV gate
- **deploy-staging.yml** - Staging with manual approval
- **deploy-prod.yml** - Production with multiple approvals and strict ARV
- **Makefile targets** - Developer-friendly deployment commands

**Design Principles:**
1. **CI separates from CD** - Checks in ci.yml, deploys in deploy-*.yml
2. **ARV gates everything** - No deployment without ARV passing
3. **Environment-aware** - Different configs per environment (dev/staging/prod)
4. **WIF authentication** - No service account keys (R4 compliant)
5. **Manual approvals** - Staging/prod require explicit approval
6. **Reusable pattern** - Copy to any IAM department repo

---

## Architecture Overview

### Workflow Dependency Graph

```
┌─────────────────────┐
│      ci.yml         │  ← Runs on: push/PR to main/develop
│   (checks only)    │
│                     │
│ - drift-check       │  ← R8: Hard Mode violations
│ - arv-check         │  ← ARV minimum + engine flags
│ - arv-department    │  ← ARV-DEPT comprehensive gate
│ - lint/test/sec     │
│ - terraform-validate│
│ - docs/structure    │
│ - ci-success        │  ← Summary job
└──────────┬──────────┘
           │
           │ requires: ci-success or runs ARV inline
           ├────────────────┬───────────────┬─────────────────┐
           │                │               │                 │
           ▼                ▼               ▼                 ▼
┌──────────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ deploy-dev.yml   │ │deploy-stg.yml│ │deploy-prod.yml│ │ release.yml │
│                  │ │              │ │              │ │             │
│ - ARV gate       │ │ - ARV gate   │ │ - ARV gate   │ │ Independent │
│ - Deploy Engine  │ │ - Approval   │ │ - Approvals  │ │ automation  │
│ - Deploy gateways│ │ - Deploy Eng │ │ - Deploy Eng │ └─────────────┘
│ - Verify health  │ │ - + gateways │ │ - + gateways │
└──────────────────┘ └─────────────┘ └──────────────┘
```

### File Structure

```
.github/workflows/
├── ci.yml                   # Main CI checks (no deploy logic)
├── deploy-dev.yml           # Dev deployment with ARV gate
├── deploy-staging.yml       # Staging with approval gate
├── deploy-prod.yml          # Prod with multiple approvals
├── portfolio-swe.yml        # Specialized (multi-repo audit)
└── release.yml              # Version automation

Makefile
├── deploy-dev               # Trigger dev deploy
├── deploy-staging           # Trigger staging deploy
├── deploy-prod              # Trigger prod deploy (with confirmation)
├── deploy-status            # Check deployment status
├── deploy-logs              # View deployment logs
├── deploy-list              # List all deploy workflows
└── deploy-help              # Show deployment help
```

---

## Workflow Details

### 1. ci.yml - Main CI Pipeline

**Purpose:** Comprehensive checks gate that blocks bad code
**Triggers:** Push to main/develop/feature/**, PRs to main/develop
**Badge:** `[![CI](https://github.com/user/repo/workflows/CI%20-%20Hard%20Mode/badge.svg)](https://github.com/user/repo/actions/workflows/ci.yml)`

**Jobs (in dependency order):**

1. **drift-check** (first, blocks all if violations)
   - R8 compliance: No alternative frameworks, no Runner in gateways
   - Exit code 1 blocks all downstream jobs

2. **arv-check** (ARV minimum + engine flags)
   - Validates minimum structural requirements
   - Validates Agent Engine flags safety

3. **arv-department** (comprehensive ARV)
   - Runs `make arv-department`
   - 7 checks across 5 categories (config, tests, RAG, engine, storage)
   - Feature-gated (conditional requirements)

4. **lint, test, security** (only if drift + ARV pass)
   - Flake8, Black, mypy
   - pytest (unit, integration)
   - Bandit, safety

5. **terraform-validate, documentation-check, structure-validation**

6. **ci-success** (summary job)
   - Depends on all previous jobs
   - Outputs clear "ready for deployment" message
   - Other workflows can depend on this job

**Key Features:**
- ✅ Checks-only (no deployment logic)
- ✅ ARV-DEPT integrated
- ✅ Clear dependency chain
- ✅ Blocks bad code early

---

### 2. deploy-dev.yml - Dev Environment Deployment

**Purpose:** Deploy to dev environment (Agent Engine + gateways)
**Triggers:** Manual dispatch ONLY (workflow_dispatch)
**Environment:** `dev` (GitHub environment with protection rules)

**Jobs (in order):**

1. **arv-gate** - ARV Readiness Gate (Dev)
   - Runs `make arv-department` with `DEPLOYMENT_ENV=dev`
   - Can be skipped with `skip_arv: true` input (emergencies only)
   - Blocks deployment if any required checks fail

2. **deploy-agent-engine** - Deploy Agent Engine (Dev)
   - WIF authentication (R4 compliant)
   - ADK CLI deployment: `adk deploy agent_engine agents/bob`
   - Uses dev-specific configs: `DEV_PROJECT_ID`, `DEV_REGION`, `DEV_STAGING_BUCKET`
   - Outputs links to GCP Console (Agent Engine, Trace, Monitoring)

3. **deploy-gateways** - Deploy Cloud Run Gateways (Dev)
   - Deploys Slack webhook to Cloud Run
   - Uses dev-specific service name: `slack-webhook-dev`
   - Verifies deployment with endpoint test
   - Requires Agent Engine deployment to succeed first

4. **deployment-success** - Deployment Summary (Dev)
   - Checks all job statuses
   - Outputs comprehensive summary
   - Fails if any component failed
   - Shows post-deployment steps

**Environment Variables (GitHub Environment: `dev`):**
- `DEV_PROJECT_ID` - GCP project for dev
- `DEV_REGION` - GCP region (e.g., us-central1)
- `DEV_STAGING_BUCKET` - GCS bucket for ADK staging

**GitHub Secrets (Organization or Repository):**
- `GCP_WORKLOAD_IDENTITY_PROVIDER` - WIF provider ID
- `GCP_SERVICE_ACCOUNT` - Service account email
- `SLACK_SIGNING_SECRET` - Slack signing secret
- `SLACK_BOT_TOKEN` - Slack bot token

**Usage:**
```bash
# Via Makefile (recommended)
make deploy-dev

# Via GitHub CLI
gh workflow run deploy-dev.yml

# Via GitHub UI
Actions → Deploy to Dev → Run workflow
```

---

### 3. deploy-staging.yml - Staging Environment Deployment (Skeleton)

**Purpose:** Deploy to staging with manual approval and stricter checks
**Triggers:** Manual dispatch ONLY
**Environment:** `staging` (requires manual approval)

**Status:** 🚧 SKELETON - Full implementation pending

**Planned Jobs:**
1. **arv-gate** - Stricter ARV checks for staging
2. **approval-gate** - Manual approval checkpoint
3. **deploy-agent-engine** - Deploy to staging project
4. **deploy-gateways** - Deploy gateways to staging
5. **smoke-tests** - Optional post-deployment smoke tests
6. **deployment-success** - Summary

**Staging-Specific Requirements:**
- ✅ Manual approval required (configured in GitHub Environment)
- ✅ Stricter ARV thresholds (zero warnings)
- ✅ Comprehensive smoke tests after deployment
- ✅ Rollback procedures documented

---

### 4. deploy-prod.yml - Production Environment Deployment (Skeleton)

**Purpose:** Deploy to production with multiple approvals and strictest checks
**Triggers:** Manual dispatch ONLY
**Environment:** `prod` (requires multiple approvals)

**Status:** 🚧 SKELETON - Full implementation pending

**Planned Jobs:**
1. **pre-deployment-checks** - Verify production readiness (git tag, changelog, etc.)
2. **arv-gate** - STRICTEST ARV checks (zero tolerance)
3. **approval-gate-1** - Engineering Lead approval
4. **approval-gate-2** - Manager/Director approval
5. **deploy-agent-engine** - Deploy to production project (blue/green or canary)
6. **deploy-gateways** - Deploy gateways with gradual traffic shift
7. **post-deployment-tests** - Comprehensive test suite
8. **rollback** - Automated rollback on failure
9. **deployment-success** - Summary

**Production-Specific Requirements:**
- ✅ Multiple manual approvals (2+ levels)
- ✅ Zero tolerance for ARV failures
- ✅ Blue/green or canary deployment strategy
- ✅ Automated rollback on failure
- ✅ Comprehensive post-deployment tests
- ✅ Production monitoring and alerting

---

## Makefile Targets (Developer Interface)

### Deployment Triggers

```bash
# Deploy to dev (with confirmation prompt)
make deploy-dev

# Deploy to staging (with confirmation prompt)
make deploy-staging

# Deploy to prod (requires typing "DEPLOY_TO_PRODUCTION")
make deploy-prod
```

### Deployment Monitoring

```bash
# Check deployment workflow status (all environments)
make deploy-status

# View logs from latest deployment
make deploy-logs ENV=dev
make deploy-logs ENV=staging
make deploy-logs ENV=prod

# List all deployment workflows
make deploy-list

# Show deployment help and requirements
make deploy-help
```

---

## Environment-Aware Configuration

### GitHub Environments

**Create GitHub Environments:**
1. Go to repo Settings → Environments
2. Create environments: `dev`, `staging`, `prod`
3. Configure protection rules per environment

**Dev Environment:**
- Protection rules: None (automatic deployment after ARV)
- Secrets: None (uses org-level secrets)
- Variables:
  - `DEV_PROJECT_ID`
  - `DEV_REGION`
  - `DEV_STAGING_BUCKET`

**Staging Environment:**
- Protection rules:
  - ✅ Required reviewers: 1
  - ✅ Deployment branches: main only
- Variables:
  - `STAGING_PROJECT_ID`
  - `STAGING_REGION`
  - `STAGING_STAGING_BUCKET`

**Prod Environment:**
- Protection rules:
  - ✅ Required reviewers: 2+ (different teams)
  - ✅ Deployment branches: main only
  - ✅ Wait timer: 5 minutes (cooling period)
- Variables:
  - `PROD_PROJECT_ID`
  - `PROD_REGION`
  - `PROD_STAGING_BUCKET`

### Workload Identity Federation (WIF) Setup

**Required GitHub Secrets (Organization or Repository level):**

1. **GCP_WORKLOAD_IDENTITY_PROVIDER**
   ```
   projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
   ```

2. **GCP_SERVICE_ACCOUNT**
   ```
   github-actions@PROJECT_ID.iam.gserviceaccount.com
   ```

**Setup Steps:**
```bash
# 1. Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

# 2. Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == 'user/repo'"

# 3. Create Service Account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

# 4. Grant IAM Permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# 5. Allow GitHub to impersonate service account
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@PROJECT_ID.iam.gserviceaccount.com \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/user/repo" \
  --role="roles/iam.workloadIdentityUser"
```

---

## ARV Gate Integration

All deployment workflows MUST include an ARV gate:

### Implementation Pattern

```yaml
arv-gate:
  name: ARV Readiness Gate (Dev)
  runs-on: ubuntu-latest
  if: github.event.inputs.skip_arv != 'true'  # Optional emergency skip

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest

    - name: Run ARV Department Check
      run: make arv-department
      env:
        DEPLOYMENT_ENV: dev  # or staging, prod

deploy-agent-engine:
  needs: [arv-gate]
  if: always() && (needs.arv-gate.result == 'success' || needs.arv-gate.result == 'skipped')
  # ... deployment logic
```

**Why ARV Gates Are Critical:**
- ✅ Prevents deploying broken code
- ✅ Validates configuration before deployment
- ✅ Ensures tests pass in target environment
- ✅ Verifies feature flags and conditional requirements
- ✅ Checks RAG, storage, notifications when enabled

---

## Deployment Flow (End-to-End)

### Development to Production

```
1. Developer pushes code to feature branch
   ↓
2. Opens PR to main/develop
   ↓
3. ci.yml runs automatically
   - Drift check (R8)
   - ARV-DEPT (comprehensive)
   - Lint, test, security
   - All checks must pass ✅
   ↓
4. PR merged to main
   ↓
5. ci.yml runs again on main (post-merge validation)
   ↓
6. Developer triggers dev deployment
   → make deploy-dev
   OR
   → gh workflow run deploy-dev.yml
   ↓
7. deploy-dev.yml runs
   - ARV gate (dev-specific checks)
   - Deploy Agent Engine to dev project
   - Deploy gateways to dev Cloud Run
   - Verify health
   ↓
8. Test in dev environment
   - Manual testing
   - Smoke tests
   - Integration tests
   ↓
9. If dev tests pass, trigger staging deployment
   → make deploy-staging
   ↓
10. deploy-staging.yml runs
    - ARV gate (stricter checks)
    - Manual approval required ⏸️
    - Deploy to staging project
    - Run smoke tests
    ↓
11. Test in staging environment
    - Full QA testing
    - Performance testing
    - Security testing
    ↓
12. If staging tests pass, trigger prod deployment
    → make deploy-prod (requires typing "DEPLOY_TO_PRODUCTION")
    ↓
13. deploy-prod.yml runs
    - Pre-deployment checks (git tag, changelog, etc.)
    - ARV gate (zero tolerance)
    - Engineering Lead approval ⏸️
    - Manager/Director approval ⏸️
    - Blue/green or canary deployment
    - Post-deployment tests
    - Automated rollback on failure
    ↓
14. Production deployment complete ✅
    - Monitor for errors
    - Update documentation
    - Notify team
```

---

## Troubleshooting

### "ARV gate failed - deployment blocked"

**Problem:** ARV checks failed, blocking deployment

**Solution:**
1. Run ARV locally: `make arv-department-verbose`
2. Fix failing checks
3. Re-trigger deployment

### "GitHub CLI not found"

**Problem:** `make deploy-*` fails with "gh not installed"

**Solution:**
```bash
# Install GitHub CLI
# macOS: brew install gh
# Linux: https://cli.github.com/manual/installation

# Authenticate
gh auth login
```

### "Workflow not found"

**Problem:** `gh workflow run` fails with "workflow not found"

**Solution:**
1. Check workflow exists: `ls .github/workflows/`
2. Use exact workflow name: `deploy-dev.yml` (not `deploy-dev`)
3. Push workflows to main branch first

### "Environment variables not set"

**Problem:** Deployment fails with "DEV_PROJECT_ID not set"

**Solution:**
1. Go to repo Settings → Environments
2. Select environment (dev/staging/prod)
3. Add variables:
   - `DEV_PROJECT_ID`
   - `DEV_REGION`
   - `DEV_STAGING_BUCKET`

### "Approval required but no approvers"

**Problem:** Staging/prod deployment stuck waiting for approval

**Solution:**
1. Go to repo Settings → Environments
2. Select environment
3. Add required reviewers under Protection rules
4. Re-run workflow after adding reviewers

---

## Porting to New Repos

### Checklist for New IAM Department Repo

**Step 1: Copy Workflow Files**
```bash
# Copy all workflow files
cp .github/workflows/ci.yml new-repo/.github/workflows/
cp .github/workflows/deploy-dev.yml new-repo/.github/workflows/
cp .github/workflows/deploy-staging.yml new-repo/.github/workflows/
cp .github/workflows/deploy-prod.yml new-repo/.github/workflows/
```

**Step 2: Copy Makefile Deployment Section**
```bash
# Copy deployment targets section (lines 368-456)
# Paste into new repo's Makefile
```

**Step 3: Update Workflow References**
- Replace agent paths (`agents/bob` → `agents/your-agent`)
- Update repository references in workflow files

**Step 4: Setup GitHub Environments**
- Create `dev`, `staging`, `prod` environments
- Add environment variables per environment
- Configure protection rules (approvals, branch restrictions)

**Step 5: Setup WIF**
- Follow WIF setup steps (see "Workload Identity Federation" section)
- Add secrets to GitHub repo or organization

**Step 6: Test**
```bash
# Run CI locally
make ci

# Run ARV locally
make arv-department

# Trigger dev deployment
make deploy-dev

# Check status
make deploy-status
```

---

## Related Documentation

**This Repo:**
- `116-DR-STND-config-and-feature-flags-standard-v1.md` - Config standard
- `117-AA-REPT-iam-department-arv-implementation.md` - ARV framework
- `CI1-WORKFLOW-INVENTORY-FINDINGS.md` - CI1 analysis

**6767 Canonical Standards:**
- `000-DR-STND-arv-minimum-gate.md` - ARV minimum requirements
- `000-RB-OPS-adk-department-operations-runbook.md` - Operations

**External:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [ADK Deployment Guide](https://cloud.google.com/vertex-ai/docs/agent-development-kit)

---

**Status:** ✅ Active
**Next Review:** After first production deployment
**Maintainer:** Build Captain (bobs-brain repo)

---

**Last Updated:** 2025-11-20
