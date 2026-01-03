# IAM Configuration
# Service accounts and permissions for Agent Engine and Cloud Run gateways

# Service Account for Agent Engine
resource "google_service_account" "agent_engine" {
  account_id   = "${var.app_name}-agent-engine-${var.environment}"
  display_name = "Bob's Brain Agent Engine (${var.environment})"
  description  = "Service account for Vertex AI Agent Engine"
  project      = var.project_id
}

# Service Account for A2A Gateway
resource "google_service_account" "a2a_gateway" {
  account_id   = "${var.app_name}-a2a-gateway-${var.environment}"
  display_name = "Bob's Brain A2A Gateway (${var.environment})"
  description  = "Service account for A2A Gateway Cloud Run service"
  project      = var.project_id
}

# Service Account for Slack Webhook
resource "google_service_account" "slack_webhook" {
  account_id   = "${var.app_name}-slack-webhook-${var.environment}"
  display_name = "Bob's Brain Slack Webhook (${var.environment})"
  description  = "Service account for Slack Webhook Cloud Run service"
  project      = var.project_id
}

# IAM Bindings for Agent Engine
# Needs access to Vertex AI services for LLM calls, memory, and tools

resource "google_project_iam_member" "agent_engine_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_engine.email}"
}

resource "google_project_iam_member" "agent_engine_vertex" {
  project = var.project_id
  role    = "roles/ml.developer"
  member  = "serviceAccount:${google_service_account.agent_engine.email}"
}

resource "google_project_iam_member" "agent_engine_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_engine.email}"
}

# Phase 3: Vertex AI Search permissions for Agent Engine
resource "google_project_iam_member" "agent_engine_discovery_engine" {
  project = var.project_id
  role    = "roles/discoveryengine.viewer"
  member  = "serviceAccount:${google_service_account.agent_engine.email}"
}

# IAM Bindings for A2A Gateway
# Needs to call Agent Engine REST API

resource "google_project_iam_member" "a2a_gateway_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

resource "google_project_iam_member" "a2a_gateway_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

# IAM Bindings for Slack Webhook
# Needs to call Agent Engine REST API

resource "google_project_iam_member" "slack_webhook_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.slack_webhook.email}"
}

resource "google_project_iam_member" "slack_webhook_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.slack_webhook.email}"
}

# Secret Manager access for Slack tokens
resource "google_project_iam_member" "slack_webhook_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.slack_webhook.email}"
}

# Service Account for GitHub Actions (Workload Identity Federation)
# R4: CI-only deployments
resource "google_service_account" "github_actions" {
  account_id   = "${var.app_name}-github-actions"
  display_name = "Bob's Brain GitHub Actions"
  description  = "Service account for GitHub Actions CI/CD"
  project      = var.project_id
}

# GitHub Actions needs permissions to deploy infrastructure
resource "google_project_iam_member" "github_actions_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Workload Identity Pool for GitHub Actions (R4)
# This allows GitHub Actions to authenticate without service account keys
# Uncomment and configure for production CI/CD

# resource "google_iam_workload_identity_pool" "github_actions" {
#   workload_identity_pool_id = "${var.app_name}-github-pool"
#   display_name              = "Bob's Brain GitHub Actions Pool"
#   description               = "Workload Identity Pool for GitHub Actions"
#   project                   = var.project_id
# }

# resource "google_iam_workload_identity_pool_provider" "github_actions" {
#   workload_identity_pool_id          = google_iam_workload_identity_pool.github_actions.workload_identity_pool_id
#   workload_identity_pool_provider_id = "github"
#   display_name                       = "GitHub Actions Provider"
#   project                            = var.project_id
#
#   attribute_mapping = {
#     "google.subject"       = "assertion.sub"
#     "attribute.actor"      = "assertion.actor"
#     "attribute.repository" = "assertion.repository"
#   }
#
#   oidc {
#     issuer_uri = "https://token.actions.githubusercontent.com"
#   }
# }

# resource "google_service_account_iam_member" "github_actions_wif" {
#   service_account_id = google_service_account.github_actions.name
#   role               = "roles/iam.workloadIdentityUser"
#   member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_actions.name}/attribute.repository/YOUR_GITHUB_ORG/bobs-brain"
# }
