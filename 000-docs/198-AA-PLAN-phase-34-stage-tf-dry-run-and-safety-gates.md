# Phase 34: Stage Terraform Dry-Run & Safety Gates

**Date:** 2025-12-11
**Status:** In Progress
**Branch:** `feature/phase-34-stage-tf-dry-run`

## Objective

Make it safe and easy to run Terraform plans for the stage environment without accidental applies. Add CI workflow with placeholder guards.

## Inputs

- Phase 30 `stage.tfvars` (on PR #19, not yet merged)
- Existing `terraform-prod.yml` workflow pattern
- Existing Terraform module structure

## Non-Goals

- Running `terraform apply` in any environment
- Changing behavior of existing prod Terraform workflow
- Modifying actual stage infrastructure

## Deliverables

1. **Stage Plan Workflow**
   - `.github/workflows/terraform-stage-plan.yml`
   - Trigger: `workflow_dispatch` only (manual)
   - Steps: fmt, init, validate, plan
   - Placeholder guard to catch TODO values

2. **Stage tfvars** (if not already present)
   - `infra/terraform/envs/stage.tfvars`
   - With clear TODO placeholders for values needing real IDs

3. **Documentation**
   - Phase PLAN doc (this file)
   - Phase AAR doc (after completion)

## Implementation Steps

1. Create plan doc (this file)
2. Create/verify stage.tfvars exists
3. Create terraform-stage-plan.yml workflow
4. Add placeholder guard step
5. Test locally (terraform fmt, validate)
6. Create AAR

## Safety Guards

The workflow will include:
```yaml
- name: Ensure stage tfvars has no TODO placeholders
  run: |
    if grep -q "TODO-SET-" infra/terraform/envs/stage.tfvars; then
      echo "Stage tfvars still contains TODO placeholders."
      exit 1
    fi
```

This ensures real plans only run after TODOs are replaced with actual values.

---
**Last Updated:** 2025-12-11
