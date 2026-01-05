# Production Environment Configuration
# terraform apply -var-file="envs/prod.tfvars"

# Project Configuration
project_id  = "bobs-brain"
region      = "us-central1"
environment = "prod"

# Application Configuration
app_name    = "bobs-brain"
app_version = "0.6.0"

# Agent Engine Configuration
agent_docker_image = "gcr.io/bobs-brain/agent:0.6.0"
agent_machine_type = "n1-standard-4"
agent_max_replicas = 5 # Higher for production

# Gateway Configuration
a2a_gateway_image     = "gcr.io/bobs-brain/a2a-gateway:0.6.0"
slack_webhook_image   = "gcr.io/bobs-brain/slack-webhook:0.6.0"
gateway_max_instances = 20 # More instances for production

# MCP Server Configuration (Phase H - Universal Tool Access)
# Enable when MCP server is production-tested
bobs_mcp_enabled = false
bobs_mcp_image   = "gcr.io/bobs-brain/bobs-mcp:0.2.0"

# Slack Configuration (production)
# Feature flag to enable Slack Bob gateway (R3 Cloud Run proxy)
slack_bob_enabled = true

# Secret Manager references (production best practice)
# Secrets must exist in Secret Manager before deployment
slack_bot_token_secret_id      = "slack-bot-token"
slack_signing_secret_id        = "slack-signing-secret"

# DEPRECATED: Direct token variables (use Secret Manager instead)
slack_bot_token      = "" # Ignored when slack_bot_token_secret_id is set
slack_signing_secret = "" # Ignored when slack_signing_secret_id is set

# SPIFFE ID (R7)
agent_spiffe_id = "spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.6.0"

# AI Model Configuration
model_name = "gemini-2.0-flash-exp"

# Vertex AI Search Configuration (Phase 3)
vertex_search_datastore_id = "adk-documentation"

# Networking
allow_public_access = true

# Labels
labels = {
  cost_center = "production"
  team        = "platform"
  critical    = "true"
}

# Knowledge Hub Configuration (org-wide knowledge repository)
# Production uses the actual datahub-intent project
knowledge_hub_project_id = "datahub-intent"
knowledge_bucket_prefix  = "datahub-intent" # Main prod bucket

# Service accounts that need knowledge hub access
# TODO: Replace with actual production service account emails
bobs_brain_runtime_sa = "" # TODO: serviceAccount:bob-runtime@bobs-brain.iam.gserviceaccount.com
bobs_brain_search_sa  = "" # TODO: serviceAccount:vertex-search@bobs-brain.iam.gserviceaccount.com

# Production consumers - add as projects onboard
consumer_service_accounts = [
  # DiagnosticPro (when ready)
  # {
  #   email  = "diagnosticpro-agent@diagnosticpro-prod.iam.gserviceaccount.com"
  #   prefix = "diagnosticpro/"
  # },
  # PipelinePilot (when ready)
  # {
  #   email  = "pipeline-agent@pipelinepilot-prod.iam.gserviceaccount.com"
  #   prefix = "pipelinepilot/"
  # }
]
