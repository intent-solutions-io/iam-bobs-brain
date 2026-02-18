"""
iam-doc A2A AgentCard

Provides AgentCard for iam-doc, the documentation specialist.

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
    """Get iam-doc's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-doc")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-doc.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-doc/dev/us-central1/0.10.0",
    )

    description = f"""iam-doc - Documentation Specialist

**Identity:** {spiffe_id}

iam-doc generates After-Action Reports (AARs), updates README files, creates design docs, and manages 000-docs/ structure.
"""

    capabilities = [
        "aar_generation",
        "readme_maintenance",
        "design_documentation",
        "docs_structure_management",
    ]

    skills = [
        {
            "skill_id": "iam_doc.generate_aar",
            "name": "Generate After-Action Report",
            "description": "Generate comprehensive AAR for completed phase",
            "input_schema": {
                "type": "object",
                "required": ["phase_info"],
                "properties": {
                    "phase_info": {
                        "type": "object",
                        "required": ["phase_name", "objectives", "outcomes"],
                        "properties": {
                            "phase_name": {"type": "string"},
                            "objectives": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "outcomes": {"type": "object"},
                            "decisions": {"type": "array", "items": {"type": "object"}},
                            "lessons_learned": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    }
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["aar_document"],
                "properties": {
                    "aar_document": {
                        "type": "object",
                        "required": ["file_path", "content", "doc_id"],
                        "properties": {
                            "file_path": {"type": "string"},
                            "content": {"type": "string"},
                            "doc_id": {"type": "string"},
                            "sections": {"type": "array", "items": {"type": "string"}},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_doc.update_readme",
            "name": "Update README",
            "description": "Update README files with latest information",
            "input_schema": {
                "type": "object",
                "required": ["readme_path", "updates"],
                "properties": {
                    "readme_path": {"type": "string"},
                    "updates": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string"},
                            "content": {"type": "string"},
                            "operation": {
                                "type": "string",
                                "enum": ["add", "update", "remove"],
                            },
                        },
                    },
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["update_result"],
                "properties": {
                    "update_result": {
                        "type": "object",
                        "required": ["status", "updated_content"],
                        "properties": {
                            "status": {"type": "string", "enum": ["SUCCESS", "FAILED"]},
                            "updated_content": {"type": "string"},
                            "changes_summary": {"type": "string"},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_doc.create_design_doc",
            "name": "Create Design Document",
            "description": "Create architecture or design documentation",
            "input_schema": {
                "type": "object",
                "required": ["design_info"],
                "properties": {
                    "design_info": {
                        "type": "object",
                        "required": ["title", "overview"],
                        "properties": {
                            "title": {"type": "string"},
                            "overview": {"type": "string"},
                            "architecture": {"type": "object"},
                            "decisions": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["design_document"],
                "properties": {
                    "design_document": {
                        "type": "object",
                        "required": ["file_path", "content"],
                        "properties": {
                            "file_path": {"type": "string"},
                            "content": {"type": "string"},
                            "doc_type": {"type": "string"},
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
    """Get iam-doc's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-doc/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
