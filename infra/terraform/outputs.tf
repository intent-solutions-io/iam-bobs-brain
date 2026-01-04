# Terraform Outputs
# Values available after deployment

# Agent Engine Outputs
output "agent_engine_name" {
  description = "Agent Engine display name"
  value       = google_vertex_ai_reasoning_engine.bob.display_name
}

output "agent_engine_region" {
  description = "Agent Engine deployment region"
  value       = var.region
}

# A2A Gateway Outputs
output "a2a_gateway_url" {
  description = "A2A Gateway public URL"
  value       = google_cloud_run_service.a2a_gateway.status[0].url
}

output "a2a_gateway_service_name" {
  description = "A2A Gateway Cloud Run service name"
  value       = google_cloud_run_service.a2a_gateway.name
}

output "a2a_agentcard_url" {
  description = "AgentCard discovery URL (A2A protocol)"
  value       = "${google_cloud_run_service.a2a_gateway.status[0].url}/.well-known/agent.json"
}

# Slack Webhook Outputs (from module)
output "slack_webhook_url" {
  description = "Slack Webhook public URL"
  value       = module.slack_bob_gateway.service_url
}

output "slack_webhook_service_name" {
  description = "Slack Webhook Cloud Run service name"
  value       = module.slack_bob_gateway.service_name
}

output "slack_events_url" {
  description = "Slack Events API webhook URL (configure in Slack app)"
  value       = module.slack_bob_gateway.webhook_url
}

output "slack_bob_enabled" {
  description = "Whether Slack Bob gateway is enabled"
  value       = module.slack_bob_gateway.enabled
}

# Service Account Outputs
output "agent_engine_service_account" {
  description = "Agent Engine service account email"
  value       = google_service_account.agent_engine.email
}

output "a2a_gateway_service_account" {
  description = "A2A Gateway service account email"
  value       = google_service_account.a2a_gateway.email
}

output "slack_webhook_service_account" {
  description = "Slack Webhook service account email"
  value       = google_service_account.slack_webhook.email
}

output "github_actions_service_account" {
  description = "GitHub Actions service account email (for CI/CD)"
  value       = google_service_account.github_actions.email
}

# Bob's MCP Server Outputs (Phase H - Universal Tool Access)
output "bobs_mcp_url" {
  description = "Bob's MCP server URL (set BOBS_MCP_URL env var to this value)"
  value       = var.bobs_mcp_enabled ? google_cloud_run_service.bobs_mcp[0].status[0].url : null
}

output "bobs_mcp_enabled" {
  description = "Whether Bob's MCP server is deployed"
  value       = var.bobs_mcp_enabled
}

# Event Trigger Outputs (Phase H)
output "github_webhook_url" {
  description = "GitHub Webhook URL (configure in GitHub repo settings)"
  value       = var.github_webhook_enabled ? google_cloud_run_service.github_webhook[0].status[0].url : null
}

output "github_webhook_endpoint" {
  description = "Full GitHub webhook endpoint URL"
  value       = var.github_webhook_enabled ? "${google_cloud_run_service.github_webhook[0].status[0].url}/github/webhook" : null
}

output "github_webhook_enabled" {
  description = "Whether GitHub webhook is deployed"
  value       = var.github_webhook_enabled
}

output "scheduler_enabled" {
  description = "Whether Cloud Scheduler is enabled"
  value       = var.scheduler_enabled
}

# Configuration Outputs
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "app_version" {
  description = "Application version"
  value       = var.app_version
}

output "spiffe_id" {
  description = "Agent SPIFFE ID (R7)"
  value       = var.agent_spiffe_id
}

# Deployment Summary
output "deployment_summary" {
  description = "Deployment summary with all important URLs"
  value = {
    environment           = var.environment
    project_id            = var.project_id
    region                = var.region
    app_version           = var.app_version
    agent_engine_id       = google_vertex_ai_reasoning_engine.bob.id
    agent_engine_endpoint = "https://${var.region}-aiplatform.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/reasoningEngines/${google_vertex_ai_reasoning_engine.bob.id}:query"
    a2a_gateway_url       = google_cloud_run_service.a2a_gateway.status[0].url
    a2a_agentcard_url     = "${google_cloud_run_service.a2a_gateway.status[0].url}/.well-known/agent.json"
    slack_webhook_url     = module.slack_bob_gateway.service_url
    slack_events_url      = module.slack_bob_gateway.webhook_url
    slack_bob_enabled     = module.slack_bob_gateway.enabled
    bobs_mcp_url          = var.bobs_mcp_enabled ? google_cloud_run_service.bobs_mcp[0].status[0].url : null
    bobs_mcp_enabled      = var.bobs_mcp_enabled
    github_webhook_url    = var.github_webhook_enabled ? google_cloud_run_service.github_webhook[0].status[0].url : null
    github_webhook_enabled = var.github_webhook_enabled
    scheduler_enabled     = var.scheduler_enabled
    spiffe_id             = var.agent_spiffe_id
  }
}
