# Deploy All Hard Mode Agents to Vertex AI Agent Engine

**Document ID:** 185-AA-PLAN-deploy-all-hard-mode-agents-to-agent-engine
**Date:** 2025-12-22
**Author:** Claude Code (via /init)
**Status:** READY FOR EXECUTION
**Phase:** Agent Engine Deployment - Full Department

## Overview

This plan details the deployment of all 10 Hard Mode agents (Bob + iam-* department) to Vertex AI Agent Engine using inline source deployment.

## Agent Inventory

**Registry:** See `000-docs/agent-engine-registry.csv` for complete tracking.

### Agents to Deploy (10 total)

**Tier 1 - User Interface:**
1. **bob** - Conversational LLM agent (Slack interface)

**Tier 2 - Orchestration:**
2. **iam-senior-adk-devops-lead** - Foreman/workflow coordinator

**Tier 3 - Specialists (8 agents):**
3. **iam-adk** - ADK compliance checking
4. **iam-issue** - GitHub issue creation
5. **iam-fix-plan** - Fix planning
6. **iam-fix-impl** - Fix implementation
7. **iam-qa** - Testing and validation
8. **iam-doc** - Documentation
9. **iam-cleanup** - Repository hygiene
10. **iam-index** - Knowledge indexing

## Prerequisites

### 1. Environment Configuration

```bash
# Set in .env or export
export GCP_PROJECT_ID="bobs-brain"  # or your GCP project
export GCP_LOCATION="us-central1"
export DEPLOYMENT_ENV="dev"
```

### 2. GCP Authentication

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project bobs-brain

# Or use service account
gcloud auth activate-service-account --key-file=path/to/key.json
```

### 3. Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### 4. Python Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Deployment Steps

### Step 1: ARV Checks (Pre-Deployment Validation)

Run ARV checks for each agent before deployment:

```bash
# Check Bob (Tier 1)
make check-inline-deploy-ready AGENT_NAME=bob ENV=dev

# Check Foreman (Tier 2)
make check-inline-deploy-ready AGENT_NAME=iam-senior-adk-devops-lead ENV=dev

# Check each specialist (Tier 3)
for agent in iam-adk iam-issue iam-fix-plan iam-fix-impl iam-qa iam-doc iam-cleanup iam-index; do
  make check-inline-deploy-ready AGENT_NAME=$agent ENV=dev
done
```

**Expected:** All ARV checks should pass before proceeding.

### Step 2: Deploy Tier 1 (Bob)

```bash
# Deploy Bob first (user-facing agent)
python3 -m agents.agent_engine.deploy_inline_source \
  --agent-name bob \
  --project $GCP_PROJECT_ID \
  --location $GCP_LOCATION \
  --env dev \
  --execute

# Save the Agent Engine ID to .env
# Look for output: "Agent Engine ID: projects/.../reasoningEngines/XXXXX"
```

**Update registry:**
- Copy Agent Engine ID to `agent-engine-registry.csv` for bob
- Set `deployment_status=DEPLOYED`
- Add `deployed_date=YYYY-MM-DD`

### Step 3: Deploy Tier 2 (Foreman)

```bash
# Deploy foreman/orchestrator
python3 -m agents.agent_engine.deploy_inline_source \
  --agent-name iam-senior-adk-devops-lead \
  --project $GCP_PROJECT_ID \
  --location $GCP_LOCATION \
  --env dev \
  --execute
```

**Update registry:**
- Save Agent Engine ID for iam-senior-adk-devops-lead

### Step 4: Deploy Tier 3 (All Specialists)

Deploy each specialist agent:

```bash
# Deploy all 8 specialists
for agent in iam-adk iam-issue iam-fix-plan iam-fix-impl iam-qa iam-doc iam-cleanup iam-index; do
  echo "🚀 Deploying $agent..."

  python3 -m agents.agent_engine.deploy_inline_source \
    --agent-name $agent \
    --project $GCP_PROJECT_ID \
    --location $GCP_LOCATION \
    --env dev \
    --execute

  echo "✅ $agent deployed"
  echo ""
done
```

**Update registry:**
- Save Agent Engine ID for each specialist
- Mark all as `DEPLOYED`

### Step 5: Post-Deployment Verification

```bash
# Smoke test Bob
make smoke-bob-agent-engine-dev

# List all deployed agents
gcloud ai reasoning-engines list --region=us-central1

# Verify count (should see 10 new Hard Mode agents)
gcloud ai reasoning-engines list --region=us-central1 --format="table(name,displayName)" | grep -E "bob|iam-"
```

### Step 6: Update AgentCards

Each agent needs its Agent Engine ID in its AgentCard:

```bash
# For each agent, update .well-known/agent-card.json
# Add endpoint URL: projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}
```

### Step 7: Configure A2A Wiring

```bash
# Update Bob's configuration to call foreman
# Update foreman's configuration with all specialist endpoints
# Test A2A communication flow
```

## Expected Results

### After Deployment

**Agent Engine Console:**
- 10 new reasoning engines visible
- Display names: bob-hard-mode, iam-foreman, iam-*-specialist
- Status: DEPLOYED / READY

**CSV Registry:**
- All 10 agents have `deployment_status=DEPLOYED`
- All have valid `agent_engine_id` values
- All have `deployed_date` filled in

**Verification:**
```bash
# Count deployed Hard Mode agents
wc -l 000-docs/agent-engine-registry.csv
# Should show 13 lines (header + 10 new + 3 legacy)
```

## Deployment Order Rationale

1. **Bob first** - Entry point for users, can be tested independently
2. **Foreman second** - Orchestration layer, depends on Bob
3. **Specialists last** - Called by foreman, can deploy in parallel

## Rollback Plan

If deployment fails:

```bash
# Delete deployed agent
gcloud ai reasoning-engines delete AGENT_ENGINE_ID \
  --region=us-central1

# Update CSV registry
# Set deployment_status=FAILED
# Add notes about error
```

## Cost Estimates

**Per Agent:**
- Deployment: $0 (one-time)
- Runtime: Pay-per-query (Gemini 2.0 Flash pricing)
- Storage: Minimal (source code storage)

**Total (10 agents):**
- Initial deployment: $0
- Monthly (estimate): Depends on query volume

## Security Considerations

- All agents use Workload Identity Federation (no service account keys)
- SPIFFE IDs for all agents
- IAM roles: Minimal permissions per agent
- Network: Private Google network only

## Success Criteria

- [ ] All 10 agents deployed successfully
- [ ] ARV checks pass for all agents
- [ ] CSV registry complete with all Agent Engine IDs
- [ ] AgentCards updated with endpoints
- [ ] Bob → Foreman → Specialists A2A flow working
- [ ] Smoke tests pass
- [ ] No legacy agents affected

## Next Steps (After Deployment)

1. **Phase 26b:** A2A Integration Testing
2. **Phase 27:** Slack Integration with Hard Mode Bob
3. **Phase 28:** Migrate from Legacy Bob (agent 6448)
4. **Phase 29:** Decommission Legacy Agents (9040, 4704)

## References

- **ARV Standard:** `000-docs/000-DR-STND-arv-minimum-gate.md`
- **Inline Deployment:** `000-docs/000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md`
- **Agent Inventory:** `000-docs/085-OD-INVT-vertex-agent-inventory.md`
- **CSV Registry:** `000-docs/agent-engine-registry.csv`

## Appendix A: Quick Deployment Script

```bash
#!/bin/bash
# deploy_all_agents.sh - Deploy all Hard Mode agents

set -e

# Configuration
export GCP_PROJECT_ID="bobs-brain"
export GCP_LOCATION="us-central1"
export DEPLOYMENT_ENV="dev"

AGENTS=(
  "bob"
  "iam-senior-adk-devops-lead"
  "iam-adk"
  "iam-issue"
  "iam-fix-plan"
  "iam-fix-impl"
  "iam-qa"
  "iam-doc"
  "iam-cleanup"
  "iam-index"
)

echo "🚀 Deploying ${#AGENTS[@]} Hard Mode agents to Agent Engine"
echo "Project: $GCP_PROJECT_ID"
echo "Location: $GCP_LOCATION"
echo ""

for agent in "${AGENTS[@]}"; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Deploying: $agent"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # ARV check
  echo "🔍 Running ARV checks..."
  python3 scripts/check_inline_deploy_ready.py \
    --agent-name "$agent" \
    --env dev || {
    echo "❌ ARV check failed for $agent"
    exit 1
  }

  # Deploy
  echo "🚀 Deploying to Agent Engine..."
  python3 -m agents.agent_engine.deploy_inline_source \
    --agent-name "$agent" \
    --project "$GCP_PROJECT_ID" \
    --location "$GCP_LOCATION" \
    --env dev \
    --execute || {
    echo "❌ Deployment failed for $agent"
    exit 1
  }

  echo "✅ $agent deployed successfully"
  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All ${#AGENTS[@]} agents deployed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo "  1. Update agent-engine-registry.csv with Agent Engine IDs"
echo "  2. Run smoke tests: make smoke-bob-agent-engine-dev"
echo "  3. Verify in console: https://console.cloud.google.com/vertex-ai/reasoning-engines"
```

## Appendix B: Update Registry Script

```bash
#!/bin/bash
# update_registry.sh - Helper to update CSV with deployed agents

REGISTRY="000-docs/agent-engine-registry.csv"

# List all deployed agents
echo "📋 Deployed Agent Engines:"
gcloud ai reasoning-engines list \
  --region=us-central1 \
  --format="csv(name,displayName)" \
  | grep -E "bob|iam-"

echo ""
echo "💡 Update $REGISTRY with the Agent Engine IDs above"
echo "   Format: projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ID"
```

---

**Status:** Ready for execution
**Blocked By:** GCP_PROJECT_ID configuration
**Estimated Time:** 30-45 minutes for all 10 agents
**Risk Level:** LOW (dev environment)
