"""
iam-senior-adk-devops-lead - Agent Engine Entrypoint for ADK Deployment

This file is REQUIRED by the 'adk deploy agent_engine' command.

When deploying with:
    adk deploy agent_engine agents.iam_senior_adk_devops_lead \
      --project bobs-brain-dev \
      --region us-central1 \
      --staging_bucket gs://bobs-brain-dev-adk-staging

ADK CLI will:
1. Find this file (agent_engine_app.py by default, or via --adk_app flag)
2. Import the 'app' variable (must be a Runner instance)
3. Package everything into a Docker container
4. Upload to staging bucket
5. Deploy to Vertex AI Agent Engine

This foreman agent orchestrates the iam-* specialist agents via A2A protocol.

Enforces:
- R1: Uses google-adk (LlmAgent + Runner)
- R2: Designed for Vertex AI Agent Engine runtime
- R5: Dual memory wiring (Session + Memory Bank)
- R7: SPIFFE ID propagation
"""

from .agent import create_runner
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables (for logging)
APP_NAME = os.getenv("APP_NAME", "iam-senior-adk-devops-lead")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.1.0",
)

# CRITICAL: ADK CLI expects a Runner instance named 'app'
# This is the entrypoint that gets packaged and deployed to Agent Engine
logger.info(
    f"Creating Runner for Foreman Agent Engine deployment via ADK CLI",
    extra={
        "app_name": APP_NAME,
        "spiffe_id": AGENT_SPIFFE_ID,
        "deployment_method": "adk-cli",
        "role": "department-foreman",
    },
)

# Create the Runner with dual memory services (R5)
app = create_runner()

logger.info(
    "✅ Foreman Runner created - ready for ADK deployment to Vertex AI Agent Engine",
    extra={
        "app_name": APP_NAME,
        "spiffe_id": AGENT_SPIFFE_ID,
        "has_session_service": True,
        "has_memory_service": True,
        "orchestrates": ["iam-adk", "iam-issue", "iam-fix-plan", "iam-fix-impl", "iam-qa", "iam-doc", "iam-cleanup", "iam-index"],
    },
)

# Note: The Agent Engine will call app.run_async() or app.run_live()
# when handling requests. The Runner manages the full execution lifecycle.
# The foreman will receive high-level tasks from Bob and delegate to specialists.