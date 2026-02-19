#!/bin/bash
# deploy_all_agents.sh - Deploy all Hard Mode agents to Vertex AI Agent Engine

set -e

# Configuration
export GCP_PROJECT_ID="bobs-brain"
export GCP_LOCATION="us-central1"
export DEPLOYMENT_ENV="dev"

# Agent list in deployment order
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

# Track deployments
DEPLOYED=()
FAILED=()

for agent in "${AGENTS[@]}"; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Deploying: $agent"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # ARV check
  echo "🔍 Running ARV checks..."
  if python3 scripts/check_inline_deploy_ready.py \
    --agent-name "$agent" \
    --env dev; then
    echo "✅ ARV checks passed"
  else
    echo "❌ ARV check failed for $agent"
    FAILED+=("$agent")
    continue
  fi

  # Deploy
  echo "🚀 Deploying to Agent Engine..."
  if python3 -m agents.agent_engine.deploy_inline_source \
    --agent-name "$agent" \
    --project "$GCP_PROJECT_ID" \
    --location "$GCP_LOCATION" \
    --env dev \
    --execute; then
    echo "✅ $agent deployed successfully"
    DEPLOYED+=("$agent")
  else
    echo "❌ Deployment failed for $agent"
    FAILED+=("$agent")
  fi

  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Deployment Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployed: ${#DEPLOYED[@]} / ${#AGENTS[@]}"
for agent in "${DEPLOYED[@]}"; do
  echo "   - $agent"
done

if [ ${#FAILED[@]} -gt 0 ]; then
  echo ""
  echo "❌ Failed: ${#FAILED[@]}"
  for agent in "${FAILED[@]}"; do
    echo "   - $agent"
  done
fi

echo ""
echo "📋 Next steps:"
echo "  1. List deployed agents to get IDs"
echo "  2. Update 000-docs/agent-engine-registry.csv with Agent Engine IDs"
echo "  3. Run smoke tests"
