"""
iam-fix-plan A2A AgentCard

Provides AgentCard for iam-fix-plan, the fix planning & implementation strategy specialist.

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
    description: str = Field(..., description="Agent description (must include SPIFFE ID per R7)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    default_input_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported input modes")
    default_output_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported output modes")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Agent skills")


def get_agent_card() -> AgentCard:
    """Get iam-fix-plan's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-fix-plan")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-fix-plan.intent.solutions")
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-fix-plan/dev/us-central1/0.10.0")

    description = f"""iam-fix-plan - Fix Planning & Implementation Strategy Specialist

**Identity:** {spiffe_id}

iam-fix-plan converts IssueSpecs into concrete FixPlan implementations with clear strategies, risk assessments, and testing plans.
"""

    capabilities = ["fix_strategy_design", "risk_assessment", "implementation_planning", "testing_strategy", "rollback_planning"]

    skills = [
        {
            "skill_id": "iam_fix_plan.create_fix_plan",
            "name": "Create Fix Plan",
            "description": "Convert IssueSpec into detailed FixPlan with implementation steps",
            "input_schema": {
                "type": "object",
                "required": ["issue_spec"],
                "properties": {
                    "issue_spec": {"type": "object"},
                    "constraints": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["fix_plan"],
                "properties": {
                    "fix_plan": {
                        "type": "object",
                        "required": ["strategy", "steps", "risk_level"],
                        "properties": {
                            "strategy": {"type": "string"},
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                            "estimated_effort": {"type": "string"},
                            "rollback_plan": {"type": "string"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_fix_plan.assess_fix_risk",
            "name": "Assess Fix Risk",
            "description": "Assess risk level and impact of proposed fix",
            "input_schema": {
                "type": "object",
                "required": ["proposed_fix"],
                "properties": {"proposed_fix": {"type": "object"}}
            },
            "output_schema": {
                "type": "object",
                "required": ["risk_assessment"],
                "properties": {
                    "risk_assessment": {
                        "type": "object",
                        "required": ["risk_level", "impact_areas"],
                        "properties": {
                            "risk_level": {"type": "string"},
                            "impact_areas": {"type": "array", "items": {"type": "string"}},
                            "mitigation_steps": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_fix_plan.design_testing_strategy",
            "name": "Design Testing Strategy",
            "description": "Design comprehensive testing strategy for fix validation",
            "input_schema": {
                "type": "object",
                "required": ["fix_plan"],
                "properties": {"fix_plan": {"type": "object"}}
            },
            "output_schema": {
                "type": "object",
                "required": ["testing_strategy"],
                "properties": {
                    "testing_strategy": {
                        "type": "object",
                        "required": ["test_types", "coverage_requirements"],
                        "properties": {
                            "test_types": {"type": "array", "items": {"type": "string"}},
                            "coverage_requirements": {"type": "object"},
                            "smoke_tests": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        }
    ]

    return AgentCard(name=app_name, version=app_version, url=public_url, description=description,
                     capabilities=capabilities, default_input_modes=["text"], default_output_modes=["text"], skills=skills)


def get_agent_card_dict() -> Dict[str, Any]:
    """Get iam-fix-plan's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-fix-plan/dev/us-central1/0.10.0")
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
