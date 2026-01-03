"""
iam-senior-adk-devops-lead A2A AgentCard

Provides AgentCard for iam-senior-adk-devops-lead, the ADK department foreman.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import List, Dict, Any
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
    """Get iam-senior-adk-devops-lead's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-senior-adk-devops-lead")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-senior-adk-devops-lead.intent.solutions")
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0")

    description = f"""iam-senior-adk-devops-lead - ADK Department Foreman

**Identity:** {spiffe_id}

iam-senior-adk-devops-lead orchestrates the IAM specialist agents, delegates tasks, coordinates workflows, and ensures quality across the department.
"""

    capabilities = ["task_orchestration", "specialist_delegation", "workflow_coordination", "quality_control", "progress_tracking"]

    skills = [
        {
            "skill_id": "iam_foreman.plan_task",
            "name": "Plan Task",
            "description": "Break down high-level task into specialist assignments",
            "input_schema": {
                "type": "object",
                "required": ["task_description"],
                "properties": {
                    "task_description": {"type": "string"},
                    "constraints": {"type": "object"},
                    "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["task_plan"],
                "properties": {
                    "task_plan": {
                        "type": "object",
                        "required": ["steps", "assigned_specialists"],
                        "properties": {
                            "steps": {"type": "array", "items": {"type": "object"}},
                            "assigned_specialists": {"type": "array", "items": {"type": "string"}},
                            "estimated_duration": {"type": "string"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_foreman.delegate_to_specialist",
            "name": "Delegate to Specialist",
            "description": "Assign task to appropriate IAM specialist agent",
            "input_schema": {
                "type": "object",
                "required": ["specialist", "task"],
                "properties": {
                    "specialist": {"type": "string", "enum": ["iam_adk", "iam_issue", "iam_fix_plan", "iam_fix_impl", "iam_qa", "iam_doc", "iam_cleanup", "iam_index"]},
                    "task": {"type": "object"},
                    "context": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["delegation_result"],
                "properties": {
                    "delegation_result": {
                        "type": "object",
                        "required": ["status", "specialist", "result"],
                        "properties": {
                            "status": {"type": "string", "enum": ["SUCCESS", "FAILED", "PENDING"]},
                            "specialist": {"type": "string"},
                            "result": {"type": "object"},
                            "duration_ms": {"type": "integer"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_foreman.coordinate_workflow",
            "name": "Coordinate Workflow",
            "description": "Orchestrate multi-step workflow across specialists",
            "input_schema": {
                "type": "object",
                "required": ["workflow_definition"],
                "properties": {
                    "workflow_definition": {
                        "type": "object",
                        "required": ["steps"],
                        "properties": {
                            "steps": {"type": "array", "items": {"type": "object"}},
                            "dependencies": {"type": "object"}
                        }
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["workflow_result"],
                "properties": {
                    "workflow_result": {
                        "type": "object",
                        "required": ["status", "completed_steps"],
                        "properties": {
                            "status": {"type": "string", "enum": ["COMPLETE", "IN_PROGRESS", "FAILED"]},
                            "completed_steps": {"type": "integer"},
                            "total_steps": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_foreman.aggregate_results",
            "name": "Aggregate Results",
            "description": "Combine and synthesize results from multiple specialists",
            "input_schema": {
                "type": "object",
                "required": ["specialist_results"],
                "properties": {
                    "specialist_results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "specialist": {"type": "string"},
                                "result": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["aggregated_result"],
                "properties": {
                    "aggregated_result": {
                        "type": "object",
                        "required": ["summary", "details"],
                        "properties": {
                            "summary": {"type": "string"},
                            "details": {"type": "object"},
                            "recommendations": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_foreman.check_quality",
            "name": "Check Quality",
            "description": "Validate work quality and compliance before delivery",
            "input_schema": {
                "type": "object",
                "required": ["work_product"],
                "properties": {
                    "work_product": {"type": "object"},
                    "quality_criteria": {"type": "array", "items": {"type": "string"}}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["quality_verdict"],
                "properties": {
                    "quality_verdict": {
                        "type": "object",
                        "required": ["passed", "checks_run"],
                        "properties": {
                            "passed": {"type": "boolean"},
                            "checks_run": {"type": "integer"},
                            "checks_failed": {"type": "integer"},
                            "issues": {"type": "array", "items": {"type": "string"}},
                            "recommendations": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        }
    ]

    return AgentCard(name=app_name, version=app_version, url=public_url, description=description,
                     capabilities=capabilities, default_input_modes=["text"], default_output_modes=["text"], skills=skills)


def get_agent_card_dict() -> Dict[str, Any]:
    """Get iam-senior-adk-devops-lead's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0")
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
