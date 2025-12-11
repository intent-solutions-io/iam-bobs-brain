# Phase 27: Deployment Pipeline Validation & Gap Closure

**Created:** 2025-12-11
**Status:** IN PROGRESS
**Branch:** feature/phase-26-repo-cleanup
**Previous Phase:** Phase 26 (Repository Cleanup & v0.14.0)

---

## Executive Summary

**CTO Decision:** The originally proposed Phases 27-29 were found to be **stale** - they proposed creating infrastructure that already exists. This revised Phase 27 focuses on **validating and testing** existing deployment infrastructure rather than recreating it.

### Key Discovery

| Proposed Work | Already Exists | File |
|---------------|----------------|------|
| Dev Agent Engine Deploy workflow | ✅ EXISTS | `.github/workflows/agent-engine-inline-dev-deploy.yml` |
| Slack Gateway Dev deployment | ✅ EXISTS | `.github/workflows/deploy-slack-gateway-dev.yml` |
| ARV gates on deploy | ✅ EXISTS | Already wired in both workflows |

**Actual Gap:** Missing GitHub secrets for WIF auth in CI workflows.

---

## Validation Results (Pre-Phase)

### ARV Checks Status

| Check | Status | Notes |
|-------|--------|-------|
| `check-arv-minimum` | ✅ PASS | All minimum requirements met |
| `check-a2a-contracts` | ✅ PASS | 11/11 AgentCards valid |
| `check-slack-gateway-config` | ✅ PASS | Config valid (dev placeholder noted) |
| `check-inline-deploy-ready` | ❌ FAIL | Missing env vars (GCP_PROJECT_ID, GCP_LOCATION) |

### GitHub Secrets Status

**Configured:**
- `GCP_PROJECT_NUMBER` ✅
- `GCP_SERVICE_ACCOUNT` ✅
- `GCP_WORKLOAD_IDENTITY_PROVIDER` ✅
- `PROJECT_ID` ✅
- `REGION` ✅
- `SLACK_BOT_TOKEN` ✅
- `SLACK_SIGNING_SECRET` ✅
- `WIF_POOL_ID` ✅
- `WIF_PROVIDER_ID` ✅

**Missing for Workflows:**
- `WIF_PROVIDER` (workflow uses this name, not `GCP_WORKLOAD_IDENTITY_PROVIDER`)
- `WIF_SERVICE_ACCOUNT` (workflow uses this name, not `GCP_SERVICE_ACCOUNT`)
- `GCP_SERVICE_ACCOUNT_DEV` (Slack gateway workflow)
- GitHub Environment variables (`DEV_PROJECT_ID`, `DEV_REGION`)

---

## Phase 27 Objectives

### Primary Goal
Close the gap between "infrastructure exists" and "infrastructure works" by:
1. Aligning secret/variable names between workflows and GitHub configuration
2. Running actual deployment workflows
3. Documenting any external blockers

### Non-Goals
- Creating new workflows (they already exist)
- Changing agent runtime behavior
- Production deployments (dev only)

---

## Implementation Steps

### Step 1: Secret Name Alignment
Audit and align GitHub secret names with workflow expectations:

```yaml
# Current workflow expects:
secrets.WIF_PROVIDER
secrets.WIF_SERVICE_ACCOUNT

# GitHub has configured:
secrets.GCP_WORKLOAD_IDENTITY_PROVIDER
secrets.GCP_SERVICE_ACCOUNT
```

**Options:**
A. Update workflow files to use existing secret names
B. Create alias secrets with expected names
C. Document mapping and update workflows

**Recommendation:** Option A (update workflows) - cleaner, no duplicate secrets

### Step 2: Add GitHub Environment Variables
Create GitHub Environment `dev` with required variables:
- `DEV_PROJECT_ID`
- `DEV_REGION`

### Step 3: Test Agent Engine Dev Deploy Workflow
1. Run `agent-engine-inline-dev-deploy.yml` via workflow_dispatch
2. Select agent: `bob`
3. Provide GCP project ID
4. Monitor for success/failure
5. Document results

### Step 4: Test Slack Gateway Dev Deploy Workflow
1. Run `deploy-slack-gateway-dev.yml` via workflow_dispatch
2. Monitor Terraform plan
3. Review apply (if safe)
4. Run smoke tests
5. Document results

### Step 5: Document Remaining Blockers
Create AAR documenting:
- What worked
- What's still blocked (external factors)
- Recommended next steps

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| WIF auth misconfigured | Medium | High | Test with dry-run first |
| Terraform state mismatch | Low | Medium | Use `-target` for isolated deploys |
| Agent Engine quota issues | Low | Low | Dev environment has separate quota |
| Secret exposure | Very Low | High | All secrets in GitHub Secrets Manager |

---

## Success Criteria

1. ✅ Secret names aligned across all deployment workflows
2. ✅ GitHub Environment `dev` configured with required vars
3. ✅ Agent Engine dev deploy workflow runs successfully OR blockers documented
4. ✅ Slack Gateway dev deploy workflow runs successfully OR blockers documented
5. ✅ Phase 27 AAR created with clear next steps

---

## Commit Strategy

```bash
# Commit 1: Secret name alignment
git commit -m "fix(ci): align secret names in deployment workflows"

# Commit 2: Environment documentation
git commit -m "docs(phase-27): add deployment validation plan"

# Commit 3: AAR
git commit -m "docs(phase-27): record deployment validation AAR"
```

---

## References

- **Existing Workflows:**
  - `.github/workflows/agent-engine-inline-dev-deploy.yml`
  - `.github/workflows/deploy-slack-gateway-dev.yml`
- **Standards:**
  - `000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
  - `000-docs/6767-DR-STND-slack-gateway-deploy-pattern.md`
- **Previous Phases:**
  - Phase 23: Dev deploy and monitoring plan
  - Phase 24-25: Slack Bob CI deploy and hardening

---

**Owner:** Jeremy Longshore
**Support:** Claude Code (Build Captain)
**Target:** Single session completion
