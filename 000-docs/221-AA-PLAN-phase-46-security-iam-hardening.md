# Phase 46: Security & IAM Hardening – PLAN

**Date:** 2025-12-12
**Status:** In Progress
**Branch:** `feature/phase-46-security-iam-hardening`

## Goals

Apply security hardening to IAM, Cloud Run, and CI/CD infrastructure.

### What This Phase Achieves

1. **Least Privilege IAM** – Replace broad `roles/editor` with specific permissions
2. **Workload Identity Federation** – Enable keyless auth for GitHub Actions
3. **Ingress Restrictions** – Restrict Cloud Run to internal traffic where possible
4. **Security Validation Script** – CI-integrated security checks
5. **Security Runbook** – Documentation for security procedures

## Analysis

### Current State

| Component | Current | Risk |
|-----------|---------|------|
| GitHub Actions SA | `roles/editor` | HIGH - overly broad |
| WIF | Commented out | MEDIUM - using keys |
| Cloud Run A2A Gateway | Public or private based on flag | LOW - configurable |
| Audit Logging | Not configured | MEDIUM - no audit trail |

### What Needs Enhancement

1. **Replace `roles/editor` with specific roles:**
   - `roles/run.admin` (already present)
   - `roles/aiplatform.admin` (already present)
   - `roles/storage.admin` (already present)
   - Add: `roles/iam.serviceAccountUser`
   - Add: `roles/secretmanager.admin`
   - Remove: `roles/editor`

2. **Enable Workload Identity Federation:**
   - Uncomment WIF resources in `iam.tf`
   - Configure for `intent-solutions-io/bobs-brain` repo

3. **Add ingress annotations for internal-only services**

4. **Add security validation script**

## High-Level Steps

### Step 1: Harden GitHub Actions IAM

1. Remove `roles/editor` from GitHub Actions SA
2. Add specific roles needed for CI/CD:
   - `roles/iam.serviceAccountUser` (impersonation)
   - `roles/secretmanager.admin` (manage secrets)
   - Keep: run.admin, aiplatform.admin, storage.admin

### Step 2: Enable Workload Identity Federation

1. Uncomment WIF resources in `iam.tf`
2. Configure for `intent-solutions-io/bobs-brain` repository
3. Add WIF provider outputs

### Step 3: Add Security Validation Script

Create `scripts/ci/check_security.sh`:
- Verify no service account keys in repo
- Check Terraform for overly permissive IAM
- Validate Secret Manager references
- Check Cloud Run ingress settings

### Step 4: Update CI Workflow

Add security check job to CI workflow.

### Step 5: Create Security Runbook

Document in `000-docs/222-RB-SEC-*.md`:
- IAM best practices
- Secret rotation procedures
- Incident response

## Design Decisions

### Why Remove `roles/editor`?

The `roles/editor` role grants broad access to most GCP resources. For CI/CD, we only need:
- Deploy Cloud Run services
- Update Agent Engine
- Manage storage buckets
- Create service account tokens

Specific roles provide the same functionality with reduced blast radius.

### Why Enable WIF?

Service account keys are a security risk:
- Can be leaked in logs or commits
- Don't expire automatically
- Hard to rotate

WIF provides:
- Keyless authentication
- Short-lived tokens
- Automatic rotation
- GitHub-native identity

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `infra/terraform/iam.tf` | Modify | Harden IAM, enable WIF |
| `infra/terraform/variables.tf` | Modify | Add WIF variables |
| `infra/terraform/outputs.tf` | Modify | Add WIF outputs |
| `scripts/ci/check_security.sh` | Create | Security validation |
| `.github/workflows/ci.yml` | Modify | Add security check |
| `000-docs/221-AA-PLAN-*.md` | Create | This file |
| `000-docs/222-RB-SEC-*.md` | Create | Security runbook |
| `000-docs/223-AA-REPT-*.md` | Create | AAR |

## Limitations

- WIF requires GitHub repo to be configured (one-time setup)
- Existing workflows need update to use WIF auth
- Some manual GCP console work may be needed for initial WIF setup

---
**Last Updated:** 2025-12-12
