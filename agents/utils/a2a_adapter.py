"""
A2A Adapter for Agent Engine Calls (Phase AE1)

This module provides utilities for calling Vertex AI Agent Engine
via the A2A (Agent-to-Agent) protocol.

NO REAL HTTP YET - Functions are stubbed for Phase AE1.
Real HTTP implementation will be added in Phase AE2 when gateways are wired.

Key Functions:
- build_agent_engine_request: Construct request payload for Agent Engine
- call_agent_engine: Stub for calling Agent Engine (returns mock response)
- resolve_agent_engine_endpoint: Get full Agent Engine REST URL

Related Docs:
- 000-docs/6767-101-AT-ARCH-agent-engine-topology-and-envs.md
"""

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Import Agent Engine configuration
from agents.config.agent_engine import (
    Environment,
    get_agent_engine_config,
    get_spiffe_id,
)


@dataclass
class AgentEngineRequest:
    """
    Request payload for Vertex AI Agent Engine REST API.

    Matches the shape expected by Agent Engine's query endpoint:
    POST https://{LOCATION}-aiplatform.googleapis.com/v1/{REASONING_ENGINE_NAME}:query
    """

    query: str
    """User prompt or query to send to the agent"""

    session_id: Optional[str] = None
    """Optional session ID for conversation continuity"""

    context: Optional[Dict[str, Any]] = None
    """Optional additional context (tool outputs, memory hints, etc.)"""

    correlation_id: Optional[str] = None
    """Optional correlation ID for tracing (pipeline_run_id)"""

    caller_spiffe_id: Optional[str] = None
    """SPIFFE ID of the calling agent (for A2A protocol)"""


@dataclass
class AgentEngineResponse:
    """
    Response from Vertex AI Agent Engine.

    Matches the shape returned by Agent Engine's query endpoint.
    """

    response: str
    """Agent's response text"""

    session_id: Optional[str] = None
    """Session ID if session persistence is enabled"""

    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata (tokens used, latency, etc.)"""

    error: Optional[str] = None
    """Error message if call failed"""


def get_current_environment() -> Environment:
    """
    Detect current environment from DEPLOYMENT_ENV variable.

    Returns:
        Environment: One of "dev", "staging", "prod"

    Defaults to "dev" if DEPLOYMENT_ENV not set.
    """
    env_str = os.getenv("DEPLOYMENT_ENV", "dev").lower()

    if env_str in ("dev", "development"):
        return "dev"
    elif env_str in ("staging", "stage"):
        return "staging"
    elif env_str in ("prod", "production"):
        return "prod"
    else:
        # Default to dev for safety
        return "dev"


def resolve_agent_engine_endpoint(
    agent_role: str, env: Optional[Environment] = None
) -> Optional[str]:
    """
    Resolve the full Agent Engine REST endpoint URL for an agent.

    Args:
        agent_role: Agent role name (bob, foreman, iam-adk, etc.)
                   For prod Bob, use "bob_current" or "bob_next_gen"
        env: Environment (defaults to current environment if not specified)

    Returns:
        Full Agent Engine REST URL, or None if agent not deployed to Engine

    Example:
        >>> url = resolve_agent_engine_endpoint("bob_current", "prod")
        >>> print(url)
        https://us-central1-aiplatform.googleapis.com/v1/projects/205354194989/locations/us-central1/reasoningEngines/5828234061910376448:query
    """
    if env is None:
        env = get_current_environment()

    config = get_agent_engine_config(env, agent_role)

    if config is None:
        # Agent not deployed to Engine (e.g., iam-adk in dev uses local stub)
        return None

    # Extract project, location, and engine ID from reasoning_engine_id
    # Format: projects/PROJECT_ID/locations/REGION/reasoningEngines/ID
    parts = config.reasoning_engine_id.split("/")

    if len(parts) != 6:
        raise ValueError(
            f"Invalid reasoning_engine_id format: {config.reasoning_engine_id}"
        )

    project_id = parts[1]
    location = parts[3]
    engine_id = parts[5]

    # Build Agent Engine REST endpoint
    return (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project_id}/locations/{location}/"
        f"reasoningEngines/{engine_id}:query"
    )


def build_agent_engine_request(
    agent_role: str,
    user_prompt: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    caller_agent_role: Optional[str] = None,
    env: Optional[Environment] = None,
) -> AgentEngineRequest:
    """
    Build a request payload for Vertex AI Agent Engine.

    Args:
        agent_role: Target agent role (bob, foreman, iam-adk, etc.)
        user_prompt: Query to send to the agent
        session_id: Optional session ID for conversation continuity
        context: Optional additional context (tool outputs, etc.)
        correlation_id: Optional correlation ID (pipeline_run_id)
        caller_agent_role: Optional calling agent's role for A2A protocol
        env: Environment (defaults to current environment)

    Returns:
        AgentEngineRequest: Structured request ready to send to Agent Engine

    Example:
        >>> request = build_agent_engine_request(
        ...     agent_role="iam-adk",
        ...     user_prompt="Audit this repo for ADK compliance",
        ...     correlation_id="12345-67890",
        ...     caller_agent_role="foreman"
        ... )
    """
    if env is None:
        env = get_current_environment()

    # Resolve caller's SPIFFE ID if caller_agent_role provided
    caller_spiffe_id = None
    if caller_agent_role:
        caller_spiffe_id = get_spiffe_id(env, caller_agent_role)

    # If no correlation_id provided, generate one
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    return AgentEngineRequest(
        query=user_prompt,
        session_id=session_id,
        context=context,
        correlation_id=correlation_id,
        caller_spiffe_id=caller_spiffe_id,
    )


def call_agent_engine(
    agent_role: str, request: AgentEngineRequest, env: Optional[Environment] = None
) -> AgentEngineResponse:
    """
    Call Vertex AI Agent Engine with a request.

    STUBBED FOR PHASE AE1 - Returns mock response.
    Real HTTP implementation will be added in Phase AE2.

    Args:
        agent_role: Target agent role (bob, foreman, iam-adk, etc.)
        request: AgentEngineRequest payload
        env: Environment (defaults to current environment)

    Returns:
        AgentEngineResponse: Agent's response (mocked in Phase AE1)

    Raises:
        ValueError: If agent not deployed to Engine in this environment

    Example:
        >>> request = build_agent_engine_request("iam-adk", "Audit repo")
        >>> response = call_agent_engine("iam-adk", request, env="staging")
        >>> print(response.response)
        [STUB] Response from iam-adk...
    """
    if env is None:
        env = get_current_environment()

    # Check if agent is deployed to Engine
    endpoint_url = resolve_agent_engine_endpoint(agent_role, env)

    if endpoint_url is None:
        raise ValueError(
            f"Agent {agent_role} is not deployed to Agent Engine in {env} environment. "
            f"Use local stub implementation instead."
        )

    # Get target agent's SPIFFE ID
    target_spiffe_id = get_spiffe_id(env, agent_role)

    # STUBBED: Return mock response (Phase AE1)
    # Real HTTP call will be implemented in Phase AE2
    return AgentEngineResponse(
        response=(
            f"[STUB - Phase AE1] Response from {agent_role} agent\n"
            f"Environment: {env}\n"
            f"Agent SPIFFE ID: {target_spiffe_id}\n"
            f"Endpoint: {endpoint_url}\n"
            f"Query: {request.query}\n"
            f"Correlation ID: {request.correlation_id}\n"
            f"Caller: {request.caller_spiffe_id or 'unknown'}\n\n"
            f"This is a stubbed response. Real Agent Engine HTTP calls "
            f"will be implemented in Phase AE2 when gateways are wired."
        ),
        session_id=request.session_id or str(uuid.uuid4()),
        metadata={
            "stub": True,
            "phase": "AE1",
            "environment": env,
            "agent_role": agent_role,
            "endpoint_url": endpoint_url,
            "target_spiffe_id": target_spiffe_id,
        },
    )


def call_agent_engine_direct(
    agent_role: str,
    user_prompt: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    caller_agent_role: Optional[str] = None,
    env: Optional[Environment] = None,
) -> AgentEngineResponse:
    """
    Convenience function to build request and call Agent Engine in one step.

    STUBBED FOR PHASE AE1 - Returns mock response.

    Args:
        agent_role: Target agent role
        user_prompt: Query to send
        session_id: Optional session ID
        context: Optional additional context
        correlation_id: Optional correlation ID
        caller_agent_role: Optional calling agent's role
        env: Environment (defaults to current environment)

    Returns:
        AgentEngineResponse: Agent's response (mocked in Phase AE1)

    Example:
        >>> response = call_agent_engine_direct(
        ...     agent_role="iam-adk",
        ...     user_prompt="Audit this repo",
        ...     correlation_id="12345",
        ...     caller_agent_role="foreman",
        ...     env="staging"
        ... )
    """
    request = build_agent_engine_request(
        agent_role=agent_role,
        user_prompt=user_prompt,
        session_id=session_id,
        context=context,
        correlation_id=correlation_id,
        caller_agent_role=caller_agent_role,
        env=env,
    )

    return call_agent_engine(agent_role, request, env=env)


def is_agent_available(agent_role: str, env: Optional[Environment] = None) -> bool:
    """
    Check if an agent is available (deployed to Agent Engine or has local stub).

    Args:
        agent_role: Agent role to check
        env: Environment (defaults to current environment)

    Returns:
        True if agent can be called, False otherwise

    Example:
        >>> is_agent_available("iam-adk", "dev")
        False  # Uses local stub, not Agent Engine
        >>> is_agent_available("iam-adk", "staging")
        True   # Deployed to Agent Engine
    """
    if env is None:
        env = get_current_environment()

    # Check if agent has Agent Engine deployment
    endpoint = resolve_agent_engine_endpoint(agent_role, env)
    return endpoint is not None


# ==============================================================================
# DEBUGGING & TESTING UTILITIES
# ==============================================================================


def print_agent_engine_info(agent_role: str, env: Optional[Environment] = None) -> None:
    """
    Print detailed Agent Engine information for an agent.

    Useful for debugging and verifying configuration.

    Args:
        agent_role: Agent role to inspect
        env: Environment (defaults to current environment)
    """
    if env is None:
        env = get_current_environment()

    config = get_agent_engine_config(env, agent_role)

    print(f"\n{'=' * 60}")
    print(f"Agent Engine Info: {agent_role} ({env})")
    print(f"{'=' * 60}")

    if config is None:
        print(f"❌ Agent {agent_role} NOT deployed to Agent Engine in {env}")
        print("   Uses local stub implementation")
        return

    print(f"✅ Agent {agent_role} deployed to Agent Engine")
    print("\nReasoning Engine ID:")
    print(f"  {config.reasoning_engine_id}")
    print("\nRegion:")
    print(f"  {config.region}")
    print("\nSPIFFE ID:")
    print(f"  {config.spiffe_id}")
    print("\nREST Endpoint:")
    endpoint = resolve_agent_engine_endpoint(agent_role, env)
    print(f"  {endpoint}")

    if config.notes:
        print("\nNotes:")
        print(f"  {config.notes}")

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    # Test the adapter with current canonical Bob
    print("Testing A2A Adapter (Phase AE1)")

    # Test 1: Resolve current canonical Bob endpoint
    print("\n1. Testing current canonical Bob:")
    print_agent_engine_info("bob_current", "prod")

    # Test 2: Build and call iam-adk in staging
    print("\n2. Testing iam-adk in staging:")
    if is_agent_available("iam-adk", "staging"):
        response = call_agent_engine_direct(
            agent_role="iam-adk",
            user_prompt="Audit this repo for ADK compliance",
            correlation_id="test-12345",
            caller_agent_role="foreman",
            env="staging",
        )
        print("\nResponse preview:")
        print(response.response[:200] + "...")
    else:
        print("iam-adk not available in staging")

    # Test 3: Check dev environment (should use local stubs)
    print("\n3. Testing iam-adk in dev (should fail - local stub):")
    print_agent_engine_info("iam-adk", "dev")

    print("\n✅ All adapter tests completed!")
