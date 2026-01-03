"""
Delegation tool for invoking iam-* specialist agents.

This tool allows the foreman to delegate tasks to specialist agents
via Agent-to-Agent (A2A) protocol using AgentCard contracts.

Follows:
- 6767-LAZY: A2A dispatcher imported inside functions
- AgentCard contracts: Uses skill_id and payload from AgentCards
- R7: SPIFFE ID propagation in delegation

Phase 17: Real A2A wiring with local specialist invocation.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# R7: Get foreman's SPIFFE ID for propagation
FOREMAN_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0"
)


def delegate_to_specialist(
    specialist: str,
    skill_id: str,
    payload: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Delegate a task to a specialist agent via A2A protocol.

    Phase 17: Real A2A wiring using AgentCard contracts and local invocation.

    Args:
        specialist: Specialist agent name (e.g., "iam_adk", "iam_issue")
        skill_id: Full skill identifier from AgentCard (e.g., "iam_adk.check_adk_compliance")
        payload: Skill input matching the skill's input_schema
        context: Optional context dict (request_id, pipeline_run_id, etc.)

    Returns:
        Dict containing:
        - specialist: Name of the agent that handled the task
        - status: "SUCCESS", "FAILED", or "PARTIAL"
        - result: The specialist's output data
        - error: Error message if failed (optional)
        - duration_ms: Execution time in milliseconds
        - timestamp: ISO 8601 completion timestamp

    Example:
        >>> result = delegate_to_specialist(
        ...     specialist="iam_adk",
        ...     skill_id="iam_adk.check_adk_compliance",
        ...     payload={"target": "agents/bob/agent.py", "focus_rules": ["R1", "R5"]},
        ...     context={"request_id": "req_123"}
        ... )

    Raises:
        A2AError: If specialist/skill not found or validation fails
    """
    # 6767-LAZY: Import A2A dispatcher at runtime, not module import time
    from agents.a2a import A2ATask, call_specialist, A2AError

    logger.info(
        f"A2A: Delegating to {specialist}.{skill_id}",
        extra={
            "specialist": specialist,
            "skill_id": skill_id,
            "foreman_spiffe": FOREMAN_SPIFFE_ID
        }
    )

    try:
        # Build A2A task envelope
        task = A2ATask(
            specialist=specialist,
            skill_id=skill_id,
            payload=payload,
            context=context or {},
            spiffe_id=FOREMAN_SPIFFE_ID  # R7: Propagate foreman's SPIFFE ID
        )

        # Invoke specialist via A2A dispatcher
        result = call_specialist(task)

        # Convert A2AResult to foreman's expected format
        return {
            "specialist": result.specialist,
            "status": result.status.lower(),  # SUCCESS → success for backward compat
            "result": result.result,
            "error": result.error,
            "metadata": {
                "skill_id": result.skill_id,
                "duration_ms": result.duration_ms,
                "timestamp": result.timestamp,
                "a2a_protocol": True,
                "phase": "Phase 17 - Real A2A Wiring"
            }
        }

    except A2AError as e:
        logger.error(
            f"A2A: Delegation failed: {e}",
            extra={
                "specialist": specialist,
                "skill_id": skill_id,
                "error": str(e)
            }
        )

        return {
            "specialist": specialist,
            "status": "failure",
            "result": None,
            "error": str(e),
            "metadata": {
                "skill_id": skill_id,
                "a2a_error": True,
                "phase": "Phase 17 - Real A2A Wiring"
            }
        }


def delegate_to_multiple(
    delegations: List[Dict[str, Any]],
    execution_mode: str = "sequential"
) -> List[Dict[str, Any]]:
    """
    Delegate tasks to multiple specialists.

    Phase 17: Sequential execution only (parallel is future phase).

    Args:
        delegations: List of delegation configurations, each containing:
            - specialist: Specialist name (e.g., "iam_adk")
            - skill_id: Full skill ID (e.g., "iam_adk.check_adk_compliance")
            - payload: Skill input data
            - context: Optional context (optional)
        execution_mode: "sequential" or "parallel" (only sequential supported in Phase 17)

    Returns:
        List of results from each specialist

    Example:
        >>> results = delegate_to_multiple([
        ...     {
        ...         "specialist": "iam_adk",
        ...         "skill_id": "iam_adk.check_adk_compliance",
        ...         "payload": {"target": "agents/bob/agent.py"}
        ...     },
        ...     {
        ...         "specialist": "iam_doc",
        ...         "skill_id": "iam_doc.generate_aar",
        ...         "payload": {"phase_info": {...}}
        ...     }
        ... ])
    """
    if execution_mode == "parallel":
        logger.warning("Parallel execution not yet implemented in Phase 17; using sequential")

    results = []

    for delegation in delegations:
        result = delegate_to_specialist(
            specialist=delegation["specialist"],
            skill_id=delegation["skill_id"],
            payload=delegation["payload"],
            context=delegation.get("context")
        )
        results.append(result)

    return results


def check_specialist_availability(specialist: str) -> bool:
    """
    Check if a specialist agent is available via AgentCard discovery.

    Phase 17: Uses A2A dispatcher to load AgentCard.

    Args:
        specialist: Name of the specialist agent

    Returns:
        True if specialist is available, False otherwise
    """
    # 6767-LAZY: Import A2A at runtime
    from agents.a2a import A2AError

    try:
        # Try to load AgentCard - if it exists and is valid, specialist is available
        from agents.a2a.dispatcher import load_agentcard
        load_agentcard(specialist)
        return True
    except A2AError:
        logger.debug(f"Specialist '{specialist}' not available: AgentCard not found or invalid")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking specialist '{specialist}': {e}")
        return False


def get_specialist_capabilities(specialist: str) -> Dict[str, Any]:
    """
    Get the capabilities of a specialist agent from its AgentCard.

    Phase 17: Reads directly from AgentCard instead of hardcoded dict.

    Args:
        specialist: Name of the specialist agent

    Returns:
        Dictionary describing the specialist's capabilities
    """
    # 6767-LAZY: Import A2A at runtime
    from agents.a2a import A2AError
    from agents.a2a.dispatcher import load_agentcard

    try:
        agentcard = load_agentcard(specialist)

        # Extract capabilities from AgentCard
        return {
            "description": agentcard.get("description", "").split("\n")[0],  # First line only
            "capabilities": agentcard.get("capabilities", []),
            "skills": [skill.get("skill_id") for skill in agentcard.get("skills", [])],
            "agentcard_version": agentcard.get("version", "unknown"),
            "spiffe_id": agentcard.get("spiffe_id", ""),
        }

    except A2AError as e:
        logger.warning(f"Failed to load capabilities for specialist '{specialist}': {e}")
        return {
            "description": f"Unknown specialist '{specialist}'",
            "capabilities": [],
            "skills": [],
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error loading capabilities for '{specialist}': {e}")
        return {
            "description": f"Error loading specialist '{specialist}'",
            "capabilities": [],
            "skills": [],
            "error": str(e)
        }