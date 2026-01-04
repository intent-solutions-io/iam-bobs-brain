# Development Environment Configuration
# terraform apply -var-file="envs/dev.tfvars"

# Project Configuration
project_id  = "bobs-brain-dev"
region      = "us-central1"
environment = "dev"

# Application Configuration
app_name    = "bobs-brain"
app_version = "0.10.0"

# Agent Engine Configuration
# Bob agent (main orchestrator)
bob_docker_image = "gcr.io/bobs-brain-dev/agent:0.10.0"

# Foreman agent (iam-senior-adk-devops-lead)
foreman_docker_image = "gcr.io/bobs-brain-dev/foreman:0.10.0"

# Agent Engine compute resources
agent_machine_type = "n1-standard-2" # Smaller for dev
agent_max_replicas = 2

# Gateway Configuration
a2a_gateway_image     = "gcr.io/bobs-brain-dev/a2a-gateway:0.10.0"
slack_webhook_image   = "gcr.io/bobs-brain-dev/slack-webhook:0.10.0"
gateway_max_instances = 5 # Fewer instances for dev

# MCP Server Configuration (Phase H - Universal Tool Access)
bobs_mcp_enabled = true
bobs_mcp_image   = "gcr.io/bobs-brain-dev/bobs-mcp:0.2.0"

# Slack Configuration (dev credentials)
# IMPORTANT: Use Secret Manager or CI/CD secrets in production
slack_bot_token      = "xoxb-dev-placeholder"
slack_signing_secret = "dev-placeholder"

# SPIFFE ID (R7) - Bob agent
agent_spiffe_id = "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0"

# AI Model Configuration
model_name = "gemini-2.0-flash-exp"

# Vertex AI Search Configuration (Phase 3)
vertex_search_datastore_id = "adk-documentation"

# Networking
allow_public_access = true

# Labels
labels = {
  cost_center = "development"
  team        = "platform"
}

# ADK Deployment Configuration
# Staging bucket created by storage.tf (output: staging_bucket_url)
# Used by: adk deploy agent_engine --staging_bucket
# Format: gs://<project-id>-adk-staging

# Knowledge Hub Configuration (org-wide knowledge repository)
# TODO: Wire actual service account emails after projects are configured
knowledge_hub_project_id = "datahub-intent"
knowledge_bucket_prefix  = "datahub-intent" # Using project name as bucket name

# Service accounts that need knowledge hub access (empty for now)
# These will be populated with actual SA emails when ready
bobs_brain_runtime_sa = "" # TODO: Get from Agent Engine deployment
bobs_brain_search_sa  = "" # TODO: Get from Vertex AI Search setup

# Additional consumers can be added here
consumer_service_accounts = [
  # Example:
  # {
  #   email  = "diagnosticpro-agent@diagnosticpro-dev.iam.gserviceaccount.com"
  #   prefix = "diagnosticpro/"
  # }
]

# ==============================================================================
# Org-Wide Knowledge Hub (LIVE1-GCS)
# ==============================================================================
# Central GCS bucket for org-wide SWE/portfolio audit data
# Disabled by default; enable explicitly to test GCS integration
# ==============================================================================

org_storage_enabled     = false # Set to true to enable org storage bucket
org_storage_bucket_name = "intent-org-knowledge-hub-dev"
org_storage_location    = "US"

# Additional service accounts that can write (future repos)
org_storage_writer_service_accounts = [
  # Will add when other repos integrate:
  # "diagnosticpro-agent@diagnosticpro-dev.iam.gserviceaccount.com",
  # "pipelinepilot-agent@pipelinepilot-dev.iam.gserviceaccount.com",
]
