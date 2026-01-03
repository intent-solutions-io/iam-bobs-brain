"""
Human-in-the-Loop Approval Tool (Phase P4).

Implements Google's Human-in-the-Loop pattern for high-risk actions.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/

This tool enables agents to pause and request human approval before
executing high-risk operations like production deployments, destructive
changes, or security-sensitive actions.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from agents.iam_contracts import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    RiskLevel,
)

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
APPROVAL_TIMEOUT_SECONDS = 300  # 5 minutes default
POLL_INTERVAL_SECONDS = 2  # How often to check for approval response


# In-memory storage for approval requests (production would use Firestore)
_pending_approvals: Dict[str, ApprovalRequest] = {}
_approval_responses: Dict[str, ApprovalResponse] = {}


def classify_risk_level(
    action: str,
    files_affected: list[str],
    context: Dict[str, Any],
) -> RiskLevel:
    """
    Classify risk level based on action and context.

    Risk Classification Guidelines:
    - LOW: Documentation updates, test additions, local dev changes
    - MEDIUM: Code refactoring, non-critical bug fixes, config changes
    - HIGH: Production deployments, database migrations, security changes
    - CRITICAL: Infrastructure changes, data deletion, auth system changes

    Args:
        action: Description of the action being performed
        files_affected: List of file paths being modified
        context: Additional context about the operation

    Returns:
        RiskLevel classification
    """
    action_lower = action.lower()

    # CRITICAL indicators
    critical_keywords = [
        "delete",
        "destroy",
        "production",
        "database migration",
        "infrastructure",
        "terraform apply",
        "authentication",
        "authorization",
        "secrets",
        "credentials",
    ]
    if any(kw in action_lower for kw in critical_keywords):
        return RiskLevel.CRITICAL

    # HIGH indicators
    high_keywords = [
        "deploy",
        "release",
        "migration",
        "security",
        "permission",
        "agent engine",
        "cloud run",
    ]
    high_paths = ["infra/", "terraform/", "service/", ".github/workflows/"]
    if any(kw in action_lower for kw in high_keywords):
        return RiskLevel.HIGH
    if any(any(hp in f for hp in high_paths) for f in files_affected):
        return RiskLevel.HIGH

    # MEDIUM indicators
    medium_keywords = [
        "refactor",
        "update",
        "modify",
        "change",
        "fix",
        "bug",
    ]
    medium_paths = ["agents/", "config/"]
    if any(kw in action_lower for kw in medium_keywords):
        return RiskLevel.MEDIUM
    if any(any(mp in f for mp in medium_paths) for f in files_affected):
        return RiskLevel.MEDIUM

    # Default to LOW for documentation, tests, etc.
    return RiskLevel.LOW


def create_approval_request(
    action: str,
    description: str,
    risk_level: RiskLevel,
    requested_by: str,
    context: Optional[Dict[str, Any]] = None,
    files_affected: Optional[list[str]] = None,
    estimated_impact: str = "",
    timeout_seconds: int = APPROVAL_TIMEOUT_SECONDS,
) -> ApprovalRequest:
    """
    Create an approval request for human review.

    Args:
        action: Short name of the action (e.g., "deploy-to-production")
        description: Detailed description of what will be done
        risk_level: Risk classification of the action
        requested_by: SPIFFE ID or agent name requesting approval
        context: Additional context for the approver
        files_affected: List of files that will be modified
        estimated_impact: Human-readable impact description
        timeout_seconds: How long to wait for approval

    Returns:
        ApprovalRequest object
    """
    request = ApprovalRequest(
        request_id=str(uuid.uuid4()),
        action=action,
        description=description,
        risk_level=risk_level,
        context=context or {},
        requested_by=requested_by,
        requested_at=datetime.utcnow(),
        timeout_seconds=timeout_seconds,
        files_affected=files_affected or [],
        estimated_impact=estimated_impact,
    )

    logger.info(
        f"Created approval request {request.request_id} for action '{action}'",
        extra={
            "request_id": request.request_id,
            "risk_level": risk_level.value,
            "requested_by": requested_by,
        },
    )

    return request


def requires_approval(risk_level: RiskLevel) -> bool:
    """
    Check if a risk level requires human approval.

    LOW and MEDIUM risk actions auto-approve.
    HIGH and CRITICAL risk actions require human approval.

    Args:
        risk_level: The risk classification to check

    Returns:
        True if human approval is required
    """
    return RiskLevel.requires_approval(risk_level)


async def request_approval(request: ApprovalRequest) -> ApprovalResponse:
    """
    Request human approval for an action.

    This is the main entry point for the Human-in-the-Loop pattern.
    For LOW/MEDIUM risk, auto-approves immediately.
    For HIGH/CRITICAL risk, sends to approval queue and waits.

    Args:
        request: The approval request

    Returns:
        ApprovalResponse with status and optional reason
    """
    # Auto-approve LOW and MEDIUM risk actions
    if not requires_approval(request.risk_level):
        response = ApprovalResponse(
            request_id=request.request_id,
            status=ApprovalStatus.AUTO_APPROVED,
            approved=True,
            reason=f"Auto-approved ({request.risk_level.value} risk)",
            approved_by="system",
            approved_at=datetime.utcnow(),
        )
        logger.info(
            f"Auto-approved request {request.request_id}",
            extra={
                "request_id": request.request_id,
                "risk_level": request.risk_level.value,
            },
        )
        return response

    # HIGH/CRITICAL: Queue for human approval
    _pending_approvals[request.request_id] = request

    logger.info(
        f"Queued request {request.request_id} for human approval",
        extra={
            "request_id": request.request_id,
            "risk_level": request.risk_level.value,
            "timeout_seconds": request.timeout_seconds,
        },
    )

    # Send notification (Slack, etc.)
    await _send_approval_notification(request)

    # Wait for approval with timeout
    try:
        response = await asyncio.wait_for(
            _poll_for_approval(request.request_id),
            timeout=request.timeout_seconds,
        )
        return response
    except asyncio.TimeoutError:
        # Timeout - treat as rejection
        response = ApprovalResponse(
            request_id=request.request_id,
            status=ApprovalStatus.TIMEOUT,
            approved=False,
            reason=f"Approval timeout - no response within {request.timeout_seconds} seconds",
            approved_at=datetime.utcnow(),
        )
        _cleanup_request(request.request_id)
        logger.warning(
            f"Approval request {request.request_id} timed out",
            extra={"request_id": request.request_id},
        )
        return response


async def _send_approval_notification(request: ApprovalRequest) -> None:
    """
    Send notification to Slack for human approval.

    In production, this would call the Slack API to send an
    interactive message with Approve/Reject buttons.
    """
    logger.info(
        f"Sending approval notification for {request.request_id}",
        extra={
            "request_id": request.request_id,
            "action": request.action,
        },
    )

    # TODO: Implement actual Slack notification
    # This would use the Slack Block Kit to create an interactive message:
    # - Action description
    # - Risk level badge
    # - Files affected
    # - Approve/Reject buttons
    # - Timeout countdown

    # Placeholder for Slack integration
    # await slack_client.send_interactive_message(
    #     channel="#approvals",
    #     blocks=format_approval_blocks(request),
    #     callback_id=request.request_id,
    # )


async def _poll_for_approval(request_id: str) -> ApprovalResponse:
    """
    Poll for approval response.

    Waits until a human provides approval or rejection via
    the approval endpoint (e.g., Slack button callback).
    """
    while True:
        if request_id in _approval_responses:
            response = _approval_responses[request_id]
            _cleanup_request(request_id)
            return response
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def _cleanup_request(request_id: str) -> None:
    """Clean up pending approval request."""
    _pending_approvals.pop(request_id, None)
    # Keep response for audit trail (in production, archive to Firestore)


def handle_approval_callback(
    request_id: str,
    approved: bool,
    approved_by: str,
    reason: str = "",
    conditions: Optional[list[str]] = None,
) -> ApprovalResponse:
    """
    Handle approval callback from Slack or other approval UI.

    This is called when a human clicks Approve or Reject.

    Args:
        request_id: The approval request ID
        approved: Whether the action was approved
        approved_by: Who approved/rejected (user ID or email)
        reason: Optional reason for the decision
        conditions: Optional conditions on the approval

    Returns:
        ApprovalResponse
    """
    if request_id not in _pending_approvals:
        logger.warning(
            f"Approval callback for unknown request {request_id}",
            extra={"request_id": request_id},
        )
        return ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.REJECTED,
            approved=False,
            reason="Request not found or already processed",
        )

    status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
    response = ApprovalResponse(
        request_id=request_id,
        status=status,
        approved=approved,
        reason=reason,
        approved_by=approved_by,
        approved_at=datetime.utcnow(),
        conditions=conditions or [],
    )

    _approval_responses[request_id] = response

    logger.info(
        f"Approval callback received for {request_id}: {status.value}",
        extra={
            "request_id": request_id,
            "status": status.value,
            "approved_by": approved_by,
        },
    )

    return response


def get_pending_approvals() -> list[ApprovalRequest]:
    """
    Get all pending approval requests.

    Used by admin UI or Slack to show outstanding approvals.
    """
    return list(_pending_approvals.values())


def get_approval_status(request_id: str) -> Optional[ApprovalResponse]:
    """
    Check the status of an approval request.

    Args:
        request_id: The approval request ID

    Returns:
        ApprovalResponse if processed, None if still pending
    """
    if request_id in _approval_responses:
        return _approval_responses[request_id]
    if request_id in _pending_approvals:
        return ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.PENDING,
            approved=False,
            reason="Awaiting human approval",
        )
    return None


# ============================================================================
# Tool Functions (for agent tool registration)
# ============================================================================


def request_human_approval(
    action: str,
    description: str,
    files_affected: list[str],
    context: dict,
    requested_by: str = "unknown-agent",
) -> dict:
    """
    Tool function for agents to request human approval.

    This is the primary tool function registered with agents.
    It classifies risk, creates the request, and handles the flow.

    Args:
        action: Short name of the action
        description: Detailed description
        files_affected: List of files being modified
        context: Additional context
        requested_by: Agent SPIFFE ID

    Returns:
        dict with approval status and details
    """
    # Classify risk based on action and files
    risk_level = classify_risk_level(action, files_affected, context)

    # Create approval request
    request = create_approval_request(
        action=action,
        description=description,
        risk_level=risk_level,
        requested_by=requested_by,
        context=context,
        files_affected=files_affected,
    )

    # For sync context (tool calls), we need to handle async
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            response = asyncio.ensure_future(request_approval(request))
            # Return pending status - agent should poll
            return {
                "request_id": request.request_id,
                "status": "pending",
                "risk_level": risk_level.value,
                "message": "Approval request submitted. Poll for status.",
            }
        else:
            response = loop.run_until_complete(request_approval(request))
    except RuntimeError:
        # No event loop - create new one
        response = asyncio.run(request_approval(request))

    return response.to_dict()


def check_approval_status(request_id: str) -> dict:
    """
    Tool function for agents to check approval status.

    Args:
        request_id: The approval request ID to check

    Returns:
        dict with current approval status
    """
    response = get_approval_status(request_id)
    if response:
        return response.to_dict()
    return {
        "request_id": request_id,
        "status": "not_found",
        "message": "Approval request not found",
    }


# Export tool functions for agent registration
__all__ = [
    # Core functions
    "classify_risk_level",
    "create_approval_request",
    "requires_approval",
    "request_approval",
    "handle_approval_callback",
    "get_pending_approvals",
    "get_approval_status",
    # Tool functions for agents
    "request_human_approval",
    "check_approval_status",
    # Types (re-exported)
    "ApprovalRequest",
    "ApprovalResponse",
    "ApprovalStatus",
    "RiskLevel",
]
