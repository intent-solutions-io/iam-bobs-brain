"""
Issue Formatting Tools

Tools for formatting issues, validating issue specs, and generating
GitHub-compatible issue content from structured IssueSpec objects.

These tools enable iam-issue to transform findings and audit reports
into well-formatted GitHub issues.
"""

import json
import logging

logger = logging.getLogger(__name__)


def validate_issue_spec(issue_data: str) -> str:
    """
    Validate an IssueSpec object for completeness and correctness.

    Checks:
    - Required fields (title, description, component, severity, type)
    - Valid enum values (component, severity, type)
    - Field format and length constraints
    - Labels format and validity

    Args:
        issue_data: JSON string containing IssueSpec data

    Returns:
        JSON string with validation results:
        {
            "is_valid": true | false,
            "errors": [
                {
                    "field": "title",
                    "message": "Title too short (min 10 characters)"
                }
            ],
            "warnings": [
                "Missing acceptance_criteria"
            ],
            "score": 0.95
        }
    """
    try:
        issue = json.loads(issue_data)

        errors = []
        warnings = []
        score = 1.0

        # Required fields
        if not issue.get("title"):
            errors.append(
                {"field": "title", "message": "title is required"}
            )
        elif len(issue["title"]) < 10:
            errors.append(
                {
                    "field": "title",
                    "message": "Title too short (minimum 10 characters)",
                }
            )
        elif len(issue["title"]) > 100:
            errors.append(
                {
                    "field": "title",
                    "message": "Title too long (maximum 100 characters)",
                }
            )

        if not issue.get("description"):
            errors.append(
                {"field": "description", "message": "description is required"}
            )
        elif len(issue["description"]) < 20:
            errors.append(
                {
                    "field": "description",
                    "message": "Description too short (minimum 20 characters)",
                }
            )

        # Valid enum values
        valid_components = ["agents", "service", "infra", "ci", "docs", "general"]
        if issue.get("component") not in valid_components:
            errors.append(
                {
                    "field": "component",
                    "message": f"component must be one of {valid_components}",
                }
            )

        valid_severities = ["low", "medium", "high", "critical"]
        if issue.get("severity") not in valid_severities:
            errors.append(
                {
                    "field": "severity",
                    "message": f"severity must be one of {valid_severities}",
                }
            )

        valid_types = ["bug", "tech_debt", "improvement", "task", "violation"]
        if issue.get("type") not in valid_types:
            errors.append(
                {
                    "field": "type",
                    "message": f"type must be one of {valid_types}",
                }
            )

        # Optional field validation
        if not issue.get("acceptance_criteria"):
            warnings.append(
                "Missing acceptance_criteria - helps define done state"
            )
            score -= 0.05

        if not issue.get("repro_steps"):
            warnings.append(
                "Missing repro_steps - useful for bug issues"
            )
            score -= 0.03

        if not issue.get("labels"):
            warnings.append("Missing labels - helps with organization")
            score -= 0.02

        return json.dumps(
            {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "score": max(0.0, score),
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in issue data: {e}")
        return json.dumps(
            {
                "is_valid": False,
                "errors": [{"field": "root", "message": f"Invalid JSON: {e!s}"}],
                "warnings": [],
                "score": 0.0,
            }
        )
    except Exception as e:
        logger.error(f"Error validating issue spec: {e}")
        return json.dumps(
            {
                "is_valid": False,
                "errors": [{"field": "root", "message": f"Validation error: {e!s}"}],
                "warnings": [],
                "score": 0.0,
            }
        )


def format_issue_markdown(issue_data: str) -> str:
    """
    Format an IssueSpec into GitHub-compatible markdown.

    Converts a structured IssueSpec object into properly formatted
    markdown that's ready to post as a GitHub issue.

    Args:
        issue_data: JSON string containing IssueSpec data

    Returns:
        Formatted markdown string for GitHub issue body
    """
    try:
        issue = json.loads(issue_data)

        markdown = f"""## Summary
{issue.get('description', 'No description provided')}

## Component
`{issue.get('component', 'general')}`

## Type
`{issue.get('type', 'task')}`

## Severity
`{issue.get('severity', 'medium')}`
"""

        # Repro steps (for bugs)
        if issue.get("repro_steps"):
            markdown += "\n## Reproduction Steps\n\n"
            for i, step in enumerate(issue["repro_steps"], 1):
                markdown += f"{i}. {step}\n"

        # Acceptance criteria
        if issue.get("acceptance_criteria"):
            markdown += "\n## Acceptance Criteria\n\n"
            for criterion in issue["acceptance_criteria"]:
                markdown += f"- [ ] {criterion}\n"

        # Notes
        if issue.get("notes"):
            markdown += f"\n## Notes\n\n{issue['notes']}\n"

        # Links/references
        if issue.get("links"):
            markdown += "\n## References\n\n"
            for link in issue["links"]:
                markdown += f"- {link}\n"

        return markdown

    except Exception as e:
        logger.error(f"Error formatting issue markdown: {e}")
        return f"Error formatting issue: {e!s}"


def generate_issue_labels(issue_data: str) -> str:
    """
    Generate GitHub labels based on issue metadata.

    Creates a set of appropriate labels based on:
    - Component (agents, service, infra, ci, docs)
    - Severity (low, medium, high, critical)
    - Type (bug, tech_debt, improvement, task, violation)
    - User-provided labels

    Args:
        issue_data: JSON string containing IssueSpec data

    Returns:
        JSON string with generated labels:
        {
            "labels": ["bug", "critical", "agents", ...],
            "suggested": true,
            "count": 5
        }
    """
    try:
        issue = json.loads(issue_data)
        labels = set()

        # Component-based labels
        component = issue.get("component", "general")
        if component != "general":
            labels.add(component)

        # Type-based labels
        issue_type = issue.get("type", "task")
        if issue_type in ["bug", "tech_debt", "improvement"]:
            labels.add(issue_type)

        # Severity-based labels
        severity = issue.get("severity", "medium")
        if severity in ["high", "critical"]:
            labels.add(f"priority-{severity}")

        # Add user-provided labels
        if issue.get("labels"):
            labels.update(issue["labels"])

        return json.dumps(
            {
                "labels": sorted(list(labels)),
                "suggested": True,
                "count": len(labels),
            }
        )

    except Exception as e:
        logger.error(f"Error generating labels: {e}")
        return json.dumps(
            {
                "labels": ["needs-triage"],
                "suggested": False,
                "count": 1,
                "error": str(e),
            }
        )


def create_github_issue_body(issue_data: str, include_metadata: bool = True) -> str:
    """
    Create a complete GitHub issue body with metadata and formatting.

    Combines formatted markdown with optional metadata comments for
    issue tracking and automation.

    Args:
        issue_data: JSON string containing IssueSpec data
        include_metadata: Whether to include metadata comments

    Returns:
        Complete GitHub issue body ready for posting
    """
    try:
        issue = json.loads(issue_data)

        # Format main issue content
        body = format_issue_markdown(issue_data)

        # Add metadata comments for automation
        if include_metadata:
            metadata = "\n\n<!-- Issue Metadata -->\n"
            metadata += f"<!-- ID: {issue.get('id', 'unassigned')} -->\n"
            metadata += f"<!-- Component: {issue.get('component', 'general')} -->\n"
            metadata += f"<!-- Type: {issue.get('type', 'task')} -->\n"
            metadata += f"<!-- Severity: {issue.get('severity', 'medium')} -->\n"

            if issue.get("created_at"):
                metadata += f"<!-- Created: {issue['created_at']} -->\n"

            body += metadata

        return body

    except Exception as e:
        logger.error(f"Error creating GitHub issue body: {e}")
        return f"Error creating issue body: {e!s}"
