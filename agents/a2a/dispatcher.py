"""
A2A Dispatcher - Local Agent Invocation

This module provides the core dispatcher logic for agent-to-agent communication.
It handles:
- AgentCard discovery and validation
- Skill existence verification
- Local specialist invocation via ADK Runner
- Input/output structural validation
- Canonical agent ID resolution (Phase D)
- Policy gate enforcement (Phase E)

Follows:
- 6767-LAZY: Imports specialists dynamically inside functions
- R7: SPIFFE ID propagation in logs
- AgentCard contracts as source of truth
- 252-DR-STND: Agent Identity Standard (canonical IDs with alias support)
- 254-DR-STND: Policy Gates and Risk Tiers (enterprise controls)
"""

import json
import logging
import os
import importlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from .types import A2ATask, A2AResult, A2AError

logger = logging.getLogger(__name__)

# Repository root for locating agent modules
REPO_ROOT = Path(__file__).parent.parent.parent


# =============================================================================
# CANONICAL ID RESOLUTION (Phase D - Agent Identity Migration)
# =============================================================================

def _resolve_specialist_id(specialist: str) -> tuple[str, str]:
    """
    Resolve any specialist ID to (canonical_id, directory_name).

    Supports both old IDs (iam_adk) and canonical IDs (iam-compliance).
    Emits deprecation warnings for non-canonical IDs.

    Args:
        specialist: Any valid specialist identifier

    Returns:
        Tuple of (canonical_id, directory_name)

    Raises:
        A2AError: If specialist ID is not recognized
    """
    # Import here to avoid circular imports (6767-LAZY)
    try:
        from agents.shared_contracts.agent_identity import (
            canonicalize,
            get_directory,
            is_valid,
        )
    except ImportError:
        # Fallback if agent_identity not available (e.g., during migration)
        logger.debug("agent_identity module not available, using direct mapping")
        directory = SPECIALIST_MODULES.get(specialist, {}).get("directory", specialist)
        return specialist, directory

    if not is_valid(specialist):
        raise A2AError(
            f"Unknown specialist ID: '{specialist}'. Use canonical IDs like "
            f"'iam-compliance', 'iam-triage', etc.",
            specialist=specialist
        )

    canonical_id = canonicalize(specialist, warn=True)
    directory = get_directory(canonical_id)
    return canonical_id, directory


# Specialist agent module mapping using canonical IDs
# Maps canonical_id -> {directory, module_path}
SPECIALIST_MODULES = {
    # Canonical IDs (preferred)
    "iam-compliance": {"directory": "iam_adk", "module": "agents.iam_adk.agent"},
    "iam-triage": {"directory": "iam_issue", "module": "agents.iam_issue.agent"},
    "iam-planner": {"directory": "iam_fix_plan", "module": "agents.iam_fix_plan.agent"},
    "iam-engineer": {"directory": "iam_fix_impl", "module": "agents.iam_fix_impl.agent"},
    "iam-qa": {"directory": "iam_qa", "module": "agents.iam_qa.agent"},
    "iam-docs": {"directory": "iam_doc", "module": "agents.iam_doc.agent"},
    "iam-hygiene": {"directory": "iam_cleanup", "module": "agents.iam_cleanup.agent"},
    "iam-index": {"directory": "iam_index", "module": "agents.iam_index.agent"},

    # Legacy IDs (deprecated, for backwards compatibility)
    "iam_adk": {"directory": "iam_adk", "module": "agents.iam_adk.agent"},
    "iam_issue": {"directory": "iam_issue", "module": "agents.iam_issue.agent"},
    "iam_fix_plan": {"directory": "iam_fix_plan", "module": "agents.iam_fix_plan.agent"},
    "iam_fix_impl": {"directory": "iam_fix_impl", "module": "agents.iam_fix_impl.agent"},
    "iam_qa": {"directory": "iam_qa", "module": "agents.iam_qa.agent"},
    "iam_doc": {"directory": "iam_doc", "module": "agents.iam_doc.agent"},
    "iam_cleanup": {"directory": "iam_cleanup", "module": "agents.iam_cleanup.agent"},
    "iam_index": {"directory": "iam_index", "module": "agents.iam_index.agent"},
}


def load_agentcard(specialist: str) -> Dict[str, Any]:
    """
    Load AgentCard JSON for a specialist.

    Args:
        specialist: Specialist name (canonical or legacy, e.g., "iam-compliance" or "iam_adk")

    Returns:
        AgentCard dictionary

    Raises:
        A2AError: If AgentCard file not found or invalid JSON
    """
    # Resolve to directory name (handles both canonical and legacy IDs)
    spec_info = SPECIALIST_MODULES.get(specialist)
    if spec_info:
        directory = spec_info["directory"]
    else:
        # Try canonical resolution
        try:
            _, directory = _resolve_specialist_id(specialist)
        except A2AError:
            directory = specialist  # Fall back to direct use

    agentcard_path = REPO_ROOT / "agents" / directory / ".well-known" / "agent-card.json"

    if not agentcard_path.exists():
        raise A2AError(
            f"AgentCard not found for specialist '{specialist}' at {agentcard_path}",
            specialist=specialist
        )

    try:
        with open(agentcard_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise A2AError(
            f"Invalid AgentCard JSON for specialist '{specialist}': {e}",
            specialist=specialist
        )


def validate_skill_exists(agentcard: Dict[str, Any], skill_id: str, specialist: str) -> Dict[str, Any]:
    """
    Verify that a skill exists in the AgentCard.

    Args:
        agentcard: AgentCard dictionary
        skill_id: Full skill ID (e.g., "iam_adk.check_adk_compliance")
        specialist: Specialist name for error messages

    Returns:
        Skill definition dictionary

    Raises:
        A2AError: If skill not found
    """
    skills = agentcard.get("skills", [])

    for skill in skills:
        # AgentCard uses "id" field for skill identifier
        if skill.get("id") == skill_id:
            return skill

    available_skills = [s.get("id") for s in skills]
    raise A2AError(
        f"Skill '{skill_id}' not found in AgentCard for '{specialist}'. Available skills: {available_skills}",
        specialist=specialist,
        skill_id=skill_id
    )


def validate_input_structure(payload: Dict[str, Any], input_schema: Dict[str, Any], skill_id: str) -> None:
    """
    Perform lightweight structural validation of input payload.

    This is NOT full JSON Schema validation (future phase).
    Just checks that required fields are present.

    Args:
        payload: Input data from A2ATask
        input_schema: Skill's input_schema from AgentCard
        skill_id: Skill ID for error messages

    Raises:
        A2AError: If required fields are missing
    """
    required_fields = input_schema.get("required", [])

    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        raise A2AError(
            f"Input payload missing required fields for skill '{skill_id}': {missing_fields}. "
            f"Provided: {list(payload.keys())}"
        )


def invoke_specialist_local(specialist: str, task: A2ATask) -> Dict[str, Any]:
    """
    Invoke specialist agent locally using ADK Runner.

    This function:
    1. Dynamically imports the specialist's agent module
    2. Calls create_agent() to instantiate the agent (lazy loading)
    3. Runs the agent with the task payload
    4. Returns the result

    Args:
        specialist: Specialist name (canonical or legacy, e.g., "iam-compliance" or "iam_adk")
        task: A2ATask with payload and context

    Returns:
        Agent output dictionary

    Raises:
        A2AError: If specialist module not found or agent execution fails
    """
    # Get module info (handles both canonical and legacy IDs)
    spec_info = SPECIALIST_MODULES.get(specialist)

    if not spec_info:
        # Try canonical resolution
        try:
            canonical_id, directory = _resolve_specialist_id(specialist)
            spec_info = SPECIALIST_MODULES.get(canonical_id)
        except A2AError:
            pass

    if not spec_info:
        # List canonical IDs in error message
        canonical_ids = [k for k in SPECIALIST_MODULES.keys() if "-" in k]
        raise A2AError(
            f"Specialist '{specialist}' not registered. "
            f"Use canonical IDs: {canonical_ids}",
            specialist=specialist
        )

    module_path = spec_info["module"]

    # Phase 18: Check ADK availability first before importing specialist module
    # This prevents ImportError when specialist modules have top-level google.adk imports
    try:
        from google.adk.runners import InMemoryRunner  # noqa: F401
        adk_available = True
    except ImportError:
        adk_available = False
        logger.debug(
            f"google.adk not available, using mock execution for {specialist}.{task.skill_id}"
        )

    try:
        # Dynamic import (6767-LAZY: happens at runtime, not module import)
        # Note: Specialist modules may have top-level google.adk imports
        # If ADK is not available, this will fail - handle gracefully
        module = importlib.import_module(module_path)

        if not hasattr(module, "create_agent"):
            raise A2AError(
                f"Specialist module '{module_path}' missing create_agent() function",
                specialist=specialist
            )

        if adk_available:
            # Phase H: Real ADK execution requires async run_debug() pattern
            # For now, fall back to mock execution since async integration is incomplete
            # TODO: Phase H+ - Implement async A2A dispatch with InMemoryRunner.run_debug()
            logger.info(
                f"A2A: Mock execution of {specialist}.{task.skill_id} (real ADK dispatch pending Phase H+)",
                extra={"specialist": specialist, "skill_id": task.skill_id}
            )

            # Verify agent can be instantiated (validates module structure)
            agent = module.create_agent()
            logger.info(
                f"A2A: Agent '{specialist}' instantiated successfully",
                extra={"specialist": specialist, "agent_type": type(agent).__name__}
            )

            # Return mock result with payload echo (simulates successful execution)
            return {
                "status": "SUCCESS",
                "message": f"Mock execution of {task.skill_id} (ADK async dispatch pending)",
                "payload_echo": task.payload,
                "mock": True,
                "phase": "Phase H - pending async integration"
            }

        else:
            # Mock fallback path (when ADK not installed)
            logger.info(
                f"A2A: Mock execution of {specialist}.{task.skill_id} (google.adk not available)",
                extra={"specialist": specialist, "skill_id": task.skill_id}
            )

            # Return mock result structure
            return {
                "status": "SUCCESS",
                "message": f"Mock execution of {task.skill_id} (ADK not installed)",
                "payload_echo": task.payload,
                "mock": True  # Flag to indicate this is mock data
            }

    except ImportError as e:
        # Phase 18: If module import fails due to missing google.adk, fall back to mock
        if "google.adk" in str(e) and not adk_available:
            logger.info(
                f"A2A: Specialist module '{module_path}' requires google.adk (not available). "
                f"Using mock execution for {specialist}.{task.skill_id}",
                extra={"specialist": specialist, "skill_id": task.skill_id}
            )

            # Return mock result
            return {
                "status": "SUCCESS",
                "message": f"Mock execution of {task.skill_id} (specialist module requires ADK)",
                "payload_echo": task.payload,
                "mock": True
            }
        else:
            # Other import errors are real problems
            raise A2AError(
                f"Failed to import specialist module '{module_path}': {e}",
                specialist=specialist
            )
    except Exception as e:
        raise A2AError(
            f"Failed to invoke specialist '{specialist}': {e}",
            specialist=specialist,
            skill_id=task.skill_id
        )


def validate_mandate(task: A2ATask) -> None:
    """
    Validate mandate authorization before specialist invocation.

    Converts the mandate dict to a Mandate object and uses its validation methods.
    Also runs policy gate checks for enterprise controls (Phase E).

    Checks:
    - Mandate is not expired
    - Budget is not exhausted
    - Iterations limit not exceeded
    - Specialist is authorized
    - Risk tier requirements met (R0-R4)
    - Approval state valid for R3/R4 operations

    Args:
        task: A2ATask with optional mandate

    Raises:
        A2AError: If mandate validation fails
    """
    # Import here to avoid circular imports (6767-LAZY pattern)
    from agents.shared_contracts.pipeline_contracts import Mandate
    from agents.shared_contracts.policy_gates import PolicyGate, GateResult
    from datetime import datetime, timezone

    # Determine risk tier from task context or mandate
    risk_tier = "R0"  # Default: no restrictions
    mandate = None

    if task.mandate:
        # Convert dict to Mandate object
        mandate_dict = task.mandate
        try:
            # Parse expires_at if present
            expires_at = None
            if mandate_dict.get("expires_at"):
                expires_str = mandate_dict["expires_at"]
                expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))

            # Parse approval_timestamp if present
            approval_timestamp = None
            if mandate_dict.get("approval_timestamp"):
                approval_str = mandate_dict["approval_timestamp"]
                approval_timestamp = datetime.fromisoformat(approval_str.replace("Z", "+00:00"))

            mandate = Mandate(
                mandate_id=mandate_dict.get("mandate_id", "unknown"),
                intent=mandate_dict.get("intent", ""),
                budget_limit=mandate_dict.get("budget_limit", 0.0),
                budget_unit=mandate_dict.get("budget_unit", "USD"),
                max_iterations=mandate_dict.get("max_iterations", 100),
                authorized_specialists=mandate_dict.get("authorized_specialists", []),
                # Enterprise controls (Phase E)
                risk_tier=mandate_dict.get("risk_tier", "R0"),
                tool_allowlist=mandate_dict.get("tool_allowlist", []),
                data_classification=mandate_dict.get("data_classification", "internal"),
                approval_state=mandate_dict.get("approval_state", "auto"),
                approver_id=mandate_dict.get("approver_id"),
                approval_timestamp=approval_timestamp,
                expires_at=expires_at,
                budget_spent=mandate_dict.get("budget_spent", 0.0),
                iterations_used=mandate_dict.get("iterations_used", 0),
            )
            risk_tier = mandate.risk_tier
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse mandate: {e}, skipping validation")
            return

    # Run policy gate preflight checks (Phase E)
    gate_results = PolicyGate.preflight_check(
        specialist_name=task.specialist,
        risk_tier=risk_tier,
        mandate=mandate
    )

    # Check for any blocking gates
    blocking = PolicyGate.get_blocking_gates(gate_results)
    if blocking:
        # Build detailed error message from blocking gates
        blocks = [f"{g.gate_name}: {g.reason}" for g in blocking]
        raise A2AError(
            f"Policy gate check failed for specialist '{task.specialist}': {'; '.join(blocks)}",
            specialist=task.specialist
        )

    # Log successful gate passage
    logger.debug(
        f"Policy gates passed for {task.specialist} (risk_tier={risk_tier})",
        extra={"specialist": task.specialist, "risk_tier": risk_tier}
    )


def call_specialist(task: A2ATask) -> A2AResult:
    """
    Main entry point for A2A delegation.

    This function orchestrates the complete A2A flow:
    1. Validate mandate authorization (Phase B)
    2. Load AgentCard for specialist
    3. Validate skill exists
    4. Validate input structure (lightweight)
    5. Invoke specialist locally
    6. Return structured result

    Args:
        task: A2ATask with specialist, skill_id, payload, context

    Returns:
        A2AResult with status, result data, and metadata

    Raises:
        A2AError: On any validation or execution failure
    """
    import time
    start_time = time.time()

    try:
        # Step 1: Validate mandate authorization (Phase B)
        validate_mandate(task)

        # Step 2: Load AgentCard
        agentcard = load_agentcard(task.specialist)

        # Step 3: Validate skill exists
        skill = validate_skill_exists(agentcard, task.skill_id, task.specialist)

        # Step 4: Validate input structure
        input_schema = skill.get("input_schema", {})
        validate_input_structure(task.payload, input_schema, task.skill_id)

        # Step 5: Invoke specialist
        result_data = invoke_specialist_local(task.specialist, task)

        # Step 6: Build success result
        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"A2A: Successfully invoked {task.specialist}.{task.skill_id} in {duration_ms}ms",
            extra={
                "specialist": task.specialist,
                "skill_id": task.skill_id,
                "duration_ms": duration_ms,
                "caller_spiffe": task.spiffe_id
            }
        )

        return A2AResult(
            status="SUCCESS",
            specialist=task.specialist,
            skill_id=task.skill_id,
            result=result_data,
            duration_ms=duration_ms
        )

    except A2AError:
        # Re-raise A2A errors as-is
        raise

    except Exception as e:
        # Wrap unexpected errors
        duration_ms = int((time.time() - start_time) * 1000)

        logger.error(
            f"A2A: Unexpected error invoking {task.specialist}.{task.skill_id}: {e}",
            extra={
                "specialist": task.specialist,
                "skill_id": task.skill_id,
                "error": str(e)
            },
            exc_info=True
        )

        return A2AResult(
            status="FAILED",
            specialist=task.specialist,
            skill_id=task.skill_id,
            error=str(e),
            duration_ms=duration_ms
        )


def discover_specialists() -> List[Dict[str, Any]]:
    """
    Discover all available specialists and their capabilities.

    Returns a list of specialist metadata including:
    - canonical_id (preferred ID)
    - name (alias for canonical_id)
    - capabilities (from AgentCard)
    - skills (list of skill IDs)

    Returns:
        List of specialist metadata dictionaries

    Raises:
        A2AError: If any AgentCard is missing or invalid
    """
    specialists = []
    seen_directories = set()

    # Only iterate over canonical IDs (those with hyphens) to avoid duplicates
    for specialist_id, spec_info in SPECIALIST_MODULES.items():
        # Skip legacy IDs (use canonical only)
        if "_" in specialist_id and specialist_id != "iam_qa":
            continue

        directory = spec_info["directory"]
        if directory in seen_directories:
            continue
        seen_directories.add(directory)

        try:
            agentcard = load_agentcard(specialist_id)

            specialists.append({
                "canonical_id": specialist_id,
                "name": specialist_id,  # Alias for backwards compatibility
                "directory": directory,
                "capabilities": agentcard.get("capabilities", []),
                "skills": [skill.get("skill_id") for skill in agentcard.get("skills", [])],
                "description": agentcard.get("description", "").split("\n")[0],  # First line only
            })

        except A2AError as e:
            logger.warning(f"Failed to discover specialist '{specialist_id}': {e}")
            # Continue discovering others, don't fail entire discovery

    return specialists
