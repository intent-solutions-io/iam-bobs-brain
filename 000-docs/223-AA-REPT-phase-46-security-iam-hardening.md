# Phase 46: Security & IAM Hardening – AAR

**Date:** 2025-12-12
**Status:** Complete
**Branch:** `feature/phase-46-security-iam-hardening`

## Summary

Applied security hardening to IAM, CI/CD infrastructure, and added comprehensive security validation. Replaced overly broad `roles/editor` with specific permissions and enabled Workload Identity Federation support.

## What Was Built

### 1. IAM Hardening (`infra/terraform/iam.tf`)

**Removed:**
- `roles/editor` - overly broad permission

**Added specific permissions:**
- `roles/iam.serviceAccountUser` - for service account impersonation
- `roles/secretmanager.admin` - for managing secrets
- `roles/logging.logWriter` - for writing logs
- `roles/artifactregistry.writer` - for pushing Docker images

### 2. Workload Identity Federation

Enabled WIF resources (conditional on `enable_wif` variable):
- `google_iam_workload_identity_pool` - GitHub Actions pool
- `google_iam_workload_identity_pool_provider` - OIDC provider
- `google_service_account_iam_member` - WIF binding

New variables:
- `enable_wif` - Toggle WIF (default: false)
- `github_repository` - Target repo (default: intent-solutions-io/bobs-brain)

New outputs:
- `wif_enabled` - Whether WIF is enabled
- `wif_pool_name` - Pool name
- `wif_provider_name` - Provider name

### 3. Security Validation Script

Created `scripts/ci/check_security.sh`:
- Checks for service account keys in repo
- Scans for hardcoded secrets (Slack tokens, GitHub PATs, AWS keys, Google API keys)
- Validates Terraform for overly permissive IAM
- Checks for .env files in git

### 4. CI Integration

Added security validation step to `.github/workflows/ci.yml`:
- Runs `check_security.sh` before Bandit scan
- Fails CI if security issues found

### 5. Make Target

Added `make check-security` target for local validation.

### 6. Security Runbook

Created `000-docs/222-RB-SEC-bobs-brain-security-runbook.md`:
- Service account documentation
- IAM best practices
- Secret management procedures
- Incident response playbook
- Compliance checklist

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `infra/terraform/iam.tf` | Modified | +60, -35 |
| `infra/terraform/variables.tf` | Modified | +18 |
| `infra/terraform/outputs.tf` | Modified | +18 |
| `scripts/ci/check_security.sh` | Created | 128 |
| `.github/workflows/ci.yml` | Modified | +3 |
| `Makefile` | Modified | +4 |
| `000-docs/221-AA-PLAN-*.md` | Created | 108 |
| `000-docs/222-RB-SEC-*.md` | Created | 265 |
| `000-docs/223-AA-REPT-*.md` | Created | This file |

## Validation

```bash
# Security check
bash scripts/ci/check_security.sh  # ✅ PASSED

# Terraform format
terraform fmt -check  # ✅ PASSED

# Make target
make check-security  # ✅ PASSED
```

## IAM Changes Summary

| Before | After |
|--------|-------|
| `roles/editor` | Removed |
| `roles/run.admin` | Kept |
| `roles/aiplatform.admin` | Kept |
| `roles/storage.admin` | Kept |
| - | `roles/iam.serviceAccountUser` (added) |
| - | `roles/secretmanager.admin` (added) |
| - | `roles/logging.logWriter` (added) |
| - | `roles/artifactregistry.writer` (added) |

## WIF Enablement

To enable WIF for keyless CI/CD authentication:

```hcl
# In tfvars
enable_wif = true
github_repository = "intent-solutions-io/bobs-brain"
```

Then update GitHub Actions workflow to use WIF authentication.

## Commit Summary

1. `feat(terraform): harden IAM and enable WIF support`
   - Remove roles/editor, add specific permissions
   - Add WIF resources (conditional)
   - Add new variables and outputs

2. `feat(ci): add security validation script`
   - Create check_security.sh
   - Add to CI workflow
   - Add Make target

3. `docs(000-docs): add Phase 46 PLAN, runbook, and AAR`
   - Planning doc, security runbook, AAR

## Next Steps

- Phase 47: RAG / Knowledge Base Wiring
- Phase 48: IAM Department Export Pack

---
**Last Updated:** 2025-12-12
