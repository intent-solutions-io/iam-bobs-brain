"""
Fix Planning Tools

Tools for creating fix plans, validating plan completeness, assessing risk,
defining testing strategies, and estimating effort for implementing fixes.

These tools enable iam-fix-plan to transform IssueSpec objects into detailed,
actionable FixPlan implementations.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def create_fix_plan(issue_data: str) -> str:
    """
    Create a detailed FixPlan from an IssueSpec.

    Converts an issue specification into a comprehensive implementation plan with:
    - Clear implementation steps
    - Risk assessment
    - Testing strategy
    - Effort estimation
    - Rollout planning

    Args:
        issue_data: JSON string containing IssueSpec data with at least:
            - title
            - description
            - component (agents|service|infra|ci|docs|general)
            - severity (low|medium|high|critical)
            - type (bug|tech_debt|improvement|task|violation)

    Returns:
        JSON string with FixPlan structure:
        {
            "summary": "High-level fix strategy",
            "impacted_areas": ["file1.py", "file2.py"],
            "steps": [
                "1. Analyze root cause",
                "2. Implement fix in file1.py"
            ],
            "risk_level": "low|medium|high",
            "testing_strategy": ["unit tests", "integration tests"],
            "issue_id": "optional-id",
            "estimated_effort": "2 hours",
            "rollout_notes": "Direct deployment",
            "dependencies": [],
            "rollback_plan": "Rollback procedure",
            "success_metrics": ["All tests pass"]
        }
    """
    try:
        issue = json.loads(issue_data)

        # Validate required fields
        required_fields = ["title", "description", "component", "severity", "type"]
        missing_fields = [f for f in required_fields if f not in issue]
        if missing_fields:
            return json.dumps(
                {
                    "error": f"Missing required fields: {missing_fields}",
                    "received_fields": list(issue.keys()),
                }
            )

        # Extract issue details
        title = issue.get("title", "Unknown issue")
        description = issue.get("description", "")
        component = issue.get("component", "general")
        severity = issue.get("severity", "medium")
        issue_type = issue.get("type", "task")

        # Generate plan based on issue type and component
        plan = _generate_plan_strategy(
            title, description, component, severity, issue_type, issue
        )

        return json.dumps(plan)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in issue_data: {e}")
        return json.dumps(
            {"error": f"Invalid JSON: {e!s}", "received": issue_data[:100]}
        )
    except Exception as e:
        logger.error(f"Error creating fix plan: {e}")
        return json.dumps({"error": str(e), "error_type": type(e).__name__})


def _generate_plan_strategy(
    title: str,
    description: str,
    component: str,
    severity: str,
    issue_type: str,
    issue: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a fix plan strategy based on issue characteristics.

    Args:
        title: Issue title
        description: Issue description
        component: Component affected (agents|service|infra|ci|docs|general)
        severity: Severity level (low|medium|high|critical)
        issue_type: Type of issue (bug|tech_debt|improvement|task|violation)
        issue: Full issue dict

    Returns:
        FixPlan-compatible dictionary
    """
    # Base effort estimates by type
    effort_by_type = {
        "bug": "4 hours",
        "tech_debt": "1 day",
        "improvement": "2 days",
        "task": "1 day",
        "violation": "2 hours",
    }

    # Component-specific impact areas
    impact_by_component = {
        "agents": ["agents/*/agent.py", "agents/*/tools/", "tests/unit/agents/"],
        "service": [
            "service/*/main.py",
            "service/*/requirements.txt",
            "tests/integration/service/",
        ],
        "infra": ["infra/terraform/", "scripts/ci/", "tests/infra/"],
        "ci": [".github/workflows/", "scripts/ci/", "tests/ci/"],
        "docs": ["000-docs/", "README.md", ".md files"],
        "general": ["various files"],
    }

    # Risk mapping
    risk_by_severity = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",  # Critical issues need careful planning
    }

    # Testing strategy by component
    testing_by_component = {
        "agents": [
            "unit tests (agent behavior)",
            "integration tests (A2A communication)",
            "memory wiring tests",
        ],
        "service": [
            "unit tests (endpoints)",
            "integration tests (gateway behavior)",
            "load tests",
        ],
        "infra": ["terraform validation", "deployment tests", "security scanning"],
        "ci": ["workflow validation", "drift detection tests", "deployment tests"],
        "docs": ["markdown validation", "link validation", "content review"],
        "general": ["test coverage", "manual verification"],
    }

    # Generate implementation steps
    steps = _generate_implementation_steps(component, issue_type, description)

    # Determine rollout strategy
    rollout_notes = _determine_rollout_strategy(component, severity)

    # Rollback plan
    rollback_plan = _generate_rollback_plan(component, severity)

    # Success metrics
    success_metrics = _generate_success_metrics(component, issue_type)

    return {
        "summary": f"Fix {title.lower()} by implementing targeted changes to {component} component",
        "impacted_areas": impact_by_component.get(component, ["various areas"]),
        "steps": steps,
        "risk_level": risk_by_severity.get(severity, "medium"),
        "testing_strategy": testing_by_component.get(
            component, ["unit tests", "integration tests"]
        ),
        "issue_id": issue.get("id"),
        "estimated_effort": effort_by_type.get(issue_type, "1 day"),
        "rollout_notes": rollout_notes,
        "dependencies": issue.get("dependencies", []),
        "rollback_plan": rollback_plan,
        "success_metrics": success_metrics,
    }


def _generate_implementation_steps(
    component: str, issue_type: str, description: str
) -> List[str]:
    """Generate specific implementation steps based on component and type."""
    steps = ["1. Analyze root cause and impact"]

    if component == "agents":
        steps.extend(
            [
                "2. Review agent.py structure for ADK compliance",
                "3. Update agent system prompt and instructions",
                "4. Modify or add tools as needed",
                "5. Update tool implementations",
                "6. Verify R1-R8 rule compliance",
                "7. Test agent locally (smoke test)",
                "8. Run drift detection check",
            ]
        )
    elif component == "service":
        steps.extend(
            [
                "2. Review service endpoints and routes",
                "3. Update gateway implementations",
                "4. Ensure no Runner imports (R3 compliance)",
                "5. Add proper error handling and logging",
                "6. Update service documentation",
                "7. Test endpoints with sample requests",
                "8. Validate API contracts",
            ]
        )
    elif component == "infra":
        steps.extend(
            [
                "2. Review Terraform configuration",
                "3. Update resource definitions",
                "4. Validate Terraform syntax (terraform validate)",
                "5. Plan changes (terraform plan)",
                "6. Update environment-specific configs",
                "7. Test in dev environment first",
                "8. Document infrastructure changes",
            ]
        )
    elif component == "ci":
        steps.extend(
            [
                "2. Review workflow definitions",
                "3. Update job definitions",
                "4. Validate workflow syntax",
                "5. Test CI changes (if possible)",
                "6. Verify WIF authentication setup",
                "7. Check drift detection integration",
                "8. Document CI changes",
            ]
        )
    elif component == "docs":
        steps.extend(
            [
                "2. Review existing documentation",
                "3. Update or create new docs",
                "4. Follow NNN-CC-ABCD naming convention",
                "5. Add markdown with proper formatting",
                "6. Validate links and references",
                "7. Update 000-docs index",
                "8. Merge changes to main",
            ]
        )
    else:
        steps.extend(
            [
                "2. Identify specific files to modify",
                "3. Plan changes by priority",
                "4. Implement changes incrementally",
                "5. Test each change",
                "6. Validate against acceptance criteria",
                "7. Create pull request with summary",
                "8. Get review and merge",
            ]
        )

    return steps


def _determine_rollout_strategy(component: str, severity: str) -> str:
    """Determine appropriate rollout strategy."""
    if severity == "critical":
        return "Staged rollout with monitoring; start in dev, then staging, then prod. Monitor closely for first 24 hours."
    elif component in ["infra", "ci"]:
        return "Direct deployment with drift detection and CI validation. Automated rollback on failure."
    elif component == "agents":
        return "Deploy to Agent Engine via ADK CLI. Automatic versioning and rollback via Terraform."
    elif component == "service":
        return "Cloud Run deployment with traffic splitting. Monitor error rates before full rollout."
    else:
        return "Standard GitHub merge to main; deploy via CI/CD pipeline."


def _generate_rollback_plan(component: str, severity: str) -> str:
    """Generate a rollback plan for the fix."""
    if component == "infra":
        return "Revert Terraform changes: git revert <commit> && terraform apply. Requires manual confirmation."
    elif component == "ci":
        return "Revert workflow changes: git revert <commit>. Previous job version will run on next push."
    elif component == "agents":
        return "Revert agent code: git revert <commit>. ADK CLI will deploy previous version to Agent Engine."
    elif component == "service":
        return "Rollback Cloud Run: switch traffic back to previous service revision. Automatic with traffic splitting."
    else:
        return f"Revert commits via git if needed. Rollback severity: {severity}. Monitor for side effects."


def _generate_success_metrics(component: str, issue_type: str) -> List[str]:
    """Generate success metrics for the fix."""
    metrics = ["All tests pass"]

    if component == "agents":
        metrics.extend(
            [
                "Agent initializes without errors",
                "R1-R8 drift detection passes",
                "Tools execute correctly",
                "Memory persistence works",
            ]
        )
    elif component == "service":
        metrics.extend(
            [
                "Endpoints respond with correct status codes",
                "No Runner imports detected",
                "Error handling works correctly",
                "Load tests show acceptable performance",
            ]
        )
    elif component == "infra":
        metrics.extend(
            [
                "Terraform validates successfully",
                "Resources created/modified as planned",
                "Security scanning passes",
                "Integration tests pass",
            ]
        )
    elif component == "ci":
        metrics.extend(
            [
                "Workflow passes on test runs",
                "Drift detection works correctly",
                "Deployment succeeds",
                "No new failures in CI",
            ]
        )

    if issue_type == "bug":
        metrics.append("Reproduction steps from issue no longer trigger bug")
    elif issue_type == "tech_debt":
        metrics.append("Code quality metrics improve")

    return metrics


def validate_fix_plan(plan_data: str) -> str:
    """
    Validate a FixPlan object for completeness and quality.

    Checks:
    - Required fields (summary, steps, risk_level, testing_strategy)
    - Valid risk levels (low, medium, high)
    - Steps are specific and actionable
    - Testing strategy is comprehensive
    - Success metrics are defined

    Args:
        plan_data: JSON string containing FixPlan data

    Returns:
        JSON string with validation results:
        {
            "is_valid": true|false,
            "errors": [{"field": "...", "message": "..."}],
            "warnings": ["..."],
            "quality_score": 0.95,
            "recommendations": ["..."]
        }
    """
    try:
        plan = json.loads(plan_data)

        errors = []
        warnings = []
        recommendations = []

        # Required fields
        required_fields = ["summary", "steps", "risk_level", "testing_strategy"]
        for field in required_fields:
            if field not in plan:
                errors.append(
                    {"field": field, "message": f"Required field '{field}' is missing"}
                )

        # Validate risk level
        if "risk_level" in plan:
            valid_risks = ["low", "medium", "high"]
            if plan["risk_level"] not in valid_risks:
                errors.append(
                    {
                        "field": "risk_level",
                        "message": f"Invalid risk level. Must be one of: {valid_risks}",
                    }
                )

        # Validate steps
        if "steps" in plan:
            if not isinstance(plan["steps"], list) or len(plan["steps"]) < 2:
                warnings.append(
                    "Steps should be a list with at least 2 items for clarity"
                )
            else:
                # Check if steps are numbered
                non_numbered = [s for s in plan["steps"] if not s[0].isdigit()]
                if non_numbered:
                    recommendations.append(
                        "Consider numbering steps for better clarity"
                    )

        # Validate testing strategy
        if "testing_strategy" in plan:
            if (
                not isinstance(plan["testing_strategy"], list)
                or len(plan["testing_strategy"]) < 1
            ):
                warnings.append(
                    "Testing strategy should include at least one test type"
                )
            expected_tests = ["unit tests", "integration tests"]
            included_tests = [t.lower() for t in plan.get("testing_strategy", [])]
            if not any(t in " ".join(included_tests) for t in expected_tests):
                recommendations.append("Consider adding unit and/or integration tests")

        # Validate success metrics
        if "success_metrics" not in plan or not plan.get("success_metrics"):
            warnings.append(
                "Success metrics are not defined - how will we know the fix worked?"
            )
        elif len(plan["success_metrics"]) < 1:
            recommendations.append("Add more specific success metrics")

        # Estimated effort
        if "estimated_effort" not in plan:
            warnings.append("Estimated effort not specified")

        # Quality score
        quality_score = 1.0
        quality_score -= len(errors) * 0.2
        quality_score -= len(warnings) * 0.1
        quality_score = max(0.0, min(1.0, quality_score))

        return json.dumps(
            {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "quality_score": quality_score,
                "recommendations": recommendations,
                "summary": f"Plan has {len(errors)} error(s) and {len(warnings)} warning(s)",
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in plan_data: {e}")
        return json.dumps({"is_valid": False, "error": f"Invalid JSON: {e!s}"})
    except Exception as e:
        logger.error(f"Error validating fix plan: {e}")
        return json.dumps({"is_valid": False, "error": str(e)})


def assess_risk_level(issue_data: str, plan_data: str) -> str:
    """
    Assess and justify the risk level for a fix plan.

    Analyzes:
    - Scope of changes (isolated vs. cross-cutting)
    - Component criticality
    - Complexity of implementation
    - Test coverage impact
    - Breaking changes potential

    Args:
        issue_data: JSON string containing IssueSpec data
        plan_data: JSON string containing FixPlan data

    Returns:
        JSON string with risk assessment:
        {
            "risk_level": "low|medium|high",
            "risk_factors": [
                {"factor": "...", "impact": "...", "severity": "..."}
            ],
            "mitigations": ["..."],
            "recommendation": "..."
        }
    """
    try:
        issue = json.loads(issue_data)
        plan = json.loads(plan_data)

        risk_factors = []
        mitigations = []

        # Analyze scope
        impacted_areas = plan.get("impacted_areas", [])
        scope_risk = len(impacted_areas) > 3
        if scope_risk:
            risk_factors.append(
                {
                    "factor": "Scope",
                    "impact": f"{len(impacted_areas)} impacted areas",
                    "severity": "medium",
                }
            )
            mitigations.append("Test integration points thoroughly")

        # Analyze component
        component = issue.get("component", "general")
        critical_components = ["infra", "ci"]
        if component in critical_components:
            risk_factors.append(
                {
                    "factor": "Component",
                    "impact": f"{component} is critical infrastructure",
                    "severity": "high",
                }
            )
            mitigations.append("Use staged rollout with drift detection")

        # Analyze severity
        severity = issue.get("severity", "medium")
        if severity in ["high", "critical"]:
            risk_factors.append(
                {
                    "factor": "Issue Severity",
                    "impact": f"Fixing {severity} severity issue",
                    "severity": "medium",
                }
            )
            mitigations.append("Ensure comprehensive testing before rollout")

        # Analyze steps for complexity
        steps = plan.get("steps", [])
        if len(steps) > 6:
            risk_factors.append(
                {
                    "factor": "Complexity",
                    "impact": f"{len(steps)} implementation steps",
                    "severity": "low",
                }
            )
            mitigations.append("Break implementation into smaller PRs if possible")

        # Determine overall risk
        if any(r["severity"] == "high" for r in risk_factors):
            risk_level = "high"
        elif (
            any(r["severity"] == "medium" for r in risk_factors)
            or len(risk_factors) > 2
        ):
            risk_level = "medium"
        else:
            risk_level = "low"

        recommendation = _generate_risk_recommendation(risk_level, component, severity)

        return json.dumps(
            {
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "mitigations": mitigations,
                "recommendation": recommendation,
                "requires_staged_rollout": risk_level in ["medium", "high"],
                "requires_monitoring": risk_level in ["high"],
            }
        )

    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        return json.dumps(
            {"error": str(e), "risk_level": "high"}  # Default to high for safety
        )


def _generate_risk_recommendation(
    risk_level: str, component: str, severity: str
) -> str:
    """Generate a risk-based recommendation for rollout."""
    if risk_level == "high":
        return f"High-risk change in {component}. Recommend: staged rollout with monitoring, automated rollback on error, and post-deployment validation."
    elif risk_level == "medium":
        return f"Medium-risk fix for {severity} severity issue. Recommend: single deployment to prod with monitoring, manual rollback plan available."
    else:
        return "Low-risk fix. Can proceed with standard merge and deployment via CI/CD."


def define_testing_strategy(
    component: str, issue_type: str, impacted_areas: str
) -> str:
    """
    Define a comprehensive testing strategy for a fix.

    Creates a detailed testing plan including:
    - Unit test targets
    - Integration test scenarios
    - E2E test cases (if applicable)
    - Regression test requirements
    - Performance testing needs

    Args:
        component: Component affected (agents|service|infra|ci|docs|general)
        issue_type: Type of issue (bug|tech_debt|improvement|task|violation)
        impacted_areas: JSON string list of affected files/areas

    Returns:
        JSON string with testing strategy:
        {
            "unit_tests": ["..."],
            "integration_tests": ["..."],
            "e2e_tests": ["..."],
            "regression_tests": ["..."],
            "coverage_target": 0.85,
            "test_priority": "..."
        }
    """
    try:
        areas = (
            json.loads(impacted_areas)
            if isinstance(impacted_areas, str)
            else impacted_areas or []
        )

        strategy = {
            "unit_tests": _generate_unit_tests(component, issue_type),
            "integration_tests": _generate_integration_tests(component, issue_type),
            "e2e_tests": _generate_e2e_tests(component, issue_type),
            "regression_tests": _generate_regression_tests(component, issue_type),
            "coverage_target": 0.85 if issue_type != "tech_debt" else 0.80,
            "test_priority": "critical" if issue_type == "bug" else "high",
            "impacted_areas": areas,
            "estimated_test_time": _estimate_test_time(len(areas), issue_type),
        }

        return json.dumps(strategy)

    except Exception as e:
        logger.error(f"Error defining testing strategy: {e}")
        return json.dumps(
            {
                "error": str(e),
                "unit_tests": ["Test basic functionality"],
                "integration_tests": ["Test component interactions"],
            }
        )


def _generate_unit_tests(component: str, issue_type: str) -> List[str]:
    """Generate unit test targets."""
    tests = []
    if component == "agents":
        tests = [
            "Test agent initialization with tools",
            "Test each tool function independently",
            "Test agent instruction handling",
        ]
    elif component == "service":
        tests = [
            "Test endpoint request/response handling",
            "Test error responses and status codes",
            "Test input validation",
        ]
    elif component == "infra":
        tests = [
            "Test Terraform variable validation",
            "Test resource configuration logic",
        ]
    else:
        tests = ["Test individual function/module behavior"]

    if issue_type == "bug":
        tests.append("Test reproduction steps from issue")
    return tests


def _generate_integration_tests(component: str, issue_type: str) -> List[str]:
    """Generate integration test scenarios."""
    tests = []
    if component == "agents":
        tests = [
            "Test agent with multiple tools in sequence",
            "Test A2A communication between agents",
            "Test memory persistence",
        ]
    elif component == "service":
        tests = [
            "Test service integration with Agent Engine",
            "Test multi-endpoint workflows",
        ]
    elif component == "infra":
        tests = [
            "Test resource dependencies",
            "Test environment variable injection",
        ]
    else:
        tests = ["Test interaction between components"]

    return tests


def _generate_e2e_tests(component: str, issue_type: str) -> List[str]:
    """Generate end-to-end test cases."""
    tests = []
    if component == "agents":
        tests = [
            "Test complete agent workflow from request to response",
            "Test agent persistence across sessions",
        ]
    elif component == "service":
        tests = [
            "Test full user workflow through gateway",
            "Test error recovery and resilience",
        ]
    else:
        tests = ["Test complete feature workflow"]

    return tests


def _generate_regression_tests(component: str, issue_type: str) -> List[str]:
    """Generate regression test requirements."""
    return [
        "Ensure existing tests still pass",
        "Run full test suite before merge",
        "Check for performance regressions",
    ]


def _estimate_test_time(num_areas: int, issue_type: str) -> str:
    """Estimate testing time based on scope."""
    if issue_type == "bug":
        hours = min(4, max(1, num_areas * 0.5))
    elif issue_type == "improvement":
        hours = min(6, max(2, num_areas * 0.75))
    else:
        hours = min(3, max(1, num_areas * 0.33))

    if hours < 2:
        return "30-60 minutes"
    elif hours < 4:
        return "1-2 hours"
    elif hours < 6:
        return "2-4 hours"
    else:
        return "4+ hours"


def estimate_effort(plan_data: str, team_expertise: str = "medium") -> str:
    """
    Estimate implementation effort for a fix plan.

    Factors in:
    - Number and complexity of steps
    - Component difficulty
    - Testing requirements
    - Review/deployment overhead
    - Team expertise level

    Args:
        plan_data: JSON string containing FixPlan data
        team_expertise: "low"|"medium"|"high" (default: "medium")

    Returns:
        JSON string with effort estimation:
        {
            "implementation_hours": 4,
            "testing_hours": 2,
            "review_hours": 1,
            "deployment_hours": 1,
            "total_hours": 8,
            "estimated_duration": "1 day",
            "confidence": 0.80,
            "notes": "..."
        }
    """
    try:
        plan = json.loads(plan_data)

        # Base estimates
        steps = plan.get("steps", [])
        impl_hours = len(steps) * 0.5

        # Component difficulty multipliers
        component_multipliers = {
            "agents": 1.2,
            "service": 1.1,
            "infra": 1.5,
            "ci": 1.4,
            "docs": 0.7,
            "general": 1.0,
        }
        estimated_effort = plan.get("estimated_effort", "1 day")
        # Parse estimated effort for multiplier
        base_mult = component_multipliers.get("general", 1.0)
        if "hour" in estimated_effort.lower():
            try:
                hours_str = estimated_effort.split()[0]
                impl_hours = float(hours_str) * base_mult
            except Exception:
                impl_hours = len(steps) * 0.5

        # Testing hours
        testing_count = len(plan.get("testing_strategy", []))
        testing_hours = testing_count * 1.0

        # Team expertise adjustment
        expertise_multipliers = {"low": 1.3, "medium": 1.0, "high": 0.8}
        multiplier = expertise_multipliers.get(team_expertise, 1.0)

        impl_hours *= multiplier
        testing_hours *= multiplier

        # Review and deployment
        review_hours = 1.0 if "high" in plan.get("risk_level", "low") else 0.5
        deployment_hours = 1.0 if "infra" in plan.get("impacted_areas", [])[:1] else 0.5

        # Calculate totals
        total_hours = impl_hours + testing_hours + review_hours + deployment_hours
        confidence = min(0.95, 0.70 + (len(steps) * 0.05))

        # Convert to duration
        if total_hours <= 4:
            duration = "1 day"
        elif total_hours <= 8:
            duration = "1-2 days"
        elif total_hours <= 16:
            duration = "2-3 days"
        else:
            duration = f"{int(total_hours / 8)} days"

        return json.dumps(
            {
                "implementation_hours": round(impl_hours, 1),
                "testing_hours": round(testing_hours, 1),
                "review_hours": round(review_hours, 1),
                "deployment_hours": round(deployment_hours, 1),
                "total_hours": round(total_hours, 1),
                "estimated_duration": duration,
                "confidence": round(confidence, 2),
                "notes": f"Estimate based on {len(steps)} implementation steps and {testing_count} testing types. Confidence {round(confidence*100)}%.",
            }
        )

    except Exception as e:
        logger.error(f"Error estimating effort: {e}")
        return json.dumps(
            {"error": str(e), "total_hours": 8, "estimated_duration": "1-2 days"}
        )
