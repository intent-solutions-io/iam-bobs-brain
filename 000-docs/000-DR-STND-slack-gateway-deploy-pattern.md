# 000-DR-STND: Slack Gateway Deployment Pattern (Phase 25)

**Document Type:** DR-STND (Documentation & Reference - Standard Operating Procedure)
**Created:** 2025-11-30
**Phase:** 25 - Slack Bob Hardening
**Status:** Canonical Standard
**Author:** Build Captain (Autonomous CTO Mode)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Canonical Deployment Pattern](#canonical-deployment-pattern)
3. [Prerequisites](#prerequisites)
4. [Configuration Management](#configuration-management)
5. [Deployment Procedures](#deployment-procedures)
6. [Validation & Smoke Testing](#validation--smoke-testing)
7. [Rollback Procedures](#rollback-procedures)
8. [What NOT to Do](#what-not-to-do)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Monitoring & Operations](#monitoring--operations)

---

## Executive Summary

**Purpose:** This SOP defines the **canonical deployment pattern** for Slack Bob Gateway (Cloud Run service) to ensure R4-compliant (Terraform+CI only), secure, and repeatable deployments.

**Key Principles:**
- ✅ **Terraform-First**: All infrastructure changes via Terraform code
- ✅ **CI-Only Deployments**: GitHub Actions workflows with WIF authentication
- ✅ **Automated Validation**: ARV checks before every deployment
- ✅ **Targeted Deploys**: Deploy only Slack gateway module (not entire infra)
- ✅ **Environment Separation**: Dev (auto) vs Prod (manual approval gates)
- ❌ **NEVER Manual**: No `gcloud run deploy` or Console changes

**Workflows:**
- **Dev**: `.github/workflows/deploy-slack-gateway-dev.yml`
- **Production**: `.github/workflows/deploy-slack-gateway-prod.yml`

**Validation:**
- **Script**: `scripts/ci/check_slack_gateway_config.py`
- **Makefile**: `make check-slack-gateway-config ENV=<env>`
- **CI Integration**: `ci.yml` job `slack-gateway-validation`

---

## Canonical Deployment Pattern

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Developer Workflow                                           │
├──────────────────────────────────────────────────────────────┤
│ 1. Update Terraform code (infra/terraform/)                  │
│ 2. Update tfvars (infra/terraform/envs/dev.tfvars)           │
│ 3. Create PR to main                                         │
│ 4. CI validates config (slack-gateway-validation job)        │
│ 5. Code review + approval                                    │
│ 6. Merge to main                                             │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ Automated Dev Deployment                                     │
├──────────────────────────────────────────────────────────────┤
│ 1. Push to main triggers deploy-slack-gateway-dev.yml        │
│ 2. ARV gate validates Slack config                           │
│ 3. Terraform plan (preview changes)                          │
│ 4. Terraform apply (auto-approve for dev)                    │
│ 5. Smoke test (health check + service URL)                   │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ Manual Production Deployment                                 │
├──────────────────────────────────────────────────────────────┤
│ 1. Manual dispatch of deploy-slack-gateway-prod.yml          │
│ 2. ARV gate validates prod config                            │
│ 3. Terraform plan (manual review required)                   │
│ 4. Manual approval gate #1 (GitHub environment protection)   │
│ 5. Terraform apply (with apply: true input)                  │
│ 6. Manual approval gate #2 (GitHub environment protection)   │
│ 7. Smoke test (health check + infrastructure verification)   │
│ 8. Post-deployment notification                              │
└──────────────────────────────────────────────────────────────┘
```

### Terraform Module Structure

**Module Location:** `infra/terraform/modules/slack_bob_gateway/`

**Key Files:**
- `main.tf` - Cloud Run service definition
- `variables.tf` - Input variables (project_id, region, secrets, etc.)
- `outputs.tf` - Service URL, service name
- `iam.tf` - Service account, IAM bindings
- `secrets.tf` - Secret Manager references

**Environment Configs:**
- `infra/terraform/envs/dev.tfvars` - Dev environment variables
- `infra/terraform/envs/staging.tfvars` - Staging variables (future)
- `infra/terraform/envs/prod.tfvars` - Production variables

---

## Prerequisites

### 1. GitHub Repository Setup

**Required GitHub Environments:**
- `dev` - Dev environment (no protection rules, auto-deploy)
- `production` - Prod environment (required reviewers + manual approval)

**Configuration:**
1. Go to **Settings** → **Environments**
2. Create `dev` environment (no protection rules)
3. Create `production` environment:
   - ✅ **Required reviewers**: Add team members (minimum 2)
   - ✅ **Wait timer**: 5 minutes (prevent accidental deploys)
   - ✅ **Deployment branches**: `main` only

### 2. GitHub Secrets & Variables

**Secrets (Organization/Repository level):**
```bash
# Workload Identity Federation (WIF)
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
GCP_SERVICE_ACCOUNT=github-actions@PROJECT_ID.iam.gserviceaccount.com
GCP_SERVICE_ACCOUNT_DEV=github-actions-dev@PROJECT_ID.iam.gserviceaccount.com

# Slack credentials (managed via Secret Manager, not hardcoded)
# (These are SECRET_IDs, not actual tokens)
```

**Environment Variables (per environment):**

**Dev:**
```bash
DEV_PROJECT_ID=bobs-brain-dev
DEV_REGION=us-central1
DEV_STAGING_BUCKET=gs://bobs-brain-dev-adk-staging
```

**Production:**
```bash
PROD_PROJECT_ID=bobs-brain
PROD_REGION=us-central1
PROD_STAGING_BUCKET=gs://bobs-brain-adk-staging
```

### 3. GCP Prerequisites

**Required GCP Resources:**
- ✅ **Terraform State Bucket**: `bobs-brain-terraform-state` (prod) or `bobs-brain-dev-terraform-state` (dev)
- ✅ **Secret Manager Secrets**:
  - `slack-bot-token` (production Slack bot token)
  - `slack-signing-secret` (production Slack signing secret)
- ✅ **Service Accounts** (created by Terraform):
  - `slack-gateway-sa@PROJECT_ID.iam.gserviceaccount.com`
- ✅ **Vertex AI Agent Engine**: Bob agent deployed and running

**IAM Permissions:**
GitHub Actions service account needs:
```bash
roles/run.developer          # Deploy Cloud Run services
roles/iam.serviceAccountUser # Impersonate service accounts
roles/secretmanager.secretAccessor # Access secrets
roles/storage.objectAdmin    # Terraform state management
```

---

## Configuration Management

### How to Configure Terraform Variables

#### Step 1: Update Environment tfvars File

**File:** `infra/terraform/envs/dev.tfvars` (or `prod.tfvars`)

**Required Variables:**
```hcl
# Core Configuration
project_id  = "bobs-brain-dev"
region      = "us-central1"
environment = "dev"  # or "prod"
app_name    = "bobs-brain"

# Slack Gateway Image (set by CI, but can override)
slack_webhook_image = "gcr.io/bobs-brain-dev/slack-webhook:0.10.0"

# Secret Manager References (PRODUCTION ONLY)
# Dev can use placeholder values for testing
slack_bot_token      = "xoxb-dev-placeholder"  # Dev only
slack_signing_secret = "dev-placeholder"        # Dev only

# Production should reference Secret Manager:
# slack_bot_token is injected via Secret Manager at runtime
# slack_signing_secret is injected via Secret Manager at runtime

# Agent Engine Configuration (required)
bob_docker_image = "gcr.io/bobs-brain-dev/agent:0.10.0"

# Labels (for cost tracking)
labels = {
  cost_center = "development"
  team        = "platform"
}
```

#### Step 2: Validate Configuration Locally

Before committing changes, validate configuration:

```bash
# Validate syntax
make check-slack-gateway-config ENV=dev

# Expected output:
# ✅ All checks passed!
# Configuration: infra/terraform/envs/dev.tfvars
# Environment: dev
```

#### Step 3: Commit & Push

```bash
git add infra/terraform/envs/dev.tfvars
git commit -m "config(terraform): update Slack gateway config for dev"
git push origin feature/slack-config-update
```

**CI will automatically:**
1. Run `slack-gateway-validation` job
2. Block merge if config invalid
3. Show validation results in PR checks

---

## Deployment Procedures

### Dev Deployment (Automatic)

**Trigger:** Push to `main` branch with changes to:
- `service/slack_webhook/**`
- `infra/terraform/modules/slack_bob_gateway/**`
- `infra/terraform/envs/dev.tfvars`

**Workflow:** `.github/workflows/deploy-slack-gateway-dev.yml`

**Steps:**
1. **Automatic Trigger**: Workflow runs on push to main
2. **ARV Gate**: Validates Slack config (`make check-slack-gateway-config ENV=dev`)
3. **Terraform Plan**: Previews infrastructure changes
4. **Terraform Apply**: Auto-applies changes (dev environment)
5. **Smoke Test**: Health check + service URL verification

**Manual Override (if needed):**
```bash
# Via GitHub CLI
gh workflow run deploy-slack-gateway-dev.yml

# Via GitHub UI
Actions → Deploy Slack Gateway (Dev) → Run workflow
```

**Monitoring:**
```bash
# Check workflow status
gh run list --workflow=deploy-slack-gateway-dev.yml --limit=5

# View logs
gh run view --workflow=deploy-slack-gateway-dev.yml --log
```

---

### Production Deployment (Manual Approval Required)

**Trigger:** Manual workflow dispatch ONLY

**Workflow:** `.github/workflows/deploy-slack-gateway-prod.yml`

**Steps:**

#### 1. Trigger Workflow (Plan Only)

```bash
# Via GitHub CLI
gh workflow run deploy-slack-gateway-prod.yml \
  --field apply=false \
  --field verbose=false

# Via GitHub UI
Actions → Deploy Slack Gateway (Production) → Run workflow
  apply: false (PLAN ONLY)
  skip_arv: false
  verbose: false
```

**Result:** Terraform plan generated and uploaded as artifact

#### 2. Review Plan

1. Go to **Actions** → Latest run
2. Download `terraform-plan-slack-gateway-prod` artifact
3. Review plan locally:
   ```bash
   cd infra/terraform
   terraform show tfplan
   ```
4. **CRITICAL:** Ensure plan shows expected changes only

#### 3. Trigger Apply (Production Deployment)

```bash
# Via GitHub CLI (requires confirmation)
gh workflow run deploy-slack-gateway-prod.yml \
  --field apply=true \
  --field verbose=false

# Via GitHub UI
Actions → Deploy Slack Gateway (Production) → Run workflow
  apply: true ← 🚨 THIS DEPLOYS TO PRODUCTION
  skip_arv: false
  verbose: false
```

#### 4. Manual Approval Gates

**Approval Gate #1: Terraform Plan Review**
- GitHub environment protection requires **manual approval**
- Minimum 2 reviewers must approve
- 5-minute wait timer (prevents accidental approvals)

**Actions:**
1. Review plan output in workflow logs
2. Verify no unexpected changes
3. Click **Review deployments** → **Approve**

**Approval Gate #2: Terraform Apply**
- Second approval required before actual deployment
- Ensures double-check before production changes

**Actions:**
1. Verify ARV checks passed
2. Confirm smoke test plan looks correct
3. Click **Review deployments** → **Approve**

#### 5. Post-Deployment Verification

**Automatic Checks:**
- Health endpoint test
- Infrastructure state verification
- Secret Manager validation

**Manual Checks:**
1. **Test Slack Bot:**
   ```
   In production Slack workspace:
   @Bob hello
   ```
2. **Check Logs:**
   ```bash
   gcloud run services logs read bobs-brain-slack-webhook-prod \
     --project=bobs-brain \
     --region=us-central1 \
     --limit=50
   ```
3. **Monitor for 15 Minutes:**
   - Watch Cloud Run logs for errors
   - Check Slack for user feedback
   - Verify Agent Engine integration

---

## Validation & Smoke Testing

### ARV Checks (Pre-Deployment)

**Automated validation before every deployment:**

```bash
# Local validation
make check-slack-gateway-config ENV=dev

# CI validation (automatic in workflows)
# - Runs in ci.yml (on all PRs)
# - Runs in deploy-slack-gateway-*.yml (pre-deployment)
```

**Checks Performed:**
1. **Terraform vars file exists and is valid HCL**
2. **Required variables present:**
   - project_id
   - region
   - environment
   - app_name
   - slack_webhook_image
3. **No hardcoded secrets in production:**
   - Scans for `xoxb-*` patterns (Slack bot tokens)
   - Scans for API key patterns
   - Scans for long hex strings (32+ chars)
4. **Environment labels present**
5. **Secret Manager references (prod only)**

**Exit Codes:**
- `0` - All checks passed (deployment proceeds)
- `1` - Validation errors (deployment blocked)
- `2` - Script error (deployment blocked)

### Smoke Tests (Post-Deployment)

**Automated smoke tests after successful deployment:**

#### Dev Smoke Test
```yaml
# Runs automatically after terraform-apply job
smoke-test:
  - Get service URL from Cloud Run
  - Test health endpoint (curl /health)
  - Verify HTTP 200 response
  - Fail deployment if health check fails
```

#### Production Smoke Test
```yaml
# Runs automatically after terraform-apply job
smoke-test:
  - Get service URL from Cloud Run
  - Test health endpoint (curl /health)
  - Verify infrastructure state (gcloud commands)
  - Check Secret Manager secrets exist
  - Fail deployment if any check fails
```

**Manual Smoke Test (Production):**
```bash
# 1. Get service URL
SERVICE_URL=$(gcloud run services describe bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --region=us-central1 \
  --format='value(status.url)')

# 2. Test health endpoint
curl -v "$SERVICE_URL/health"

# Expected response:
# HTTP/2 200
# {"status": "healthy", "service": "slack-bob-gateway", "version": "0.11.0"}

# 3. Test Slack bot in production workspace
# In Slack: @Bob status

# 4. Check logs for errors
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --limit=100 \
  --format=json | jq '.[] | select(.severity=="ERROR")'
```

---

## Rollback Procedures

### Scenario 1: Failed Terraform Apply

**Symptoms:**
- Terraform apply job fails
- Error in workflow logs
- Service deployment incomplete

**Procedure:**
1. **DO NOT RETRY IMMEDIATELY** - Investigate first
2. **Review Error Logs:**
   ```bash
   # Via GitHub UI
   Actions → Failed run → terraform-apply job → View logs

   # Via CLI
   gh run view WORKFLOW_RUN_ID --log
   ```
3. **Determine Root Cause:**
   - Configuration error? → Fix tfvars, retry
   - Permissions error? → Check IAM, service account
   - Resource conflict? → Check Cloud Run console
4. **Fix & Redeploy:**
   ```bash
   # Fix configuration
   vim infra/terraform/envs/prod.tfvars

   # Validate locally
   make check-slack-gateway-config ENV=prod

   # Commit & trigger workflow again
   git add infra/terraform/envs/prod.tfvars
   git commit -m "fix(terraform): correct Slack gateway config"
   git push origin main

   # Trigger production deployment
   gh workflow run deploy-slack-gateway-prod.yml --field apply=true
   ```

### Scenario 2: Failed Smoke Test

**Symptoms:**
- Terraform apply succeeded
- Smoke test job failed
- Health check returning errors

**Procedure:**
1. **Check Service Status:**
   ```bash
   gcloud run services describe bobs-brain-slack-webhook-prod \
     --project=bobs-brain \
     --region=us-central1 \
     --format=yaml
   ```
2. **Check Logs:**
   ```bash
   gcloud run services logs read bobs-brain-slack-webhook-prod \
     --project=bobs-brain \
     --limit=200
   ```
3. **Common Issues:**
   - **Cold start delay**: Wait 2-3 minutes, retest health endpoint
   - **Secret Manager permissions**: Check IAM bindings
   - **Agent Engine connection**: Verify Agent Engine is running
4. **If Still Failing - Rollback:**
   ```bash
   # Revert to previous Terraform state
   cd infra/terraform
   terraform init -backend-config="bucket=bobs-brain-terraform-state"

   # Get previous state version
   gsutil ls -l gs://bobs-brain-terraform-state/default.tfstate*

   # Restore previous state (CAREFUL!)
   gsutil cp gs://bobs-brain-terraform-state/default.tfstate.BACKUP \
     gs://bobs-brain-terraform-state/default.tfstate

   # Re-apply previous configuration
   terraform apply -var-file=envs/prod.tfvars -target=module.slack_bob_gateway
   ```

### Scenario 3: Production Issues Post-Deployment

**Symptoms:**
- Deployment succeeded
- Slack bot not responding or returning errors
- Users reporting issues

**Immediate Actions:**
1. **Check Cloud Run Logs:**
   ```bash
   gcloud run services logs read bobs-brain-slack-webhook-prod \
     --project=bobs-brain \
     --follow
   ```
2. **Check Agent Engine Status:**
   ```bash
   gcloud ai reasoning-engines list \
     --project=bobs-brain \
     --region=us-central1 \
     --filter="displayName:bob"
   ```
3. **Roll Back to Previous Version:**
   ```bash
   # Find previous working image
   gcloud container images list-tags gcr.io/bobs-brain/slack-webhook \
     --limit=10 \
     --format="table(tags,timestamp)"

   # Update tfvars with previous image
   vim infra/terraform/envs/prod.tfvars
   # Change: slack_webhook_image = "gcr.io/bobs-brain/slack-webhook:0.10.0"
   # (replace with last known good version)

   # Deploy previous version
   gh workflow run deploy-slack-gateway-prod.yml --field apply=true
   # Approve gates
   # Monitor for recovery
   ```
4. **Document Incident:**
   - Create incident report in 000-docs/
   - Document in Phase 25 AAR
   - Update runbook with lessons learned

---

## What NOT to Do

### ❌ BANNED: Manual `gcloud` Deployments

**NEVER use these commands:**
```bash
# ❌ VIOLATES R4 - DO NOT USE
gcloud run deploy slack-webhook \
  --source service/slack_webhook \
  --region us-central1

# ❌ VIOLATES R4 - DO NOT USE
gcloud run services update slack-webhook \
  --set-env-vars="SLACK_BOT_TOKEN=xoxb-..."

# ❌ VIOLATES R4 - DO NOT USE
gcloud run services update-traffic slack-webhook \
  --to-latest
```

**Why This is Banned:**
1. **Creates Configuration Drift**: Terraform state doesn't match reality
2. **Bypasses ARV Gates**: No validation checks run
3. **No Audit Trail**: No record of who deployed what
4. **Breaks Rollback**: Cannot revert via Terraform
5. **Violates R4**: CI-only deployment rule

**Correct Alternative:**
```bash
# ✅ CORRECT: Update Terraform code
vim infra/terraform/modules/slack_bob_gateway/main.tf
vim infra/terraform/envs/prod.tfvars

# ✅ CORRECT: Deploy via workflow
gh workflow run deploy-slack-gateway-prod.yml --field apply=true
```

### ❌ BANNED: Google Cloud Console Changes

**DO NOT:**
- Edit Cloud Run service via Console UI
- Update environment variables in Console
- Change service accounts in Console
- Modify traffic splitting in Console

**Why:**
- Same reasons as manual gcloud commands
- Harder to track changes
- Cannot be code-reviewed
- Bypasses all gates

**Correct Alternative:**
- All changes in Terraform code
- Code review via PR
- Deploy via GitHub Actions

### ❌ BANNED: Direct Secret Hardcoding

**DO NOT:**
```hcl
# ❌ DO NOT HARDCODE SECRETS
slack_bot_token = "xoxb-1234567890-REAL_TOKEN_HERE"
slack_signing_secret = "abcdef1234567890real_secret"
```

**Correct Alternative:**
```hcl
# ✅ CORRECT: Use Secret Manager references
# Production tfvars should NOT have token values
# They are injected at runtime from Secret Manager

# In module main.tf:
env {
  name = "SLACK_BOT_TOKEN"
  value_source {
    secret_key_ref {
      secret  = "slack-bot-token"
      version = "latest"
    }
  }
}
```

---

## Troubleshooting Guide

### Issue: ARV Check Fails with "Missing Required Variables"

**Error:**
```
❌ ERROR: Missing required variables: slack_webhook_image
Hint: Add these variables to your tfvars file
```

**Cause:** tfvars file missing required variable

**Solution:**
```bash
# 1. Check which variable is missing
make check-slack-gateway-config ENV=dev

# 2. Add missing variable to tfvars
vim infra/terraform/envs/dev.tfvars

# Add:
slack_webhook_image = "gcr.io/bobs-brain-dev/slack-webhook:0.11.0"

# 3. Validate again
make check-slack-gateway-config ENV=dev

# 4. Commit and push
git add infra/terraform/envs/dev.tfvars
git commit -m "fix(terraform): add missing slack_webhook_image variable"
git push
```

### Issue: ARV Check Fails with "Hardcoded Secret Detected"

**Error:**
```
⚠️  WARNING: Potential hardcoded Slack bot token detected
Hint: Use Secret Manager for sensitive values
```

**Cause:** Production tfvars contains actual secret values (not allowed)

**Solution:**
```bash
# 1. Remove hardcoded secrets from prod tfvars
vim infra/terraform/envs/prod.tfvars

# Remove these lines:
# slack_bot_token = "xoxb-REAL_TOKEN"
# slack_signing_secret = "REAL_SECRET"

# 2. Ensure secrets exist in Secret Manager
gcloud secrets describe slack-bot-token --project=bobs-brain
gcloud secrets describe slack-signing-secret --project=bobs-brain

# 3. Module automatically references Secret Manager (no tfvars needed)
# See: infra/terraform/modules/slack_bob_gateway/main.tf

# 4. Commit and push
git add infra/terraform/envs/prod.tfvars
git commit -m "fix(security): remove hardcoded secrets from prod tfvars"
git push
```

### Issue: Workflow Fails with "Terraform State Locked"

**Error:**
```
Error: Error locking state: Error acquiring the state lock
Lock Info:
  ID:        abc123-def456
  Operation: OperationTypeApply
  Who:       user@example.com
  Created:   2025-11-30 10:15:30 UTC
```

**Cause:** Previous Terraform run didn't complete cleanly

**Solution:**
```bash
# 1. Check if workflow is actually running
gh run list --workflow=deploy-slack-gateway-prod.yml --limit=5

# If no workflow running:
# 2. Force unlock (CAUTION: Only if you're sure no apply is running)
cd infra/terraform
terraform force-unlock abc123-def456

# 3. Retry deployment
gh workflow run deploy-slack-gateway-prod.yml --field apply=true
```

### Issue: Health Check Fails After Deployment

**Error:**
```
❌ Health check failed
Response: FAILED (connection refused)
```

**Possible Causes & Solutions:**

**1. Cold Start Delay (Most Common):**
```bash
# Wait 2-3 minutes for Cloud Run to fully start
sleep 180

# Retry health check
curl https://SERVICE_URL/health
```

**2. Service Account Permissions:**
```bash
# Check service account has required permissions
gcloud run services get-iam-policy bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --region=us-central1

# Should show: slack-gateway-sa@PROJECT_ID.iam.gserviceaccount.com
```

**3. Secret Manager Access:**
```bash
# Check secrets exist and are accessible
gcloud secrets versions access latest \
  --secret=slack-bot-token \
  --impersonate-service-account=slack-gateway-sa@bobs-brain.iam.gserviceaccount.com

# If permission denied, add IAM binding:
gcloud secrets add-iam-policy-binding slack-bot-token \
  --member="serviceAccount:slack-gateway-sa@bobs-brain.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**4. Agent Engine Connection:**
```bash
# Check Agent Engine is running
gcloud ai reasoning-engines list \
  --project=bobs-brain \
  --region=us-central1 \
  --filter="displayName:bob"

# Check logs for connection errors
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --limit=100 \
  --format=json | jq '.[] | select(.textPayload | contains("Agent Engine"))'
```

### Issue: Slack Bot Not Responding

**Symptoms:**
- Health check passes
- Logs show no errors
- @Bob mentions in Slack get no response

**Debugging Steps:**

**1. Verify Slack Webhook URL:**
```bash
# Get current service URL
gcloud run services describe bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --region=us-central1 \
  --format='value(status.url)'

# Compare with Slack app config:
# 1. Go to https://api.slack.com/apps
# 2. Select Bob's Brain app
# 3. Event Subscriptions → Request URL
# 4. Ensure URL matches Cloud Run service URL + /slack/events
```

**2. Check Slack Event Subscriptions:**
```bash
# Ensure these events are enabled:
# - app_mention
# - message.im
# - message.channels (if applicable)
```

**3. Check Signature Verification:**
```bash
# Get signing secret from Secret Manager
gcloud secrets versions access latest \
  --secret=slack-signing-secret \
  --project=bobs-brain

# Compare with Slack app config
# Slack App → Basic Information → Signing Secret
```

**4. Test Webhook Manually:**
```bash
# Send test event to webhook (requires valid signature)
# See: https://api.slack.com/authentication/verifying-requests-from-slack
```

---

## Monitoring & Operations

### Cloud Run Metrics

**Key Metrics to Monitor:**
```bash
# Request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --project=bobs-brain

# Request latencies (p50, p95, p99)
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"' \
  --project=bobs-brain

# Container instance count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/instance_count"' \
  --project=bobs-brain
```

### Logs

**Structured Logging:**
```bash
# All logs (last hour)
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --limit=1000

# Error logs only
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --log-filter='severity>=ERROR'

# Specific event type
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --log-filter='jsonPayload.event_type="app_mention"'
```

### Alerting (Future Enhancement)

**Recommended Alerts:**
1. **Error Rate > 5%**: Alert if 5xx responses exceed 5% of total requests
2. **Latency > 10s**: Alert if p95 latency exceeds 10 seconds
3. **Health Check Failures**: Alert if 3 consecutive health checks fail
4. **Secret Manager Access Denied**: Alert on permission errors

**Setup:**
```bash
# Example: Create alert for error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Slack Gateway Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-aggregation-window=60s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"'
```

---

## Appendix: Quick Reference

### Commands Cheat Sheet

```bash
# Validate configuration locally
make check-slack-gateway-config ENV=dev
make check-slack-gateway-config ENV=prod

# Trigger deployments (via GitHub CLI)
gh workflow run deploy-slack-gateway-dev.yml
gh workflow run deploy-slack-gateway-prod.yml --field apply=true

# Check workflow status
gh run list --workflow=deploy-slack-gateway-dev.yml --limit=5
gh run view --workflow=deploy-slack-gateway-prod.yml --log

# Get service URL
gcloud run services describe bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint
curl https://$(gcloud run services describe bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --region=us-central1 \
  --format='value(status.url)')/health

# Check logs
gcloud run services logs read bobs-brain-slack-webhook-prod \
  --project=bobs-brain \
  --limit=50
```

### File Locations

```
bobs-brain/
├── .github/workflows/
│   ├── deploy-slack-gateway-dev.yml    # Dev deployment workflow
│   ├── deploy-slack-gateway-prod.yml   # Prod deployment workflow (approval gates)
│   └── ci.yml                          # CI validation (includes slack-gateway-validation)
├── scripts/ci/
│   └── check_slack_gateway_config.py   # ARV validation script
├── infra/terraform/
│   ├── modules/slack_bob_gateway/       # Terraform module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── iam.tf
│   └── envs/
│       ├── dev.tfvars                  # Dev environment config
│       ├── staging.tfvars              # Staging config
│       └── prod.tfvars                 # Production config
├── service/slack_webhook/               # Source code
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── 000-docs/
│   ├── 000-DR-STND-slack-gateway-deploy-pattern.md  # This SOP
│   ├── 171-AA-PLAN-phase-25-slack-bob-hardening.md       # Phase 25 plan
│   └── 172-AA-REPT-phase-25-slack-bob-hardening.md       # Phase 25 AAR (TBD)
└── Makefile                             # make check-slack-gateway-config
```

### Emergency Contacts

**For Production Issues:**
1. Check #ops-alerts Slack channel
2. Escalate to @platform-team
3. Page on-call engineer if critical

**For Deployment Issues:**
1. Check GitHub Actions logs first
2. Review Terraform state in GCS bucket
3. Consult this SOP troubleshooting section
4. Create incident report if unresolved within 30 minutes

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-30
**Phase:** 25 - Slack Bob Hardening
**Status:** Canonical Standard (6767-series)
**Next Review:** Phase 26 (Post-Dev Deployment)
