"""
A2A Gateway - FastAPI Proxy to Agent Engine

Enforces R3: Cloud Run as gateway only (proxy to Agent Engine via REST).

This service:
1. Exposes AgentCard at /.well-known/agent.json
2. Proxies queries to Agent Engine via REST API
3. Does NOT import Runner (R3 compliance)
4. Deployed to Cloud Run as gateway

Environment Variables:
- AGENT_ENGINE_URL: Full URL to Agent Engine REST endpoint
- PROJECT_ID: GCP project ID
- LOCATION: GCP region
- AGENT_ENGINE_ID: Agent Engine instance ID
- PORT: Service port (default 8080)
"""

import logging
import os
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment configuration
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
PORT = int(os.getenv("PORT", "8080"))

# Agent Engine REST API endpoint
# Format: https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}:query
AGENT_ENGINE_URL = os.getenv(
    "AGENT_ENGINE_URL",
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}:query",
)

# Validate required environment variables
if not all([PROJECT_ID, LOCATION, AGENT_ENGINE_ID]):
    raise ValueError(
        "Missing required environment variables: PROJECT_ID, LOCATION, AGENT_ENGINE_ID"
    )

# Create FastAPI app
app = FastAPI(
    title="Bob's Brain A2A Gateway",
    description="A2A Protocol gateway proxying to Vertex AI Agent Engine",
    version="0.6.0",
)

# R3 Compliance: No agent code imports
# AgentCard logic is inlined here to avoid importing from agents/bob/

# ==============================================================================
# A2A PROTOCOL DATA MODELS (Phase AE2)
# ==============================================================================


class A2AAgentCall(BaseModel):
    """
    Request payload for A2A agent-to-agent calls.

    This is the standard shape for internal agent calls via the A2A protocol.
    Phase AE2: Initial definition (stub implementation).
    """

    agent_role: str
    """Target agent role (bob, foreman, iam-adk, iam-issue, etc.)"""

    prompt: str
    """User prompt or task description to send to the agent"""

    context: Optional[Dict[str, Any]] = None
    """Optional additional context (tool outputs, prior results, etc.)"""

    correlation_id: Optional[str] = None
    """Optional correlation ID for tracing (pipeline_run_id)"""

    caller_spiffe_id: Optional[str] = None
    """SPIFFE ID of the calling agent (for authentication and logging)"""

    session_id: Optional[str] = None
    """Optional session ID for conversation continuity"""

    env: Optional[str] = None
    """Target environment (dev, staging, prod). Defaults to current."""


class A2AAgentResult(BaseModel):
    """
    Response payload for A2A agent-to-agent calls.

    This is the standard shape returned from agent calls via the A2A protocol.
    Phase AE2: Initial definition (stub implementation).
    """

    response: str
    """Agent's response text"""

    session_id: Optional[str] = None
    """Session ID if session persistence enabled"""

    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata (tokens used, latency, etc.)"""

    error: Optional[str] = None
    """Error message if call failed"""

    correlation_id: Optional[str] = None
    """Correlation ID from request (for tracing)"""

    target_spiffe_id: Optional[str] = None
    """SPIFFE ID of the target agent that handled the request"""


# Additional environment variables for AgentCard
APP_NAME = os.getenv("APP_NAME", "bobs-brain")
APP_VERSION = os.getenv("APP_VERSION", "0.6.0")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://example.com")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/unknown/unknown/unknown",
)


def get_agent_card_dict() -> Dict[str, Any]:
    """
    Generate AgentCard as dictionary (inlined for R3 compliance).

    R3 Compliance: This logic is inlined here instead of importing
    from agents/bob/ to avoid gateway importing agent code.

    R7 Compliance: Includes SPIFFE ID in description and explicit field.

    Returns:
        dict: AgentCard with agent metadata and capabilities
    """
    # R7: Include SPIFFE ID in description
    description = f"""Bob's Brain - AI Assistant

Identity: {AGENT_SPIFFE_ID}

Capabilities:
- General question answering
- Information lookup
- Task execution via tools
- Multi-turn conversations with memory

This agent uses dual memory (Session + Memory Bank) for context retention
and is deployed on Vertex AI Agent Engine.

A2A Protocol: This agent can be invoked by other agents using the
Agent-to-Agent protocol for multi-agent orchestration.
"""

    return {
        "name": APP_NAME,
        "description": description.strip(),
        "url": PUBLIC_URL,
        "version": APP_VERSION,
        "skills": [],
        "spiffe_id": AGENT_SPIFFE_ID,  # R7: Explicit SPIFFE field
    }


@app.get("/.well-known/agent.json")
async def agent_card() -> Dict[str, Any]:
    """
    A2A Protocol: Return AgentCard for agent discovery.

    This endpoint is required by the A2A protocol specification
    for agent discovery and capability negotiation.

    R3 Compliance: AgentCard logic is inlined here, no agent imports.

    Returns:
        dict: AgentCard with agent metadata and capabilities
    """
    try:
        card_dict = get_agent_card_dict()
        logger.info("AgentCard served", extra={"spiffe_id": card_dict.get("spiffe_id")})
        return card_dict
    except Exception as e:
        logger.error(f"Failed to generate AgentCard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate AgentCard")


@app.post("/query")
async def query(request: Request) -> Dict[str, Any]:
    """
    Proxy query to Agent Engine via REST API.

    R3 Compliance: This gateway does NOT run the agent locally.
    It proxies requests to the Agent Engine REST endpoint.

    Body:
        {
            "query": "user question",
            "session_id": "optional-session-id"
        }

    Returns:
        dict: Agent response from Agent Engine
    """
    try:
        # Parse request body
        body = await request.json()
        query_text = body.get("query")
        session_id = body.get("session_id")

        if not query_text:
            raise HTTPException(status_code=400, detail="Missing 'query' field")

        logger.info(
            "Proxying query to Agent Engine",
            extra={
                "query_length": len(query_text),
                "session_id": session_id,
                "agent_engine_url": AGENT_ENGINE_URL,
            },
        )

        # Prepare request to Agent Engine
        payload = {"query": query_text}

        if session_id:
            payload["session_id"] = session_id

        # Call Agent Engine via REST API (R3: no local Runner)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                AGENT_ENGINE_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            result = response.json()

        logger.info(
            "Agent Engine response received",
            extra={"status_code": response.status_code, "session_id": session_id},
        )

        return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Agent Engine returned error: {e.response.status_code}",
            extra={"detail": e.response.text},
            exc_info=True,
        )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Agent Engine error: {e.response.text}",
        )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Agent Engine: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Agent Engine unavailable")
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/a2a/run")
async def a2a_run(call: A2AAgentCall) -> A2AAgentResult:
    """
    A2A Protocol: Agent-to-Agent call endpoint (AE2).

    Routes agent-to-agent calls to Vertex AI Agent Engine using the
    centralized agent_engine.py config module.

    Body:
        A2AAgentCall with:
        - agent_role: Target agent (bob, foreman, iam-adk, etc.)
        - prompt: Task for the agent
        - context: Optional additional context
        - correlation_id: Optional tracing ID
        - caller_spiffe_id: Optional calling agent identity
        - session_id: Optional session for continuity
        - env: Optional target environment

    Returns:
        A2AAgentResult: Agent response from Agent Engine

    Phase AE2: Real Agent Engine integration implemented.
    """
    try:
        # Import agent_engine_client (local import to avoid issues)
        from agent_engine_client import call_agent_engine

        # Generate correlation ID if not provided
        correlation_id = call.correlation_id or str(uuid.uuid4())

        logger.info(
            "A2A call received",
            extra={
                "agent_role": call.agent_role,
                "caller_spiffe_id": call.caller_spiffe_id,
                "correlation_id": correlation_id,
                "prompt_length": len(call.prompt),
                "env": call.env or "current",
                "session_id": call.session_id,
            },
        )

        # Call Agent Engine
        result = await call_agent_engine(
            agent_role=call.agent_role,
            prompt=call.prompt,
            session_id=call.session_id,
            correlation_id=correlation_id,
            context=call.context,
            env=call.env,
        )

        # Convert to A2A result format
        a2a_result = A2AAgentResult(
            response=result.response,
            session_id=result.session_id,
            correlation_id=correlation_id,
            target_spiffe_id=result.metadata.get("spiffe_id") if result.metadata else None,
            metadata=result.metadata,
            error=result.error,
        )

        if result.error:
            logger.error(
                "A2A call completed with error",
                extra={
                    "correlation_id": correlation_id,
                    "agent_role": call.agent_role,
                    "error": result.error,
                },
            )
        else:
            logger.info(
                "A2A call completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "agent_role": call.agent_role,
                    "response_length": len(result.response),
                    "session_id": result.session_id,
                },
            )

        return a2a_result

    except Exception as e:
        logger.error(
            f"A2A call failed with exception: {e}",
            exc_info=True,
            extra={
                "agent_role": call.agent_role,
                "correlation_id": call.correlation_id or "unknown",
            },
        )
        return A2AAgentResult(
            response="",
            error=f"A2A call failed: {e!s}",
            correlation_id=call.correlation_id or str(uuid.uuid4()),
            metadata={
                "phase": "AE2",
                "error": True,
                "exception_type": type(e).__name__,
                "agent_role": call.agent_role,
            },
        )


@app.get("/health")
async def health() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "a2a-gateway",
        "version": "0.6.0",
        "agent_engine_url": AGENT_ENGINE_URL,
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint - service info.

    Returns:
        dict: Service metadata
    """
    return {
        "name": "Bob's Brain A2A Gateway",
        "version": "0.9.0",
        "description": "A2A Protocol gateway to Vertex AI Agent Engine",
        "endpoints": {
            "agent_card": "/.well-known/agent.json",
            "query": "/query",
            "a2a_run": "/a2a/run",  # Phase AE2: A2A protocol endpoint (implemented)
            "health": "/health",
        },
        "phase": "AE2-complete",
        "features": {
            "a2a_protocol": "enabled",  # AE2: Real Agent Engine integration
            "agent_engine_proxy": "enabled",
            "centralized_config": "enabled",  # Uses agents.config.agent_engine
            "multi_agent_routing": "enabled",  # Routes to bob, foreman, iam-*
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting A2A Gateway on port {PORT}",
        extra={
            "project_id": PROJECT_ID,
            "location": LOCATION,
            "agent_engine_id": AGENT_ENGINE_ID,
        },
    )

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
