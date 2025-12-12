# Phase 42: Agent Engine Dev Deployment via CI – PLAN

**Date:** 2025-12-12
**Status:** In Progress
**Branch:** `feature/phase-42-agent-engine-dev-ci-deploy`

## Goals

Deploy Bob and Foreman to Vertex AI Agent Engine (dev environment) via CI only. No manual `gcloud` commands.

### What This Phase Achieves

1. **CI-based dev deployment** – GitHub Actions workflow deploys Bob and Foreman
2. **Smoke tests integrated** – Post-deployment health checks validate the deployed agents
3. **No manual gcloud** – All deployment via scripts invoked from CI, not manual CLI
4. **Fallback documentation** – Clear docs on what to do if deployment fails

## Analysis of Existing Infrastructure

### Already Exists ✅

| Component | Location | Status |
|-----------|----------|--------|
| Deploy script | `scripts/deploy_inline_source.py` | ✅ Working |
| Dev workflow | `.github/workflows/agent-engine-inline-dev-deploy.yml` | ✅ Manual-only |
| Smoke test | `scripts/smoke_test_bob_agent_engine_dev.py` | ✅ Working |
| Make targets | `Makefile` | ✅ Partial (missing foreman dev) |

### What This Phase Adds

1. **Optional push trigger** – Deploy on push to main (configurable)
2. **Smoke tests in workflow** – Run after deploy to validate
3. **Foreman support in workflow** – Deploy foreman alongside bob
4. **Combined dev deploy target** – `deploy-dev-all` for bob + foreman

## High-Level Steps

### Step 1: Enhance Workflow

Update `.github/workflows/agent-engine-inline-dev-deploy.yml`:
- Add optional push to main trigger (disabled by default, can enable via env var)
- Add smoke test step after deploy
- Support both bob and foreman deployment
- Add workflow_call for reuse

### Step 2: Add Make Targets

Add to `Makefile`:
```makefile
deploy-bob-dev:         # Deploy bob to dev via script
deploy-foreman-dev:     # Deploy foreman to dev via script
deploy-dev-all:         # Deploy bob + foreman to dev
smoke-agent-engine-dev: # Run smoke tests for all dev agents
```

### Step 3: Create Smoke Test for Foreman

Create `scripts/smoke_test_foreman_agent_engine_dev.py`:
- Similar pattern to bob smoke test
- Uses `FOREMAN_AGENT_ENGINE_NAME_DEV` env var

### Step 4: Documentation

Create:
- This PLAN doc (211)
- AAR doc (212) after completion

## Design Decisions

### Push Trigger: Disabled by Default

The workflow supports push to main but is disabled by default. This is intentional:
- Dev deploys should be explicit (intentional)
- Prevents accidental deploys on every merge
- Can be enabled by setting `AUTO_DEPLOY_DEV=true` in workflow

### Smoke Tests as Optional Step

Smoke tests run after deploy but use `continue-on-error: true`:
- Deployment success is the primary gate
- Smoke test failure logs a warning but doesn't fail the workflow
- This allows for transient Agent Engine startup delays

### No Changes to Deploy Script

The existing `scripts/deploy_inline_source.py` already supports:
- `--agent bob|foreman`
- `--env dev`
- Dry-run mode
- WIF authentication

No changes needed to the deploy script itself.

## Explicit Rules

1. **No manual gcloud** – All deployment via CI workflows or Make targets (which call Python scripts)
2. **ARV gates must pass** – Deployment blocked if ARV checks fail
3. **Dry-run first** – Always validate config before real deployment
4. **Smoke tests log only** – Don't fail deployment on smoke test failure (transient issues)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `.github/workflows/agent-engine-inline-dev-deploy.yml` | Modify | Add smoke tests, foreman support |
| `scripts/smoke_test_foreman_agent_engine_dev.py` | Create | Smoke test for foreman |
| `Makefile` | Modify | Add new dev deploy targets |
| `000-docs/211-AA-PLAN-*.md` | Create | This file |
| `000-docs/212-AA-REPT-*.md` | Create | AAR after completion |

## Fallback Plan

If deployment fails:
1. Capture error in AAR
2. Leave workflow in place with TODO comments
3. Add `if: always() && false` to skip problematic steps temporarily
4. Document the specific API error and remediation steps

---
**Last Updated:** 2025-12-12
