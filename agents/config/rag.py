"""
RAG Configuration for Bob and Foreman Agents

Centralizes all RAG-related configuration including Vertex AI Search
datastore IDs, environment selection, and tool factory helpers.

This is the canonical source for RAG configuration across the department.
"""

import os
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class VertexSearchConfig:
    """Configuration for Vertex AI Search integration."""

    project_id: str
    location: str
    datastore_id: str
    env: Literal["dev", "staging", "prod"]

    def is_placeholder(self) -> bool:
        """Check if this config contains placeholder values."""
        placeholder_indicators = [
            "your-project",
            "your-datastore",
            "placeholder",
            "TODO",
            "FIXME",
        ]
        return any(
            indicator in self.project_id.lower()
            or indicator in self.datastore_id.lower()
            for indicator in placeholder_indicators
        )


def get_current_env() -> Literal["dev", "staging", "prod"]:
    """
    Determine the current environment from DEPLOYMENT_ENV or APP_ENV.

    Returns:
        Environment string: "dev", "staging", or "prod"

    Environment Variables:
        DEPLOYMENT_ENV: Explicit deployment environment
        APP_ENV: Fallback environment variable
        Default: "dev" (safest default)

    Examples:
        export DEPLOYMENT_ENV=prod
        export DEPLOYMENT_ENV=staging
        (no env set) → defaults to "dev"
    """
    env = os.getenv("DEPLOYMENT_ENV") or os.getenv("APP_ENV") or "dev"
    env_lower = env.lower()

    # Normalize variations
    if env_lower in ("production", "prod"):
        return "prod"
    elif env_lower in ("staging", "stage"):
        return "staging"
    else:
        # Default to dev for safety
        return "dev"


def get_vertex_search_config(
    env: Optional[Literal["dev", "staging", "prod"]] = None,
) -> VertexSearchConfig:
    """
    Get Vertex AI Search configuration for the specified environment.

    Args:
        env: Environment to get config for (auto-detected if not provided)

    Returns:
        VertexSearchConfig with project, location, and datastore ID

    Environment Variables:
        VERTEX_SEARCH_PROJECT_ID: GCP project ID for Vertex Search
        VERTEX_SEARCH_LOCATION: GCP region (e.g., "global", "us-central1")
        VERTEX_SEARCH_DATASTORE_ID_DEV: Datastore ID for dev
        VERTEX_SEARCH_DATASTORE_ID_STAGING: Datastore ID for staging
        VERTEX_SEARCH_DATASTORE_ID_PROD: Datastore ID for production

    Raises:
        ValueError: If required environment variables are missing
    """
    if env is None:
        env = get_current_env()

    # Get common config
    project_id = os.getenv("VERTEX_SEARCH_PROJECT_ID")
    location = os.getenv("VERTEX_SEARCH_LOCATION", "global")

    if not project_id:
        raise ValueError(
            "VERTEX_SEARCH_PROJECT_ID environment variable is required. "
            "Set it to your GCP project ID."
        )

    # Get environment-specific datastore ID
    datastore_env_var = f"VERTEX_SEARCH_DATASTORE_ID_{env.upper()}"
    datastore_id = os.getenv(datastore_env_var)

    if not datastore_id:
        raise ValueError(
            f"{datastore_env_var} environment variable is required. "
            f"Set it to the Vertex AI Search datastore ID for {env}."
        )

    return VertexSearchConfig(
        project_id=project_id, location=location, datastore_id=datastore_id, env=env
    )


def get_bob_vertex_search_config(
    env: Optional[Literal["dev", "staging", "prod"]] = None,
) -> VertexSearchConfig:
    """
    Get Vertex AI Search configuration for Bob (orchestrator).

    Currently uses the same datastore as other agents, but this function
    provides a clear extension point if Bob needs a different configuration.

    Args:
        env: Environment (auto-detected if not provided)

    Returns:
        VertexSearchConfig for Bob
    """
    return get_vertex_search_config(env)


def get_foreman_vertex_search_config(
    env: Optional[Literal["dev", "staging", "prod"]] = None,
) -> VertexSearchConfig:
    """
    Get Vertex AI Search configuration for iam-senior-adk-devops-lead (foreman).

    Currently uses the same datastore as other agents, but this function
    provides a clear extension point if the foreman needs different configuration.

    Args:
        env: Environment (auto-detected if not provided)

    Returns:
        VertexSearchConfig for foreman
    """
    return get_vertex_search_config(env)


def validate_rag_config(env: Optional[str] = None) -> dict:
    """
    Validate RAG configuration for the specified environment.

    Args:
        env: Environment to validate (auto-detected if not provided)

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "env": str,
            "config": VertexSearchConfig or None,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    if env is None:
        env = get_current_env()

    errors = []
    warnings = []
    config = None

    try:
        config = get_vertex_search_config(env)

        # Check for placeholder values
        if config.is_placeholder():
            warnings.append(
                "Configuration contains placeholder values. "
                "Update environment variables with real datastore IDs."
            )

        # Validate structure
        if not config.project_id:
            errors.append("Project ID is empty")
        if not config.datastore_id:
            errors.append("Datastore ID is empty")
        if not config.location:
            errors.append("Location is empty")

    except ValueError as e:
        errors.append(str(e))

    return {
        "valid": len(errors) == 0,
        "env": env,
        "config": config,
        "errors": errors,
        "warnings": warnings,
    }


# Example usage and testing
if __name__ == "__main__":
    print("🔍 RAG Configuration Check")
    print("=" * 60)

    # Show current environment
    current_env = get_current_env()
    print(f"\nCurrent Environment: {current_env}")

    # Validate configuration
    print(f"\nValidating RAG configuration for {current_env}...")
    validation = validate_rag_config(current_env)

    if validation["valid"]:
        print("✅ Configuration is valid")
        config = validation["config"]
        print(f"   Project: {config.project_id}")
        print(f"   Location: {config.location}")
        print(f"   Datastore: {config.datastore_id}")

        if validation["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
    else:
        print("❌ Configuration is invalid")
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"   - {error}")

    print("\n" + "=" * 60)
    print("Environment Variables Used:")
    print("  - DEPLOYMENT_ENV (or APP_ENV)")
    print("  - VERTEX_SEARCH_PROJECT_ID")
    print("  - VERTEX_SEARCH_LOCATION")
    print(f"  - VERTEX_SEARCH_DATASTORE_ID_{current_env.upper()}")
