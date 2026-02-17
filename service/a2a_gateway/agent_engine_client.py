"""
Agent Engine Client for A2A Gateway (AE2)

This module provides a helper for calling Vertex AI Agent Engine from the a2a gateway.
It uses the centralized agent_engine.py config module and handles authentication,
request formatting, and error handling.

Key Features:
- Uses Application Default Credentials (ADC) for authentication
- Reads Agent Engine IDs from environment via agent_engine.py
- Formats requests for Agent Engine REST API
- Handles timeouts, retries, and error responses
- Correlates requests with trace/correlation IDs

Usage:
    from agent_engine_client import call_agent_engine

    result = await call_agent_engine(
        agent_role="bob",
        prompt="Hello, Bob!",
        session_id="abc123",
        correlation_id="xyz789",
    )
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.config.agent_engine import (
    build_agent_config,
    get_current_environment,
    get_reasoning_engine_url,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentEngineResponse:
    """Response from Agent Engine."""
    response: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def get_gcp_token() -> str:
    """
    Get GCP OAuth token using Application Default Credentials.

    Returns:
        str: Bearer token for API calls

    Raises:
        RuntimeError: If token cannot be obtained
    """
    try:
        from google.auth import default
        from google.auth.transport.requests import Request

        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

        # Refresh token if needed
        if not credentials.valid:
            credentials.refresh(Request())

        return credentials.token
    except Exception as e:
        logger.error(f"Failed to get GCP token: {e}")
        raise RuntimeError(f"Authentication failed: {e}")


async def call_agent_engine(
    agent_role: str,
    prompt: str,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    env: Optional[str] = None,
) -> AgentEngineResponse:
    """
    Call Vertex AI Agent Engine for a specific agent role.

    Args:
        agent_role: Agent role (e.g., "bob", "foreman", "iam-adk")
        prompt: User query/message to send to agent
        session_id: Optional session ID for conversation continuity
        correlation_id: Optional correlation ID for request tracking
        context: Optional additional context to pass to agent
        timeout: Request timeout in seconds (default: 30.0)
        env: Environment override (defaults to current environment)

    Returns:
        AgentEngineResponse: Response from Agent Engine

    Raises:
        ValueError: If agent not configured or config invalid
        RuntimeError: If Agent Engine call fails

    Example:
        >>> result = await call_agent_engine(
        ...     agent_role="bob",
        ...     prompt="What is ADK?",
        ...     session_id="session-123",
        ... )
        >>> print(result.response)
        "ADK stands for Agent Development Kit..."
    """
    # Determine environment
    if env is None:
        env = get_current_environment()

    # Get Agent Engine config for this agent
    agent_config = build_agent_config(agent_role, env)
    if not agent_config:
        error_msg = f"Agent '{agent_role}' not configured for {env} environment"
        logger.error(
            error_msg,
            extra={
                "agent_role": agent_role,
                "env": env,
                "correlation_id": correlation_id,
            },
        )
        return AgentEngineResponse(
            response="",
            error=error_msg,
            metadata={
                "agent_role": agent_role,
                "env": env,
                "reason": "Agent not configured - set environment variable",
            },
        )

    # Get OAuth token
    try:
        token = get_gcp_token()
    except RuntimeError as e:
        error_msg = f"Authentication failed: {e}"
        logger.error(error_msg, extra={"correlation_id": correlation_id})
        return AgentEngineResponse(
            response="",
            error=error_msg,
            metadata={"reason": "Authentication failure"},
        )

    # Build Agent Engine URL
    engine_url = get_reasoning_engine_url(agent_config.reasoning_engine_id)

    # Build request payload
    payload = {"query": prompt}
    if session_id:
        payload["session_id"] = session_id
    if context:
        payload["context"] = context

    # Add correlation headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    if agent_config.spiffe_id:
        headers["X-SPIFFE-ID"] = agent_config.spiffe_id

    # Log request
    logger.info(
        f"Calling Agent Engine for {agent_role}",
        extra={
            "agent_role": agent_role,
            "env": env,
            "engine_id": agent_config.reasoning_engine_id,
            "session_id": session_id,
            "correlation_id": correlation_id,
            "spiffe_id": agent_config.spiffe_id,
        },
    )

    # Make request to Agent Engine
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                engine_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        # Extract response
        response_text = result.get("response", result.get("output", ""))
        response_session_id = result.get("session_id")
        response_metadata = result.get("metadata", {})

        # Add our tracking metadata
        response_metadata.update({
            "agent_role": agent_role,
            "env": env,
            "engine_id": agent_config.reasoning_engine_id,
            "spiffe_id": agent_config.spiffe_id,
            "correlation_id": correlation_id,
        })

        logger.info(
            f"✅ Agent Engine response received from {agent_role}",
            extra={
                "agent_role": agent_role,
                "correlation_id": correlation_id,
                "response_length": len(response_text),
                "session_id": response_session_id,
            },
        )

        return AgentEngineResponse(
            response=response_text,
            session_id=response_session_id,
            metadata=response_metadata,
            error=None,
        )

    except httpx.HTTPStatusError as e:
        error_msg = f"Agent Engine HTTP error: {e.response.status_code} - {e.response.text}"
        logger.error(
            error_msg,
            extra={
                "agent_role": agent_role,
                "correlation_id": correlation_id,
                "status_code": e.response.status_code,
                "response_text": e.response.text[:200],  # Truncate for logs
            },
        )
        return AgentEngineResponse(
            response="",
            error=error_msg,
            metadata={
                "agent_role": agent_role,
                "status_code": e.response.status_code,
                "correlation_id": correlation_id,
            },
        )

    except httpx.TimeoutException:
        error_msg = f"Agent Engine timeout after {timeout}s"
        logger.error(
            error_msg,
            extra={
                "agent_role": agent_role,
                "correlation_id": correlation_id,
                "timeout": timeout,
            },
        )
        return AgentEngineResponse(
            response="",
            error=error_msg,
            metadata={
                "agent_role": agent_role,
                "timeout": timeout,
                "correlation_id": correlation_id,
            },
        )

    except Exception as e:
        error_msg = f"Agent Engine call failed: {e!s}"
        logger.error(
            error_msg,
            extra={
                "agent_role": agent_role,
                "correlation_id": correlation_id,
                "exception": str(e),
                "exception_type": type(e).__name__,
            },
        )
        return AgentEngineResponse(
            response="",
            error=error_msg,
            metadata={
                "agent_role": agent_role,
                "exception_type": type(e).__name__,
                "correlation_id": correlation_id,
            },
        )


# For testing
if __name__ == "__main__":
    import asyncio

    async def test_call():
        """Test Agent Engine call (dev only)."""
        # This will fail without proper GCP credentials and Agent Engine setup
        # But useful for verifying imports and basic structure
        print("Testing Agent Engine client...")
        print()

        result = await call_agent_engine(
            agent_role="bob",
            prompt="Test query",
            session_id="test-123",
            correlation_id="test-corr-456",
        )

        print(f"Response: {result.response[:100] if result.response else 'N/A'}")
        print(f"Error: {result.error}")
        print(f"Metadata: {result.metadata}")

    asyncio.run(test_call())
