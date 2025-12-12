# Cloud Run Gateways
# R3: Cloud Run as gateway only (proxy to Agent Engine via REST)

# A2A Gateway Service
resource "google_cloud_run_service" "a2a_gateway" {
  name     = "${var.app_name}-a2a-gateway-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.a2a_gateway.email

      containers {
        image = var.a2a_gateway_image

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
          name  = "AGENT_ENGINE_ID"
          value = google_vertex_ai_reasoning_engine.bob.id
        }

        env {
          name  = "AGENT_ENGINE_URL"
          value = "https://${var.region}-aiplatform.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/reasoningEngines/${google_vertex_ai_reasoning_engine.bob.id}:query"
        }

        env {
          name  = "APP_NAME"
          value = var.app_name
        }

        env {
          name  = "APP_VERSION"
          value = var.app_version
        }

        env {
          name  = "PUBLIC_URL"
          value = coalesce(var.a2a_gateway_url, "https://${var.app_name}-a2a-gateway-${var.environment}-${data.google_project.project.number}.run.app")
        }

        env {
          name  = "AGENT_SPIFFE_ID"
          value = var.agent_spiffe_id
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
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        # Health check
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          timeout_seconds       = 3
          period_seconds        = 10
          failure_threshold     = 3
        }
      }

      # Scaling
      container_concurrency = 80

      # Timeout
      timeout_seconds = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"  = "0"
        "autoscaling.knative.dev/maxScale"  = tostring(var.gateway_max_instances)
        "run.googleapis.com/cpu-throttling" = "true"
      }

      labels = merge(
        var.labels,
        {
          environment = var.environment
          app         = var.app_name
          version     = replace(var.app_version, ".", "-")
          component   = "a2a-gateway"
        }
      )
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_service_account.a2a_gateway,
    google_project_iam_member.a2a_gateway_aiplatform,
    google_vertex_ai_reasoning_engine.bob,
  ]
}

# A2A Gateway IAM Policy (allow unauthenticated access)
resource "google_cloud_run_service_iam_member" "a2a_gateway_public" {
  count = var.allow_public_access ? 1 : 0

  service  = google_cloud_run_service.a2a_gateway.name
  location = google_cloud_run_service.a2a_gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Slack Bob Gateway Module
# R3: Cloud Run as gateway only (proxy to Agent Engine via REST)
# Conditionally deployed based on slack_bob_enabled feature flag
module "slack_bob_gateway" {
  source = "./modules/slack_bob_gateway"

  enable      = var.slack_bob_enabled
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  app_name    = var.app_name

  # Docker image (set by CI)
  image = var.slack_webhook_image

  # Agent Engine configuration
  agent_engine_name = google_vertex_ai_reasoning_engine.bob.name
  agent_engine_id   = tostring(google_vertex_ai_reasoning_engine.bob.id)

  # Secret Manager references (production best practice)
  slack_signing_secret_id   = var.slack_signing_secret_id
  slack_bot_token_secret_id = var.slack_bot_token_secret_id

  # Service account
  service_account_email = google_service_account.slack_webhook.email

  # Networking
  allow_unauthenticated = var.allow_public_access

  # Scaling
  max_instances = var.gateway_max_instances
  min_instances = 0

  # Resource limits
  cpu_limit    = "1000m"
  memory_limit = "512Mi"

  # Labels
  labels = var.labels

  depends_on = [
    google_service_account.slack_webhook,
    google_project_iam_member.slack_webhook_aiplatform,
    google_vertex_ai_reasoning_engine.bob,
  ]
}

# Data source for project number (needed for Cloud Run URLs)
data "google_project" "project" {
  project_id = var.project_id
}
