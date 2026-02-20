"""
Agent Engine Configuration Module (Phase AE1)

This module provides centralized configuration for Vertex AI Agent Engine
deployments across all environments (dev, staging, prod).

Key Principles:
- Single source of truth for Agent Engine IDs and configuration
- Environment-aware: reads from env vars with smart defaults
- Never hard-code full resource paths in other modules
- Helper functions to construct resource names from components

Environment Variables:
- GCP_PROJECT_ID: GCP project ID
- VERTEX_LOCATION: GCP region (default: us-central1)
- AGENT_ENGINE_BOB_ID_DEV: Bob's Engine ID in dev
- AGENT_ENGINE_FOREMAN_ID_DEV: Foreman's Engine ID in dev
- AGENT_ENGINE_BOB_ID_STAGING: Bob's Engine ID in staging
- AGENT_ENGINE_BOB_ID_PROD: Bob's Engine ID in prod
- (Additional agents: AGENT_ENGINE_{AGENT}_ID_{ENV})

Related Docs:
- 000-docs/6767-101-AT-ARCH-agent-engine-topology-and-envs.md
"""

import os
from dataclasses import dataclass
from typing import Dict, Literal, Optional

# Import environment detection from features module
from agents.config.features import get_current_environment

# Type alias for environment names
Environment = Literal["dev", "staging", "prod"]


@dataclass
class AgentEngineConfig:
    """Configuration for a single agent in Vertex AI Agent Engine."""

    reasoning_engine_id: str
    """Reasoning engine ID (just the ID, not full path)"""

    project_id: str
    """GCP project ID where the engine is deployed"""

    location: str
    """GCP region where the engine is deployed (e.g., us-central1)"""

    spiffe_id: str
    """SPIFFE ID for agent identity: spiffe://trust-domain/agent/name/env/region/version"""

    notes: Optional[str] = None
    """Optional notes about this agent deployment"""

    def get_full_resource_name(self) -> str:
        """
        Get full reasoning engine resource name.

        Returns:
            Full resource path: projects/{project}/locations/{location}/reasoningEngines/{id}
        """
        return f"projects/{self.project_id}/locations/{self.location}/reasoningEngines/{self.reasoning_engine_id}"


# ==============================================================================
# ENVIRONMENT VARIABLE HELPERS
# ==============================================================================


def _get_env_var(
    key: str, default: Optional[str] = None, required: bool = False
) -> Optional[str]:
    """
    Get environment variable with optional default and required check.

    Args:
        key: Environment variable name
        default: Default value if not set
        required: If True, raise ValueError if not set and no default

    Returns:
        Value from environment or default
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable not set: {key}")
    return value


def get_project_id() -> str:
    """
    Get GCP project ID from environment.

    Returns:
        Project ID from GCP_PROJECT_ID or PROJECT_ID

    Raises:
        ValueError: If project ID not set
    """
    return _get_env_var("GCP_PROJECT_ID") or _get_env_var("PROJECT_ID", required=True)


def get_location() -> str:
    """
    Get GCP location/region from environment.

    Returns:
        Location from VERTEX_LOCATION or LOCATION, defaults to us-central1
    """
    return _get_env_var("VERTEX_LOCATION") or _get_env_var(
        "LOCATION", default="us-central1"
    )


def get_agent_engine_id(
    agent_role: str, env: Optional[Environment] = None
) -> Optional[str]:
    """
    Get Agent Engine ID for a specific agent role and environment.

    Checks environment variables in this order:
    1. AGENT_ENGINE_{AGENT}_ID_{ENV} (e.g., AGENT_ENGINE_BOB_ID_DEV)
    2. Falls back to hardcoded defaults for known agents

    Args:
        agent_role: Agent role name (bob, foreman, iam-adk, etc.)
        env: Environment (if None, uses current environment)

    Returns:
        Engine ID or None if not configured

    Examples:
        >>> os.environ["AGENT_ENGINE_BOB_ID_DEV"] = "12345"
        >>> get_agent_engine_id("bob", "dev")
        "12345"

        >>> get_agent_engine_id("bob", "prod")  # Falls back to hardcoded
        "5828234061910376448"
    """
    if env is None:
        env = get_current_environment()

    # Normalize agent role for env var (replace dashes with underscores, uppercase)
    agent_var_name = agent_role.replace("-", "_").upper()
    env_var_name = f"AGENT_ENGINE_{agent_var_name}_ID_{env.upper()}"

    engine_id = _get_env_var(env_var_name)
    if engine_id:
        return engine_id

    # Fallback to hardcoded defaults for known agents
    # Prod canonical Bob is always this ID:
    if agent_role == "bob_current" and env == "prod":
        return "5828234061910376448"

    # No configuration found
    return None


# ==============================================================================
# RESOURCE PATH HELPERS
# ==============================================================================


def make_reasoning_engine_path(
    engine_id: str, project_id: Optional[str] = None, location: Optional[str] = None
) -> str:
    """
    Construct full reasoning engine resource path from components.

    This is the single source of truth for assembling Agent Engine resource paths.
    Never hard-code these paths in other modules.

    Args:
        engine_id: Reasoning engine ID
        project_id: GCP project ID (if None, reads from environment)
        location: GCP location (if None, reads from environment)

    Returns:
        Full resource path: projects/{project}/locations/{location}/reasoningEngines/{id}

    Examples:
        >>> make_reasoning_engine_path("12345")
        "projects/my-project/locations/us-central1/reasoningEngines/12345"

        >>> make_reasoning_engine_path("12345", "custom-project", "us-west1")
        "projects/custom-project/locations/us-west1/reasoningEngines/12345"
    """
    proj = project_id or get_project_id()
    loc = location or get_location()
    return f"projects/{proj}/locations/{loc}/reasoningEngines/{engine_id}"


def get_reasoning_engine_url(
    engine_id: str, project_id: Optional[str] = None, location: Optional[str] = None
) -> str:
    """
    Construct Agent Engine REST API URL for query endpoint.

    Args:
        engine_id: Reasoning engine ID
        project_id: GCP project ID (if None, reads from environment)
        location: GCP location (if None, reads from environment)

    Returns:
        Full HTTPS URL to Agent Engine query endpoint

    Examples:
        >>> get_reasoning_engine_url("12345")
        "https://us-central1-aiplatform.googleapis.com/v1/projects/my-project/locations/us-central1/reasoningEngines/12345:query"
    """
    loc = location or get_location()
    resource_path = make_reasoning_engine_path(engine_id, project_id, loc)
    return f"https://{loc}-aiplatform.googleapis.com/v1/{resource_path}:query"


# ==============================================================================
# AGENT CONFIG BUILDERS
# ==============================================================================


def build_agent_config(
    agent_role: str, env: Optional[Environment] = None, spiffe_version: str = "0.9.0"
) -> Optional[AgentEngineConfig]:
    """
    Build AgentEngineConfig for an agent by reading environment variables.

    This is the primary way to get agent configuration at runtime.

    Args:
        agent_role: Agent role name (bob, foreman, iam-adk, etc.)
        env: Environment (if None, uses current environment)
        spiffe_version: Version string for SPIFFE ID (default: 0.9.0)

    Returns:
        AgentEngineConfig if engine ID is configured, None otherwise

    Examples:
        >>> os.environ["AGENT_ENGINE_BOB_ID_DEV"] = "12345"
        >>> config = build_agent_config("bob", "dev")
        >>> print(config.get_full_resource_name())
        "projects/my-project/locations/us-central1/reasoningEngines/12345"
    """
    if env is None:
        env = get_current_environment()

    engine_id = get_agent_engine_id(agent_role, env)
    if not engine_id:
        return None

    project_id = get_project_id()
    location = get_location()

    # Construct SPIFFE ID
    agent_name = f"bobs-brain-{agent_role}" if agent_role != "bob" else "bobs-brain"
    spiffe_id = f"spiffe://intent.solutions/agent/{agent_name}/{env}/{location}/{spiffe_version}"

    return AgentEngineConfig(
        reasoning_engine_id=engine_id,
        project_id=project_id,
        location=location,
        spiffe_id=spiffe_id,
        notes=f"Runtime config for {agent_role} in {env}",
    )


# ==============================================================================
# STATIC FALLBACK CONFIGS (For Reference / Documentation)
# ==============================================================================

# These are kept for documentation purposes and as fallbacks
# when environment variables aren't set. Production deployments
# should always use environment variables.

CANONICAL_BOB_PROD_ID = "5828234061910376448"
"""The current canonical Bob production Engine ID (pre-ADK architecture)"""


def get_canonical_bob_config() -> AgentEngineConfig:
    """
    Get configuration for the current canonical production Bob.

    This is the pre-ADK Bob that is currently serving production traffic.

    Returns:
        AgentEngineConfig for canonical production Bob
    """
    return AgentEngineConfig(
        reasoning_engine_id=CANONICAL_BOB_PROD_ID,
        project_id="205354194989",  # bobs-brain-prod project
        location="us-central1",
        spiffe_id="spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.8.0",
        notes="⭐ CURRENT CANONICAL BOB (pre-ADK architecture) - Active production",
    )


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================


def is_agent_deployed_to_engine(
    agent_role: str, env: Optional[Environment] = None
) -> bool:
    """
    Check if an agent is deployed to Agent Engine (vs local stub).

    Args:
        agent_role: Agent role name
        env: Environment (if None, uses current environment)

    Returns:
        True if agent has Agent Engine deployment, False otherwise

    Examples:
        >>> is_agent_deployed_to_engine("bob", "prod")
        True
        >>> is_agent_deployed_to_engine("iam-adk", "dev")
        False  # Might use local stub in dev
    """
    return build_agent_config(agent_role, env) is not None


def list_configured_agents(
    env: Optional[Environment] = None,
) -> Dict[str, AgentEngineConfig]:
    """
    List all agents configured in a specific environment.

    Scans environment variables for AGENT_ENGINE_*_{ENV} patterns.

    Args:
        env: Environment (if None, uses current environment)

    Returns:
        Dictionary mapping agent role to config

    Examples:
        >>> agents = list_configured_agents("dev")
        >>> print([role for role in agents.keys()])
        ['bob', 'foreman']
    """
    if env is None:
        env = get_current_environment()

    configured = {}

    # Common agent roles to check
    agent_roles = [
        "bob",
        "bob_current",
        "bob_next_gen",
        "foreman",
        "iam-adk",
        "iam-issue",
        "iam-fix",
        "iam-qa",
    ]

    for role in agent_roles:
        config = build_agent_config(role, env)
        if config:
            configured[role] = config

    return configured


# ==============================================================================
# CONFIGURATION VALIDATION
# ==============================================================================


def validate_config(env: Optional[Environment] = None) -> None:
    """
    Validate that required configuration is present for an environment.

    Checks:
    - Project ID is set
    - Location is set
    - At least one agent is configured (typically Bob)

    Args:
        env: Environment to validate (if None, uses current)

    Raises:
        ValueError: If configuration is invalid or incomplete
    """
    if env is None:
        env = get_current_environment()

    # Check basic config
    try:
        project_id = get_project_id()
        location = get_location()
    except ValueError as e:
        raise ValueError(f"Missing required configuration: {e}")

    # Check at least one agent is configured
    configured_agents = list_configured_agents(env)
    if not configured_agents:
        raise ValueError(
            f"No agents configured for {env} environment. "
            f"Set at least AGENT_ENGINE_BOB_ID_{env.upper()} environment variable."
        )

    print(f"✅ Agent Engine configuration valid for {env}")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    print(f"   Configured agents: {', '.join(configured_agents.keys())}")


# ==============================================================================
# MAIN (FOR TESTING)
# ==============================================================================

if __name__ == "__main__":
    print("Agent Engine Configuration")
    print("=" * 70)
    print()

    # Show current environment
    env = get_current_environment()
    print(f"Current Environment: {env}")
    print()

    # Show project and location
    try:
        project = get_project_id()
        location = get_location()
        print(f"Project ID: {project}")
        print(f"Location: {location}")
        print()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print()
        print(
            "Set GCP_PROJECT_ID and optionally VERTEX_LOCATION environment variables."
        )
        exit(1)

    # Show configured agents
    print("Configured Agents:")
    print("-" * 70)
    agents = list_configured_agents(env)

    if not agents:
        print(f"  No agents configured for {env} environment")
        print()
        print("  Set environment variables like:")
        print(f"    export AGENT_ENGINE_BOB_ID_{env.upper()}=your-engine-id")
    else:
        for role, config in agents.items():
            print(f"  {role}:")
            print(f"    Engine ID: {config.reasoning_engine_id}")
            print(f"    Resource: {config.get_full_resource_name()}")
            print(f"    SPIFFE ID: {config.spiffe_id}")
            print()

    # Validate
    try:
        validate_config(env)
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        exit(1)
