# Event Triggers for Bob's Brain
# Phase H: Universal Autonomous AI Crew - Event-Driven Autonomy
#
# This file defines:
# 1. GitHub Webhook - Cloud Run service for GitHub events
# 2. Cloud Scheduler - Cron jobs for scheduled tasks

# ============================================================================
# GitHub Webhook Service
# ============================================================================

# GitHub Webhook Cloud Run Service
resource "google_cloud_run_service" "github_webhook" {
  count    = var.github_webhook_enabled ? 1 : 0
  name     = "${var.app_name}-github-webhook-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.github_webhook[0].email

      containers {
        image = var.github_webhook_image

        # Environment variables
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "DEPLOYMENT_ENV"
          value = var.environment
        }

        env {
          name  = "GITHUB_WEBHOOK_ENABLED"
          value = "true"
        }

        env {
          name  = "A2A_GATEWAY_URL"
          value = google_cloud_run_service.a2a_gateway.status[0].url
        }

        env {
          name  = "PORT"
          value = "8080"
        }

        # GitHub webhook secret from Secret Manager
        dynamic "env" {
          for_each = var.github_webhook_secret_id != "" ? [1] : []
          content {
            name = "GITHUB_WEBHOOK_SECRET"
            value_from {
              secret_key_ref {
                name = var.github_webhook_secret_id
                key  = "latest"
              }
            }
          }
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

      # Timeout (webhooks should respond quickly)
      timeout_seconds = 120
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"  = "0"
        "autoscaling.knative.dev/maxScale"  = "5"
        "run.googleapis.com/cpu-throttling" = "true"
      }

      labels = merge(
        var.labels,
        {
          environment = var.environment
          app         = var.app_name
          version     = replace(var.app_version, ".", "-")
          component   = "github-webhook"
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
    google_service_account.github_webhook,
    google_project_iam_member.github_webhook_logging,
    google_cloud_run_service.a2a_gateway,
  ]
}

# GitHub Webhook Service Account
resource "google_service_account" "github_webhook" {
  count = var.github_webhook_enabled ? 1 : 0

  account_id   = "${var.app_name}-gh-webhook-${var.environment}"
  display_name = "GitHub Webhook Service Account"
  project      = var.project_id
}

# GitHub Webhook IAM - Logging
resource "google_project_iam_member" "github_webhook_logging" {
  count = var.github_webhook_enabled ? 1 : 0

  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.github_webhook[0].email}"
}

# GitHub Webhook IAM - Secret Manager (to read webhook secret)
resource "google_project_iam_member" "github_webhook_secrets" {
  count = var.github_webhook_enabled && var.github_webhook_secret_id != "" ? 1 : 0

  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.github_webhook[0].email}"
}

# GitHub Webhook Public Access (GitHub needs to reach the endpoint)
resource "google_cloud_run_service_iam_member" "github_webhook_public" {
  count = var.github_webhook_enabled ? 1 : 0

  service  = google_cloud_run_service.github_webhook[0].name
  location = google_cloud_run_service.github_webhook[0].location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# Cloud Scheduler - Cron Triggers
# ============================================================================

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  count = var.scheduler_enabled ? 1 : 0

  account_id   = "${var.app_name}-scheduler-${var.environment}"
  display_name = "Cloud Scheduler Service Account"
  project      = var.project_id
}

# Scheduler IAM - Cloud Run Invoker
resource "google_project_iam_member" "scheduler_run_invoker" {
  count = var.scheduler_enabled ? 1 : 0

  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler[0].email}"
}

# Daily Health Check Job
# Runs every day at 6 AM UTC - triggers full ADK compliance audit
resource "google_cloud_scheduler_job" "daily_health_check" {
  count = var.scheduler_enabled ? 1 : 0

  name             = "${var.app_name}-daily-health-${var.environment}"
  description      = "Daily ADK compliance and repository health check"
  schedule         = "0 6 * * *"
  time_zone        = "UTC"
  attempt_deadline = "600s"
  region           = var.region
  project          = var.project_id

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.a2a_gateway.status[0].url}/a2a/run"

    body = base64encode(jsonencode({
      agent_role       = "iam-orchestrator"
      prompt           = "Run daily health check: 1) ADK compliance audit for all agents, 2) Repository hygiene scan, 3) Update knowledge index. Report findings to Slack."
      session_id       = "scheduler_daily_health"
      caller_spiffe_id = "spiffe://intent.solutions/scheduler/daily-health"
      env              = var.environment
    }))

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.scheduler[0].email
      audience              = google_cloud_run_service.a2a_gateway.status[0].url
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "60s"
    max_backoff_duration = "600s"
    max_retry_duration   = "1800s"
    max_doublings        = 3
  }
}

# Weekly Audit Job
# Runs every Sunday at midnight UTC - comprehensive audit
resource "google_cloud_scheduler_job" "weekly_audit" {
  count = var.scheduler_enabled ? 1 : 0

  name             = "${var.app_name}-weekly-audit-${var.environment}"
  description      = "Weekly comprehensive repository audit"
  schedule         = "0 0 * * 0"
  time_zone        = "UTC"
  attempt_deadline = "1800s"
  region           = var.region
  project          = var.project_id

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.a2a_gateway.status[0].url}/a2a/run"

    body = base64encode(jsonencode({
      agent_role       = "iam-orchestrator"
      prompt           = "Run weekly comprehensive audit: 1) Full Hard Mode compliance check (R1-R8), 2) Dependency vulnerability scan, 3) Documentation freshness check, 4) Clean up stale branches. Generate report for stakeholders."
      session_id       = "scheduler_weekly_audit"
      caller_spiffe_id = "spiffe://intent.solutions/scheduler/weekly-audit"
      env              = var.environment
    }))

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.scheduler[0].email
      audience              = google_cloud_run_service.a2a_gateway.status[0].url
    }
  }

  retry_config {
    retry_count          = 2
    min_backoff_duration = "120s"
    max_backoff_duration = "900s"
    max_retry_duration   = "3600s"
    max_doublings        = 2
  }
}
