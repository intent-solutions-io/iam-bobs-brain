"""
iam-cleanup A2A AgentCard

Provides AgentCard for iam-cleanup, the repository hygiene specialist.

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
    """Get iam-cleanup's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-cleanup")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-cleanup.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-cleanup/dev/us-central1/0.10.0",
    )

    description = f"""iam-cleanup - Repository Hygiene & Cleanup Specialist

**Identity:** {spiffe_id}

iam-cleanup detects dead code, finds duplicated code, identifies structural issues, and proposes CleanupTask specifications.
"""

    capabilities = [
        "dead_code_detection",
        "duplication_detection",
        "structural_analysis",
        "cleanup_task_generation",
    ]

    skills = [
        {
            "skill_id": "iam_cleanup.detect_dead_code",
            "name": "Detect Dead Code",
            "description": "Identify unused code, functions, and dependencies",
            "input_schema": {
                "type": "object",
                "required": ["scope"],
                "properties": {
                    "scope": {"type": "string"},
                    "include_dependencies": {"type": "boolean", "default": True},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["dead_code_report"],
                "properties": {
                    "dead_code_report": {
                        "type": "object",
                        "required": ["items_found", "total_loc"],
                        "properties": {
                            "items_found": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "function",
                                                "class",
                                                "module",
                                                "dependency",
                                            ],
                                        },
                                        "name": {"type": "string"},
                                        "file": {"type": "string"},
                                        "confidence": {
                                            "type": "string",
                                            "enum": ["HIGH", "MEDIUM", "LOW"],
                                        },
                                    },
                                },
                            },
                            "total_loc": {"type": "integer"},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_cleanup.find_code_duplication",
            "name": "Find Code Duplication",
            "description": "Detect duplicated code blocks and refactoring opportunities",
            "input_schema": {
                "type": "object",
                "required": ["scope"],
                "properties": {
                    "scope": {"type": "string"},
                    "min_lines": {"type": "integer", "default": 10},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["duplication_report"],
                "properties": {
                    "duplication_report": {
                        "type": "object",
                        "required": ["duplicate_groups", "total_duplicates"],
                        "properties": {
                            "duplicate_groups": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "locations": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "lines": {"type": "integer"},
                                        "refactor_suggestion": {"type": "string"},
                                    },
                                },
                            },
                            "total_duplicates": {"type": "integer"},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_cleanup.generate_cleanup_tasks",
            "name": "Generate Cleanup Tasks",
            "description": "Generate prioritized cleanup task specifications",
            "input_schema": {
                "type": "object",
                "required": ["analysis_results"],
                "properties": {"analysis_results": {"type": "object"}},
            },
            "output_schema": {
                "type": "object",
                "required": ["cleanup_tasks"],
                "properties": {
                    "cleanup_tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [
                                "task_id",
                                "description",
                                "priority",
                                "safety_level",
                            ],
                            "properties": {
                                "task_id": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {
                                    "type": "string",
                                    "enum": ["HIGH", "MEDIUM", "LOW"],
                                },
                                "safety_level": {
                                    "type": "string",
                                    "enum": ["SAFE", "MODERATE_RISK", "HIGH_RISK"],
                                },
                                "estimated_impact": {"type": "string"},
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
    """Get iam-cleanup's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-cleanup/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
