"""
Bob's Brain - Agent Engine Entrypoint for ADK Deployment

This file is REQUIRED by the 'adk deploy agent_engine' command.

When deploying with:
    adk deploy agent_engine my_agent \
      --project bobs-brain-dev \
      --region us-central1 \
      --staging_bucket gs://bobs-brain-dev-adk-staging

ADK CLI will:
1. Find this file (agent_engine_app.py by default, or via --adk_app flag)
2. Import the 'app' variable (must be a Runner instance)
3. Package everything into a Docker container
4. Upload to staging bucket
5. Deploy to Vertex AI Agent Engine

Enforces:
- R1: Uses google-adk (LlmAgent + Runner)
- R2: Designed for Vertex AI Agent Engine runtime
- R5: Dual memory wiring (Session + Memory Bank)
- R7: SPIFFE ID propagation
"""

import logging
import os

from .agent import create_runner

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables (for logging)
APP_NAME = os.getenv("APP_NAME", "bobs-brain")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/unknown/unknown/unknown",
)

# CRITICAL: ADK CLI expects a Runner instance named 'app'
# This is the entrypoint that gets packaged and deployed to Agent Engine
logger.info(
    "Creating Runner for Agent Engine deployment via ADK CLI",
    extra={
        "app_name": APP_NAME,
        "spiffe_id": AGENT_SPIFFE_ID,
        "deployment_method": "adk-cli",
    },
)

# Create the Runner with dual memory services (R5)
app = create_runner()

logger.info(
    "✅ Runner created - ready for ADK deployment to Vertex AI Agent Engine",
    extra={
        "app_name": APP_NAME,
        "spiffe_id": AGENT_SPIFFE_ID,
        "has_session_service": True,
        "has_memory_service": True,
    },
)

# Note: The Agent Engine will call app.run_async() or app.run_live()
# when handling requests. The Runner manages the full execution lifecycle.
