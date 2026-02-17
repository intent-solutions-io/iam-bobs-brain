"""
ARV (Agent Readiness Verification) Specification for IAM Department

This module defines the ARV checks for the bobs-brain IAM/ADK department.
Each check maps to an existing script or test suite.

Design:
- ArvCheck: Definition of a single readiness check
- ArvResult: Result of executing a check
- ALL_CHECKS: Complete checklist for this department
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# Type aliases
Environment = Literal["dev", "staging", "prod"]
Category = Literal["config", "tests", "rag", "engine", "storage", "notifications"]


@dataclass
class ArvCheck:
    """
    Definition of a single ARV check.

    Attributes:
        id: Unique identifier (kebab-case)
        description: Human-readable description
        category: Logical grouping
        required: Whether this check is required for the environment
        command: Shell command or script to execute
        required_when: Optional condition (e.g., "LIVE_RAG_BOB_ENABLED=true")
        envs: Environments where this check applies
    """

    id: str
    description: str
    category: Category
    required: bool
    command: str
    required_when: Optional[str] = None
    envs: List[Environment] = field(default_factory=lambda: ["dev", "staging", "prod"])


@dataclass
class ArvResult:
    """
    Result of executing an ARV check.

    Attributes:
        check: The check that was executed
        passed: Whether the check passed
        skipped: Whether the check was skipped (not applicable)
        details: Additional information (error message, output, etc.)
        exit_code: Exit code from the check command (if applicable)
    """

    check: ArvCheck
    passed: bool
    skipped: bool = False
    details: Optional[str] = None
    exit_code: Optional[int] = None


# ==================================================
# ARV CHECKLIST FOR IAM/ADK DEPARTMENT
# ==================================================

ALL_CHECKS: List[ArvCheck] = [
    # ========================================
    # CONFIG CATEGORY
    # ========================================
    ArvCheck(
        id="config-basic",
        description="Environment configuration validation",
        category="config",
        required=True,
        command="python3 scripts/check_config_all.py",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # TESTS CATEGORY
    # ========================================
    ArvCheck(
        id="tests-unit",
        description="Unit tests for agents",
        category="tests",
        required=True,
        command="pytest tests/unit -v --tb=short",
        envs=["dev", "staging", "prod"],
    ),
    ArvCheck(
        id="tests-swe-pipeline",
        description="Portfolio/SWE pipeline tests",
        category="tests",
        required=True,
        command="pytest tests/test_swe_pipeline.py -v --tb=short",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # RAG CATEGORY (Feature-gated)
    # ========================================
    ArvCheck(
        id="rag-readiness",
        description="RAG configuration and Vertex AI Search readiness",
        category="rag",
        required=False,  # Only required when RAG is enabled
        command="python3 scripts/check_rag_readiness.py",
        required_when="LIVE_RAG_BOB_ENABLED=true OR LIVE_RAG_FOREMAN_ENABLED=true",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # ENGINE CATEGORY
    # ========================================
    ArvCheck(
        id="engine-flags-safety",
        description="Agent Engine flags safety validation",
        category="engine",
        required=True,
        command="python3 scripts/check_arv_engine_flags.py",
        envs=["dev", "staging", "prod"],
    ),
    ArvCheck(
        id="arv-minimum-requirements",
        description="ARV minimum structural requirements",
        category="engine",
        required=True,
        command="python3 scripts/check_arv_minimum.py",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # STORAGE CATEGORY (Feature-gated)
    # ========================================
    ArvCheck(
        id="storage-readiness",
        description="Org-wide GCS storage readiness",
        category="storage",
        required=False,  # Only required when storage writes are enabled
        command="python3 scripts/check_org_storage_readiness.py",
        required_when="ORG_STORAGE_WRITE_ENABLED=true",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # NOTIFICATIONS CATEGORY (LIVE3)
    # ========================================
    ArvCheck(
        id="live3-config-readiness",
        description="LIVE3 configuration readiness (Slack + GitHub environment-aware safety)",
        category="notifications",
        required=False,  # Non-blocking - informational only
        command="python3 scripts/check_live3_readiness.py",
        required_when="SLACK_NOTIFICATIONS_ENABLED=true OR GITHUB_ISSUE_CREATION_ENABLED=true",
        envs=["dev", "staging", "prod"],
    ),
    # ========================================
    # LIVE3 E2E CATEGORY (Optional, LIVE3-E2E-DEV)
    # ========================================
    ArvCheck(
        id="live3-dev-smoke",
        description="LIVE3 end-to-end smoke test (portfolio + GCS + Slack + GitHub)",
        category="notifications",  # Fits with notifications/integrations
        required=False,  # Optional - doesn't block deployments
        command="python3 scripts/run_live3_dev_smoke.py --repo bobs-brain",
        required_when="ANY LIVE3 FEATURE ENABLED (SLACK/GITHUB/ORG_STORAGE)",
        envs=["dev"],  # Only runs in dev for now
    ),
    # ========================================
    # AGENT ENGINE E2E CATEGORY (Optional, AE3)
    # ========================================
    ArvCheck(
        id="agent-engine-dev-smoke",
        description="Agent Engine dev smoke test (config + a2a gateway + Agent Engine)",
        category="engine",
        required=False,  # Optional - doesn't block deployments
        command="python3 scripts/run_agent_engine_dev_smoke.py",
        required_when="Agent Engine IDs configured for dev (AGENT_ENGINE_*_ID_DEV)",
        envs=["dev"],  # Only runs in dev for now
    ),
]


def get_checks_for_env(env: Environment) -> List[ArvCheck]:
    """
    Get all checks applicable to the given environment.

    Args:
        env: Target environment (dev, staging, prod)

    Returns:
        List of ArvCheck objects applicable to the environment
    """
    return [check for check in ALL_CHECKS if env in check.envs]


def get_required_checks(env: Environment) -> List[ArvCheck]:
    """
    Get required checks for the given environment.

    Note: This returns checks that are always required.
    Conditional checks (required_when) are evaluated at runtime.

    Args:
        env: Target environment

    Returns:
        List of required ArvCheck objects
    """
    return [check for check in get_checks_for_env(env) if check.required]


def get_optional_checks(env: Environment) -> List[ArvCheck]:
    """
    Get optional/conditional checks for the given environment.

    Args:
        env: Target environment

    Returns:
        List of optional ArvCheck objects
    """
    return [check for check in get_checks_for_env(env) if not check.required]


def get_checks_by_category(env: Environment, category: Category) -> List[ArvCheck]:
    """
    Get all checks in a specific category for the given environment.

    Args:
        env: Target environment
        category: Check category to filter by

    Returns:
        List of ArvCheck objects in the specified category
    """
    return [check for check in get_checks_for_env(env) if check.category == category]


def get_check_by_id(check_id: str) -> Optional[ArvCheck]:
    """
    Get a specific check by its ID.

    Args:
        check_id: Unique check identifier

    Returns:
        ArvCheck object if found, None otherwise
    """
    for check in ALL_CHECKS:
        if check.id == check_id:
            return check
    return None


# ==================================================
# CATEGORY METADATA
# ==================================================

CATEGORY_DESCRIPTIONS = {
    "config": "Configuration validation (env vars, feature flags)",
    "tests": "Test suite execution (unit, integration, pipeline)",
    "rag": "RAG (Vertex AI Search) readiness and connectivity",
    "engine": "Agent Engine structural requirements and flags",
    "storage": "GCS storage connectivity and permissions",
    "notifications": "Slack and GitHub notification infrastructure",
}


def get_category_description(category: Category) -> str:
    """Get human-readable description of a category."""
    return CATEGORY_DESCRIPTIONS.get(category, "Unknown category")


# ==================================================
# SUMMARY HELPERS
# ==================================================


def get_check_summary() -> dict:
    """
    Get summary statistics about the ARV checklist.

    Returns:
        Dictionary with counts and metadata
    """
    return {
        "total_checks": len(ALL_CHECKS),
        "required_checks": len([c for c in ALL_CHECKS if c.required]),
        "optional_checks": len([c for c in ALL_CHECKS if not c.required]),
        "categories": list(set(c.category for c in ALL_CHECKS)),
        "checks_by_category": {
            category: len([c for c in ALL_CHECKS if c.category == category])
            for category in CATEGORY_DESCRIPTIONS.keys()
        },
    }
