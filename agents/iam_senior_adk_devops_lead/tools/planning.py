"""
Task planning and result aggregation tools for the foreman.

These tools help the foreman create execution plans and aggregate
results from multiple specialist agents.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(Enum):
    """Task execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ITERATIVE = "iterative"


def create_task_plan(
    request_description: str,
    request_type: str = "general",
    constraints: Optional[Dict[str, Any]] = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Create a detailed task execution plan.

    Analyzes the request and creates a structured plan identifying:
    - Which specialists are needed
    - Execution order and dependencies
    - Success criteria
    - Risk factors

    Args:
        request_description: High-level description of the request
        request_type: Type of request (audit, fix, implement, document)
        constraints: Optional constraints (time_limit, scope, resources)
        priority: Task priority (low, normal, high, critical)

    Returns:
        Structured task plan with steps, specialists, and metadata

    Example:
        >>> plan = create_task_plan(
        ...     request_description="Fix ADK compliance issues in agents/bob",
        ...     request_type="fix",
        ...     constraints={"time_limit": "2_hours"},
        ...     priority="high"
        ... )
    """
    logger.info(f"Creating task plan for: {request_description[:100]}...")

    # Validate priority
    try:
        priority_enum = TaskPriority(priority)
    except ValueError:
        priority_enum = TaskPriority.NORMAL

    # Base plan structure
    plan = {
        "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "request_description": request_description,
        "request_type": request_type,
        "priority": priority_enum.value,
        "constraints": constraints or {},
        "created_at": datetime.now().isoformat(),
        "execution_mode": ExecutionMode.SEQUENTIAL.value,
        "steps": [],
        "specialists_required": [],
        "estimated_duration": None,
        "success_criteria": [],
        "risk_factors": [],
        "dependencies": []
    }

    # Determine steps based on request type
    if request_type == "audit":
        plan["execution_mode"] = ExecutionMode.PARALLEL.value
        plan["steps"] = [
            {
                "step_id": "audit_1",
                "description": "Analyze codebase for ADK compliance",
                "specialist": "iam-adk",
                "priority": "high",
                "estimated_duration": "30 minutes"
            },
            {
                "step_id": "audit_2",
                "description": "Check existing GitHub issues",
                "specialist": "iam-issue",
                "priority": "normal",
                "estimated_duration": "15 minutes"
            },
            {
                "step_id": "audit_3",
                "description": "Review documentation completeness",
                "specialist": "iam-doc",
                "priority": "normal",
                "estimated_duration": "20 minutes"
            }
        ]
        plan["specialists_required"] = ["iam-adk", "iam-issue", "iam-doc"]
        plan["estimated_duration"] = "30 minutes (parallel)"

    elif request_type == "fix":
        plan["execution_mode"] = ExecutionMode.SEQUENTIAL.value
        plan["steps"] = [
            {
                "step_id": "fix_1",
                "description": "Analyze the problem",
                "specialist": "iam-adk",
                "priority": "high",
                "estimated_duration": "15 minutes"
            },
            {
                "step_id": "fix_2",
                "description": "Create fix plan",
                "specialist": "iam-fix-plan",
                "priority": "high",
                "estimated_duration": "20 minutes",
                "dependencies": ["fix_1"]
            },
            {
                "step_id": "fix_3",
                "description": "Implement the fix",
                "specialist": "iam-fix-impl",
                "priority": "high",
                "estimated_duration": "45 minutes",
                "dependencies": ["fix_2"]
            },
            {
                "step_id": "fix_4",
                "description": "Test the changes",
                "specialist": "iam-qa",
                "priority": "high",
                "estimated_duration": "15 minutes",
                "dependencies": ["fix_3"]
            },
            {
                "step_id": "fix_5",
                "description": "Document the fix",
                "specialist": "iam-doc",
                "priority": "normal",
                "estimated_duration": "15 minutes",
                "dependencies": ["fix_4"]
            }
        ]
        plan["specialists_required"] = ["iam-adk", "iam-fix-plan", "iam-fix-impl", "iam-qa", "iam-doc"]
        plan["estimated_duration"] = "110 minutes (sequential)"

    elif request_type == "implement":
        plan["execution_mode"] = ExecutionMode.SEQUENTIAL.value
        plan["steps"] = [
            {
                "step_id": "impl_1",
                "description": "Design the implementation",
                "specialist": "iam-fix-plan",
                "priority": "high",
                "estimated_duration": "30 minutes"
            },
            {
                "step_id": "impl_2",
                "description": "Code the implementation",
                "specialist": "iam-fix-impl",
                "priority": "high",
                "estimated_duration": "60 minutes",
                "dependencies": ["impl_1"]
            },
            {
                "step_id": "impl_3",
                "description": "Test implementation",
                "specialist": "iam-qa",
                "priority": "high",
                "estimated_duration": "20 minutes",
                "dependencies": ["impl_2"]
            },
            {
                "step_id": "impl_4",
                "description": "Clean up code",
                "specialist": "iam-cleanup",
                "priority": "normal",
                "estimated_duration": "15 minutes",
                "dependencies": ["impl_3"]
            },
            {
                "step_id": "impl_5",
                "description": "Create documentation",
                "specialist": "iam-doc",
                "priority": "normal",
                "estimated_duration": "25 minutes",
                "dependencies": ["impl_4"]
            }
        ]
        plan["specialists_required"] = ["iam-fix-plan", "iam-fix-impl", "iam-qa", "iam-cleanup", "iam-doc"]
        plan["estimated_duration"] = "150 minutes (sequential)"

    elif request_type == "document":
        plan["execution_mode"] = ExecutionMode.PARALLEL.value
        plan["steps"] = [
            {
                "step_id": "doc_1",
                "description": "Analyze what needs documentation",
                "specialist": "iam-adk",
                "priority": "normal",
                "estimated_duration": "15 minutes"
            },
            {
                "step_id": "doc_2",
                "description": "Create documentation",
                "specialist": "iam-doc",
                "priority": "high",
                "estimated_duration": "45 minutes",
                "dependencies": ["doc_1"]
            },
            {
                "step_id": "doc_3",
                "description": "Update knowledge index",
                "specialist": "iam-index",
                "priority": "normal",
                "estimated_duration": "10 minutes",
                "dependencies": ["doc_2"]
            }
        ]
        plan["specialists_required"] = ["iam-adk", "iam-doc", "iam-index"]
        plan["estimated_duration"] = "70 minutes (mixed)"

    else:
        # General request - need analysis first
        plan["steps"] = [
            {
                "step_id": "general_1",
                "description": "Analyze request and determine approach",
                "specialist": "iam-adk",
                "priority": "high",
                "estimated_duration": "15 minutes"
            }
        ]
        plan["specialists_required"] = ["iam-adk"]
        plan["estimated_duration"] = "TBD after analysis"

    # Add success criteria
    plan["success_criteria"] = [
        "All specialist tasks complete successfully",
        "No test failures introduced",
        "Documentation updated if applicable",
        "Code follows ADK patterns"
    ]

    # Add risk factors
    plan["risk_factors"] = []
    if priority_enum in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
        plan["risk_factors"].append("High priority - expedited review may miss issues")

    if constraints and "time_limit" in constraints:
        plan["risk_factors"].append(f"Time constraint: {constraints['time_limit']}")

    return plan


def aggregate_results(
    results: List[Dict[str, Any]],
    plan: Optional[Dict[str, Any]] = None,
    output_format: str = "summary"
) -> Dict[str, Any]:
    """
    Aggregate results from multiple specialist agents.

    Combines outputs from different specialists into a coherent
    summary for reporting back to Bob.

    Args:
        results: List of results from specialist agents
        plan: Optional original task plan for context
        output_format: Format for aggregation (summary, detailed, raw)

    Returns:
        Aggregated results with summary and details

    Example:
        >>> aggregated = aggregate_results(
        ...     results=[result1, result2, result3],
        ...     plan=task_plan,
        ...     output_format="summary"
        ... )
    """
    logger.info(f"Aggregating {len(results)} specialist results...")

    # Base aggregation structure
    aggregation = {
        "aggregation_id": f"agg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "plan_id": plan.get("plan_id") if plan else None,
        "specialists_involved": [],
        "overall_status": "success",
        "summary": "",
        "details": {},
        "artifacts": [],
        "issues": [],
        "follow_ups": []
    }

    # Process each result
    successful_count = 0
    failed_count = 0

    for result in results:
        specialist = result.get("specialist", "unknown")
        status = result.get("status", "unknown")
        output = result.get("result", {})

        aggregation["specialists_involved"].append(specialist)

        if status == "success":
            successful_count += 1
            aggregation["details"][specialist] = {
                "status": "success",
                "output": output
            }

            # Extract artifacts if present
            if isinstance(output, dict):
                if "documents_created" in output:
                    aggregation["artifacts"].extend(output["documents_created"])
                if "files_modified" in output:
                    aggregation["artifacts"].extend(output["files_modified"])
                if "issue_url" in output:
                    aggregation["artifacts"].append(output["issue_url"])

        else:
            failed_count += 1
            aggregation["details"][specialist] = {
                "status": "failure",
                "error": output
            }
            aggregation["issues"].append(f"{specialist} failed: {output}")

    # Determine overall status
    if failed_count == 0:
        aggregation["overall_status"] = "success"
    elif successful_count > 0:
        aggregation["overall_status"] = "partial"
    else:
        aggregation["overall_status"] = "failure"

    # Create summary based on format
    if output_format == "summary":
        aggregation["summary"] = _create_summary(aggregation, plan)
    elif output_format == "detailed":
        aggregation["summary"] = _create_detailed_summary(aggregation, plan)
    # For "raw" format, leave as is

    # Add follow-up recommendations
    aggregation["follow_ups"] = _generate_follow_ups(aggregation)

    return aggregation


def _create_summary(aggregation: Dict[str, Any], plan: Optional[Dict[str, Any]]) -> str:
    """Create a concise summary of aggregated results."""
    status = aggregation["overall_status"]
    specialist_count = len(aggregation["specialists_involved"])

    if status == "success":
        summary = f"✅ Successfully completed all {specialist_count} specialist tasks"
    elif status == "partial":
        summary = f"⚠️ Partially completed: {len([d for d in aggregation['details'].values() if d['status'] == 'success'])}/{specialist_count} tasks successful"
    else:
        summary = f"❌ Failed to complete specialist tasks"

    if plan:
        summary += f" for {plan.get('request_type', 'general')} request"

    if aggregation["artifacts"]:
        summary += f". Created/modified {len(aggregation['artifacts'])} artifacts"

    return summary


def _create_detailed_summary(aggregation: Dict[str, Any], plan: Optional[Dict[str, Any]]) -> str:
    """Create a detailed summary of aggregated results."""
    lines = ["## Task Execution Summary\n"]

    # Overall status
    status_emoji = {
        "success": "✅",
        "partial": "⚠️",
        "failure": "❌"
    }.get(aggregation["overall_status"], "❓")

    lines.append(f"**Overall Status:** {status_emoji} {aggregation['overall_status'].upper()}\n")

    # Specialist results
    lines.append("### Specialist Results\n")
    for specialist, details in aggregation["details"].items():
        status = "✅" if details["status"] == "success" else "❌"
        lines.append(f"- **{specialist}**: {status}")

    # Artifacts
    if aggregation["artifacts"]:
        lines.append("\n### Artifacts Created\n")
        for artifact in aggregation["artifacts"]:
            lines.append(f"- {artifact}")

    # Issues
    if aggregation["issues"]:
        lines.append("\n### Issues Encountered\n")
        for issue in aggregation["issues"]:
            lines.append(f"- ⚠️ {issue}")

    # Follow-ups
    if aggregation["follow_ups"]:
        lines.append("\n### Recommended Follow-ups\n")
        for follow_up in aggregation["follow_ups"]:
            lines.append(f"- {follow_up}")

    return "\n".join(lines)


def _generate_follow_ups(aggregation: Dict[str, Any]) -> List[str]:
    """Generate follow-up recommendations based on results."""
    follow_ups = []

    # Check for failures
    if aggregation["overall_status"] == "failure":
        follow_ups.append("Investigate and retry failed tasks")

    # Check for partial completion
    if aggregation["overall_status"] == "partial":
        follow_ups.append("Review partially completed tasks for manual intervention")

    # Check specific specialist outputs
    for specialist, details in aggregation["details"].items():
        if details["status"] == "success" and isinstance(details["output"], dict):
            output = details["output"]

            # Check for QA issues
            if specialist == "iam-qa" and output.get("tests_failed", 0) > 0:
                follow_ups.append("Fix failing tests identified by QA")

            # Check for ADK compliance issues
            if specialist == "iam-adk" and output.get("compliance_score", 100) < 90:
                follow_ups.append("Address ADK compliance issues")

            # Check for documentation needs
            if specialist == "iam-doc" and not output.get("documents_created"):
                follow_ups.append("Consider creating documentation for this work")

    return follow_ups


def validate_plan_execution(
    plan: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate that execution followed the plan.

    Args:
        plan: Original task plan
        results: Execution results

    Returns:
        Validation report with compliance status
    """
    validation = {
        "plan_id": plan.get("plan_id"),
        "planned_steps": len(plan.get("steps", [])),
        "executed_steps": len(results),
        "compliance": "full",
        "deviations": []
    }

    # Check step count
    if validation["planned_steps"] != validation["executed_steps"]:
        validation["compliance"] = "partial"
        validation["deviations"].append(
            f"Step count mismatch: planned {validation['planned_steps']}, executed {validation['executed_steps']}"
        )

    # Check specialists used
    planned_specialists = set(plan.get("specialists_required", []))
    used_specialists = set([r.get("specialist") for r in results])

    if planned_specialists != used_specialists:
        validation["compliance"] = "partial"
        missing = planned_specialists - used_specialists
        extra = used_specialists - planned_specialists

        if missing:
            validation["deviations"].append(f"Missing specialists: {missing}")
        if extra:
            validation["deviations"].append(f"Unplanned specialists: {extra}")

    return validation