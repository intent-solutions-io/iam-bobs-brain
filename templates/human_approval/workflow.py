"""
Human Approval Pattern - Standalone Template

Implements Google's Human-in-the-Loop pattern for risk-gated execution.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# Risk Level Classification
# ============================================================================


class RiskLevel(Enum):
    """Risk classification for actions."""
    LOW = "low"           # Auto-approve
    MEDIUM = "medium"     # Auto-approve + logging
    HIGH = "high"         # Require human approval
    CRITICAL = "critical" # Require approval + escalation

    @classmethod
    def requires_approval(cls, level: "RiskLevel") -> bool:
        """Check if risk level requires human approval."""
        return level in [cls.HIGH, cls.CRITICAL]

    @classmethod
    def from_string(cls, value: str) -> "RiskLevel":
        """Parse string to RiskLevel, defaulting to HIGH."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.HIGH  # Safe default


def classify_risk(
    action: str,
    files_affected: List[str],
    context: Optional[Dict[str, Any]] = None,
) -> RiskLevel:
    """
    Classify action risk level.

    Args:
        action: Description of the action
        files_affected: List of files being modified
        context: Additional context

    Returns:
        RiskLevel classification
    """
    action_lower = action.lower()
    context = context or {}

    # CRITICAL indicators
    critical_keywords = ["delete", "destroy", "drop", "production", "credentials"]
    if any(kw in action_lower for kw in critical_keywords):
        return RiskLevel.CRITICAL

    # HIGH indicators
    high_keywords = ["deploy", "release", "migrate", "security", "permission"]
    high_paths = ["infra/", "terraform/", "service/", ".github/workflows/"]
    if any(kw in action_lower for kw in high_keywords):
        return RiskLevel.HIGH
    if any(any(p in f for p in high_paths) for f in files_affected):
        return RiskLevel.HIGH

    # MEDIUM indicators
    medium_keywords = ["refactor", "update", "modify", "fix"]
    medium_paths = ["agents/", "config/"]
    if any(kw in action_lower for kw in medium_keywords):
        return RiskLevel.MEDIUM
    if any(any(p in f for p in medium_paths) for f in files_affected):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


# ============================================================================
# Approval Contracts
# ============================================================================


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.HIGH
    context: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""
    requested_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300  # 5 minutes
    files_affected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action": self.action,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "context": self.context,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "timeout_seconds": self.timeout_seconds,
            "files_affected": self.files_affected,
        }


@dataclass
class ApprovalResponse:
    """Response to an approval request."""
    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved: bool = False
    reason: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "approved": self.approved,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


# ============================================================================
# Approval Workflow Factories
# ============================================================================


def create_approval_gate_callback(
    risk_key: str = "risk_level",
    approval_key: str = "approval_result",
) -> Callable:
    """
    Create approval gate callback.

    This callback checks risk level and gates execution on approval
    for HIGH/CRITICAL actions.

    Args:
        risk_key: State key containing risk level
        approval_key: State key for approval result

    Returns:
        Callback function
    """
    def approval_gate(ctx):
        risk_data = ctx.state.get(risk_key, {})

        # Parse risk level
        if isinstance(risk_data, dict):
            risk_str = risk_data.get("risk_level", "HIGH")
        else:
            risk_str = str(risk_data)

        risk_level = RiskLevel.from_string(risk_str)

        # Check if approval is needed
        if not RiskLevel.requires_approval(risk_level):
            ctx.state[approval_key] = {
                "status": "auto_approved",
                "risk_level": risk_level.value,
                "message": f"Auto-approved ({risk_level.value} risk)",
            }
            logger.info(f"Auto-approved: {risk_level.value} risk")
            return

        # HIGH/CRITICAL: Queue for approval
        request = ApprovalRequest(
            action=ctx.state.get("action", "unknown"),
            risk_level=risk_level,
            context={"state": dict(ctx.state)},
        )

        ctx.state["pending_approval"] = request.to_dict()
        ctx.state[approval_key] = {
            "status": "pending",
            "request_id": request.request_id,
            "risk_level": risk_level.value,
            "message": "Awaiting human approval",
        }

        logger.info(f"Approval required: {risk_level.value} risk")

        # In production, this would:
        # 1. Send Slack notification
        # 2. Wait for response (with timeout)
        # 3. Update state with approval result

    return approval_gate


def create_risk_assessor_agent(model: str = "gemini-2.0-flash-exp"):
    """
    Create risk assessment agent.

    Args:
        model: LLM model to use

    Returns:
        Configured risk assessor LlmAgent
    """
    from google.adk.agents import LlmAgent

    return LlmAgent(
        name="risk_assessor",
        model=model,
        instruction="""Assess the risk level of the proposed action.

Input: {action_request}

Classify risk based on:
- File locations (infra/, service/ = HIGH)
- Action type (delete, deploy = HIGH/CRITICAL)
- Scope (many files = higher risk)

Output JSON:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reason": "Brief explanation",
  "files_affected": [...],
  "recommended_action": "proceed|request_approval|block"
}
""",
        output_key="risk_assessment",
    )


# ============================================================================
# Example: Deployment Approval Workflow
# ============================================================================


def create_deployment_approval_flow():
    """
    Example: Create approval workflow for deployments.

    1. Assess risk of deployment
    2. Gate on approval if HIGH/CRITICAL
    3. Proceed with deployment if approved
    """
    from google.adk.agents import SequentialAgent, LlmAgent

    # Risk assessor
    risk_assessor = create_risk_assessor_agent()
    risk_assessor.after_agent_callback = create_approval_gate_callback(
        risk_key="risk_assessment",
        approval_key="approval_status",
    )

    # Deployer (only runs if approved)
    deployer = LlmAgent(
        name="deployer",
        model="gemini-2.0-flash-exp",
        instruction="""Execute the deployment.

Approval: {approval_status}

If approved, proceed with deployment.
If not approved, report why and stop.

Output deployment result.
""",
        output_key="deployment_result",
    )

    return SequentialAgent(
        name="deployment_approval_flow",
        sub_agents=[risk_assessor, deployer],
    )


__all__ = [
    # Risk classification
    "RiskLevel",
    "classify_risk",
    # Approval contracts
    "ApprovalStatus",
    "ApprovalRequest",
    "ApprovalResponse",
    # Workflow factories
    "create_approval_gate_callback",
    "create_risk_assessor_agent",
    "create_deployment_approval_flow",
]
