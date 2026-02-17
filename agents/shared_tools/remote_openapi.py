"""
Remote OpenAPI Tools Module (STUB)

This module will contain OpenAPI-based tools that connect to external APIs
via Cloud Run services. These services act as secure gateways to third-party APIs.

IMPORTANT: Tools here configure connections to Cloud Run services that proxy API calls.
They do NOT directly call external APIs.

Status: STUB ONLY - No OpenAPI gateways deployed yet
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# OPENAPI TOOLS - Connect to Cloud Run API gateways
# ============================================================================


def get_github_api_tool() -> Optional[Any]:
    """
    Get GitHub API tool (FUTURE).

    This would connect to a Cloud Run service that proxies GitHub API calls.
    The service handles authentication and rate limiting.

    TODO: Deploy GitHub API gateway first, then wire here.
    """
    # TODO: When ready to implement:
    # 1. Deploy Cloud Run service with OpenAPI spec
    # 2. Service handles GitHub token from Secret Manager
    # 3. Wire here:
    #
    # from google.adk.toolsets import OpenAPIToolset
    # gateway_url = os.getenv("GITHUB_GATEWAY_URL")
    # if gateway_url:
    #     return OpenAPIToolset(
    #         openapi_spec_url=f"{gateway_url}/openapi.json",
    #         server_url=gateway_url
    #     )

    logger.info("GitHub API tool not configured (no gateway deployed)")
    return None


def get_jira_api_tool() -> Optional[Any]:
    """
    Get Jira API tool (FUTURE).

    This would connect to a Cloud Run service that proxies Jira API calls.
    Useful for issue tracking and project management.

    TODO: Deploy Jira API gateway with proper auth.
    """
    # TODO: Implementation pattern:
    # 1. Create Cloud Run service with Jira API proxy
    # 2. Configure Jira credentials in Secret Manager
    # 3. Wire connection here

    logger.info("Jira API tool not configured (no gateway deployed)")
    return None


def get_slack_api_tool() -> Optional[Any]:
    """
    Get Slack API tool (FUTURE).

    This would connect to a Cloud Run service that proxies Slack Web API calls.
    Different from the webhook service - this is for full API access.

    TODO: Deploy Slack API gateway.
    """
    # TODO: When ready:
    # 1. Deploy Cloud Run service with Slack Web API proxy
    # 2. Configure OAuth token in Secret Manager
    # 3. Wire here with OpenAPIToolset

    logger.info("Slack API tool not configured (no gateway deployed)")
    return None


def list_available_openapi_gateways() -> List[str]:
    """
    List currently available OpenAPI gateways.

    Returns:
        List of configured gateway names
    """
    # TODO: Once we have gateways, return their names
    return []  # No OpenAPI gateways deployed yet


# ============================================================================
# OPENAPI GATEWAY DEPLOYMENT NOTES
# ============================================================================
"""
When we need OpenAPI gateways, the pattern will be:

1. Create gateway implementation in service/{name}_api_gateway/
   - Dockerfile for the Cloud Run service
   - main.py with FastAPI/Flask + OpenAPI spec
   - requirements.txt
   - openapi.yaml specification

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy {name}-api-gateway \\
     --source service/{name}_api_gateway \\
     --project bobs-brain \\
     --region us-central1
   ```

3. Wire in this file:
   - Add environment variable for the Cloud Run URL
   - Create OpenAPIToolset with that URL
   - Return the toolset

4. Document in 6767-NNN-OD-DEPL-{name}-api-gateway.md:
   - Why we need this gateway
   - What API it proxies
   - Security considerations
   - Rate limiting strategy
"""

# ============================================================================
# POLICY: OpenAPI tools connect to Cloud Run gateways
# ============================================================================
# These tools:
# - Are ADK OpenAPIToolset instances
# - Connect to Cloud Run services that proxy external APIs
# - Do NOT call external APIs directly
# - Require the Cloud Run gateway to be deployed first
# - Should handle authentication at the gateway level
