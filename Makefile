# Bob's Brain - Enhanced Makefile
# Professional development workflow for all Bob versions

.PHONY: help setup test lint format clean docker version benchmark ci all

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
FLAKE8 := $(PYTHON) -m flake8
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# Version selector
VERSION ?= current

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

#################################
# Help & Information
#################################

help: ## Show this help message
	@echo "$(BLUE)🤖 Bob's Brain - Development Makefile$(NC)"
	@echo "$(BLUE)=====================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Version-specific targets:$(NC)"
	@echo "  $(GREEN)run-v1$(NC)               Run Bob v1 (Basic CLI)"
	@echo "  $(GREEN)run-v2$(NC)               Run Bob v2 (Slack Bot)"
	@echo "  $(GREEN)test-v1$(NC)              Test Bob v1"
	@echo "  $(GREEN)test-v2$(NC)              Test Bob v2"
	@echo ""
	@echo "$(YELLOW)Docker targets:$(NC)"
	@echo "  $(GREEN)docker-v1$(NC)            Build & run Bob v1 in Docker"
	@echo "  $(GREEN)docker-v2$(NC)            Build & run Bob v2 in Docker"
	@echo "  $(GREEN)docker-all$(NC)           Run all versions in Docker"

#################################
# Setup & Installation
#################################

setup: ## Complete development environment setup
	@echo "$(BLUE)🔧 Setting up Bob's Brain development environment...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	$(PIP) install pre-commit pytest black flake8 mypy
	pre-commit install
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

install-hooks: ## Install git pre-commit hooks
	@echo "$(BLUE)🔧 Installing git hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ Git hooks installed!$(NC)"

deps: ## Install all dependencies
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

#################################
# Code Quality
#################################

lint: ## Run linting checks
	@echo "$(BLUE)🔍 Running lint checks...$(NC)"
	$(FLAKE8) . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(FLAKE8) . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(GREEN)✅ Lint checks passed!$(NC)"

format: ## Format code with black
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	$(BLACK) .
	@echo "$(GREEN)✅ Code formatted!$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)🎨 Checking code format...$(NC)"
	$(BLACK) --check .
	@echo "$(GREEN)✅ Code format check passed!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)🔍 Running type checks...$(NC)"
	mypy versions/ --ignore-missing-imports || true
	@echo "$(GREEN)✅ Type check completed!$(NC)"

#################################
# A2A Contract Validation
#################################

check-a2a-contracts: ## Validate all AgentCard JSON files for A2A protocol compliance
	@echo "$(BLUE)🔍 Validating A2A contracts...$(NC)"
	$(PYTHON) scripts/check_a2a_contracts.py --all
	@echo "$(GREEN)✅ A2A contract validation passed!$(NC)"

check-a2a-single: ## Validate a single AgentCard (usage: make check-a2a-single CARD=path/to/agent-card.json)
	@echo "$(BLUE)🔍 Validating AgentCard: $(CARD)$(NC)"
	$(PYTHON) scripts/check_a2a_contracts.py $(CARD)

smoke-agents: ## Smoke test all agents for lazy-loading App pattern (6774)
	@echo "$(BLUE)🧪 Running agent lazy-loading smoke test...$(NC)"
	$(PYTHON) scripts/smoke_check_agents.py
	@echo "$(GREEN)✅ All agents follow lazy-loading pattern!$(NC)"

#################################
# Testing
#################################

test: ## Run all tests
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	$(PYTEST) tests/ -v --color=yes
	@echo "$(GREEN)✅ All tests passed!$(NC)"

test-v1: ## Test Bob v1 specifically
	@echo "$(BLUE)🧪 Testing Bob v1...$(NC)"
	$(PYTEST) tests/test_v1_basic.py -v --color=yes
	@echo "$(GREEN)✅ Bob v1 tests passed!$(NC)"

test-v2: ## Test Bob v2 specifically
	@echo "$(BLUE)🧪 Testing Bob v2...$(NC)"
	$(PYTEST) tests/test_v2_unified.py -v --color=yes
	@echo "$(GREEN)✅ Bob v2 tests passed!$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	$(PYTEST) tests/ --cov=versions --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

#################################
# Running Bob Versions
#################################

run-v1: ## Run Bob v1 (Basic CLI)
	@echo "$(BLUE)🤖 Starting Bob v1 (Basic CLI)...$(NC)"
	cd versions/v1-basic && $(PYTHON) run_bob.py

run-v2: ## Run Bob v2 (Slack Bot)
	@echo "$(BLUE)🤖 Starting Bob v2 (Slack Bot)...$(NC)"
	cd versions/v2-unified && ./start_unified_bob_v2.sh

run-selector: ## Run interactive version selector
	@echo "$(BLUE)🎯 Starting version selector...$(NC)"
	$(PYTHON) scripts/version-selector.py

#################################
# Docker Operations
#################################

docker-build: ## Build all Docker images
	@echo "$(BLUE)🐳 Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Docker images built!$(NC)"

docker-v1: ## Run Bob v1 in Docker
	@echo "$(BLUE)🐳 Running Bob v1 in Docker...$(NC)"
	$(DOCKER_COMPOSE) --profile v1 up

docker-v2: ## Run Bob v2 in Docker
	@echo "$(BLUE)🐳 Running Bob v2 in Docker...$(NC)"
	$(DOCKER_COMPOSE) --profile v2 up

docker-all: ## Run all versions in Docker
	@echo "$(BLUE)🐳 Running all Bob versions...$(NC)"
	$(DOCKER_COMPOSE) --profile all up

docker-stop: ## Stop all Docker containers
	@echo "$(BLUE)🛑 Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Containers stopped!$(NC)"

docker-clean: ## Clean Docker volumes and images
	@echo "$(YELLOW)⚠️  Cleaning Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v
	docker image prune -f
	@echo "$(GREEN)✅ Docker cleaned!$(NC)"

#################################
# Benchmarks & Performance
#################################

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)📊 Running performance benchmarks...$(NC)"
	$(PYTHON) tests/benchmarks.py 2>/dev/null || echo "$(YELLOW)⚠️  Benchmarks not implemented yet$(NC)"

#################################
# CI/CD Commands
#################################

ci: lint test ## Run CI checks (lint + test)
	@echo "$(GREEN)✅ CI checks passed!$(NC)"

safe-commit: lint format-check test ## Full safety check before commit
	@echo "$(GREEN)🛡️ All safety checks passed!$(NC)"
	@echo "$(GREEN)✅ Ready to commit safely$(NC)"
	@echo "$(BLUE)💡 Use: git add . && git commit -m 'your message'$(NC)"

pre-release: ci docker-build ## Prepare for release
	@echo "$(BLUE)📦 Preparing release...$(NC)"
	@echo "$(GREEN)✅ Ready for release!$(NC)"

#################################
# Cleanup
#################################

clean: ## Clean temporary files and caches
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	@echo "$(GREEN)✅ Cleaned!$(NC)"

clean-all: clean docker-clean ## Deep clean including Docker
	@echo "$(GREEN)✅ Deep clean completed!$(NC)"

#################################
# Development Utilities
#################################

version: ## Show Bob versions
	@echo "$(BLUE)📌 Bob's Brain Versions:$(NC)"
	@echo "  v1-basic:  Simple CLI Assistant"
	@echo "  v2-unified: Enterprise Slack Bot"
	@echo ""
	@echo "$(BLUE)📦 Package versions:$(NC)"
	@$(PYTHON) --version
	@$(PIP) show slack-sdk 2>/dev/null | grep Version || echo "slack-sdk: not installed"
	@$(PIP) show chromadb 2>/dev/null | grep Version || echo "chromadb: not installed"

logs: ## Show recent logs
	@echo "$(BLUE)📜 Recent logs:$(NC)"
	tail -n 50 logs/*.log 2>/dev/null || echo "$(YELLOW)No logs found$(NC)"

#################################
# Composite Targets
#################################

all: setup lint test ## Complete setup, lint, and test
	@echo "$(GREEN)✅ All tasks completed!$(NC)"

dev: setup run-selector ## Setup and run version selector
	@echo "$(GREEN)✅ Development mode ready!$(NC)"

prod: docker-v2 ## Production deployment (Docker v2)
	@echo "$(GREEN)✅ Production deployment started!$(NC)"

#################################
# ADK Documentation Crawler
#################################

crawl-adk-docs: ## Crawl ADK docs and upload to GCS for RAG
	@echo "$(BLUE)🕷️  Crawling ADK documentation...$(NC)"
	@echo "$(YELLOW)Loading configuration from .env.crawler$(NC)"
	@export $$(cat .env.crawler 2>/dev/null | grep -v '^#' | xargs) && \
		$(PYTHON) -m tools
	@echo "$(GREEN)✅ Crawl complete! Check GCS bucket for results.$(NC)"

crawl-test: ## Test crawler configuration without uploading
	@echo "$(BLUE)🔍 Testing crawler configuration...$(NC)"
	@export $$(cat .env.crawler 2>/dev/null | grep -v '^#' | xargs) && \
		$(PYTHON) -c "from tools.config import load_config, validate_gcp_credentials; config = load_config(); validate_gcp_credentials(); print('✅ Configuration valid')"

#################################
# RAG Readiness & ARV Gates
#################################

check-config: ## Validate environment configuration for current DEPLOYMENT_ENV
	@echo "$(BLUE)🔍 Validating config for DEPLOYMENT_ENV=$${DEPLOYMENT_ENV:-dev}...$(NC)"
	@$(PYTHON) scripts/check_config_all.py

check-rag-readiness: ## Check RAG readiness for Bob and foreman (ARV gate)
	@echo "$(BLUE)🔍 Checking RAG Readiness...$(NC)"
	@$(PYTHON) scripts/check_rag_readiness.py
	@echo ""

check-rag-readiness-verbose: ## Verbose RAG readiness check with details
	@echo "$(BLUE)🔍 Checking RAG Readiness (Verbose)...$(NC)"
	@$(PYTHON) scripts/check_rag_readiness.py --verbose
	@echo ""

check-arv-minimum: ## Check ARV minimum requirements (Phase RC2)
	@echo "$(BLUE)🔍 Checking ARV Minimum Requirements...$(NC)"
	@$(PYTHON) scripts/check_arv_minimum.py
	@echo ""

check-arv-minimum-verbose: ## Verbose ARV minimum check with details
	@echo "$(BLUE)🔍 Checking ARV Minimum Requirements (Verbose)...$(NC)"
	@$(PYTHON) scripts/check_arv_minimum.py --verbose
	@echo ""

check-arv-portfolio: ## Check ARV minimum across all local repos (PORT2)
	@echo "$(BLUE)📦 Checking ARV Minimum Requirements (Portfolio Mode)...$(NC)"
	@$(PYTHON) scripts/check_arv_minimum.py --portfolio
	@echo ""

check-arv-engine-flags: ## Check ARV engine flags safety (Phase AE3)
	@echo "$(BLUE)🚦 Checking ARV Engine Flags...$(NC)"
	@$(PYTHON) scripts/check_arv_engine_flags.py
	@echo ""

check-arv-engine-flags-verbose: ## Verbose ARV engine flags check with details
	@echo "$(BLUE)🚦 Checking ARV Engine Flags (Verbose)...$(NC)"
	@$(PYTHON) scripts/check_arv_engine_flags.py --verbose
	@echo ""

check-arv-agents: ## Check agent structure and ADK compliance (R1 - SPEC-ALIGN-ARV-EXPANSION)
	@echo "$(BLUE)🤖 Checking Agent Structure and ADK Compliance (R1)...$(NC)"
	@$(PYTHON) scripts/check_arv_agents.py
	@echo ""

check-arv-services: ## Check gateway separation and service compliance (R3 - SPEC-ALIGN-ARV-EXPANSION)
	@echo "$(BLUE)🚪 Checking Gateway Separation and Service Compliance (R3)...$(NC)"
	@$(PYTHON) scripts/check_arv_services.py
	@echo ""

check-arv-config: ## Check configuration and feature flag defaults (SPEC-ALIGN-ARV-EXPANSION)
	@echo "$(BLUE)⚙️  Checking Configuration and Feature Flag Defaults...$(NC)"
	@$(PYTHON) scripts/check_arv_config.py
	@echo ""

check-slack-gateway-config: ## Validate Slack gateway Terraform config (Phase 25)
	@echo "$(BLUE)🔍 Validating Slack gateway configuration (ENV=$${ENV:-dev})...$(NC)"
	@$(PYTHON) scripts/ci/check_slack_gateway_config.py $${ENV:-dev}
	@echo ""

check-slack-gateway-config-all: ## Validate Slack gateway config for all environments
	@echo "$(BLUE)🔍 Validating Slack gateway configuration (ALL ENVIRONMENTS)...$(NC)"
	@echo ""
	@echo "$(YELLOW)=== Dev Environment ===$(NC)"
	@$(PYTHON) scripts/ci/check_slack_gateway_config.py dev || true
	@echo ""
	@echo "$(YELLOW)=== Staging Environment ===$(NC)"
	@$(PYTHON) scripts/ci/check_slack_gateway_config.py staging || true
	@echo ""
	@echo "$(YELLOW)=== Production Environment ===$(NC)"
	@$(PYTHON) scripts/ci/check_slack_gateway_config.py prod || true
	@echo ""

check-arv-spec: check-arv-agents check-arv-services check-arv-config ## Run all ADK spec compliance checks (R1, R3, config)
	@echo "$(BLUE)📋 Running ADK Spec Compliance Checks...$(NC)"
	@echo "$(GREEN)✅ All ADK spec checks passed!$(NC)"
	@echo ""

print-rag-config: ## Print current RAG configuration (dry-run)
	@echo "$(BLUE)📋 Current RAG Configuration:$(NC)"
	@$(PYTHON) scripts/print_rag_config.py
	@echo ""

print-agent-engine-config: ## Print Agent Engine deployment configuration (Phase AE1)
	@echo "$(BLUE)🔍 Agent Engine Configuration:$(NC)"
	@$(PYTHON) scripts/print_agent_engine_config.py
	@echo ""

print-agent-engine-config-verbose: ## Verbose Agent Engine config with full details
	@echo "$(BLUE)🔍 Agent Engine Configuration (Verbose):$(NC)"
	@$(PYTHON) scripts/print_agent_engine_config.py --verbose
	@echo ""

agent-engine-dev-smoke: ## Run dev smoke test for Agent Engine wiring (AE3)
	@echo "$(BLUE)🧪 Running Agent Engine Dev Smoke Test (AE3)...$(NC)"
	@$(PYTHON) scripts/run_agent_engine_dev_smoke.py
	@echo ""

agent-engine-dev-smoke-verbose: ## Run dev smoke test with detailed output
	@echo "$(BLUE)🧪 Running Agent Engine Dev Smoke Test (Verbose)...$(NC)"
	@$(PYTHON) scripts/run_agent_engine_dev_smoke.py --verbose
	@echo ""

## ============================================================================
## Inline Source Deployment (Phase 3+4) - ARV gates and safe deployment
## ============================================================================

check-inline-deploy-ready: ## ARV check: Validate readiness for inline source deployment (Phase 4)
	@echo "$(BLUE)🔍 ARV: Checking inline deploy readiness...$(NC)"
	@$(PYTHON) scripts/check_inline_deploy_ready.py \
		--agent-name $${AGENT_NAME:-bob} \
		--env $${ENV:-dev}
	@echo ""

deploy-inline-dry-run: ## Dry-run validation for inline source deploy (DEFAULT, safe)
	@echo "$(BLUE)🔍 Inline Source Deploy - DRY RUN (Validation Only)...$(NC)"
	@echo "$(YELLOW)ℹ️  This validates config without deploying. Use deploy-inline-dev-execute for actual deploy.$(NC)"
	@$(PYTHON) -m agents.agent_engine.deploy_inline_source \
		--agent-name bob \
		--project $${GCP_PROJECT_ID:-test-project-placeholder} \
		--location $${GCP_LOCATION:-us-central1} \
		--env dev
	@echo ""

deploy-inline-dev-execute: check-inline-deploy-ready ## MANUAL ONLY: Execute inline deploy to dev (ARV gate enforced)
	@echo "$(GREEN)✅ ARV checks passed$(NC)"
	@echo "$(RED)⚠️  EXECUTING INLINE DEPLOY TO DEV - This will create real Agent Engine resources!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C now to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@$(PYTHON) -m agents.agent_engine.deploy_inline_source \
		--agent-name bob \
		--project $${GCP_PROJECT_ID:-test-project-placeholder} \
		--location $${GCP_LOCATION:-us-central1} \
		--env dev \
		--execute
	@echo ""

deploy-inline-staging-execute: check-inline-deploy-ready ## MANUAL ONLY: Execute inline deploy to staging (ARV gate enforced)
	@echo "$(GREEN)✅ ARV checks passed$(NC)"
	@echo "$(RED)⚠️  EXECUTING INLINE DEPLOY TO STAGING$(NC)"
	@echo "$(YELLOW)Press Ctrl+C now to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@$(PYTHON) -m agents.agent_engine.deploy_inline_source \
		--agent-name bob \
		--project $${GCP_PROJECT_ID:-test-project-placeholder} \
		--location $${GCP_LOCATION:-us-central1} \
		--env staging \
		--execute
	@echo ""

## ============================================================================
## Stage Agent Engine Deploy (Phase 36) - CI-only deployment to stage
## ============================================================================

deploy-bob-stage: ## Deploy Bob to stage Agent Engine (CI use only)
	@echo "$(BLUE)🚀 Deploying Bob to Stage Agent Engine...$(NC)"
	@$(PYTHON) scripts/deploy_inline_source.py \
		--agent bob \
		--env stage \
		--project $${PROJECT_ID_STAGE:-$${GCP_PROJECT_ID_STAGE}} \
		--region $${LOCATION_STAGE:-$${GCP_LOCATION:-us-central1}}
	@echo ""

deploy-foreman-stage: ## Deploy Foreman to stage Agent Engine (CI use only)
	@echo "$(BLUE)🚀 Deploying Foreman to Stage Agent Engine...$(NC)"
	@$(PYTHON) scripts/deploy_inline_source.py \
		--agent foreman \
		--env stage \
		--project $${PROJECT_ID_STAGE:-$${GCP_PROJECT_ID_STAGE}} \
		--region $${LOCATION_STAGE:-$${GCP_LOCATION:-us-central1}}
	@echo ""

deploy-stage-all: deploy-bob-stage deploy-foreman-stage ## Deploy all agents to stage (Bob + Foreman)
	@echo "$(GREEN)✅ All agents deployed to stage!$(NC)"

deploy-stage-dry-run: ## Validate stage deployment config (dry-run)
	@echo "$(BLUE)🔍 Validating Stage Deployment Configuration...$(NC)"
	@$(PYTHON) scripts/deploy_inline_source.py \
		--agent bob \
		--env stage \
		--dry-run
	@$(PYTHON) scripts/deploy_inline_source.py \
		--agent foreman \
		--env stage \
		--dry-run
	@echo "$(GREEN)✅ Stage deployment configuration valid$(NC)"
	@echo ""

smoke-bob-agent-engine-dev: ## Run dev smoke test against Bob's Agent Engine instance (Phase 5)
	@echo "$(BLUE)🚦 Running Bob Agent Engine dev smoke test...$(NC)"
	@echo "$(YELLOW)ℹ️  Requires BOB_AGENT_ENGINE_NAME_DEV to be set after dev deployment$(NC)"
	@$(PYTHON) -m scripts.smoke_test_bob_agent_engine_dev
	@echo ""

## ============================================================================

arv-department: ## Run comprehensive ARV for IAM/ADK department (ARIV-DEPT)
	@echo "$(BLUE)🚦 Running ARV for IAM/ADK department (DEPLOYMENT_ENV=$${DEPLOYMENT_ENV:-dev})...$(NC)"
	@$(PYTHON) scripts/run_arv_department.py --env "$${DEPLOYMENT_ENV:-dev}"

arv-department-verbose: ## Run ARV with detailed output
	@echo "$(BLUE)🚦 Running ARV for IAM/ADK department (Verbose)...$(NC)"
	@$(PYTHON) scripts/run_arv_department.py --env "$${DEPLOYMENT_ENV:-dev}" --verbose

arv-department-list: ## List all ARV checks
	@$(PYTHON) scripts/run_arv_department.py --list

arv-gates: check-rag-readiness check-arv-minimum check-arv-engine-flags check-arv-spec ## Run all ARV gates (RAG + minimum + engine flags + spec)
	@echo "$(BLUE)🚦 Running Agent Readiness Verification (ARV) Gates...$(NC)"
	@echo "$(GREEN)✅ All ARV gates passed!$(NC)"

#################################
# SWE Pipeline Testing
#################################

test-swe-pipeline: ## Run SWE pipeline tests
	@echo "$(BLUE)🔧 Running SWE Pipeline Tests...$(NC)"
	@$(PYTEST) tests/test_swe_pipeline.py -v --color=yes
	@echo "$(GREEN)✅ SWE Pipeline tests passed!$(NC)"

test-swe-pipeline-verbose: ## Run SWE pipeline tests with detailed output
	@echo "$(BLUE)🔧 Running SWE Pipeline Tests (Verbose)...$(NC)"
	@$(PYTEST) tests/test_swe_pipeline.py -vvs --color=yes --tb=short
	@echo "$(GREEN)✅ SWE Pipeline tests passed!$(NC)"

test-swe-pipeline-coverage: ## Run SWE pipeline tests with coverage
	@echo "$(BLUE)📊 Running SWE Pipeline Tests with Coverage...$(NC)"
	@$(PYTEST) tests/test_swe_pipeline.py --cov=agents.iam_senior_adk_devops_lead --cov=agents.shared_contracts --cov-report=term --cov-report=html
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

run-swe-pipeline-demo: ## Run SWE pipeline demo with synthetic repo
	@echo "$(BLUE)🚀 Running SWE Pipeline Demo...$(NC)"
	@$(PYTHON) scripts/run_swe_pipeline_once.py --repo-path tests/data/synthetic_repo --task "Audit ADK compliance and fix violations"
	@echo "$(GREEN)✅ Pipeline demo completed!$(NC)"

run-swe-pipeline-interactive: ## Run interactive SWE pipeline
	@echo "$(BLUE)🎯 Starting Interactive SWE Pipeline...$(NC)"
	@$(PYTHON) -c "from agents.iam_senior_adk_devops_lead.orchestrator import run_swe_pipeline, PipelineRequest; \
		import json; \
		req = PipelineRequest('tests/data/synthetic_repo', 'Interactive audit', 'dev'); \
		result = run_swe_pipeline(req); \
		print(f'\n📊 Pipeline Results:'); \
		print(f'  - Issues found: {result.total_issues_found}'); \
		print(f'  - Issues fixed: {result.issues_fixed}'); \
		print(f'  - Duration: {result.pipeline_duration_seconds:.2f}s')"

#################################
# LIVE3 End-to-End Testing (E2E)
#################################

live3-dev-smoke: ## Run LIVE3 dev smoke test (E2E validation of LIVE3 features)
	@echo "$(BLUE)🧪 Running LIVE3 Dev Smoke Test...$(NC)"
	@echo "$(YELLOW)Testing: Portfolio audit + GCS + Slack + GitHub$(NC)"
	@$(PYTHON) scripts/run_live3_dev_smoke.py --repo bobs-brain
	@echo "$(GREEN)✅ LIVE3 smoke test completed!$(NC)"

live3-dev-smoke-verbose: ## Run LIVE3 smoke test with detailed output
	@echo "$(BLUE)🧪 Running LIVE3 Dev Smoke Test (Verbose)...$(NC)"
	@$(PYTHON) scripts/run_live3_dev_smoke.py --repo bobs-brain --verbose
	@echo "$(GREEN)✅ LIVE3 smoke test completed!$(NC)"

live3-dev-smoke-all: ## Run LIVE3 smoke test on all local repos
	@echo "$(BLUE)🧪 Running LIVE3 Dev Smoke Test (All Repos)...$(NC)"
	@$(PYTHON) scripts/run_live3_dev_smoke.py --repo all --verbose
	@echo "$(GREEN)✅ LIVE3 smoke test completed!$(NC)"

#################################
# Slack Integration Testing (SLACK-ENDTOEND-DEV)
#################################

slack-dev-smoke: ## Run Slack webhook dev smoke test (SLACK-ENDTOEND-DEV S3)
	@echo "$(BLUE)🧪 Running Slack Webhook Dev Smoke Test...$(NC)"
	@echo "$(YELLOW)Testing: Slack webhook → A2A gateway → Agent Engine$(NC)"
	@$(PYTHON) scripts/run_slack_dev_smoke.py
	@echo "$(GREEN)✅ Slack smoke test completed!$(NC)"

slack-dev-smoke-verbose: ## Run Slack smoke test with detailed output
	@echo "$(BLUE)🧪 Running Slack Webhook Dev Smoke Test (Verbose)...$(NC)"
	@$(PYTHON) scripts/run_slack_dev_smoke.py --verbose
	@echo "$(GREEN)✅ Slack smoke test completed!$(NC)"

slack-dev-smoke-health: ## Run Slack smoke test (health check only)
	@echo "$(BLUE)🩺 Checking Slack Webhook Health...$(NC)"
	@$(PYTHON) scripts/run_slack_dev_smoke.py --health-only
	@echo "$(GREEN)✅ Health check completed!$(NC)"

slack-dev-smoke-cloud: ## Run Slack smoke test against Cloud Run deployment
	@echo "$(BLUE)🧪 Running Slack Webhook Smoke Test (Cloud Run)...$(NC)"
	@command -v gcloud >/dev/null 2>&1 || { echo "$(RED)❌ gcloud CLI not installed$(NC)"; exit 1; }
	@SERVICE_URL=$$(gcloud run services describe slack-webhook --region=us-central1 --format='value(status.url)' 2>/dev/null); \
	if [ -z "$$SERVICE_URL" ]; then \
		echo "$(RED)❌ Slack webhook service not found in Cloud Run$(NC)"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)Testing Cloud Run service: $$SERVICE_URL$(NC)"; \
	$(PYTHON) scripts/run_slack_dev_smoke.py --url $$SERVICE_URL --verbose
	@echo "$(GREEN)✅ Cloud Run smoke test completed!$(NC)"

#################################
# A2A Inspector (Debugging & Validation)
#################################

a2a-inspector-dev: ## Run A2A Inspector against dev gateway (Docker method)
	@echo "$(BLUE)🔍 Starting A2A Inspector for Development...$(NC)"
	@echo "$(YELLOW)See: 000-docs/123-DR-STND-a2a-inspector-usage-and-local-setup.md$(NC)"
	@echo ""
	@# Check if Docker is available
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker not installed$(NC)"; exit 1; }
	@# Check if a2a-inspector image exists, build if not
	@if ! docker images | grep -q a2a-inspector; then \
		echo "$(YELLOW)Building a2a-inspector Docker image...$(NC)"; \
		if [ -d /tmp/a2a-inspector ]; then \
			cd /tmp/a2a-inspector && git pull; \
		else \
			git clone https://github.com/a2aproject/a2a-inspector.git /tmp/a2a-inspector; \
		fi; \
		cd /tmp/a2a-inspector && docker build -t a2a-inspector .; \
	fi
	@# Stop existing container if running
	@docker ps -a | grep a2a-inspector | awk '{print $$1}' | xargs -r docker stop 2>/dev/null || true
	@docker ps -a | grep a2a-inspector | awk '{print $$1}' | xargs -r docker rm 2>/dev/null || true
	@# Start new container
	@echo "$(BLUE)Starting a2a-inspector on port 8080...$(NC)"
	@docker run -d -p 8080:8080 --name a2a-inspector a2a-inspector
	@echo ""
	@echo "$(GREEN)✅ A2A Inspector running!$(NC)"
	@echo ""
	@echo "$(BLUE)Access:$(NC) http://127.0.0.1:8080"
	@echo ""
	@if [ -n "$$A2A_GATEWAY_DEV_URL" ]; then \
		echo "$(BLUE)Dev Gateway URL (from .env):$(NC) $$A2A_GATEWAY_DEV_URL"; \
	else \
		echo "$(YELLOW)⚠ A2A_GATEWAY_DEV_URL not set in .env$(NC)"; \
		echo "$(YELLOW)Set it to your dev A2A gateway endpoint$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)To stop:$(NC) make a2a-inspector-stop"

a2a-inspector-stop: ## Stop A2A Inspector container
	@echo "$(BLUE)🛑 Stopping A2A Inspector...$(NC)"
	@docker ps -a | grep a2a-inspector | awk '{print $$1}' | xargs -r docker stop 2>/dev/null || true
	@docker ps -a | grep a2a-inspector | awk '{print $$1}' | xargs -r docker rm 2>/dev/null || true
	@echo "$(GREEN)✅ A2A Inspector stopped$(NC)"

a2a-inspector-logs: ## View A2A Inspector logs
	@docker logs a2a-inspector

a2a-inspector-status: ## Check A2A Inspector status
	@echo "$(BLUE)🔍 A2A Inspector Status:$(NC)"
	@if docker ps | grep -q a2a-inspector; then \
		echo "$(GREEN)✅ Running on http://127.0.0.1:8080$(NC)"; \
		docker ps | grep a2a-inspector; \
	else \
		echo "$(YELLOW)⚠ Not running$(NC)"; \
		echo "$(YELLOW)Start with: make a2a-inspector-dev$(NC)"; \
	fi

#################################
# Deployment Operations (CICD-DEPT)
#################################

deploy-dev: ## Trigger dev deployment via GitHub Actions
	@echo "$(BLUE)🚀 Triggering deployment to dev environment...$(NC)"
	@command -v gh >/dev/null 2>&1 || { echo "$(RED)❌ GitHub CLI (gh) not installed$(NC)"; exit 1; }
	@echo "⚠️  This will deploy to dev. Continue? [y/N] " && read ans && [ $${ans:-N} = y ] || { echo "Cancelled"; exit 1; }
	@gh workflow run deploy-dev.yml
	@echo "$(GREEN)✅ Deployment triggered! Check status with: make deploy-status$(NC)"

deploy-staging: ## Trigger staging deployment via GitHub Actions
	@echo "$(BLUE)🚀 Triggering deployment to staging environment...$(NC)"
	@command -v gh >/dev/null 2>&1 || { echo "$(RED)❌ GitHub CLI (gh) not installed$(NC)"; exit 1; }
	@echo "⚠️  This will deploy to STAGING. Continue? [y/N] " && read ans && [ $${ans:-N} = y ] || { echo "Cancelled"; exit 1; }
	@gh workflow run deploy-staging.yml
	@echo "$(GREEN)✅ Deployment triggered! Check status with: make deploy-status$(NC)"

deploy-prod: ## Trigger production deployment via GitHub Actions (CAUTION!)
	@echo "$(RED)⚠️ WARNING: PRODUCTION DEPLOYMENT$(NC)"
	@echo "$(RED)This will deploy to PRODUCTION and requires multiple approvals.$(NC)"
	@command -v gh >/dev/null 2>&1 || { echo "$(RED)❌ GitHub CLI (gh) not installed$(NC)"; exit 1; }
	@echo "$(RED)Are you ABSOLUTELY SURE? Type 'DEPLOY_TO_PRODUCTION' to confirm: $(NC)" && read ans && [ "$$ans" = "DEPLOY_TO_PRODUCTION" ] || { echo "Cancelled"; exit 1; }
	@gh workflow run deploy-prod.yml
	@echo "$(GREEN)✅ Production deployment triggered!$(NC)"
	@echo "$(YELLOW)⚠️ Remember: Multiple approvals required before deployment proceeds.$(NC)"

deploy-status: ## Check deployment workflow status
	@echo "$(BLUE)📊 Checking deployment workflow status...$(NC)"
	@command -v gh >/dev/null 2>&1 || { echo "$(RED)❌ GitHub CLI (gh) not installed$(NC)"; exit 1; }
	@gh run list --workflow=deploy-dev.yml --limit=3
	@echo ""
	@gh run list --workflow=deploy-staging.yml --limit=3
	@echo ""
	@gh run list --workflow=deploy-prod.yml --limit=3

deploy-logs: ## View logs from latest deployment (specify ENV=dev|staging|prod)
	@echo "$(BLUE)📜 Viewing deployment logs for $(ENV:-dev)...$(NC)"
	@command -v gh >/dev/null 2>&1 || { echo "$(RED)❌ GitHub CLI (gh) not installed$(NC)"; exit 1; }
	@gh run view --workflow=deploy-$(ENV:-dev).yml --log

deploy-list: ## List all deployment workflows
	@echo "$(BLUE)📋 Available deployment workflows:$(NC)"
	@echo ""
	@echo "  $(GREEN)deploy-dev.yml$(NC)      - Deploy to dev environment"
	@echo "  $(GREEN)deploy-staging.yml$(NC)  - Deploy to staging (requires approval)"
	@echo "  $(GREEN)deploy-prod.yml$(NC)     - Deploy to production (multiple approvals)"
	@echo ""
	@echo "$(YELLOW)Trigger deployments with:$(NC)"
	@echo "  make deploy-dev"
	@echo "  make deploy-staging"
	@echo "  make deploy-prod"
	@echo ""
	@echo "$(YELLOW)Check status with:$(NC)"
	@echo "  make deploy-status"

deploy-help: ## Show deployment help and requirements
	@echo "$(BLUE)🚀 Deployment Help$(NC)"
	@echo ""
	@echo "$(YELLOW)Prerequisites:$(NC)"
	@echo "  1. GitHub CLI (gh) installed"
	@echo "  2. Authenticated to GitHub (gh auth login)"
	@echo "  3. CI checks passing (make ci or check GitHub Actions)"
	@echo "  4. ARV checks passing (make arv-department)"
	@echo ""
	@echo "$(YELLOW)Deployment Flow:$(NC)"
	@echo "  1. Code changes pushed to main/develop"
	@echo "  2. CI workflow runs (ci.yml)"
	@echo "  3. All checks pass (drift, ARV, tests, security)"
	@echo "  4. Trigger deployment: make deploy-dev"
	@echo "  5. ARV gate runs in deployment workflow"
	@echo "  6. Deployment proceeds if ARV passes"
	@echo "  7. Check status: make deploy-status"
	@echo ""
	@echo "$(YELLOW)Environment Requirements:$(NC)"
	@echo "  $(GREEN)dev$(NC)      - Automatic after ARV gate"
	@echo "  $(GREEN)staging$(NC)  - Manual approval + ARV gate"
	@echo "  $(GREEN)prod$(NC)     - Multiple approvals + strict ARV"
	@echo ""
	@echo "$(YELLOW)GitHub Environment Variables Required:$(NC)"
	@echo "  DEV_PROJECT_ID, DEV_REGION, DEV_STAGING_BUCKET"
	@echo "  STAGING_PROJECT_ID, STAGING_REGION, STAGING_STAGING_BUCKET"
	@echo "  PROD_PROJECT_ID, PROD_REGION, PROD_STAGING_BUCKET"
	@echo ""
	@echo "$(YELLOW)GitHub Secrets Required:$(NC)"
	@echo "  GCP_WORKLOAD_IDENTITY_PROVIDER"
	@echo "  GCP_SERVICE_ACCOUNT"
	@echo "  SLACK_SIGNING_SECRET"
	@echo "  SLACK_BOT_TOKEN"

.PHONY: help setup test lint format clean docker version benchmark ci all
.PHONY: install-hooks deps format-check type-check
.PHONY: test-v1 test-v2 test-coverage
.PHONY: run-v1 run-v2 run-selector
.PHONY: docker-build docker-v1 docker-v2 docker-all docker-stop docker-clean
.PHONY: safe-commit pre-release clean-all version logs dev prod
.PHONY: crawl-adk-docs crawl-test
.PHONY: check-config check-rag-readiness check-rag-readiness-verbose print-rag-config arv-gates arv-department arv-department-verbose arv-department-list
.PHONY: print-agent-engine-config print-agent-engine-config-verbose deploy-inline-dry-run deploy-inline-dev-execute deploy-inline-staging-execute
.PHONY: test-swe-pipeline test-swe-pipeline-verbose test-swe-pipeline-coverage
.PHONY: run-swe-pipeline-demo run-swe-pipeline-interactive
.PHONY: live3-dev-smoke live3-dev-smoke-verbose live3-dev-smoke-all
.PHONY: slack-dev-smoke slack-dev-smoke-verbose slack-dev-smoke-health slack-dev-smoke-cloud
.PHONY: deploy-dev deploy-staging deploy-prod deploy-status deploy-logs deploy-list deploy-help