"""
GitHub Webhook - FastAPI Proxy to Agent Engine

Enforces R3: Cloud Run as gateway only (proxy to Agent Engine via REST).

This service:
1. Receives GitHub webhook events (issues, PRs, pushes)
2. Proxies to Agent Engine via A2A gateway
3. Does NOT import Runner (R3 compliance)
4. Routes events to appropriate specialists

Event Routing:
- issues.opened, issues.labeled → iam-triage
- pull_request.opened → iam-qa (for review)
- push (to main) → iam-compliance (for audit)

Environment Variables:
- GITHUB_WEBHOOK_SECRET: GitHub webhook secret for signature verification
- A2A_GATEWAY_URL: A2A gateway URL for routing
- PROJECT_ID: GCP project ID
- DEPLOYMENT_ENV: Deployment environment (dev/prod)
- PORT: Service port (default 8080)

Phase H: Universal Autonomous AI Crew - Event Triggers
"""

import hashlib
import hmac
import logging
import os
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment configuration
GITHUB_WEBHOOK_ENABLED = os.getenv("GITHUB_WEBHOOK_ENABLED", "false").lower() == "true"
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
A2A_GATEWAY_URL = os.getenv("A2A_GATEWAY_URL")
PROJECT_ID = os.getenv("PROJECT_ID")
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "dev")
PORT = int(os.getenv("PORT", "8080"))


# Validate required environment variables
def validate_config() -> tuple[bool, list[str]]:
    """
    Validate GitHub webhook configuration.

    Returns:
        (is_valid, missing_vars): Tuple of validation status and list of missing variables
    """
    if not GITHUB_WEBHOOK_ENABLED:
        logger.info("GitHub webhook is DISABLED (GITHUB_WEBHOOK_ENABLED=false)")
        return True, []  # Valid config when disabled

    missing = []

    # Required for webhook signature verification
    if not GITHUB_WEBHOOK_SECRET:
        missing.append("GITHUB_WEBHOOK_SECRET")

    # Required for routing to Agent Engine
    if not A2A_GATEWAY_URL:
        missing.append("A2A_GATEWAY_URL")

    if missing:
        logger.error(
            f"GitHub webhook ENABLED but missing required variables: {', '.join(missing)}"
        )
        return False, missing

    logger.info("GitHub webhook ENABLED and configured")
    return True, []


config_valid, missing_vars = validate_config()

# Create FastAPI app
app = FastAPI(
    title="Bob's Brain GitHub Webhook",
    description="GitHub event handler proxying to Vertex AI Agent Engine",
    version="0.1.0",
)


def verify_github_signature(body: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature (HMAC-SHA256).

    Args:
        body: Raw request body
        signature: X-Hub-Signature-256 header

    Returns:
        bool: True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = (
        "sha256="
        + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
    )

    # Compare signatures (constant-time)
    return hmac.compare_digest(expected_signature, signature)


# ============================================================================
# Event Routing Logic
# ============================================================================


def get_target_agent_and_prompt(event_type: str, action: str, payload: Dict[str, Any]) -> tuple[str, str]:
    """
    Determine which agent to route to and build the prompt.

    Args:
        event_type: GitHub event type (issues, pull_request, push)
        action: Event action (opened, closed, etc.)
        payload: Full webhook payload

    Returns:
        (agent_role, prompt): Target agent and formatted prompt
    """
    # Issue events
    if event_type == "issues":
        issue = payload.get("issue", {})
        repo = payload.get("repository", {}).get("full_name", "unknown")
        title = issue.get("title", "")
        body = issue.get("body", "") or ""
        number = issue.get("number", 0)
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        if action == "opened":
            return "iam-orchestrator", f"""
New GitHub issue opened in {repo}:

Issue #{number}: {title}
Labels: {', '.join(labels) if labels else 'none'}

{body[:2000]}

Please analyze this issue and:
1. Triage for priority and type
2. Identify which specialist(s) should handle it
3. Create a plan for resolution
"""

        if action == "labeled":
            label_name = payload.get("label", {}).get("name", "")
            if label_name in ["bug", "critical", "urgent"]:
                return "iam-orchestrator", f"""
Issue #{number} in {repo} was labeled as '{label_name}':

Title: {title}
Current labels: {', '.join(labels)}

Please prioritize and create a fix plan for this {label_name}.
"""

    # Pull request events
    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {}).get("full_name", "unknown")
        title = pr.get("title", "")
        body = pr.get("body", "") or ""
        number = pr.get("number", 0)
        head_branch = pr.get("head", {}).get("ref", "unknown")
        base_branch = pr.get("base", {}).get("ref", "unknown")

        if action == "opened":
            return "iam-orchestrator", f"""
New pull request opened in {repo}:

PR #{number}: {title}
Branch: {head_branch} → {base_branch}

{body[:2000]}

Please:
1. Review for ADK compliance and Hard Mode rules
2. Check for test coverage
3. Validate documentation updates if needed
"""

        if action == "synchronize":  # New commits pushed
            return "iam-orchestrator", f"""
PR #{number} in {repo} was updated with new commits:

Title: {title}
Branch: {head_branch} → {base_branch}

Please re-run compliance checks on the updated code.
"""

    # Push events (to main branch)
    if event_type == "push":
        repo = payload.get("repository", {}).get("full_name", "unknown")
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])

        if ref in ["refs/heads/main", "refs/heads/master"]:
            commit_messages = "\n".join([
                f"- {c.get('message', '').split(chr(10))[0]}"
                for c in commits[:5]
            ])

            return "iam-orchestrator", f"""
New push to {ref} in {repo}:

Recent commits:
{commit_messages}

Please:
1. Run ADK compliance audit
2. Check for any pattern violations
3. Update knowledge index if needed
"""

    # Default: Route to foreman for triage
    return "iam-orchestrator", f"""
GitHub event received: {event_type}.{action}

Repository: {payload.get('repository', {}).get('full_name', 'unknown')}

Please analyze this event and determine appropriate action.
"""


# ============================================================================
# Webhook Endpoint
# ============================================================================


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
) -> Dict[str, Any]:
    """
    Handle GitHub webhook events.

    Receives events from GitHub and proxies to Agent Engine via A2A.

    R3 Compliance: Does NOT run agent locally - proxies via REST.

    Events handled:
    - issues: Issue created, labeled, etc.
    - pull_request: PR opened, synchronized, etc.
    - push: Code pushed to branches

    Returns:
        dict: Processing status
    """
    try:
        # Check if webhook is enabled
        if not GITHUB_WEBHOOK_ENABLED:
            logger.info("GitHub webhook disabled - ignoring event")
            return {"ok": True, "status": "disabled"}

        # Read raw body for signature verification
        body = await request.body()

        # Verify GitHub signature (production security)
        if GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
            if not verify_github_signature(body, x_hub_signature_256):
                logger.warning("Invalid GitHub signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON
        payload = await request.json()

        # Get action (if present)
        action = payload.get("action", "")

        logger.info(
            f"GitHub event: {x_github_event}.{action}",
            extra={
                "delivery_id": x_github_delivery,
                "repo": payload.get("repository", {}).get("full_name"),
            },
        )

        # Ping event (webhook setup verification)
        if x_github_event == "ping":
            logger.info("GitHub ping event received")
            return {"ok": True, "status": "pong"}

        # Determine routing
        agent_role, prompt = get_target_agent_and_prompt(
            x_github_event, action, payload
        )

        # Query Agent Engine via A2A gateway
        _response = await route_to_agent(
            agent_role=agent_role,
            prompt=prompt,
            context={
                "github_event": x_github_event,
                "github_action": action,
                "delivery_id": x_github_delivery,
                "repository": payload.get("repository", {}).get("full_name"),
            }
        )

        return {
            "ok": True,
            "status": "processed",
            "agent": agent_role,
            "delivery_id": x_github_delivery,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub event processing failed: {e}", exc_info=True)
        # Return 200 to GitHub to prevent retries
        return {"ok": False, "error": str(e)}


async def route_to_agent(
    agent_role: str,
    prompt: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Route request to agent via A2A gateway.

    R3 Compliance: Proxies to Agent Engine, does not run locally.

    Args:
        agent_role: Target agent (e.g., iam-orchestrator)
        prompt: Request prompt
        context: Additional context

    Returns:
        dict: Agent response
    """
    try:
        logger.info(
            f"Routing to {agent_role} via A2A gateway",
            extra={
                "prompt_length": len(prompt),
                "context": context,
            },
        )

        # Build A2A call payload
        a2a_payload = {
            "agent_role": agent_role,
            "prompt": prompt,
            "session_id": f"github_{context.get('delivery_id', 'unknown')}",
            "caller_spiffe_id": "spiffe://intent.solutions/github/webhook",
            "env": DEPLOYMENT_ENV,
            "context": context,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{A2A_GATEWAY_URL}/a2a/run",
                json=a2a_payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

        logger.info(
            "A2A gateway response received",
            extra={
                "response_length": len(result.get("response", "")),
                "correlation_id": result.get("correlation_id"),
            },
        )

        return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error during agent call: {e.response.status_code}",
            extra={"detail": e.response.text},
            exc_info=True,
        )
        return {"error": f"HTTP {e.response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to A2A gateway: {e}", exc_info=True)
        return {"error": "Connection failed"}

    except Exception as e:
        logger.error(f"Routing failed: {e}", exc_info=True)
        return {"error": str(e)}


# ============================================================================
# Health and Info Endpoints
# ============================================================================


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint with configuration status.

    Returns:
        dict: Service health status and configuration
    """
    return {
        "status": "healthy" if (not GITHUB_WEBHOOK_ENABLED or config_valid) else "degraded",
        "service": "github-webhook",
        "version": "0.1.0",
        "github_webhook_enabled": GITHUB_WEBHOOK_ENABLED,
        "config_valid": config_valid,
        "missing_vars": missing_vars if not config_valid else [],
        "a2a_gateway_url": A2A_GATEWAY_URL if A2A_GATEWAY_URL else None,
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint - service info.

    Returns:
        dict: Service metadata
    """
    return {
        "name": "Bob's Brain GitHub Webhook",
        "version": "0.1.0",
        "description": "GitHub event handler proxying to Vertex AI Agent Engine",
        "endpoints": {
            "webhook": "/github/webhook",
            "health": "/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting GitHub Webhook on port {PORT}",
        extra={
            "project_id": PROJECT_ID,
            "env": DEPLOYMENT_ENV,
        },
    )

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
