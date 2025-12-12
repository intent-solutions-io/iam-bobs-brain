# Phase 30: Stage Environment Baseline

**Date:** 2025-12-11
**Status:** In Progress
**Branch:** `feature/phase-30-stage-env-baseline`

## Objective

Define a stage environment configuration enabling dev -> stage -> prod progression for Bob's Brain deployments.

## Inputs

- Existing `infra/terraform/envs/prod.tfvars` (current production config)
- Existing `infra/terraform/envs/dev.tfvars` (development config)
- Existing `infra/terraform/envs/staging.tfvars` (outdated, to be replaced)
- Phase 23 & 24 documentation (Slack Bob deployment patterns)
- Phase 27 deployment validation work

## Non-Goals

- Actually provisioning stage infrastructure in GCP
- Creating real GCP projects or resources
- Applying Terraform changes to any environment
- Using direct gcloud CLI commands

## Constraints

- No production changes
- No direct gcloud usage (R4 compliance)
- Config must be syntactically valid even with placeholder values
- Stage config follows same patterns as prod

## Deliverables

1. **Terraform Stage Config**
   - `infra/terraform/envs/stage.tfvars` (replaces outdated staging.tfvars)
   - Aligned with current v0.14.x patterns from dev/prod
   - Clear TODO placeholders for IDs that need real values

2. **CI Workflow for Stage**
   - `.github/workflows/terraform-stage.yml`
   - Plan-only (never applies)
   - Uses stage.tfvars

3. **Documentation**
   - This plan document
   - AAR documenting results

## Implementation Steps

1. Create stage.tfvars modeled after prod.tfvars with placeholders
2. Add terraform-stage.yml workflow (plan-only)
3. Run local validation (format, validate)
4. Document any validation errors in AAR

---
**Last Updated:** 2025-12-11
