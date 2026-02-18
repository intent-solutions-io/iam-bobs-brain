"""
Configuration Inventory for Bob's Brain

Centralized enumeration of ALL environment variables and feature flags.
This module is the single source of truth for config validation.

Used by:
- scripts/check_config_all.py (validation)
- CI workflows (pre-deploy checks)
- Documentation generation
- ARV (Agent Readiness Verification)

DO NOT import from other config modules here to avoid circular dependencies.
This is a pure data module.
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# Type aliases
Environment = Literal["dev", "staging", "prod"]
VarCategory = Literal[
    "core",  # Core GCP/app config
    "rag",  # Vertex AI Search / RAG
    "engine",  # Agent Engine topology
    "features",  # Feature flags (LIVE1-3, etc.)
    "storage",  # Org GCS storage
    "notifications",  # Slack notifications
    "github",  # GitHub integration
    "slack_bot",  # Slack bot (separate from notifications)
]


@dataclass
class EnvVarSpec:
    """
    Specification for a single environment variable.

    Attributes:
        name: Environment variable name (e.g., "PROJECT_ID")
        required: Is this variable required for any environment?
        default: Default value if not set (None = no default)
        description: Human-readable description
        category: Category for grouping
        envs: Which environments need this var (["dev", "staging", "prod"])
        required_when: Optional condition (e.g., "LIVE_RAG_BOB_ENABLED=true")
        deprecated: Is this variable deprecated?
        canonical_replacement: If deprecated, what should be used instead?
    """

    name: str
    required: bool
    default: Optional[str]
    description: str
    category: VarCategory
    envs: List[Environment] = field(default_factory=lambda: ["dev", "staging", "prod"])
    required_when: Optional[str] = None
    deprecated: bool = False
    canonical_replacement: Optional[str] = None

    def is_required_for_env(self, env: Environment) -> bool:
        """Check if this variable is required for the given environment."""
        if not self.required:
            return False
        return env in self.envs

    def is_optional_for_env(self, env: Environment) -> bool:
        """Check if this variable is optional (present in env list but not required)."""
        if self.required:
            return False
        return env in self.envs


# ==============================================================================
# CORE CONFIGURATION
# ==============================================================================

CORE_VARS = [
    EnvVarSpec(
        name="DEPLOYMENT_ENV",
        required=False,  # Auto-detected if missing
        default="dev",
        description="Deployment environment (dev, staging, prod)",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="PROJECT_ID",
        required=True,
        default=None,
        description="GCP project ID for Vertex AI and Agent Engine",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="LOCATION",
        required=True,
        default="us-central1",
        description="GCP region for Agent Engine deployment",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_ID",
        required=False,  # Only required when using Agent Engine
        default=None,
        description="Vertex AI Agent Engine reasoning engine ID",
        category="engine",
        envs=["dev", "staging", "prod"],
        required_when="ENGINE_MODE_* flags enabled",
    ),
    EnvVarSpec(
        name="AGENT_SPIFFE_ID",
        required=True,
        default=None,
        description="SPIFFE ID for agent identity (spiffe://intent.solutions/agent/...)",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="APP_NAME",
        required=False,
        default="bobs-brain",
        description="Application name for logging and telemetry",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="APP_VERSION",
        required=False,
        default="0.9.0",
        description="Application version for tracking",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="LOG_LEVEL",
        required=False,
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        category="core",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="PUBLIC_URL",
        required=False,
        default=None,
        description="Public URL for A2A gateway (https://...run.app)",
        category="core",
        envs=["staging", "prod"],
    ),
]


# ==============================================================================
# RAG CONFIGURATION (Vertex AI Search)
# ==============================================================================

RAG_VARS = [
    EnvVarSpec(
        name="VERTEX_SEARCH_PROJECT_ID",
        required=False,
        default=None,
        description="GCP project ID for Vertex AI Search (can differ from main PROJECT_ID)",
        category="rag",
        envs=["dev", "staging", "prod"],
        required_when="LIVE_RAG_BOB_ENABLED=true or LIVE_RAG_FOREMAN_ENABLED=true",
    ),
    EnvVarSpec(
        name="VERTEX_SEARCH_LOCATION",
        required=False,
        default="global",
        description="GCP region for Vertex AI Search (usually 'global')",
        category="rag",
        envs=["dev", "staging", "prod"],
        required_when="LIVE_RAG_*_ENABLED=true",
    ),
    EnvVarSpec(
        name="VERTEX_SEARCH_DATASTORE_ID_DEV",
        required=False,
        default=None,
        description="Vertex AI Search datastore ID for dev environment",
        category="rag",
        envs=["dev"],
        required_when="LIVE_RAG_*_ENABLED=true and DEPLOYMENT_ENV=dev",
    ),
    EnvVarSpec(
        name="VERTEX_SEARCH_DATASTORE_ID_STAGING",
        required=False,
        default=None,
        description="Vertex AI Search datastore ID for staging environment",
        category="rag",
        envs=["staging"],
        required_when="LIVE_RAG_*_ENABLED=true and DEPLOYMENT_ENV=staging",
    ),
    EnvVarSpec(
        name="VERTEX_SEARCH_DATASTORE_ID_PROD",
        required=False,
        default=None,
        description="Vertex AI Search datastore ID for production environment",
        category="rag",
        envs=["prod"],
        required_when="LIVE_RAG_*_ENABLED=true and DEPLOYMENT_ENV=prod",
    ),
]


# ==============================================================================
# AGENT ENGINE TOPOLOGY (AE1)
# ==============================================================================
# Per-agent, per-environment Engine IDs for Agent Engine deployment
# These follow the pattern: AGENT_ENGINE_{AGENT}_{ENV}
# Read by: agents/config/agent_engine.py

ENGINE_VARS = [
    # Bob Agent Engine IDs
    EnvVarSpec(
        name="AGENT_ENGINE_BOB_ID_DEV",
        required=False,
        default=None,
        description="Bob's Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="ENGINE_MODE enabled for Bob in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_BOB_ID_STAGING",
        required=False,
        default=None,
        description="Bob's Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="ENGINE_MODE enabled for Bob in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_BOB_ID_PROD",
        required=False,
        default=None,
        description="Bob's Agent Engine ID in prod (uses canonical fallback 5828234061910376448)",
        category="engine",
        envs=["prod"],
        required_when="ENGINE_MODE enabled for Bob in prod",
    ),
    # Foreman Agent Engine IDs
    EnvVarSpec(
        name="AGENT_ENGINE_FOREMAN_ID_DEV",
        required=False,
        default=None,
        description="Foreman's Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="ENGINE_MODE enabled for foreman in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_FOREMAN_ID_STAGING",
        required=False,
        default=None,
        description="Foreman's Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="ENGINE_MODE enabled for foreman in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_FOREMAN_ID_PROD",
        required=False,
        default=None,
        description="Foreman's Agent Engine ID in prod environment",
        category="engine",
        envs=["prod"],
        required_when="ENGINE_MODE enabled for foreman in prod",
    ),
    # IAM Specialist Agent Engine IDs (Future-proofing)
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ADK_ID_DEV",
        required=False,
        default=None,
        description="iam-adk Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ADK=true in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ADK_ID_STAGING",
        required=False,
        default=None,
        description="iam-adk Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ADK=true in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ADK_ID_PROD",
        required=False,
        default=None,
        description="iam-adk Agent Engine ID in prod environment",
        category="engine",
        envs=["prod"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ADK=true in prod",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ISSUE_ID_DEV",
        required=False,
        default=None,
        description="iam-issue Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ISSUE=true in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ISSUE_ID_STAGING",
        required=False,
        default=None,
        description="iam-issue Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ISSUE=true in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_ISSUE_ID_PROD",
        required=False,
        default=None,
        description="iam-issue Agent Engine ID in prod environment",
        category="engine",
        envs=["prod"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_ISSUE=true in prod",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_FIX_ID_DEV",
        required=False,
        default=None,
        description="iam-fix Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_FIX=true in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_FIX_ID_STAGING",
        required=False,
        default=None,
        description="iam-fix Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_FIX=true in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_FIX_ID_PROD",
        required=False,
        default=None,
        description="iam-fix Agent Engine ID in prod environment",
        category="engine",
        envs=["prod"],
        required_when="ENGINE_MODE_FOREMAN_TO_IAM_FIX=true in prod",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_QA_ID_DEV",
        required=False,
        default=None,
        description="iam-qa Agent Engine ID in dev environment",
        category="engine",
        envs=["dev"],
        required_when="iam-qa deployed to Agent Engine in dev",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_QA_ID_STAGING",
        required=False,
        default=None,
        description="iam-qa Agent Engine ID in staging environment",
        category="engine",
        envs=["staging"],
        required_when="iam-qa deployed to Agent Engine in staging",
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_IAM_QA_ID_PROD",
        required=False,
        default=None,
        description="iam-qa Agent Engine ID in prod environment",
        category="engine",
        envs=["prod"],
        required_when="iam-qa deployed to Agent Engine in prod",
    ),
    # Alternative naming support (GCP_PROJECT_ID, VERTEX_LOCATION)
    EnvVarSpec(
        name="GCP_PROJECT_ID",
        required=False,
        default=None,
        description="Alternative name for PROJECT_ID (GCP-style naming)",
        category="engine",
        envs=["dev", "staging", "prod"],
        deprecated=False,  # Not deprecated, just an alias
        canonical_replacement="PROJECT_ID",
    ),
    EnvVarSpec(
        name="VERTEX_LOCATION",
        required=False,
        default=None,
        description="Alternative name for LOCATION (Vertex AI style naming)",
        category="engine",
        envs=["dev", "staging", "prod"],
        deprecated=False,  # Not deprecated, just an alias
        canonical_replacement="LOCATION",
    ),
]


# ==============================================================================
# FEATURE FLAGS (LIVE1-3, RAG, Engine, Blue/Green)
# ==============================================================================

FEATURE_FLAGS = [
    # RAG flags
    EnvVarSpec(
        name="LIVE_RAG_BOB_ENABLED",
        required=False,
        default="false",
        description="Enable Vertex AI Search for Bob agent (LIVE2)",
        category="features",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="LIVE_RAG_FOREMAN_ENABLED",
        required=False,
        default="false",
        description="Enable Vertex AI Search for foreman agent (LIVE2)",
        category="features",
        envs=["dev", "staging", "prod"],
    ),
    # Agent Engine A2A flags
    EnvVarSpec(
        name="ENGINE_MODE_FOREMAN_TO_IAM_ADK",
        required=False,
        default="false",
        description="Enable foreman → iam-adk via Agent Engine (vs local)",
        category="features",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="ENGINE_MODE_FOREMAN_TO_IAM_ISSUE",
        required=False,
        default="false",
        description="Enable foreman → iam-issue via Agent Engine",
        category="features",
        envs=["staging", "prod"],
    ),
    EnvVarSpec(
        name="ENGINE_MODE_FOREMAN_TO_IAM_FIX",
        required=False,
        default="false",
        description="Enable foreman → iam-fix-* via Agent Engine",
        category="features",
        envs=["staging", "prod"],
    ),
    # Gateway routing
    EnvVarSpec(
        name="SLACK_SWE_PIPELINE_MODE_ENABLED",
        required=False,
        default="false",
        description="Enable Slack → a2a_gateway routing (Option B)",
        category="features",
        envs=["staging", "prod"],
    ),
    # Blue/Green migration (Bob current → next-gen)
    EnvVarSpec(
        name="AGENT_ENGINE_BOB_NEXT_GEN_ENABLED",
        required=False,
        default="false",
        description="Enable routing to Bob next-gen (ADK-based)",
        category="features",
        envs=["staging", "prod"],
    ),
    EnvVarSpec(
        name="AGENT_ENGINE_BOB_NEXT_GEN_PERCENT",
        required=False,
        default="0",
        description="Traffic percentage to Bob next-gen (0-100)",
        category="features",
        envs=["prod"],
    ),
    EnvVarSpec(
        name="BLUE_GREEN_SHADOW_TRAFFIC_ENABLED",
        required=False,
        default="false",
        description="Enable shadow traffic for comparison testing",
        category="features",
        envs=["staging", "prod"],
    ),
]


# ==============================================================================
# ORG STORAGE (LIVE1-GCS)
# ==============================================================================

STORAGE_VARS = [
    EnvVarSpec(
        name="ORG_STORAGE_BUCKET",
        required=False,
        default=None,
        description="Org-wide GCS bucket for knowledge hub (intent-org-knowledge-hub-{env})",
        category="storage",
        envs=["dev", "staging", "prod"],
        required_when="ORG_STORAGE_WRITE_ENABLED=true",
    ),
    EnvVarSpec(
        name="ORG_STORAGE_WRITE_ENABLED",
        required=False,
        default="false",
        description="Enable writing portfolio/SWE results to org GCS bucket (LIVE1)",
        category="storage",
        envs=["dev", "staging", "prod"],
    ),
]


# ==============================================================================
# NOTIFICATIONS (LIVE3A - Slack)
# ==============================================================================

NOTIFICATION_VARS = [
    EnvVarSpec(
        name="SLACK_NOTIFICATIONS_ENABLED",
        required=False,
        default="false",
        description="Enable Slack notifications for portfolio/SWE completion (LIVE3A)",
        category="notifications",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="SLACK_SWE_CHANNEL_WEBHOOK_URL",
        required=False,
        default=None,
        description="Slack webhook URL for SWE notifications (preferred method)",
        category="notifications",
        envs=["dev", "staging", "prod"],
        required_when="SLACK_NOTIFICATIONS_ENABLED=true",
    ),
    EnvVarSpec(
        name="SLACK_SWE_CHANNEL_ID",
        required=False,
        default=None,
        description="Slack channel ID for SWE notifications (alternative to webhook)",
        category="notifications",
        envs=["dev", "staging", "prod"],
        required_when="SLACK_NOTIFICATIONS_ENABLED=true AND no webhook URL",
    ),
    # Environment-aware safety flags (Phase LIVE3-STAGE-PROD-SAFETY)
    EnvVarSpec(
        name="SLACK_ENABLE_STAGING",
        required=False,
        default="false",
        description="Allow Slack notifications in staging (requires explicit override) - L3P1",
        category="notifications",
        envs=["staging"],
    ),
    EnvVarSpec(
        name="SLACK_ENABLE_PROD",
        required=False,
        default="false",
        description="Allow Slack notifications in prod (requires explicit override) - L3P1",
        category="notifications",
        envs=["prod"],
    ),
    EnvVarSpec(
        name="SLACK_ENV_LABEL",
        required=False,
        default=None,
        description="Optional environment label for Slack message prefixes (e.g., 'QA') - L3P1",
        category="notifications",
        envs=["dev", "staging", "prod"],
    ),
]


# ==============================================================================
# GITHUB INTEGRATION (LIVE3B)
# ==============================================================================

GITHUB_VARS = [
    EnvVarSpec(
        name="GITHUB_TOKEN",
        required=False,
        default=None,
        description="GitHub Personal Access Token for API operations",
        category="github",
        envs=["dev", "staging", "prod"],
        required_when="GITHUB_ISSUE_CREATION_ENABLED=true",
    ),
    EnvVarSpec(
        name="GITHUB_ISSUE_CREATION_ENABLED",
        required=False,
        default="false",
        description="Enable GitHub issue creation from SWE findings (LIVE3B)",
        category="github",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="GITHUB_ISSUE_CREATION_ALLOWED_REPOS",
        required=False,
        default="",
        description="Comma-separated list of repo IDs allowed for issue creation (* = all)",
        category="github",
        envs=["dev", "staging", "prod"],
        required_when="GITHUB_ISSUE_CREATION_ENABLED=true",
    ),
    EnvVarSpec(
        name="GITHUB_ISSUES_DRY_RUN",
        required=False,
        default="true",
        description="Dry-run mode for GitHub issues (log only, no API calls) - LIVE3B",
        category="github",
        envs=["dev", "staging", "prod"],
    ),
    # Environment-aware safety flags (Phase LIVE3-STAGE-PROD-SAFETY)
    EnvVarSpec(
        name="GITHUB_ENABLE_STAGING",
        required=False,
        default="false",
        description="Allow real GitHub issue creation in staging (requires explicit override) - L3P1",
        category="github",
        envs=["staging"],
    ),
    EnvVarSpec(
        name="GITHUB_ENABLE_PROD",
        required=False,
        default="false",
        description="Allow real GitHub issue creation in prod (requires explicit override) - L3P1",
        category="github",
        envs=["prod"],
    ),
]


# ==============================================================================
# SLACK BOT (Separate from notifications)
# ==============================================================================

SLACK_BOT_VARS = [
    EnvVarSpec(
        name="SLACK_BOT_TOKEN",
        required=False,
        default=None,
        description="Slack bot token (xoxb-...) for bot API operations",
        category="slack_bot",
        envs=["staging", "prod"],
    ),
    EnvVarSpec(
        name="SLACK_SIGNING_SECRET",
        required=False,
        default=None,
        description="Slack signing secret for webhook verification",
        category="slack_bot",
        envs=["staging", "prod"],
    ),
    EnvVarSpec(
        name="SLACK_APP_ID",
        required=False,
        default=None,
        description="Slack app ID",
        category="slack_bot",
        envs=["staging", "prod"],
    ),
    # SLACK-ENDTOEND-DEV: Feature flag for Slack bot interaction
    EnvVarSpec(
        name="SLACK_BOB_ENABLED",
        required=False,
        default="false",
        description="Enable Slack bot interaction (talk to Bob via @mentions) - S1",
        category="slack_bot",
        envs=["dev", "staging", "prod"],
    ),
    EnvVarSpec(
        name="A2A_GATEWAY_URL",
        required=False,
        default=None,
        description="A2A gateway URL for Slack → Agent Engine routing - S2",
        category="slack_bot",
        envs=["dev", "staging", "prod"],
        required_when="SLACK_BOB_ENABLED=true",
    ),
    EnvVarSpec(
        name="SLACK_WEBHOOK_URL",
        required=False,
        default=None,
        description="Legacy Slack webhook URL (use SLACK_SWE_CHANNEL_WEBHOOK_URL instead)",
        category="slack_bot",
        envs=["staging", "prod"],
        deprecated=True,
        canonical_replacement="SLACK_SWE_CHANNEL_WEBHOOK_URL",
    ),
]


# ==============================================================================
# FULL INVENTORY
# ==============================================================================

ALL_VARS: List[EnvVarSpec] = (
    CORE_VARS
    + RAG_VARS
    + ENGINE_VARS
    + FEATURE_FLAGS
    + STORAGE_VARS
    + NOTIFICATION_VARS
    + GITHUB_VARS
    + SLACK_BOT_VARS
)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def get_all_vars() -> List[EnvVarSpec]:
    """Get all environment variable specifications."""
    return ALL_VARS


def get_vars_by_category(category: VarCategory) -> List[EnvVarSpec]:
    """
    Get all variables in a specific category.

    Args:
        category: Category name

    Returns:
        List of EnvVarSpec objects
    """
    return [v for v in ALL_VARS if v.category == category]


def get_required_vars(env: Environment) -> List[EnvVarSpec]:
    """
    Get all required variables for a specific environment.

    Args:
        env: Environment name

    Returns:
        List of required EnvVarSpec objects
    """
    return [v for v in ALL_VARS if v.is_required_for_env(env)]


def get_optional_vars(env: Environment) -> List[EnvVarSpec]:
    """
    Get all optional variables for a specific environment.

    Args:
        env: Environment name

    Returns:
        List of optional EnvVarSpec objects
    """
    return [v for v in ALL_VARS if v.is_optional_for_env(env)]


def get_var_by_name(name: str) -> Optional[EnvVarSpec]:
    """
    Get variable specification by name.

    Args:
        name: Variable name

    Returns:
        EnvVarSpec if found, None otherwise
    """
    for var in ALL_VARS:
        if var.name == name:
            return var
    return None


def get_deprecated_vars() -> List[EnvVarSpec]:
    """Get all deprecated variables."""
    return [v for v in ALL_VARS if v.deprecated]


def get_categories() -> List[VarCategory]:
    """Get all unique categories."""
    categories = {v.category for v in ALL_VARS}
    return sorted(categories)


# ==============================================================================
# STATS & SUMMARY
# ==============================================================================


def get_inventory_stats() -> dict:
    """
    Get statistics about the configuration inventory.

    Returns:
        Dictionary with counts and breakdowns
    """
    total = len(ALL_VARS)
    required = len([v for v in ALL_VARS if v.required])
    optional = total - required
    deprecated = len(get_deprecated_vars())

    by_category = {}
    for category in get_categories():
        by_category[category] = len(get_vars_by_category(category))

    return {
        "total_vars": total,
        "required": required,
        "optional": optional,
        "deprecated": deprecated,
        "by_category": by_category,
        "categories": get_categories(),
    }


# ==============================================================================
# TESTING & VALIDATION
# ==============================================================================

if __name__ == "__main__":
    """
    Config inventory module test.

    Run this to verify the inventory is complete and consistent.
    """
    print("📋 Configuration Inventory")
    print("=" * 70)

    # Stats
    stats = get_inventory_stats()
    print(f"\nTotal Variables: {stats['total_vars']}")
    print(f"  Required: {stats['required']}")
    print(f"  Optional: {stats['optional']}")
    print(f"  Deprecated: {stats['deprecated']}")

    # By category
    print("\nBy Category:")
    for category in stats["categories"]:
        count = stats["by_category"][category]
        print(f"  {category}: {count}")

    # Show required vars for each env
    for env in ["dev", "staging", "prod"]:
        required_vars = get_required_vars(env)
        print(f"\nRequired for {env}: {len(required_vars)}")
        for var in required_vars[:5]:  # Show first 5
            print(f"  - {var.name}")
        if len(required_vars) > 5:
            print(f"  ... and {len(required_vars) - 5} more")

    # Deprecated vars
    deprecated = get_deprecated_vars()
    if deprecated:
        print("\n⚠️  Deprecated Variables:")
        for var in deprecated:
            print(f"  - {var.name} → use {var.canonical_replacement}")

    print("\n" + "=" * 70)
    print("✅ Inventory module loaded successfully")
