"""
iam-issue A2A AgentCard

Provides AgentCard for iam-issue, the issue authoring & formatting specialist.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """
    AgentCard model for A2A protocol.

    Represents iam-issue's identity, capabilities, and skills.
    """

    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent version")
    url: str = Field(..., description="Agent public URL")
    description: str = Field(
        ..., description="Agent description (must include SPIFFE ID per R7)"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    default_input_modes: List[str] = Field(
        default_factory=lambda: ["text"], description="Supported input modes"
    )
    default_output_modes: List[str] = Field(
        default_factory=lambda: ["text"], description="Supported output modes"
    )
    skills: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent skills"
    )


def get_agent_card() -> AgentCard:
    """
    Get iam-issue's AgentCard.

    Returns:
        AgentCard with iam-issue's identity, capabilities, and skills

    Environment Variables Required:
        - APP_NAME: Application name (default: "iam-issue")
        - APP_VERSION: Application version (default: "0.10.0")
        - PUBLIC_URL: Public URL for this agent (default: "https://iam-issue.intent.solutions")
        - AGENT_SPIFFE_ID: SPIFFE ID (required per R7)
    """
    app_name = os.getenv("APP_NAME", "iam-issue")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-issue.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-issue/dev/us-central1/0.10.0",
    )

    # Description with SPIFFE ID (R7 requirement)
    description = f"""iam-issue - Issue Author & Formatter Specialist

**Identity:** {spiffe_id}

iam-issue specializes in converting audit findings and analysis results into well-formatted GitHub issues. Core expertise includes:
- Converting AuditReports and findings into GitHub IssueSpecs
- Formatting issues with proper markdown structure and sections
- Validating issue specs for completeness and clarity
- Generating appropriate labels based on severity and category
- Creating high-quality issue bodies ready for GitHub submission
- Ensuring issues follow repository standards and conventions

This agent produces structured IssueSpec artifacts that can be directly submitted to GitHub or reviewed by QA.
"""

    # Capabilities (what iam-issue can do technically)
    capabilities = [
        "issue_authoring",
        "markdown_formatting",
        "issue_validation",
        "label_generation",
        "github_issue_formatting",
    ]

    # Skills (specific tasks iam-issue can perform)
    skills = [
        {
            "skill_id": "iam_issue.convert_finding_to_issue",
            "name": "Convert Finding to Issue",
            "description": "Convert audit finding or compliance violation into GitHub issue spec",
            "input_schema": {
                "type": "object",
                "required": ["finding"],
                "properties": {
                    "finding": {
                        "type": "object",
                        "required": ["message", "severity"],
                        "properties": {
                            "message": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                            },
                            "file": {"type": "string"},
                            "rule": {"type": "string"},
                            "recommendation": {"type": "string"},
                        },
                    },
                    "repo_context": {
                        "type": "object",
                        "properties": {
                            "repo_name": {"type": "string"},
                            "branch": {"type": "string"},
                        },
                    },
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["issue_spec"],
                "properties": {
                    "issue_spec": {
                        "type": "object",
                        "required": ["title", "body", "labels"],
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string"}},
                            "assignees": {"type": "array", "items": {"type": "string"}},
                            "milestone": {"type": "string"},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_issue.format_issue_body",
            "name": "Format Issue Body",
            "description": "Format issue body with markdown structure and required sections",
            "input_schema": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "steps_to_reproduce": {"type": "string"},
                    "expected_behavior": {"type": "string"},
                    "actual_behavior": {"type": "string"},
                    "additional_context": {"type": "string"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["formatted_body"],
                "properties": {
                    "formatted_body": {
                        "type": "string",
                        "description": "Markdown-formatted issue body",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of included sections",
                    },
                },
            },
        },
        {
            "skill_id": "iam_issue.generate_labels",
            "name": "Generate Issue Labels",
            "description": "Generate appropriate labels based on issue content and severity",
            "input_schema": {
                "type": "object",
                "required": ["issue_content"],
                "properties": {
                    "issue_content": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "category": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                            },
                        },
                    }
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["labels"],
                "properties": {
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "priority_label": {"type": "string"},
                    "type_label": {"type": "string"},
                },
            },
        },
        {
            "skill_id": "iam_issue.validate_issue_spec",
            "name": "Validate Issue Spec",
            "description": "Validate issue spec for completeness and quality before submission",
            "input_schema": {
                "type": "object",
                "required": ["issue_spec"],
                "properties": {
                    "issue_spec": {
                        "type": "object",
                        "required": ["title", "body"],
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string"}},
                        },
                    }
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["valid", "validation_results"],
                "properties": {
                    "valid": {"type": "boolean"},
                    "validation_results": {
                        "type": "object",
                        "required": ["errors", "warnings"],
                        "properties": {
                            "errors": {"type": "array", "items": {"type": "string"}},
                            "warnings": {"type": "array", "items": {"type": "string"}},
                            "suggestions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    ]

    return AgentCard(
        name=app_name,
        version=app_version,
        url=public_url,
        description=description,
        capabilities=capabilities,
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=skills,
    )


def get_agent_card_dict() -> Dict[str, Any]:
    """
    Get iam-issue's AgentCard as a dictionary.

    Returns:
        Dict representation of AgentCard with explicit spiffe_id field (R7)
    """
    card = get_agent_card()
    card_dict = card.model_dump()

    # Add explicit SPIFFE ID field (R7 requirement)
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-issue/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id

    return card_dict


# Module exports
__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
