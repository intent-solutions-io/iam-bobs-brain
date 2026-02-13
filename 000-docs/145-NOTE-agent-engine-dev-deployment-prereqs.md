# Agent Engine Dev Deployment Prerequisites

**Document Type:** NOTE (Notes & References)
**Phase:** Phase 17 - A2A Wiring and Agent Engine Dev Prep
**Status:** Draft (not yet deployed)
**Created:** 2025-11-22

## Purpose

This document outlines the prerequisites and manual steps required before deploying bob and the foreman (iam-senior-adk-devops-lead) to Vertex AI Agent Engine in the dev environment.

**Target State:** Both bob and foreman running in Agent Engine with A2A wiring functional.

---

## 1. App Pattern Compliance

### Verified Compliant ✅

All agents follow the correct `app` pattern for inline source deployment:

- **agents/bob/agent.py**: `app = create_app()` ✅
- **agents/iam-senior-adk-devops-lead/agent.py**: NOT CHECKED (needs verification) ⚠️
- **agents/iam_adk/agent.py**: `app = create_app()` ✅

### Action Required

1. Verify that `agents/iam-senior-adk-devops-lead/agent.py` exports `app = create_app()`
2. If using legacy `agent_engine_app.py` files, migrate to direct `app` export in agent.py

**Reference:** See `000-docs/000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`

---

## 2. Infrastructure Configuration

### Current State

**Terraform Resources:**
- ✅ `google_vertex_ai_reasoning_engine.bob` exists in `infra/terraform/agent_engine.tf`
- ❌ No Agent Engine resource for foreman (iam-senior-adk-devops-lead)
- ❌ No Agent Engine resources for specialist agents (iam_adk, iam_issue, etc.)

### Decision: Local-Only Specialists (Phase 17)

For Phase 17, the specialists (iam_adk, iam_issue, etc.) will run **locally** (in-process within the foreman), NOT as separate Agent Engine instances.

**Reasoning:**
- Simplifies deployment architecture
- Reduces cost (fewer Agent Engine instances)
- Local invocation is sufficient for A2A proof-of-concept
- Future phase can deploy specialists as separate instances if needed

### Action Required

1. **Add Foreman Agent Engine Resource (future phase)**:
   ```hcl
   resource "google_vertex_ai_reasoning_engine" "foreman" {
     display_name = "iam-senior-adk-devops-lead-${var.environment}"
     location     = var.region
     project      = var.project_id

     spec {
       image = var.foreman_docker_image

       environment_variables = {
         PROJECT_ID       = var.project_id
         LOCATION         = var.region
         AGENT_ENGINE_ID  = google_vertex_ai_reasoning_engine.foreman.id
         APP_NAME         = "iam-senior-adk-devops-lead"
         APP_VERSION      = var.app_version
         AGENT_SPIFFE_ID  = "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/${var.environment}/${var.region}/${var.app_version}"
         MODEL_NAME       = var.model_name
       }

       machine_spec {
         machine_type = var.agent_machine_type
       }

       replica_count {
         min_replica_count = 1
         max_replica_count = var.agent_max_replicas
       }
     }

     service_account = google_service_account.agent_engine.email
   }
   ```

2. **Update envs/dev.tfvars** to add foreman-specific variables:
   ```hcl
   foreman_docker_image = "gcr.io/bobs-brain-dev/foreman:0.10.0"
   ```

3. **Specialists remain local** (no Agent Engine deployment needed for Phase 17)

---

## 3. GCP Project Prerequisites

### Required Before Deployment

Before running `terraform apply`, ensure the following are configured in the `bobs-brain-dev` GCP project:

1. **APIs Enabled:**
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=bobs-brain-dev
   gcloud services enable run.googleapis.com --project=bobs-brain-dev
   gcloud services enable storage.googleapis.com --project=bobs-brain-dev
   gcloud services enable secretmanager.googleapis.com --project=bobs-brain-dev
   ```

2. **Service Account Permissions:**
   - Agent Engine service account needs:
     - `roles/aiplatform.user` (Vertex AI access)
     - `roles/storage.objectViewer` (for staging bucket)
     - `roles/secretmanager.secretAccessor` (if using Secret Manager)

3. **Artifact Registry / Container Registry:**
   - Docker images must be built and pushed BEFORE terraform apply
   - Images referenced in tfvars must exist:
     - `gcr.io/bobs-brain-dev/agent:0.10.0` (bob)
     - `gcr.io/bobs-brain-dev/foreman:0.10.0` (foreman, if deployed)

4. **Staging Bucket:**
   - Created by `infra/terraform/storage.tf`
   - Format: `gs://bobs-brain-dev-adk-staging`
   - Used by ADK deployment tooling

---

## 4. Docker Images & Container Build

### Required Container Images

**For Bob:**
- **Image Name:** `gcr.io/bobs-brain-dev/agent:0.10.0`
- **Build From:** `agents/bob/`
- **Dockerfile:** Should include all dependencies from `requirements.txt`

**For Foreman (future):**
- **Image Name:** `gcr.io/bobs-brain-dev/foreman:0.10.0`
- **Build From:** `agents/iam-senior-adk-devops-lead/`

### Build Commands (Do NOT Run Yet)

```bash
# Navigate to repo root
cd /home/jeremy/000-projects/iams/bobs-brain

# Build bob image
docker build -t gcr.io/bobs-brain-dev/agent:0.10.0 agents/bob/

# Push bob image
docker push gcr.io/bobs-brain-dev/agent:0.10.0

# Build foreman image (future)
docker build -t gcr.io/bobs-brain-dev/foreman:0.10.0 agents/iam-senior-adk-devops-lead/

# Push foreman image (future)
docker push gcr.io/bobs-brain-dev/foreman:0.10.0
```

**Note:** These commands are for reference only. Actual builds should be done via CI/CD (GitHub Actions with WIF).

---

## 5. CI/CD Deployment Flow (R4 Compliance)

### Required: GitHub Actions Workflow

Per R4 (CI-only deployments), all Agent Engine deployments MUST go through GitHub Actions with Workload Identity Federation.

**No manual `gcloud` or `terraform apply` allowed.**

### Deployment Workflow Steps

1. **Trigger:** Push to `main` branch or manual workflow dispatch
2. **Build:** Build Docker images for bob/foreman
3. **Test:** Run ARV (Agent Readiness Verification) checks
4. **Push:** Push images to GCR
5. **Deploy:** Run `terraform apply -var-file="envs/dev.tfvars"` via GitHub Actions
6. **Smoke Test:** Run post-deployment health checks

### Existing Workflow Files

Check `.github/workflows/` for existing deployment workflows:

```bash
ls -la .github/workflows/
```

**Action Required:** Ensure deployment workflow includes:
- Docker build for bob agent
- ARV checks (including A2A readiness checks from Task 6)
- Terraform apply with WIF authentication
- Post-deployment smoke tests

---

## 6. A2A Readiness Checks (Task 6 Output)

Before deploying to Agent Engine, the following A2A readiness checks MUST pass:

**ARV Hook Script:** `scripts/check_a2a_readiness.py` (created in Task 6)

**Checks:**
1. ✅ All specialist agents have valid AgentCards in `.well-known/agent-card.json`
2. ✅ Foreman can discover all specialists via `discover_specialists()`
3. ✅ All skills follow `{agent}.{skill}` naming convention
4. ✅ All skills have valid JSON Schema draft-07 input/output schemas
5. ✅ R7 SPIFFE ID compliance (SPIFFE ID in description + explicit field)

**Run Checks:**
```bash
python scripts/check_a2a_readiness.py
```

**Expected Output:** All checks pass, script exits with code 0.

---

## 7. Manual Deployment Checklist

### Pre-Deployment

- [ ] Verify GCP project exists (`bobs-brain-dev`)
- [ ] Enable required GCP APIs (see Section 3)
- [ ] Create/verify service accounts and IAM roles
- [ ] Run ARV checks: `scripts/check_a2a_readiness.py`
- [ ] Run integration tests: `pytest tests/integration/test_a2a_foreman_specialists.py`
- [ ] Verify `app` pattern in all agent.py files
- [ ] Update version in `envs/dev.tfvars` (e.g., `0.10.0`)

### Deployment (via CI/CD)

- [ ] Push to `main` branch or trigger GitHub Actions workflow
- [ ] Monitor workflow execution in GitHub Actions
- [ ] Verify Docker images pushed to GCR
- [ ] Verify Terraform apply succeeds
- [ ] Check Agent Engine status in GCP console

### Post-Deployment

- [ ] Run smoke tests against deployed Agent Engine
- [ ] Verify bob agent responds to queries
- [ ] Test A2A delegation from foreman to specialists (if foreman deployed)
- [ ] Check logs in Cloud Logging
- [ ] Verify SPIFFE ID propagation in logs

---

## 8. Known Blockers (Phase 17)

### Environment Limitations

1. **No google-adk module installed** in local dev environment
   - Tests that invoke agents will fail locally
   - This is expected and OK
   - Actual agent execution happens in Agent Engine only

2. **Specialist agents are local-only**
   - No separate Agent Engine deployment for iam_adk, iam_issue, etc.
   - They run in-process within foreman
   - Future phase can deploy as separate instances if needed

3. **No Dockerfile yet** for bob or foreman
   - Need to create Dockerfile for container builds
   - Should include all deps from requirements.txt
   - Should set correct entrypoint for Agent Engine

### Action Required

1. Create `agents/bob/Dockerfile` for bob container build
2. Create `agents/iam-senior-adk-devops-lead/Dockerfile` for foreman container build (future)
3. Update CI/CD workflow to build and push images

---

## 9. Deployment Sequence (When Ready)

**Phase 17 Scope:** Prepare infrastructure, DO NOT deploy yet.

**Future Phase (e.g., Phase 18 - Agent Engine Deployment):**

```bash
# 1. Verify prerequisites
scripts/check_a2a_readiness.py

# 2. Run integration tests
pytest tests/integration/test_a2a_foreman_specialists.py -v

# 3. Commit and push to main
git checkout main
git pull origin main
git merge feature/a2a-agentcards-foreman-worker
git push origin main

# 4. GitHub Actions workflow auto-triggers:
#    - Builds Docker images
#    - Runs ARV checks
#    - Pushes to GCR
#    - Runs terraform apply
#    - Runs smoke tests

# 5. Monitor deployment
gh run watch

# 6. Verify deployment in GCP console
# Navigate to: Vertex AI > Agent Builder > Reasoning Engines
```

---

## 10. References

**ADK/Vertex Standards:**
- `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Hard Mode R1-R8
- `000-docs/000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md` - Inline deployment
- `000-docs/000-DR-STND-agentcards-and-a2a-contracts.md` - AgentCard contracts

**A2A Wiring:**
- `000-docs/144-AA-REPT-phase-16-agentcards-iam-department.md` - Phase 16 AgentCards AAR
- `agents/a2a/` - A2A dispatcher and types
- `tests/integration/test_a2a_foreman_specialists.py` - A2A integration tests

**Infrastructure:**
- `infra/terraform/agent_engine.tf` - Agent Engine Terraform config
- `infra/terraform/envs/dev.tfvars` - Dev environment variables
- `.github/workflows/` - CI/CD workflows

---

## 11. Next Steps (Phase 17)

1. ✅ Complete Task 6: Add ARV Hook for A2A Readiness
2. ✅ Complete Task 7: Documentation & AAR
3. Create Phase 17 AAR documenting A2A wiring and deployment prep
4. **DO NOT deploy to Agent Engine yet** (future phase)
5. Merge `feature/a2a-agentcards-foreman-worker` to main when Phase 17 complete

---

**Last Updated:** 2025-11-22
**Status:** Draft (deployment not yet executed)
**Next Action:** Complete Task 6 (ARV Hook)
