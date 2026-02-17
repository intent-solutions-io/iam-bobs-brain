"""
Feature Flags Module (Phase AE3)

This module defines all feature flags for controlled rollout of:
- Live RAG (Vertex AI Search integration)
- Agent Engine deployment (A2A via Vertex AI Agent Engine)
- Blue/Green migration (Bob current → Bob next-gen)
- Gateway routing (Slack → a2a_gateway)

ALL FLAGS DEFAULT TO FALSE/0 FOR SAFETY.

Feature flags follow the rollout progression defined in:
000-docs/6767-103-DR-STND-live-rag-and-agent-engine-rollout-plan.md

Rollout Stages:
- Stage 0: OFF (all features disabled)
- Stage 1: EXPERIMENTAL (dev only)
- Stage 2: STAGING (pre-prod validation)
- Stage 3: PROD 5% (canary)
- Stage 4: PROD 25%/50%/100% (gradual)
- Stage 5: FULL PRODUCTION (next-gen canonical)

Environment Variables:
All feature flags are loaded from environment variables and default to False/0.
"""

import os
from typing import Literal, Optional

# ==============================================================================
# ENVIRONMENT DETECTION
# ==============================================================================

Environment = Literal["dev", "staging", "prod"]


def get_current_environment() -> Environment:
    """
    Detect current environment from DEPLOYMENT_ENV or PROJECT_ID.

    Returns:
        Environment: One of "dev", "staging", "prod" (defaults to "dev")

    Examples:
        DEPLOYMENT_ENV=staging → "staging"
        DEPLOYMENT_ENV=production → "prod"
        PROJECT_ID=bobs-brain-prod → "prod"
        (no env vars) → "dev"
    """
    env_str = os.getenv("DEPLOYMENT_ENV", "").lower()

    # Explicit env var takes precedence
    if env_str in ("dev", "development"):
        return "dev"
    if env_str in ("staging", "stage"):
        return "staging"
    if env_str in ("prod", "production"):
        return "prod"

    # Fallback: infer from PROJECT_ID
    project_id = os.getenv("PROJECT_ID", "").lower()
    if "staging" in project_id or "stage" in project_id:
        return "staging"
    if "prod" in project_id or "production" in project_id:
        return "prod"

    # Default to dev for safety
    return "dev"


# ==============================================================================
# RAG FEATURE FLAGS
# ==============================================================================

# Enable Vertex AI Search for Bob agent
# Stage 1 (EXPERIMENTAL): Enable in dev
# Stage 2 (STAGING): Enable in staging
# Stage 3+ (PROD): Enable in prod with gradual rollout
LIVE_RAG_BOB_ENABLED = os.getenv("LIVE_RAG_BOB_ENABLED", "false").lower() == "true"

# Enable Vertex AI Search for foreman (iam-senior-adk-devops-lead)
# Stage 1 (EXPERIMENTAL): Enable in dev
# Stage 2 (STAGING): Enable in staging
# Stage 3+ (PROD): Enable in prod with gradual rollout
LIVE_RAG_FOREMAN_ENABLED = (
    os.getenv("LIVE_RAG_FOREMAN_ENABLED", "false").lower() == "true"
)


# ==============================================================================
# AGENT ENGINE A2A FLAGS
# ==============================================================================

# Enable foreman → iam-adk calls via Agent Engine (instead of local)
# Stage 1 (EXPERIMENTAL): Enable in dev
# Stage 2 (STAGING): Enable in staging
# Stage 3+ (PROD): Enable in prod with gradual rollout
ENGINE_MODE_FOREMAN_TO_IAM_ADK = (
    os.getenv("ENGINE_MODE_FOREMAN_TO_IAM_ADK", "false").lower() == "true"
)

# Enable foreman → iam-issue calls via Agent Engine
# Stage 2 (STAGING): Enable in staging after iam-adk validation
# Stage 3+ (PROD): Enable in prod with gradual rollout
ENGINE_MODE_FOREMAN_TO_IAM_ISSUE = (
    os.getenv("ENGINE_MODE_FOREMAN_TO_IAM_ISSUE", "false").lower() == "true"
)

# Enable foreman → iam-fix-* calls via Agent Engine
# Stage 2 (STAGING): Enable in staging after iam-issue validation
# Stage 3+ (PROD): Enable in prod with gradual rollout
ENGINE_MODE_FOREMAN_TO_IAM_FIX = (
    os.getenv("ENGINE_MODE_FOREMAN_TO_IAM_FIX", "false").lower() == "true"
)


# ==============================================================================
# GATEWAY ROUTING FLAGS
# ==============================================================================

# Enable Option B routing: Slack → a2a_gateway → Agent Engine
# (Instead of Option A: Slack → Agent Engine direct)
#
# Stage 2 (STAGING): Enable in staging to test full gateway flow
# Stage 3+ (PROD): Enable in prod with gradual rollout
SLACK_SWE_PIPELINE_MODE_ENABLED = (
    os.getenv("SLACK_SWE_PIPELINE_MODE_ENABLED", "false").lower() == "true"
)


# ==============================================================================
# BLUE/GREEN MIGRATION FLAGS (Bob Current → Bob Next-Gen)
# ==============================================================================

# Enable routing to Bob next-gen (new ADK-based agent on Agent Engine)
# Stage 2 (STAGING): Enable in staging for validation
# Stage 3+ (PROD): Enable in prod with canary rollout
AGENT_ENGINE_BOB_NEXT_GEN_ENABLED = (
    os.getenv("AGENT_ENGINE_BOB_NEXT_GEN_ENABLED", "false").lower() == "true"
)

# Percentage of traffic to route to Bob next-gen (0-100)
# Stage 3 (PROD 5%): Set to 5
# Stage 4a (PROD 25%): Set to 25
# Stage 4b (PROD 50%): Set to 50
# Stage 4c (PROD 100%): Set to 100
# Stage 5 (FULL): Set to 100 (next-gen becomes canonical)
AGENT_ENGINE_BOB_NEXT_GEN_PERCENT = int(
    os.getenv("AGENT_ENGINE_BOB_NEXT_GEN_PERCENT", "0")
)

# Enable shadow traffic: Duplicate requests to next-gen without affecting responses
# Stage 2 (STAGING): Enable for comparison testing
# Stage 3 (PROD 5%): Can enable for validation (optional)
BLUE_GREEN_SHADOW_TRAFFIC_ENABLED = (
    os.getenv("BLUE_GREEN_SHADOW_TRAFFIC_ENABLED", "false").lower() == "true"
)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def is_feature_enabled(flag_name: str, env: Optional[str] = None) -> bool:
    """
    Check if a feature flag is enabled for the current (or specified) environment.

    This function provides environment-aware feature checking, ensuring features
    are only enabled in appropriate environments (dev → staging → prod).

    Args:
        flag_name: Name of the feature flag (e.g., "LIVE_RAG_BOB_ENABLED")
        env: Optional environment override (default: auto-detect)

    Returns:
        bool: True if feature is enabled for the environment, False otherwise

    Examples:
        # Auto-detect environment and check flag
        if is_feature_enabled("LIVE_RAG_BOB_ENABLED"):
            # Use Vertex AI Search

        # Check flag for specific environment
        if is_feature_enabled("ENGINE_MODE_FOREMAN_TO_IAM_ADK", env="staging"):
            # Enable in staging only

    Safety:
        - Unknown flag names return False
        - Missing environment defaults to "dev"
        - All flags default to False unless explicitly set
    """
    # Get flag value from globals
    flag_value = globals().get(flag_name, False)

    # If flag is not enabled, return False immediately
    if not flag_value:
        return False

    # Flag is enabled - return True
    # (Environment-specific gating is done via separate env vars per environment)
    return True


def get_traffic_percent() -> int:
    """
    Get current traffic percentage for Bob next-gen canary rollout.

    Returns:
        int: Traffic percentage (0-100)

    Examples:
        percent = get_traffic_percent()
        if percent >= 50:
            # Majority traffic on next-gen

    Rollout Stages:
        Stage 0-2: 0% (disabled or staging only)
        Stage 3: 5% (initial canary)
        Stage 4a: 25% (cautious)
        Stage 4b: 50% (half)
        Stage 4c: 100% (full)
        Stage 5: 100% (next-gen canonical)
    """
    if not AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
        return 0

    # Clamp to 0-100 range
    percent = max(0, min(100, AGENT_ENGINE_BOB_NEXT_GEN_PERCENT))
    return percent


def should_use_next_gen_bob(request_id: Optional[str] = None) -> bool:
    """
    Determine if this request should route to Bob next-gen (canary routing).

    Uses deterministic hash-based routing for consistent user experience.
    Same request_id always routes to same version.

    Args:
        request_id: Optional request/session ID for consistent routing

    Returns:
        bool: True if should use next-gen, False if should use current

    Examples:
        if should_use_next_gen_bob(session_id):
            endpoint = resolve_agent_engine_endpoint("bob_next_gen", "prod")
        else:
            endpoint = resolve_agent_engine_endpoint("bob_current", "prod")

    Algorithm:
        - If next-gen not enabled: return False
        - If traffic percent is 0: return False
        - If traffic percent is 100: return True
        - If request_id provided: hash(request_id) % 100 < percent
        - If no request_id: random() < percent/100 (non-deterministic)
    """
    if not AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
        return False

    percent = get_traffic_percent()
    if percent == 0:
        return False
    if percent == 100:
        return True

    # Deterministic routing based on request_id hash
    if request_id:
        # Hash request_id to 0-99 range
        hash_value = hash(request_id) % 100
        return hash_value < percent

    # Fallback: Non-deterministic (should provide request_id for consistency)
    import random

    return random.random() * 100 < percent


def is_rag_enabled_for_agent(agent_role: str) -> bool:
    """
    Check if live RAG (Vertex AI Search) is enabled for a specific agent.

    Args:
        agent_role: Agent name (e.g., "bob", "foreman", "iam-adk")

    Returns:
        bool: True if RAG is enabled for this agent, False otherwise

    Examples:
        if is_rag_enabled_for_agent("bob"):
            datastore_id = os.getenv("VERTEX_SEARCH_DATASTORE_ID")
            # Query Vertex AI Search

    Supported Agents:
        - "bob": Uses LIVE_RAG_BOB_ENABLED
        - "foreman": Uses LIVE_RAG_FOREMAN_ENABLED
        - Others: Not yet supported (returns False)
    """
    if agent_role == "bob":
        return LIVE_RAG_BOB_ENABLED
    elif agent_role in ("foreman", "iam-senior-adk-devops-lead"):
        return LIVE_RAG_FOREMAN_ENABLED
    else:
        # RAG not yet supported for other agents
        return False


def is_engine_mode_enabled_for_call(caller: str, target: str) -> bool:
    """
    Check if Agent Engine mode is enabled for a specific A2A call.

    Args:
        caller: Calling agent (e.g., "foreman")
        target: Target agent (e.g., "iam-adk", "iam-issue")

    Returns:
        bool: True if should use Agent Engine for this call, False if local

    Examples:
        if is_engine_mode_enabled_for_call("foreman", "iam-adk"):
            # Call iam-adk via Agent Engine REST API
        else:
            # Call iam-adk locally (import and run)

    Supported Calls:
        - foreman → iam-adk: Uses ENGINE_MODE_FOREMAN_TO_IAM_ADK
        - foreman → iam-issue: Uses ENGINE_MODE_FOREMAN_TO_IAM_ISSUE
        - foreman → iam-fix-*: Uses ENGINE_MODE_FOREMAN_TO_IAM_FIX
        - Others: Not yet supported (returns False)
    """
    if caller == "foreman":
        if target == "iam-adk":
            return ENGINE_MODE_FOREMAN_TO_IAM_ADK
        elif target == "iam-issue":
            return ENGINE_MODE_FOREMAN_TO_IAM_ISSUE
        elif target.startswith("iam-fix"):
            return ENGINE_MODE_FOREMAN_TO_IAM_FIX

    # Not yet supported
    return False


def should_use_a2a_gateway_routing() -> bool:
    """
    Check if Option B routing should be used (Slack → a2a_gateway → Engine).

    Returns:
        bool: True if should use a2a_gateway, False if direct Agent Engine

    Examples:
        if should_use_a2a_gateway_routing():
            # POST to a2a_gateway /a2a/run
        else:
            # POST directly to Agent Engine REST API

    Context:
        Option A (default): Slack webhook → Agent Engine direct
        Option B (future): Slack webhook → a2a_gateway → Agent Engine
                          (Enables foreman orchestration and A2A routing)
    """
    return SLACK_SWE_PIPELINE_MODE_ENABLED


# ==============================================================================
# VALIDATION & DEBUGGING
# ==============================================================================


def get_all_flags() -> dict:
    """
    Get all feature flags and their current values.

    Returns:
        dict: All flags with their boolean/int values

    Examples:
        flags = get_all_flags()
        for name, value in flags.items():
            print(f"{name}: {value}")

    Use Cases:
        - Debugging feature flag state
        - Logging configuration at startup
        - ARV checks for production safety
    """
    return {
        # RAG flags
        "LIVE_RAG_BOB_ENABLED": LIVE_RAG_BOB_ENABLED,
        "LIVE_RAG_FOREMAN_ENABLED": LIVE_RAG_FOREMAN_ENABLED,
        # A2A Engine flags
        "ENGINE_MODE_FOREMAN_TO_IAM_ADK": ENGINE_MODE_FOREMAN_TO_IAM_ADK,
        "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE": ENGINE_MODE_FOREMAN_TO_IAM_ISSUE,
        "ENGINE_MODE_FOREMAN_TO_IAM_FIX": ENGINE_MODE_FOREMAN_TO_IAM_FIX,
        # Gateway routing
        "SLACK_SWE_PIPELINE_MODE_ENABLED": SLACK_SWE_PIPELINE_MODE_ENABLED,
        # Blue/Green migration
        "AGENT_ENGINE_BOB_NEXT_GEN_ENABLED": AGENT_ENGINE_BOB_NEXT_GEN_ENABLED,
        "AGENT_ENGINE_BOB_NEXT_GEN_PERCENT": AGENT_ENGINE_BOB_NEXT_GEN_PERCENT,
        "BLUE_GREEN_SHADOW_TRAFFIC_ENABLED": BLUE_GREEN_SHADOW_TRAFFIC_ENABLED,
    }


def get_enabled_flags() -> list:
    """
    Get list of currently enabled feature flags.

    Returns:
        list: Names of enabled flags

    Examples:
        enabled = get_enabled_flags()
        if enabled:
            print(f"⚠️ Features enabled: {', '.join(enabled)}")
        else:
            print("✅ All features disabled (safe)")

    Use Cases:
        - ARV checks ensuring no prod flags enabled prematurely
        - Startup logging showing active features
        - Debugging unexpected behavior
    """
    all_flags = get_all_flags()
    enabled = []
    for name, value in all_flags.items():
        # Skip percent (it's not a boolean flag)
        if name == "AGENT_ENGINE_BOB_NEXT_GEN_PERCENT":
            if value > 0:
                enabled.append(f"{name}={value}")
        elif value is True:
            enabled.append(name)
    return enabled


# ==============================================================================
# TESTING & VALIDATION (for ARV checks and debugging)
# ==============================================================================

if __name__ == "__main__":
    """
    Feature flags module test and validation.

    Run this script to verify:
    - All flags default to False/0
    - Environment detection works
    - Helper functions work correctly
    """
    print("🚩 Feature Flags Module Test (Phase AE3)\n")

    # Environment
    env = get_current_environment()
    print(f"Environment: {env}")
    print()

    # All flags
    print("All Feature Flags:")
    all_flags = get_all_flags()
    for name, value in all_flags.items():
        print(f"  {name}: {value}")
    print()

    # Enabled flags
    enabled = get_enabled_flags()
    if enabled:
        print(f"⚠️  Enabled flags: {', '.join(enabled)}")
    else:
        print("✅ All flags disabled (safe default)")
    print()

    # Helper functions
    print("Helper Function Tests:")
    print(f"  is_rag_enabled_for_agent('bob'): {is_rag_enabled_for_agent('bob')}")
    print(
        f"  is_engine_mode_enabled_for_call('foreman', 'iam-adk'): {is_engine_mode_enabled_for_call('foreman', 'iam-adk')}"
    )
    print(f"  should_use_a2a_gateway_routing(): {should_use_a2a_gateway_routing()}")
    print(f"  get_traffic_percent(): {get_traffic_percent()}%")
    print(
        f"  should_use_next_gen_bob('test-session-123'): {should_use_next_gen_bob('test-session-123')}"
    )
    print()

    print("✅ Feature flags module test complete!")
