"""
iam-qa A2A AgentCard

Provides AgentCard for iam-qa, the testing & quality assurance specialist.

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
    """Get iam-qa's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-qa")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-qa.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-qa/dev/us-central1/0.10.0",
    )

    description = f"""iam-qa - Testing & Quality Assurance Specialist

**Identity:** {spiffe_id}

iam-qa designs test suites, validates coverage, runs smoke tests, and produces QAVerdict verdicts for deployment decisions.
"""

    capabilities = [
        "test_design",
        "coverage_validation",
        "smoke_testing",
        "qa_verdict_generation",
    ]

    skills = [
        {
            "skill_id": "iam_qa.design_test_suite",
            "name": "Design Test Suite",
            "description": "Design comprehensive test suite for implemented changes",
            "input_schema": {
                "type": "object",
                "required": ["implementation"],
                "properties": {
                    "implementation": {"type": "object"},
                    "coverage_target": {"type": "number", "default": 80},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["test_suite"],
                "properties": {
                    "test_suite": {
                        "type": "object",
                        "required": ["test_cases", "estimated_coverage"],
                        "properties": {
                            "test_cases": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                            "estimated_coverage": {"type": "number"},
                            "test_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_qa.validate_test_coverage",
            "name": "Validate Test Coverage",
            "description": "Validate that test coverage meets quality standards",
            "input_schema": {
                "type": "object",
                "required": ["test_results"],
                "properties": {
                    "test_results": {"type": "object"},
                    "min_coverage": {"type": "number", "default": 80},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["coverage_valid", "coverage_percentage"],
                "properties": {
                    "coverage_valid": {"type": "boolean"},
                    "coverage_percentage": {"type": "number"},
                    "gaps": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        {
            "skill_id": "iam_qa.run_smoke_tests",
            "name": "Run Smoke Tests",
            "description": "Execute smoke tests for basic functionality validation",
            "input_schema": {
                "type": "object",
                "required": ["target"],
                "properties": {
                    "target": {"type": "string"},
                    "test_scope": {"type": "string"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["smoke_test_results"],
                "properties": {
                    "smoke_test_results": {
                        "type": "object",
                        "required": ["passed", "failed", "status"],
                        "properties": {
                            "passed": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "status": {"type": "string", "enum": ["PASS", "FAIL"]},
                            "failures": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                },
            },
        },
        {
            "skill_id": "iam_qa.generate_qa_verdict",
            "name": "Generate QA Verdict",
            "description": "Produce QA verdict for deployment decision",
            "input_schema": {
                "type": "object",
                "required": ["test_results", "coverage_analysis"],
                "properties": {
                    "test_results": {"type": "object"},
                    "coverage_analysis": {"type": "object"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["verdict"],
                "properties": {
                    "verdict": {
                        "type": "object",
                        "required": ["decision", "confidence"],
                        "properties": {
                            "decision": {
                                "type": "string",
                                "enum": ["APPROVE", "REJECT", "CONDITIONAL"],
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["HIGH", "MEDIUM", "LOW"],
                            },
                            "blocking_issues": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string"},
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
    """Get iam-qa's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/iam-qa/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
