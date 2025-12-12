# Stage Environment Configuration
# terraform apply -var-file="envs/stage.tfvars"
#
# PURPOSE: Pre-production validation environment
# FLOW: dev -> stage -> prod
#
# NOTE: This file uses TODO placeholders for values that must be set
# before actual stage deployment. Search for "TODO-SET-" to find them.

# ==============================================================================
# Project Configuration
# ==============================================================================
project_id  = "bobs-brain-stage" # TODO-SET-STAGE-PROJECT-ID
region      = "us-central1"
environment = "stage"

# ==============================================================================
# Application Configuration
# ==============================================================================
app_name    = "bobs-brain"
app_version = "0.14.1"

# ==============================================================================
# Agent Engine Configuration
# ==============================================================================
# Bob agent (main orchestrator)
bob_docker_image = "gcr.io/bobs-brain-stage/agent:0.14.1"

# Foreman agent (iam-senior-adk-devops-lead)
foreman_docker_image = "gcr.io/bobs-brain-stage/foreman:0.14.1"

# Agent Engine compute resources (moderate for stage)
agent_machine_type = "n1-standard-2"
agent_max_replicas = 3

# Legacy single image (kept for backward compatibility)
agent_docker_image = "gcr.io/bobs-brain-stage/agent:0.14.1"

# ==============================================================================
# Gateway Configuration
# ==============================================================================
a2a_gateway_image     = "gcr.io/bobs-brain-stage/a2a-gateway:0.14.1"
slack_webhook_image   = "gcr.io/bobs-brain-stage/slack-webhook:0.14.1"
gateway_max_instances = 10

# ==============================================================================
# Slack Configuration (Stage)
# ==============================================================================
# Feature flag to enable Slack Bob gateway (R3 Cloud Run proxy)
slack_bob_enabled = true

# Secret Manager references (stage secrets)
# These secrets must exist in Secret Manager before deployment
slack_bot_token_secret_id = "slack-bot-token-stage"      # TODO-SET-STAGE-SECRET
slack_signing_secret_id   = "slack-signing-secret-stage" # TODO-SET-STAGE-SECRET

# DEPRECATED: Direct token variables (use Secret Manager instead)
slack_bot_token      = "" # Ignored when slack_bot_token_secret_id is set
slack_signing_secret = "" # Ignored when slack_signing_secret_id is set

# ==============================================================================
# SPIFFE ID (R7 Compliance)
# ==============================================================================
agent_spiffe_id = "spiffe://intent.solutions/agent/bobs-brain/stage/us-central1/0.14.1"

# ==============================================================================
# AI Model Configuration
# ==============================================================================
model_name = "gemini-2.0-flash-exp"

# ==============================================================================
# Vertex AI Search Configuration
# ==============================================================================
vertex_search_datastore_id = "adk-documentation"

# ==============================================================================
# Networking
# ==============================================================================
allow_public_access = true

# ==============================================================================
# Labels
# ==============================================================================
labels = {
  cost_center = "stage"
  team        = "platform"
  environment = "stage"
}

# ==============================================================================
# Knowledge Hub Configuration (org-wide knowledge repository)
# ==============================================================================
knowledge_hub_project_id = "datahub-intent"
knowledge_bucket_prefix  = "datahub-intent-stage"

# Service accounts that need knowledge hub access
bobs_brain_runtime_sa = "" # TODO-SET-STAGE-SA: serviceAccount:bob-runtime@bobs-brain-stage.iam.gserviceaccount.com
bobs_brain_search_sa  = "" # TODO-SET-STAGE-SA: serviceAccount:vertex-search@bobs-brain-stage.iam.gserviceaccount.com

# Additional consumers
consumer_service_accounts = []

# ==============================================================================
# Org-Wide Knowledge Hub (LIVE1-GCS)
# ==============================================================================
# Central GCS bucket for org-wide SWE/portfolio audit data
# Disabled by default; enable when stage infra is ready
org_storage_enabled     = false
org_storage_bucket_name = "intent-org-knowledge-hub-stage"
org_storage_location    = "US"

# Additional service accounts that can write
org_storage_writer_service_accounts = []

# ==============================================================================
# Agent Engine IDs (for promotion workflow)
# ==============================================================================
# These IDs are set after initial Agent Engine deployment
# Used by scripts/promote_agent_engine_config.py
#
# bob_agent_engine_id     = "TODO-SET-STAGE-ENGINE-ID"
# foreman_agent_engine_id = "TODO-SET-STAGE-ENGINE-ID"
