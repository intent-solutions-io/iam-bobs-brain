"""
iam-fix-impl A2A AgentCard

Provides AgentCard for iam-fix-impl, the implementation specialist.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """AgentCard model for A2A protocol."""

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
    """Get iam-fix-impl's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-fix-impl")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-fix-impl.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-fix-impl/dev/us-central1/0.10.0",
    )

    description = f"""iam-fix-impl - Implementation Specialist

**Identity:** {spiffe_id}

iam-fix-impl implements fixes from FixPlan specifications, writes code changes, creates unit tests, and ensures Hard Mode compliance.
"""

    capabilities = [
        "code_implementation",
        "test_writing",
        "hard_mode_compliance",
        "implementation_documentation",
    ]

    skills = [
        {
            "skill_id": "iam_fix_impl.implement_fix",
            "name": "Implement Fix",
            "description": "Implement code changes according to FixPlan specification",
            "input_schema": {
                "type": "object",
                "required": ["fix_plan"],
                "properties": {
                    "fix_plan": {"type": "object"},
                    "target_files": {"type": "array", "items": {"type": "string"}},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["implementation_result"],
                "properties": {
                    "implementation_result": {
                        "type": "object",
                        "required": ["status", "files_modified"],
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["SUCCESS", "PARTIAL", "FAILED"],
                            },
                            "files_modified": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "changes_summary": {"type": "string"},
                            "test_files_created": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_fix_impl.generate_code_diff",
            "name": "Generate Code Diff",
            "description": "Generate unified diff for proposed code changes",
            "input_schema": {
                "type": "object",
                "required": ["file_path", "proposed_changes"],
                "properties": {
                    "file_path": {"type": "string"},
                    "proposed_changes": {"type": "string"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["diff"],
                "properties": {
                    "diff": {"type": "string"},
                    "lines_added": {"type": "integer"},
                    "lines_removed": {"type": "integer"},
                },
            },
        },
        {
            "skill_id": "iam_fix_impl.create_unit_tests",
            "name": "Create Unit Tests",
            "description": "Create unit tests for implemented changes",
            "input_schema": {
                "type": "object",
                "required": ["implementation"],
                "properties": {"implementation": {"type": "object"}},
            },
            "output_schema": {
                "type": "object",
                "required": ["test_files"],
                "properties": {
                    "test_files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "test_count": {"type": "integer"},
                                "coverage": {"type": "string"},
                            },
                        },
                    }
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
    """Get iam-fix-impl's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-fix-impl/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
