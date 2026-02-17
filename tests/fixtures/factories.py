"""
Factory functions for creating test objects with sensible defaults.

All factories accept keyword overrides so tests only specify what they care about.

Usage:
    # Create a mandate with defaults
    mandate = make_mandate()

    # Override specific fields
    mandate = make_mandate(risk_tier="R3", max_iterations=3)

    # Create an A2A task
    task = make_a2a_task(specialist="iam_adk", skill_id="iam_adk.check_adk_compliance")
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def make_mandate(
    mandate_id: str = "test-mandate-001",
    intent: str = "test-intent",
    budget_limit: float = 10.0,
    budget_unit: str = "USD",
    max_iterations: int = 100,
    authorized_specialists: Optional[List[str]] = None,
    risk_tier: str = "R0",
    tool_allowlist: Optional[List[str]] = None,
    data_classification: str = "internal",
    approval_state: str = "auto",
    approver_id: Optional[str] = None,
    approval_timestamp: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    budget_spent: float = 0.0,
    iterations_used: int = 0,
):
    """Create a Mandate instance with sensible test defaults.

    Returns a Mandate dataclass from pipeline_contracts.
    """
    from agents.shared_contracts.pipeline_contracts import Mandate

    if authorized_specialists is None:
        authorized_specialists = ["iam_adk", "iam_issue", "iam_qa"]
    if tool_allowlist is None:
        tool_allowlist = []

    return Mandate(
        mandate_id=mandate_id,
        intent=intent,
        budget_limit=budget_limit,
        budget_unit=budget_unit,
        max_iterations=max_iterations,
        authorized_specialists=authorized_specialists,
        risk_tier=risk_tier,
        tool_allowlist=tool_allowlist,
        data_classification=data_classification,
        approval_state=approval_state,
        approver_id=approver_id,
        approval_timestamp=approval_timestamp,
        expires_at=expires_at,
        budget_spent=budget_spent,
        iterations_used=iterations_used,
    )


def make_mandate_dict(
    expires_in_hours: Optional[float] = 24.0,
    **overrides,
) -> Dict[str, Any]:
    """Create a mandate dict (as it appears in A2ATask.mandate).

    This is the raw dict form before parsing into a Mandate dataclass.
    Useful for testing dispatcher.validate_mandate() and _mandate_from_dict().
    """
    now = datetime.now(timezone.utc)
    expires_at = (
        (now + timedelta(hours=expires_in_hours)).isoformat()
        if expires_in_hours is not None
        else None
    )

    base = {
        "mandate_id": "test-mandate-001",
        "intent": "test-intent",
        "budget_limit": 10.0,
        "budget_unit": "USD",
        "max_iterations": 100,
        "authorized_specialists": ["iam_adk", "iam_issue", "iam_qa"],
        "risk_tier": "R0",
        "tool_allowlist": [],
        "data_classification": "internal",
        "approval_state": "auto",
        "approver_id": None,
        "approval_timestamp": None,
        "expires_at": expires_at,
        "budget_spent": 0.0,
        "iterations_used": 0,
    }
    base.update(overrides)
    return base


def make_a2a_task(
    specialist: str = "iam_adk",
    skill_id: str = "iam_adk.check_adk_compliance",
    payload: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    spiffe_id: Optional[str] = "spiffe://bobs-brain/agent/iam-orchestrator",
    mandate: Optional[Dict[str, Any]] = None,
):
    """Create an A2ATask instance with sensible test defaults."""
    from agents.a2a.types import A2ATask

    if payload is None:
        payload = {"target": "agents/iam_adk", "focus_rules": ["R1", "R5"]}
    if context is None:
        context = {"request_id": "test-req-001", "pipeline_run_id": "test-run-001"}

    return A2ATask(
        specialist=specialist,
        skill_id=skill_id,
        payload=payload,
        context=context,
        spiffe_id=spiffe_id,
        mandate=mandate,
    )


def make_a2a_result(
    status: str = "SUCCESS",
    specialist: str = "iam_adk",
    skill_id: str = "iam_adk.check_adk_compliance",
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    duration_ms: Optional[int] = 150,
    timestamp: Optional[str] = None,
):
    """Create an A2AResult instance with sensible test defaults."""
    from agents.a2a.types import A2AResult

    if result is None and status == "SUCCESS":
        result = {"compliance_status": "COMPLIANT", "violations": []}
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    return A2AResult(
        status=status,
        specialist=specialist,
        skill_id=skill_id,
        result=result,
        error=error,
        duration_ms=duration_ms,
        timestamp=timestamp,
    )


def make_gate_result(
    allowed: bool = True,
    reason: str = "Test gate passed",
    risk_tier: str = "R0",
    gate_name: str = "test_gate",
    blocking_requirement: Optional[str] = None,
):
    """Create a GateResult instance with sensible test defaults."""
    from agents.shared_contracts.policy_gates import GateResult

    return GateResult(
        allowed=allowed,
        reason=reason,
        risk_tier=risk_tier,
        gate_name=gate_name,
        blocking_requirement=blocking_requirement,
    )
