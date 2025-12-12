# Slack Bob Gateway Module - Main Resources
# R3: Cloud Run as gateway only (proxy to Agent Engine via REST)
# NO local Runner, NO alternate frameworks - only REST proxy to Agent Engine

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.6"
    }
  }
}

# Conditional resource creation based on enable flag
locals {
  enabled      = var.enable ? 1 : 0
  service_name = "${var.app_name}-slack-webhook-${var.environment}"
}

# Cloud Run Service - Slack Gateway (R3 compliant proxy)
resource "google_cloud_run_v2_service" "slack_gateway" {
  count = local.enabled

  name     = local.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    timeout = "${var.timeout_seconds}s"

    containers {
      image = var.image

      # Environment variables
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "LOCATION"
        value = var.region
      }

      env {
        name  = "AGENT_ENGINE_NAME"
        value = var.agent_engine_name
      }

      env {
        name  = "AGENT_ENGINE_ID"
        value = var.agent_engine_id
      }

      env {
        name  = "AGENT_ENGINE_URL"
        value = "https://${var.region}-aiplatform.googleapis.com/v1/${var.agent_engine_name}:query"
      }

      # Critical: Enable Slack bot processing
      env {
        name  = "SLACK_BOB_ENABLED"
        value = "true"
      }

      # Slack secrets from Secret Manager
      env {
        name = "SLACK_SIGNING_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.slack_signing_secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SLACK_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = var.slack_bot_token_secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "DEPLOYMENT_ENV"
        value = var.environment
      }

      env {
        name  = "PORT"
        value = "8080"
      }

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      # Health check probe
      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      app         = var.app_name
      component   = "slack-gateway"
      managed_by  = "terraform"
    }
  )

  lifecycle {
    ignore_changes = [
      # Ignore client and client_version as they change with each deployment
      client,
      client_version,
    ]
  }
}

# IAM: Allow unauthenticated access (required for Slack webhooks)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? local.enabled : 0

  project  = google_cloud_run_v2_service.slack_gateway[0].project
  location = google_cloud_run_v2_service.slack_gateway[0].location
  name     = google_cloud_run_v2_service.slack_gateway[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Optional: Uptime monitoring (can be extended later)
# resource "google_monitoring_uptime_check_config" "slack_gateway" {
#   count = local.enabled
#   ...
# }
