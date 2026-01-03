# Terraform Variables
# Environment-specific values in envs/*.tfvars

# Project Configuration
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

# Application Configuration
variable "app_name" {
  description = "Application name"
  type        = string
  default     = "bobs-brain"
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "0.10.0"
}

# Agent Engine Configuration
variable "bob_docker_image" {
  description = "Docker image for Bob agent (GCR path)"
  type        = string
  default     = "" # Computed from project_id and app_version if empty
  # Example: gcr.io/bobs-brain-dev/agent:0.10.0
}

variable "foreman_docker_image" {
  description = "Docker image for Foreman agent (GCR path)"
  type        = string
  default     = "" # Computed from project_id and app_version if empty
  # Example: gcr.io/bobs-brain-dev/foreman:0.10.0
}

# Legacy variable for backward compatibility (deprecated in Phase 19)
variable "agent_docker_image" {
  description = "DEPRECATED: Use bob_docker_image instead"
  type        = string
  default     = ""
}

variable "agent_machine_type" {
  description = "Machine type for Agent Engine"
  type        = string
  default     = "n1-standard-4"
}

variable "agent_max_replicas" {
  description = "Maximum number of Agent Engine replicas"
  type        = number
  default     = 3
}

# Gateway Configuration
variable "a2a_gateway_image" {
  description = "Docker image for A2A Gateway (GCR path)"
  type        = string
  # Example: gcr.io/bobs-brain/a2a-gateway:0.6.0
}

variable "slack_webhook_image" {
  description = "Docker image for Slack Webhook (GCR path)"
  type        = string
  # Example: gcr.io/bobs-brain/slack-webhook:0.6.0
}

variable "gateway_max_instances" {
  description = "Maximum instances for Cloud Run gateways"
  type        = number
  default     = 10
}

# Slack Configuration
# Feature flag to enable/disable Slack gateway
variable "slack_bob_enabled" {
  description = "Enable Slack Bob gateway (R3 Cloud Run proxy to Agent Engine)"
  type        = bool
  default     = false
}

# Secret Manager references (recommended for production)
variable "slack_bot_token_secret_id" {
  description = "Secret Manager secret ID for Slack bot token"
  type        = string
  default     = "slack-bot-token"
}

variable "slack_signing_secret_id" {
  description = "Secret Manager secret ID for Slack signing secret"
  type        = string
  default     = "slack-signing-secret"
}

# DEPRECATED: Direct token variables (only for dev/testing)
# Use Secret Manager in production via slack_bot_token_secret_id
variable "slack_bot_token" {
  description = "DEPRECATED: Use Secret Manager (slack_bot_token_secret_id) in production"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_signing_secret" {
  description = "DEPRECATED: Use Secret Manager (slack_signing_secret_id) in production"
  type        = string
  sensitive   = true
  default     = ""
}

# SPIFFE ID (R7)
variable "agent_spiffe_id" {
  description = "SPIFFE ID for agent identity"
  type        = string
  # Format: spiffe://intent.solutions/agent/bobs-brain/{env}/{region}/{version}
}

# Public URLs (set after deployment or use custom domains)
variable "a2a_gateway_url" {
  description = "Public URL for A2A Gateway (optional, defaults to Cloud Run URL)"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Public URL for Slack Webhook (optional, defaults to Cloud Run URL)"
  type        = string
  default     = ""
}

# AI Model Configuration
variable "model_name" {
  description = "Gemini model to use"
  type        = string
  default     = "gemini-2.0-flash-exp"
}

# Vertex AI Search Configuration (Phase 3)
variable "vertex_search_datastore_id" {
  description = "Vertex AI Search datastore ID for ADK documentation"
  type        = string
  default     = "adk-documentation"
}

# Networking
variable "allow_public_access" {
  description = "Allow unauthenticated access to gateways"
  type        = bool
  default     = true
}

# Labels
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}

# ==============================================================================
# Org-Wide Knowledge Hub (LIVE1-GCS)
# ==============================================================================
# Central GCS bucket for org-wide agent audit data, portfolio results, and
# knowledge artifacts. Shared across all repos/products.
#
# Feature flags control whether the bucket is created and whether writes are enabled.
# Default: disabled (must opt-in per environment)
# ==============================================================================

variable "org_storage_enabled" {
  description = "Enable org-wide knowledge hub bucket (LIVE1-GCS)"
  type        = bool
  default     = false
}

variable "org_storage_bucket_name" {
  description = "Org-wide knowledge hub bucket name (intent-org-knowledge-hub-{env})"
  type        = string
  default     = ""
}

variable "org_storage_location" {
  description = "GCS location for org storage bucket"
  type        = string
  default     = "US"
}

variable "org_storage_writer_service_accounts" {
  description = "Additional service accounts that can write to org storage (future repos)"
  type        = list(string)
  default     = []
}
