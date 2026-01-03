"""
A2A Dispatcher - Local Agent Invocation

This module provides the core dispatcher logic for agent-to-agent communication.
It handles:
- AgentCard discovery and validation
- Skill existence verification
- Local specialist invocation via ADK Runner
- Input/output structural validation

Follows:
- 6767-LAZY: Imports specialists dynamically inside functions
- R7: SPIFFE ID propagation in logs
- AgentCard contracts as source of truth
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

# Specialist agent module mapping (agent_name -> module_path)
SPECIALIST_MODULES = {
    "iam_adk": "agents.iam_adk.agent",
    "iam_issue": "agents.iam_issue.agent",
    "iam_fix_plan": "agents.iam_fix_plan.agent",
    "iam_fix_impl": "agents.iam_fix_impl.agent",
    "iam_qa": "agents.iam_qa.agent",
    "iam_doc": "agents.iam_doc.agent",
    "iam_cleanup": "agents.iam_cleanup.agent",
    "iam_index": "agents.iam_index.agent",
}


def load_agentcard(specialist: str) -> Dict[str, Any]:
    """
    Load AgentCard JSON for a specialist.

    Args:
        specialist: Specialist name (e.g., "iam_adk")

    Returns:
        AgentCard dictionary

    Raises:
        A2AError: If AgentCard file not found or invalid JSON
    """
    agentcard_path = REPO_ROOT / "agents" / specialist / ".well-known" / "agent-card.json"

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
        if skill.get("skill_id") == skill_id:
            return skill

    available_skills = [s.get("skill_id") for s in skills]
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
        specialist: Specialist name (e.g., "iam_adk")
        task: A2ATask with payload and context

    Returns:
        Agent output dictionary

    Raises:
        A2AError: If specialist module not found or agent execution fails
    """
    module_path = SPECIALIST_MODULES.get(specialist)

    if not module_path:
        raise A2AError(
            f"Specialist '{specialist}' not registered in SPECIALIST_MODULES. "
            f"Available: {list(SPECIALIST_MODULES.keys())}",
            specialist=specialist
        )

    # Phase 18: Check ADK availability first before importing specialist module
    # This prevents ImportError when specialist modules have top-level google.adk imports
    try:
        from google.adk import Runner
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
            # Real execution path (Phase 18)
            logger.info(
                f"A2A: Invoking {specialist}.{task.skill_id} via ADK Runner",
                extra={"specialist": specialist, "skill_id": task.skill_id}
            )

            # Instantiate agent (lazy loading)
            agent = module.create_agent()

            # Create Runner for single-turn execution
            runner = Runner(agent)

            # Execute agent with task payload
            # The payload is the input to the skill, formatted as a prompt or structured input
            # depending on the skill's expectations
            result = runner.run(json.dumps(task.payload))

            # Parse and structure the result
            return {
                "status": "SUCCESS",
                "message": f"Executed {task.skill_id} via ADK Runner",
                "result": result,  # Raw result from Runner
                "payload": task.payload
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

    Checks:
    - Mandate is not expired
    - Budget is not exhausted
    - Iterations limit not exceeded
    - Specialist is authorized

    Args:
        task: A2ATask with optional mandate

    Raises:
        A2AError: If mandate validation fails
    """
    if not task.mandate:
        return  # No mandate = no restrictions

    # Import here to avoid circular imports (6767-LAZY pattern)
    from agents.shared_contracts.pipeline_contracts import Mandate
    from datetime import datetime, timezone

    # Convert dict to Mandate object
    mandate_dict = task.mandate
    try:
        # Parse expires_at if present
        expires_at = None
        if mandate_dict.get("expires_at"):
            expires_str = mandate_dict["expires_at"]
            expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))

        mandate = Mandate(
            mandate_id=mandate_dict.get("mandate_id", "unknown"),
            intent=mandate_dict.get("intent", ""),
            budget_limit=mandate_dict.get("budget_limit", 0.0),
            budget_unit=mandate_dict.get("budget_unit", "USD"),
            max_iterations=mandate_dict.get("max_iterations", 100),
            authorized_specialists=mandate_dict.get("authorized_specialists", []),
            expires_at=expires_at,
            budget_spent=mandate_dict.get("budget_spent", 0.0),
            iterations_used=mandate_dict.get("iterations_used", 0),
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse mandate: {e}, skipping validation")
        return

    # Use Mandate class methods for validation
    if mandate.is_expired():
        raise A2AError(
            f"Mandate '{mandate.mandate_id}' has expired",
            specialist=task.specialist
        )

    if mandate.is_budget_exhausted():
        raise A2AError(
            f"Budget exhausted for mandate '{mandate.mandate_id}': "
            f"spent {mandate.budget_spent} >= limit {mandate.budget_limit}",
            specialist=task.specialist
        )

    if mandate.is_iterations_exhausted():
        raise A2AError(
            f"Iterations exhausted for mandate '{mandate.mandate_id}': "
            f"used {mandate.iterations_used} >= limit {mandate.max_iterations}",
            specialist=task.specialist
        )

    if not mandate.can_invoke_specialist(task.specialist):
        raise A2AError(
            f"Specialist '{task.specialist}' not authorized by mandate '{mandate.mandate_id}'. "
            f"Authorized: {mandate.authorized_specialists}",
            specialist=task.specialist
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
    - name
    - capabilities (from AgentCard)
    - skills (list of skill IDs)

    Returns:
        List of specialist metadata dictionaries

    Raises:
        A2AError: If any AgentCard is missing or invalid
    """
    specialists = []

    for specialist_name in SPECIALIST_MODULES.keys():
        try:
            agentcard = load_agentcard(specialist_name)

            specialists.append({
                "name": specialist_name,
                "capabilities": agentcard.get("capabilities", []),
                "skills": [skill.get("skill_id") for skill in agentcard.get("skills", [])],
                "description": agentcard.get("description", "").split("\n")[0],  # First line only
            })

        except A2AError as e:
            logger.warning(f"Failed to discover specialist '{specialist_name}': {e}")
            # Continue discovering others, don't fail entire discovery

    return specialists
