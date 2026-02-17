"""
Agent Identity Standard (252-DR-STND)

Provides canonical agent IDs and backwards-compatible alias resolution
for the Vision Alignment GA rollout.

Canonical Naming Convention:
- Tier 1: bob (only one Bob - user interface)
- Tier 2: iam-orchestrator (foreman/scheduler)
- Tier 3: iam-{function} (specialists: iam-compliance, iam-triage, etc.)

This module supports a one-release compatibility window where old IDs
(iam_adk, iam_senior_adk_devops_lead) continue to work via aliases
but generate deprecation warnings.

Usage:
    from agents.shared_contracts.agent_identity import canonicalize, is_canonical

    # Resolve any agent ID to its canonical form
    canonical_id = canonicalize("iam_adk")  # Returns "iam-compliance"

    # Check if an ID is already canonical
    if is_canonical("iam-compliance"):
        ...
"""

import logging
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

logger = logging.getLogger(__name__)


class AgentTier(Enum):
    """Agent hierarchy tiers in Bob's Brain architecture."""

    TIER_1_UI = 1  # User interface (Bob)
    TIER_2_ORCHESTRATOR = 2  # Foreman/scheduler
    TIER_3_SPECIALIST = 3  # Function workers


@dataclass(frozen=True)
class AgentDefinition:
    """Canonical agent definition."""

    canonical_id: str
    tier: AgentTier
    description: str
    spiffe_template: str
    old_ids: List[str]  # Previous IDs for alias mapping


# =============================================================================
# CANONICAL AGENT REGISTRY
# =============================================================================

CANONICAL_AGENTS: Dict[str, AgentDefinition] = {
    # Tier 1: User Interface
    "bob": AgentDefinition(
        canonical_id="bob",
        tier=AgentTier.TIER_1_UI,
        description="Conversational AI assistant - user interface layer",
        spiffe_template="spiffe://intent.solutions/agent/bob/{env}/{region}/{version}",
        old_ids=["bob_agent", "bob-agent"],
    ),
    # Tier 2: Orchestrator
    "iam-orchestrator": AgentDefinition(
        canonical_id="iam-orchestrator",
        tier=AgentTier.TIER_2_ORCHESTRATOR,
        description="Foreman agent - workflow orchestration and delegation",
        spiffe_template="spiffe://intent.solutions/agent/iam-orchestrator/{env}/{region}/{version}",
        old_ids=[
            "iam_senior_adk_devops_lead",
            "iam-senior-adk-devops-lead",
            "iam_foreman",
            "iam-foreman",
            "foreman",
        ],
    ),
    # Tier 3: Specialists
    "iam-compliance": AgentDefinition(
        canonical_id="iam-compliance",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="ADK/Vertex pattern analysis and compliance checking",
        spiffe_template="spiffe://intent.solutions/agent/iam-compliance/{env}/{region}/{version}",
        old_ids=["iam_adk", "iam-adk"],
    ),
    "iam-triage": AgentDefinition(
        canonical_id="iam-triage",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Issue decomposition, scoping, and GitHub issue creation",
        spiffe_template="spiffe://intent.solutions/agent/iam-triage/{env}/{region}/{version}",
        old_ids=["iam_issue", "iam-issue"],
    ),
    "iam-planner": AgentDefinition(
        canonical_id="iam-planner",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Fix planning and rollout design",
        spiffe_template="spiffe://intent.solutions/agent/iam-planner/{env}/{region}/{version}",
        old_ids=["iam_fix_plan", "iam-fix-plan"],
    ),
    "iam-engineer": AgentDefinition(
        canonical_id="iam-engineer",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Implementation and coding",
        spiffe_template="spiffe://intent.solutions/agent/iam-engineer/{env}/{region}/{version}",
        old_ids=["iam_fix_impl", "iam-fix-impl"],
    ),
    "iam-qa": AgentDefinition(
        canonical_id="iam-qa",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Testing, verification, and CI/CD validation",
        spiffe_template="spiffe://intent.solutions/agent/iam-qa/{env}/{region}/{version}",
        old_ids=["iam_qa"],  # Already close to canonical
    ),
    "iam-docs": AgentDefinition(
        canonical_id="iam-docs",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Documentation and AAR creation",
        spiffe_template="spiffe://intent.solutions/agent/iam-docs/{env}/{region}/{version}",
        old_ids=["iam_doc", "iam-doc"],
    ),
    "iam-hygiene": AgentDefinition(
        canonical_id="iam-hygiene",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Repository cleanup and tech debt management",
        spiffe_template="spiffe://intent.solutions/agent/iam-hygiene/{env}/{region}/{version}",
        old_ids=["iam_cleanup", "iam-cleanup"],
    ),
    "iam-index": AgentDefinition(
        canonical_id="iam-index",
        tier=AgentTier.TIER_3_SPECIALIST,
        description="Knowledge management, search, and cataloging",
        spiffe_template="spiffe://intent.solutions/agent/iam-index/{env}/{region}/{version}",
        old_ids=["iam_index"],  # Already close to canonical
    ),
}


# =============================================================================
# ALIAS MAP (built from CANONICAL_AGENTS)
# =============================================================================


def _build_alias_map() -> Dict[str, str]:
    """Build reverse lookup from old IDs to canonical IDs."""
    alias_map = {}
    for canonical_id, definition in CANONICAL_AGENTS.items():
        # Map canonical ID to itself
        alias_map[canonical_id] = canonical_id
        # Map all old IDs to canonical
        for old_id in definition.old_ids:
            alias_map[old_id] = canonical_id
    return alias_map


AGENT_ALIASES: Dict[str, str] = _build_alias_map()


# =============================================================================
# DIRECTORY NAME MAPPING
# =============================================================================

# Maps canonical IDs to current directory names in agents/
# This will be updated as directories are renamed
CANONICAL_TO_DIRECTORY: Dict[str, str] = {
    "bob": "bob",
    "iam-orchestrator": "iam_senior_adk_devops_lead",  # Will change to iam_orchestrator
    "iam-compliance": "iam_adk",
    "iam-triage": "iam_issue",
    "iam-planner": "iam_fix_plan",
    "iam-engineer": "iam_fix_impl",
    "iam-qa": "iam_qa",
    "iam-docs": "iam_doc",
    "iam-hygiene": "iam_cleanup",
    "iam-index": "iam_index",
}

# Reverse mapping
DIRECTORY_TO_CANONICAL: Dict[str, str] = {
    v: k for k, v in CANONICAL_TO_DIRECTORY.items()
}


# =============================================================================
# PUBLIC API
# =============================================================================


def canonicalize(agent_id: str, warn: bool = True) -> str:
    """
    Resolve any agent ID to its canonical form.

    Args:
        agent_id: Any agent identifier (canonical, old, or alias)
        warn: If True, emit deprecation warning for non-canonical IDs

    Returns:
        Canonical agent ID

    Raises:
        ValueError: If agent_id is not recognized

    Examples:
        >>> canonicalize("iam_adk")
        'iam-compliance'
        >>> canonicalize("iam-senior-adk-devops-lead")
        'iam-orchestrator'
        >>> canonicalize("iam-compliance")  # Already canonical
        'iam-compliance'
    """
    canonical = AGENT_ALIASES.get(agent_id)

    if canonical is None:
        raise ValueError(
            f"Unknown agent ID: '{agent_id}'. "
            f"Valid canonical IDs: {list(CANONICAL_AGENTS.keys())}"
        )

    # Warn if using deprecated ID
    if warn and agent_id != canonical:
        warning_msg = (
            f"Agent ID '{agent_id}' is deprecated. "
            f"Use canonical ID '{canonical}' instead. "
            f"Aliases will be removed in the next major version."
        )
        warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
        logger.warning(warning_msg)

    return canonical


def is_canonical(agent_id: str) -> bool:
    """
    Check if an agent ID is already in canonical form.

    Args:
        agent_id: Agent identifier to check

    Returns:
        True if the ID is canonical, False otherwise
    """
    return agent_id in CANONICAL_AGENTS


def is_valid(agent_id: str) -> bool:
    """
    Check if an agent ID is valid (canonical or known alias).

    Args:
        agent_id: Agent identifier to check

    Returns:
        True if the ID is valid, False otherwise
    """
    return agent_id in AGENT_ALIASES


def get_definition(agent_id: str) -> AgentDefinition:
    """
    Get the canonical definition for an agent.

    Args:
        agent_id: Any valid agent identifier

    Returns:
        AgentDefinition for the canonical agent

    Raises:
        ValueError: If agent_id is not recognized
    """
    canonical = canonicalize(agent_id, warn=False)
    return CANONICAL_AGENTS[canonical]


def get_directory(agent_id: str) -> str:
    """
    Get the directory name for an agent.

    Args:
        agent_id: Any valid agent identifier

    Returns:
        Directory name under agents/

    Raises:
        ValueError: If agent_id is not recognized
    """
    canonical = canonicalize(agent_id, warn=False)
    return CANONICAL_TO_DIRECTORY[canonical]


def get_spiffe_id(
    agent_id: str, env: str = "dev", region: str = "us-central1", version: str = "0.1.0"
) -> str:
    """
    Generate SPIFFE ID for an agent.

    Args:
        agent_id: Any valid agent identifier
        env: Environment (dev, staging, prod)
        region: GCP region
        version: Agent version

    Returns:
        Formatted SPIFFE ID string
    """
    definition = get_definition(agent_id)
    return definition.spiffe_template.format(env=env, region=region, version=version)


def list_canonical_ids() -> List[str]:
    """Return list of all canonical agent IDs."""
    return list(CANONICAL_AGENTS.keys())


def list_by_tier(tier: AgentTier) -> List[str]:
    """Return list of canonical IDs for a specific tier."""
    return [
        agent_id for agent_id, defn in CANONICAL_AGENTS.items() if defn.tier == tier
    ]


def list_specialists() -> List[str]:
    """Return list of all Tier 3 specialist canonical IDs."""
    return list_by_tier(AgentTier.TIER_3_SPECIALIST)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AGENT_ALIASES",
    "CANONICAL_AGENTS",
    "CANONICAL_TO_DIRECTORY",
    "DIRECTORY_TO_CANONICAL",
    "AgentDefinition",
    "AgentTier",
    "canonicalize",
    "get_definition",
    "get_directory",
    "get_spiffe_id",
    "is_canonical",
    "is_valid",
    "list_by_tier",
    "list_canonical_ids",
    "list_specialists",
]
