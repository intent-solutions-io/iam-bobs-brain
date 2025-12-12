# Stage Environment Configuration
# terraform plan -var-file="envs/stage.tfvars"
#
# NOTE: This file contains TODO placeholders that MUST be replaced
# before running terraform plan/apply. The terraform-stage-plan.yml
# workflow will fail if these placeholders remain.

# Project Configuration
project_id  = "TODO-SET-STAGE-PROJECT-ID" # e.g., "bobs-brain-stage"
region      = "us-central1"
environment = "stage"

# Application Configuration
app_name    = "bobs-brain"
app_version = "0.14.1"

# Agent Engine Configuration
# Bob agent (main orchestrator)
bob_docker_image = "gcr.io/TODO-SET-STAGE-PROJECT-ID/agent:0.14.1"

# Foreman agent (iam-senior-adk-devops-lead)
foreman_docker_image = "gcr.io/TODO-SET-STAGE-PROJECT-ID/foreman:0.14.1"

# Agent Engine compute resources
agent_machine_type = "n1-standard-2"
agent_max_replicas = 3

# Gateway Configuration
a2a_gateway_image     = "gcr.io/TODO-SET-STAGE-PROJECT-ID/a2a-gateway:0.14.1"
slack_webhook_image   = "gcr.io/TODO-SET-STAGE-PROJECT-ID/slack-webhook:0.14.1"
gateway_max_instances = 5

# Slack Configuration (stage credentials)
# IMPORTANT: These should reference Secret Manager secrets, not plaintext
slack_bot_token_secret_id      = "slack-bot-token-stage"
slack_signing_secret_secret_id = "slack-signing-secret-stage"

# SPIFFE ID (R7) - Bob agent
agent_spiffe_id = "spiffe://intent.solutions/agent/bobs-brain/stage/us-central1/0.14.1"

# AI Model Configuration
model_name = "gemini-2.0-flash-exp"

# Vertex AI Search Configuration
vertex_search_datastore_id = "adk-documentation"

# Networking
allow_public_access = true

# Labels
labels = {
  cost_center = "staging"
  team        = "platform"
  env         = "stage"
}

# ADK Deployment Configuration
# Staging bucket: gs://<project-id>-adk-staging

# Knowledge Hub Configuration
knowledge_hub_project_id = "datahub-intent"
knowledge_bucket_prefix  = "datahub-intent"

# Service accounts (to be configured after project setup)
bobs_brain_runtime_sa = ""
bobs_brain_search_sa  = ""

# Consumer service accounts
consumer_service_accounts = []

# ==============================================================================
# Org-Wide Knowledge Hub (LIVE1-GCS)
# ==============================================================================
org_storage_enabled                 = false
org_storage_bucket_name             = "intent-org-knowledge-hub-stage"
org_storage_location                = "US"
org_storage_writer_service_accounts = []
