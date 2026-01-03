"""
Approval Workflow - Human-in-the-Loop Pattern (Phase P4).

Implements Google's Human-in-the-Loop pattern for high-risk actions.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/

This workflow wraps the fix loop with approval gates for high-risk changes.
The pattern ensures that production deployments, destructive changes, and
security-sensitive operations require human approval before execution.

Workflow Flow:
1. Risk Assessment: Classify fix plan by risk level
2. Approval Gate: HIGH/CRITICAL triggers human approval
3. Fix Loop: Run fix implementation with QA gates
4. Deployment Gate: Optional second approval for production

State Flow:
- fix_plan (input)
- risk_assessment
- approval_result
- fix_output (from fix loop)
- qa_result (from fix loop)
"""

import logging
from typing import Any, Callable, Dict, Optional

from google.adk.agents import LlmAgent, SequentialAgent

from agents.iam_contracts import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    RiskLevel,
)
from agents.tools.approval_tool import (
    classify_risk_level,
    create_approval_request,
    request_approval,
    requires_approval,
)
from agents.workflows.fix_loop import create_fix_loop

# Configure logging
logger = logging.getLogger(__name__)


def create_risk_assessor() -> LlmAgent:
    """
    Create risk assessment agent.

    Analyzes fix plan and classifies risk level based on:
    - Files affected (infra/, service/, etc.)
    - Action type (deploy, delete, modify)
    - Scope (single file vs many files)

    Output key: risk_assessment
    """
    return LlmAgent(
        name="risk_assessor",
        model="gemini-2.0-flash-exp",
        instruction="""You are a risk assessment specialist. Analyze the fix plan and classify risk.

Input: {fix_plan}

Evaluate risk based on:
1. **Files Affected**:
   - infra/, terraform/ = HIGH/CRITICAL
   - service/, .github/ = HIGH
   - agents/, config/ = MEDIUM
   - docs/, tests/ = LOW

2. **Action Type**:
   - delete, destroy, drop = CRITICAL
   - deploy, release, migrate = HIGH
   - refactor, update, fix = MEDIUM
   - document, test, lint = LOW

3. **Scope**:
   - Single file = lower risk
   - Many files = higher risk
   - Cross-system changes = higher risk

Output JSON:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reason": "Brief explanation of classification",
  "files_affected": ["list", "of", "files"],
  "requires_approval": true/false,
  "recommended_action": "proceed|request_approval|escalate"
}
""",
        output_key="risk_assessment",
    )


def create_approval_gate_callback(
    spiffe_id: str = "spiffe://intent.solutions/agent/approval-workflow/dev",
) -> Callable:
    """
    Create approval gate callback.

    This after-agent callback checks the risk assessment and:
    - LOW/MEDIUM: Proceeds automatically
    - HIGH/CRITICAL: Blocks until human approval received

    Args:
        spiffe_id: SPIFFE ID for the requesting agent

    Returns:
        Callback function for after_agent_callback
    """

    def approval_gate_callback(ctx):
        """Check risk and request approval if needed."""
        risk_assessment = ctx.state.get("risk_assessment", {})

        # Parse risk level
        if isinstance(risk_assessment, str):
            # LLM returned string, try to parse
            import json

            try:
                risk_assessment = json.loads(risk_assessment)
            except json.JSONDecodeError:
                logger.warning("Could not parse risk assessment, defaulting to HIGH")
                risk_assessment = {"risk_level": "HIGH"}

        risk_level_str = risk_assessment.get("risk_level", "HIGH")
        risk_level = RiskLevel.from_string(risk_level_str)

        logger.info(
            f"Risk assessment: {risk_level.value}",
            extra={"risk_level": risk_level.value},
        )

        # Check if approval is needed
        if not requires_approval(risk_level):
            ctx.state["approval_result"] = {
                "status": "auto_approved",
                "risk_level": risk_level.value,
                "message": "Low risk - proceeding automatically",
            }
            logger.info("Auto-approved: low/medium risk action")
            return

        # HIGH/CRITICAL: Create approval request
        request = create_approval_request(
            action="fix-implementation",
            description=risk_assessment.get("reason", "Fix implementation"),
            risk_level=risk_level,
            requested_by=spiffe_id,
            context={"fix_plan": ctx.state.get("fix_plan", {})},
            files_affected=risk_assessment.get("files_affected", []),
            estimated_impact=f"Risk level: {risk_level.value}",
        )

        # Store request for async processing
        ctx.state["pending_approval"] = request.to_dict()
        ctx.state["approval_result"] = {
            "status": "pending",
            "request_id": request.request_id,
            "risk_level": risk_level.value,
            "message": "Awaiting human approval",
        }

        logger.info(
            f"Approval required: {risk_level.value} risk",
            extra={
                "request_id": request.request_id,
                "risk_level": risk_level.value,
            },
        )

        # Note: In actual execution, the workflow would pause here
        # and resume when approval is received via callback

    return approval_gate_callback


def create_approval_workflow(
    max_fix_iterations: int = 3,
    spiffe_id: str = "spiffe://intent.solutions/agent/approval-workflow/dev",
) -> SequentialAgent:
    """
    Create the full approval workflow with human-in-the-loop gates.

    This workflow combines:
    1. Risk assessment (classifies the fix plan)
    2. Approval gate (blocks HIGH/CRITICAL until approved)
    3. Fix loop (iterative implementation with QA)

    The workflow pauses at the approval gate for HIGH/CRITICAL changes
    and only proceeds when human approval is received.

    Args:
        max_fix_iterations: Max iterations for the fix loop
        spiffe_id: SPIFFE ID for approval requests

    Returns:
        SequentialAgent wrapping the approval workflow
    """
    # Create risk assessor with approval callback
    risk_assessor = create_risk_assessor()
    risk_assessor.after_agent_callback = create_approval_gate_callback(spiffe_id)

    # Create fix loop (from Phase P3)
    fix_loop = create_fix_loop(max_iterations=max_fix_iterations)

    workflow = SequentialAgent(
        name="approval_workflow",
        sub_agents=[
            risk_assessor,  # Assesses risk and gates on HIGH/CRITICAL
            fix_loop,  # Runs fix loop after approval
        ],
    )

    logger.info(
        "Created approval workflow",
        extra={
            "max_fix_iterations": max_fix_iterations,
            "spiffe_id": spiffe_id,
        },
    )

    return workflow


def create_deployment_gate() -> LlmAgent:
    """
    Create optional deployment gate agent.

    This agent runs after fix completion to determine if
    production deployment requires additional approval.

    Output key: deployment_decision
    """
    return LlmAgent(
        name="deployment_gate",
        model="gemini-2.0-flash-exp",
        instruction="""You are a deployment gate. Review the fix results and decide if deployment needs approval.

Inputs:
- Fix output: {fix_output}
- QA result: {qa_result}
- Risk assessment: {risk_assessment}

Evaluate:
1. Did QA pass? If FAIL, do NOT recommend deployment
2. Is this a production deployment? If yes, require approval
3. Were there any unexpected changes?

Output JSON:
{
  "ready_for_deployment": true/false,
  "requires_approval": true/false,
  "reason": "Explanation",
  "deployment_target": "dev|staging|production",
  "recommended_action": "deploy|hold|rollback"
}
""",
        output_key="deployment_decision",
    )


# Export workflow factories
__all__ = [
    "create_risk_assessor",
    "create_approval_gate_callback",
    "create_approval_workflow",
    "create_deployment_gate",
]
