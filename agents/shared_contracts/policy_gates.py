"""
Policy Gates for Enterprise Controls (Phase E - Vision Alignment).

This module implements risk tier enforcement and preflight gate checks
for the A2A dispatcher. It ensures that high-risk operations (R3/R4)
require human approval before execution.

Risk Tier Definitions (per 254-DR-STND):
- R0: Read-only, no side effects (DEFAULT - no mandate required)
- R1: Local changes, reversible (mandate optional)
- R2: External writes (GitHub issues, etc.) - mandate + budget required
- R3: Infrastructure changes - mandate + human approval required
- R4: Payment/financial operations - mandate + 2-person approval required

See: 000-docs/254-DR-STND-policy-gates-risk-tiers.md
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from agents.shared_contracts.pipeline_contracts import Mandate


class RiskTier(str, Enum):
    """Risk tier levels for operations."""
    R0 = "R0"  # Read-only, no side effects
    R1 = "R1"  # Local changes, reversible
    R2 = "R2"  # External writes
    R3 = "R3"  # Infrastructure changes
    R4 = "R4"  # Payment/financial


# Risk tier descriptions for documentation and error messages
RISK_TIER_DESCRIPTIONS = {
    RiskTier.R0: "Read-only operations with no side effects",
    RiskTier.R1: "Local changes that are reversible",
    RiskTier.R2: "External writes (GitHub issues, PRs, comments)",
    RiskTier.R3: "Infrastructure changes (requires human approval)",
    RiskTier.R4: "Payment/financial operations (requires 2-person approval)",
}


@dataclass
class GateResult:
    """Result of a policy gate check."""
    allowed: bool
    reason: str
    risk_tier: str
    gate_name: str
    blocking_requirement: Optional[str] = None

    def __bool__(self) -> bool:
        """Allow using GateResult in boolean context."""
        return self.allowed


class PolicyGate:
    """
    Policy gate enforcer for risk-based access control.

    Implements preflight checks before specialist invocations to ensure
    operations meet their risk tier requirements.
    """

    @staticmethod
    def check_mandate_required(
        risk_tier: str,
        mandate: Optional[Mandate] = None
    ) -> GateResult:
        """
        Check if a mandate is required for the operation's risk tier.

        R0-R1: Mandate optional (return allowed)
        R2+: Mandate required
        """
        tier = RiskTier(risk_tier)

        if tier in (RiskTier.R0, RiskTier.R1):
            return GateResult(
                allowed=True,
                reason="R0/R1 operations do not require a mandate",
                risk_tier=risk_tier,
                gate_name="mandate_required"
            )

        if mandate is None:
            return GateResult(
                allowed=False,
                reason=f"R2+ operations require a mandate. Risk tier: {risk_tier}",
                risk_tier=risk_tier,
                gate_name="mandate_required",
                blocking_requirement="mandate"
            )

        return GateResult(
            allowed=True,
            reason="Mandate provided for R2+ operation",
            risk_tier=risk_tier,
            gate_name="mandate_required"
        )

    @staticmethod
    def check_approval_required(
        risk_tier: str,
        mandate: Optional[Mandate] = None
    ) -> GateResult:
        """
        Check if human approval is required and granted.

        R0-R2: No approval required
        R3: Single human approval required
        R4: Two-person approval required (checked via approver_id)
        """
        tier = RiskTier(risk_tier)

        if tier in (RiskTier.R0, RiskTier.R1, RiskTier.R2):
            return GateResult(
                allowed=True,
                reason="R0-R2 operations do not require approval",
                risk_tier=risk_tier,
                gate_name="approval_required"
            )

        if mandate is None:
            return GateResult(
                allowed=False,
                reason=f"R3/R4 operations require a mandate with approval",
                risk_tier=risk_tier,
                gate_name="approval_required",
                blocking_requirement="mandate"
            )

        if mandate.is_pending_approval():
            return GateResult(
                allowed=False,
                reason="Operation pending human approval",
                risk_tier=risk_tier,
                gate_name="approval_required",
                blocking_requirement="approval"
            )

        if mandate.is_denied():
            return GateResult(
                allowed=False,
                reason="Operation was denied by approver",
                risk_tier=risk_tier,
                gate_name="approval_required",
                blocking_requirement="approval_denied"
            )

        if not mandate.is_approved():
            return GateResult(
                allowed=False,
                reason=f"R3/R4 operations require human approval. State: {mandate.approval_state}",
                risk_tier=risk_tier,
                gate_name="approval_required",
                blocking_requirement="approval"
            )

        return GateResult(
            allowed=True,
            reason=f"Approved by {mandate.approver_id}",
            risk_tier=risk_tier,
            gate_name="approval_required"
        )

    @staticmethod
    def check_tool_allowed(
        tool_name: str,
        mandate: Optional[Mandate] = None
    ) -> GateResult:
        """
        Check if a tool is allowed by the mandate's tool_allowlist.

        Empty allowlist = all tools allowed
        """
        if mandate is None:
            # No mandate = no restrictions
            return GateResult(
                allowed=True,
                reason="No mandate = no tool restrictions",
                risk_tier="R0",
                gate_name="tool_allowed"
            )

        if mandate.can_use_tool(tool_name):
            return GateResult(
                allowed=True,
                reason=f"Tool '{tool_name}' is allowed",
                risk_tier=mandate.risk_tier,
                gate_name="tool_allowed"
            )

        return GateResult(
            allowed=False,
            reason=f"Tool '{tool_name}' not in allowlist: {mandate.tool_allowlist}",
            risk_tier=mandate.risk_tier,
            gate_name="tool_allowed",
            blocking_requirement="tool_allowlist"
        )

    @staticmethod
    def check_specialist_authorized(
        specialist_name: str,
        mandate: Optional[Mandate] = None
    ) -> GateResult:
        """
        Check if a specialist is authorized by the mandate.

        Empty authorized_specialists = all specialists allowed
        """
        if mandate is None:
            return GateResult(
                allowed=True,
                reason="No mandate = no specialist restrictions",
                risk_tier="R0",
                gate_name="specialist_authorized"
            )

        if mandate.can_invoke_specialist(specialist_name):
            return GateResult(
                allowed=True,
                reason=f"Specialist '{specialist_name}' is authorized",
                risk_tier=mandate.risk_tier,
                gate_name="specialist_authorized"
            )

        # Determine the specific blocking reason
        if mandate.is_expired():
            blocking = "mandate_expired"
            reason = "Mandate has expired"
        elif mandate.is_budget_exhausted():
            blocking = "budget_exhausted"
            reason = f"Budget exhausted (spent: {mandate.budget_spent}/{mandate.budget_limit})"
        elif mandate.is_iterations_exhausted():
            blocking = "iterations_exhausted"
            reason = f"Iterations exhausted ({mandate.iterations_used}/{mandate.max_iterations})"
        elif mandate.requires_approval() and not mandate.is_approved():
            blocking = "approval_required"
            reason = f"Approval required for {mandate.risk_tier} operation"
        else:
            blocking = "unauthorized_specialist"
            reason = f"Specialist '{specialist_name}' not in authorized list"

        return GateResult(
            allowed=False,
            reason=reason,
            risk_tier=mandate.risk_tier,
            gate_name="specialist_authorized",
            blocking_requirement=blocking
        )

    @classmethod
    def preflight_check(
        cls,
        specialist_name: str,
        risk_tier: str = "R0",
        mandate: Optional[Mandate] = None,
        tools_to_use: Optional[List[str]] = None
    ) -> List[GateResult]:
        """
        Run all preflight gate checks before invoking a specialist.

        Returns a list of all gate results. Check that all are allowed
        before proceeding with the operation.

        Args:
            specialist_name: The specialist to invoke
            risk_tier: The risk tier of the operation (defaults to R0)
            mandate: Optional mandate authorizing the operation
            tools_to_use: Optional list of tools the operation will use

        Returns:
            List of GateResult objects (check all .allowed before proceeding)
        """
        results = []

        # Check mandate requirement
        results.append(cls.check_mandate_required(risk_tier, mandate))

        # Check approval requirement
        results.append(cls.check_approval_required(risk_tier, mandate))

        # Check specialist authorization
        results.append(cls.check_specialist_authorized(specialist_name, mandate))

        # Check tool allowlist (if tools specified)
        if tools_to_use:
            for tool in tools_to_use:
                results.append(cls.check_tool_allowed(tool, mandate))

        return results

    @classmethod
    def is_all_gates_passed(cls, results: List[GateResult]) -> bool:
        """Check if all gate results are allowed."""
        return all(result.allowed for result in results)

    @classmethod
    def get_blocking_gates(cls, results: List[GateResult]) -> List[GateResult]:
        """Get all gates that blocked the operation."""
        return [r for r in results if not r.allowed]


def preflight_check(
    specialist_name: str,
    risk_tier: str = "R0",
    mandate: Optional[Mandate] = None,
    tools_to_use: Optional[List[str]] = None
) -> List[GateResult]:
    """
    Convenience function for running preflight checks.

    See PolicyGate.preflight_check for details.
    """
    return PolicyGate.preflight_check(
        specialist_name=specialist_name,
        risk_tier=risk_tier,
        mandate=mandate,
        tools_to_use=tools_to_use
    )
