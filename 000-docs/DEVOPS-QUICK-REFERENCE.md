# Bob's Brain - DevOps Quick Reference Card
**For:** Operations teams needing quick answers
**Updated:** 2025-11-21
**Version:** v0.10.0

---

## What Is Bob?

A **production AI agent system** on Google Cloud:
- **Runtime:** Vertex AI Agent Engine (managed)
- **Framework:** Google ADK only (R1)
- **Architecture:** Multi-agent (bob orchestrator + 8 specialists)
- **Gateways:** Cloud Run (A2A protocol + Slack)
- **Deployment:** GitHub Actions CI/CD + Terraform

---

## One-Time Setup

```bash
# 1. GCP Project
export PROJECT_ID=your-gcp-project
export LOCATION=us-central1
gcloud config set project ${PROJECT_ID}

# 2. Enable APIs (Terraform does this)
# Required: aiplatform, run, compute, storage, discoveryengine, iam

# 3. Clone & Test Locally
git clone https://github.com/jeremylongshore/bobs-brain.git
cd bobs-brain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/ci/check_nodrift.sh  # MUST PASS

# 4. Terraform State Bucket
gsutil mb gs://${PROJECT_ID}-tf-state

# 5. GitHub Secrets (Workload Identity)
# Instructions: 000-docs/068-OD-CONF-github-secrets-configuration.md
# Need: WIF_PROVIDER, WIF_SERVICE_ACCOUNT

# 6. Deploy Infrastructure
cd infra/terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state"
terraform apply -var-file=envs/dev.tfvars

# Done! Push to main triggers automatic CI/CD
git push origin main
```

---

## Health Checks (Daily - 5 min)

```bash
#!/bin/bash
PROJECT_ID="your-project"
DEPLOYMENT_ENV="prod"
LOCATION="us-central1"

# Agent Engine
echo "Agent Engine:"
gcloud ai agent-engines list --region=${LOCATION}

# Cloud Run
echo "Cloud Run:"
gcloud run services list --region=${LOCATION}

# Gateway test
echo "A2A Gateway:"
curl -X POST https://a2a-gateway-${DEPLOYMENT_ENV}.run.app/call/bob \
  -H "Content-Type: application/json" \
  -d '{"query":"health check"}'

# Errors (last 1 hour)
echo "Recent errors:"
gcloud logging read "severity=ERROR" --limit 10 --format json
```

---

## Deployment Commands

### Deploy to Dev (Automatic)
```bash
# Just push to main - GitHub Actions handles everything
git push origin main
# Watch workflow: gh workflow run ci.yml
```

### Deploy to Staging (Manual)
```bash
# From GitHub UI or command line
gh workflow run deploy-staging.yml \
  --ref main \
  --field skip_arv=false
```

### Deploy to Production (Manual - High Ceremony)
```bash
gh workflow run deploy-prod.yml \
  --ref main \
  --field skip_arv=false \
  --field verbose=true
```

### Emergency Deploy (Skip ARV)
```bash
# ONLY in true emergencies
gh workflow run deploy-prod.yml \
  --ref main \
  --field skip_arv=true
```

### Manual Deployment (Local - Development Only)
```bash
# NOT for production - use CI/CD
cd agents/bob
adk deploy agent_engine \
  --project-id=${PROJECT_ID} \
  --region=us-central1 \
  --staging-bucket=gs://${PROJECT_ID}-adk-staging
```

---

## Common Issues & Fixes

### Agent Not Responding
```
Symptoms: 503 error, timeout, no response

1. Check Agent Engine state
   gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION}
   Look for: desiredReplicaCount vs actualReplicaCount (should be equal)

2. Wait 30-60 seconds (cold start) and retry

3. Check gateway logs
   gcloud logging read "resource.type=cloud_run_revision AND \
     resource.labels.service_name=a2a-gateway" --limit 50

4. Check agent logs
   gcloud logging read "agent_id=bob" --limit 50

5. If stuck: Restart Agent Engine
   gcloud ai agent-engines delete ${AGENT_ENGINE_ID} --region=${LOCATION}
   # Terraform will recreate it
```

### Drift Detection Fails
```
Symptom: CI fails with "Drift violations detected"

Causes & Quick Fixes:

1. LangChain/CrewAI imported
   Fix: Remove alternative frameworks (ADK only - R1)

2. Runner imports in service/
   Fix: Remove Runner, use REST API calls (R3)

3. Credentials in code
   Fix: Remove keys, use Secret Manager (R4)

Solution: Look at failing line, delete non-ADK code
```

### GCS Org Storage Not Writing
```
Symptom: Portfolio runs but no files in GCS

Quick Checks:

1. Feature flag enabled?
   export ORG_STORAGE_WRITE_ENABLED=true

2. Bucket exists?
   gsutil ls gs://intent-org-knowledge-hub-dev/
   If not: terraform apply -var-file=envs/dev.tfvars

3. Service account has permission?
   gcloud projects get-iam-policy ${PROJECT_ID} | grep storage

4. Run write test
   python3 scripts/check_org_storage_readiness.py --write-test
```

### Slack Integration Broken
```
Symptom: Slack messages don't trigger agent

1. Check webhook running
   gcloud run services describe slack-webhook --region=${LOCATION}

2. Verify secrets
   gcloud secrets versions access latest --secret=slack-bot-token
   gcloud secrets versions access latest --secret=slack-signing-secret

3. Verify Slack app settings
   Slack UI → Your Apps → bobs_brain → Event Subscriptions
   Request URL should match deployed webhook

4. Check logs
   gcloud logging read "resource.type=cloud_run_revision AND \
     resource.labels.service_name=slack-webhook" --limit 50
```

---

## Infrastructure Commands

### View Current State
```bash
cd infra/terraform

# See what exists
terraform state list
terraform state show google_cloud_aiplatform_agent_engine.bob

# See outputs (URLs, service accounts)
terraform output

# Detailed state dump
terraform state pull | jq '.'
```

### Change Machine Type (Prod)
```bash
cd infra/terraform

# Edit envs/prod.tfvars
# agent_machine_type = "n1-standard-8"  # Was n1-standard-4

# Plan & apply
terraform plan -var-file=envs/prod.tfvars
terraform apply -var-file=envs/prod.tfvars

# Wait ~10 min for new instance
```

### Scale Replicas
```bash
cd infra/terraform

# Edit envs/{env}.tfvars
# agent_max_replicas = 10  # Was 5

terraform apply -var-file=envs/{env}.tfvars
```

### Backup Terraform State
```bash
cd infra/terraform
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).json
gsutil cp backup-*.json gs://backups-prod/terraform/
```

### Destroy & Recreate (Emergency)
```bash
# WARNING: Destructive operation
cd infra/terraform

# Show what will be deleted
terraform plan -destroy -var-file=envs/prod.tfvars

# Delete
terraform destroy -var-file=envs/prod.tfvars

# Recreate
terraform apply -var-file=envs/prod.tfvars
```

---

## Monitoring & Logs

### Real-Time Logs (Last 50 entries)
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json \
  | jq '.[] | {timestamp: .timestamp, severity: .severity, message: .textPayload}'
```

### Error Only (Last 24 Hours)
```bash
gcloud logging read "severity=ERROR AND timestamp>='2025-11-21T00:00:00Z'" \
  --limit 100 \
  --format="table(timestamp, severity, jsonPayload.message)"
```

### Agent Execution Trace
```bash
# See where time is spent
gcloud trace list --limit 10
gcloud trace describe ${TRACE_ID}
```

### Create Dashboard (Cloud Monitoring)
```bash
# Manual: Cloud Console → Monitoring → Dashboards → Create Dashboard
# Add charts for:
# - Agent Engine CPU/Memory
# - Cloud Run request count/latency
# - Errors (5xx responses)
# - GCS write latency
```

---

## Testing & Validation

### Local Tests (Before Pushing)
```bash
# Drift detection (MUST PASS)
bash scripts/ci/check_nodrift.sh

# Unit tests
pytest tests/unit/ -v

# A2A contract validation
pytest tests/unit/test_agentcard_json.py -v

# All tests with coverage
pytest --cov=agents --cov-report=html
# View: htmlcov/index.html
```

### ARV Readiness Check
```bash
# Agent readiness verification (used in CI)
python3 scripts/check_arv_minimum.py

# More detailed
python3 scripts/check_arv_agents.py
python3 scripts/check_arv_config.py
```

### Smoke Test (Post-Deployment)
```bash
# Agent responsiveness
python3 scripts/run_agent_engine_dev_smoke.py

# Portfolio orchestrator
python3 scripts/run_portfolio_swe.py --repos bobs-brain --mode preview

# Storage readiness
python3 scripts/check_org_storage_readiness.py --write-test
```

---

## Secrets & Credentials

### Rotate Slack Credentials
```bash
# 1. Get new token from Slack App settings
# 2. Update Secret Manager
gcloud secrets versions add slack-bot-token \
  --data-file=<(echo 'xoxb-new-token-here')

gcloud secrets versions add slack-signing-secret \
  --data-file=<(echo 'new-signing-secret-here')

# 3. Redeploy webhook
gh workflow run deploy-slack-webhook.yml --ref main
```

### Rotate GitHub WIF Credentials
```bash
# 1. Regenerate OIDC token in GitHub Actions settings
# 2. Update GitHub Secrets
#    - WORKLOAD_IDENTITY_PROVIDER
#    - SERVICE_ACCOUNT_EMAIL

# 3. Next CI/CD run uses new credentials automatically
```

### View All Secrets
```bash
gcloud secrets list --format="table(name,created.date())"

# View secret value (careful!)
gcloud secrets versions access latest --secret=slack-bot-token
```

---

## Useful Commands Cheat Sheet

```bash
# Project setup
export PROJECT_ID=your-project
export LOCATION=us-central1
gcloud config set project ${PROJECT_ID}

# Terraform
cd infra/terraform
terraform init
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
terraform output

# Agents
gcloud ai agent-engines list --region=${LOCATION}
gcloud ai agent-engines describe ${AGENT_ENGINE_ID} --region=${LOCATION}

# Cloud Run
gcloud run services list --region=${LOCATION}
gcloud run services describe a2a-gateway --region=${LOCATION}
gcloud run logs read a2a-gateway --region=${LOCATION}

# GCS
gsutil ls gs://intent-org-knowledge-hub-dev/
gsutil du -s gs://intent-org-knowledge-hub-dev/
gsutil stat gs://intent-org-knowledge-hub-dev/portfolio/runs/

# Docker (build locally)
cd agents/bob
docker build -t gcr.io/${PROJECT_ID}/agent:latest .
docker push gcr.io/${PROJECT_ID}/agent:latest

# GitHub Actions
gh run list --workflow=ci.yml --limit 5
gh run view ${RUN_ID}
gh workflow run deploy-dev.yml --ref main
```

---

## When to Call an Engineer

| Issue | Action |
|-------|--------|
| Drift detection fails | Review error message, check code |
| Agent Engine won't deploy | Check Terraform, infrastructure, credentials |
| Memory Bank errors | Review agent.py for after_agent_callback |
| GCS write failing | Check service account IAM, bucket exists |
| Slack integration down | Check secrets, webhook URL, Slack app settings |
| Performance degradation | Check metrics, check logs, scale if needed |
| Cost spike | Review Cloud Billing, check for runaway resources |
| Unsure about anything | Read README.md or 000-docs/000-* files |

---

## Quick Facts

- **Repo:** https://github.com/jeremylongshore/bobs-brain
- **Version:** 0.10.0 (released 2025-11-21)
- **Python:** 3.12+ required
- **Cost:** ~$300-400/month (all environments)
- **Uptime Target:** 99.5% (SLA for Agent Engine)
- **Deploy Time:** ~5-10 minutes
- **Hard Mode Rules:** 8 enforced in CI/CD (R1-R8)
- **Agents:** 1 orchestrator + 8 specialists
- **Test Coverage:** 40+ tests, all passing
- **Documentation:** 100+ docs in 000-docs/

---

## First Time Setup Checklist

- [ ] GCP project created
- [ ] APIs enabled (Terraform does this)
- [ ] Workload Identity configured (GitHub → GCP)
- [ ] GitHub secrets set (WIF_PROVIDER, WIF_SERVICE_ACCOUNT)
- [ ] Terraform backend bucket created
- [ ] `terraform apply` run successfully
- [ ] Tests pass locally: `bash scripts/ci/check_nodrift.sh && pytest`
- [ ] First push to main triggers CI ✅
- [ ] First deployment to dev succeeds ✅
- [ ] Agent responds to test request ✅
- [ ] Logs appear in Cloud Logging ✅
- [ ] Alerts configured (email/Slack) ✅

---

## Documentation Map

**Quick Start:** README.md (1,027 lines)
**Architecture:** CLAUDE.md (209 lines)
**Full Analysis:** `claudes-docs/DEVOPS-ONBOARDING-ANALYSIS.md`
**This Card:** `claudes-docs/DEVOPS-QUICK-REFERENCE.md`
**Standards:** `000-docs/000-DR-STND-*.md`
**Runbooks:** `000-docs/*-OD-RBOK-*.md` & `000-docs/*-RB-OPS-*.md`
**Configuration:** `.env.example` & `infra/terraform/`

---

## Support & Escalation

**For Questions About:**
- Architecture & rules → README.md & CLAUDE.md
- Deployment → 000-docs/070-OD-RBOK-deployment-runbook.md
- Monitoring → 000-docs/069-OD-TELE-observability-telemetry-guide.md
- Troubleshooting → This card or full analysis document
- Code issues → GitHub Issues
- Urgent problems → Review logs first, then escalate

**Resources:**
- GitHub: https://github.com/jeremylongshore/bobs-brain
- Google ADK: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- Vertex AI: https://cloud.google.com/vertex-ai

---

**Version:** Quick Reference v1.0
**Last Updated:** 2025-11-21
**For:** DevOps teams operating Bob's Brain in production
