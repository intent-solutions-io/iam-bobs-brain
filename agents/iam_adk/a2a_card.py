"""
iam-adk A2A AgentCard

Provides AgentCard for iam-adk, the ADK/Vertex design & static analysis specialist.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """
    AgentCard model for A2A protocol.

    Represents iam-adk's identity, capabilities, and skills.
    """
    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent version")
    url: str = Field(..., description="Agent public URL")
    description: str = Field(..., description="Agent description (must include SPIFFE ID per R7)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    default_input_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported input modes")
    default_output_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported output modes")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Agent skills")


def get_agent_card() -> AgentCard:
    """
    Get iam-adk's AgentCard.

    Returns:
        AgentCard with iam-adk's identity, capabilities, and skills

    Environment Variables Required:
        - APP_NAME: Application name (default: "iam-adk")
        - APP_VERSION: Application version (default: "0.10.0")
        - PUBLIC_URL: Public URL for this agent (default: "https://iam-adk.intent.solutions")
        - AGENT_SPIFFE_ID: SPIFFE ID (required per R7)
    """
    app_name = os.getenv("APP_NAME", "iam-adk")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-adk.intent.solutions")
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-adk/dev/us-central1/0.10.0")

    # Description with SPIFFE ID (R7 requirement)
    description = f"""iam-adk - ADK/Vertex Design & Static Analysis Specialist

**Identity:** {spiffe_id}

iam-adk specializes in analyzing ADK agent implementations for pattern compliance and best practices. Core expertise includes:
- Reviewing ADK agent code against Hard Mode rules (R1-R8)
- Analyzing Agent-to-Agent (A2A) communication patterns
- Validating AgentCard schemas and skill definitions
- Detecting ADK anti-patterns and architectural issues
- Producing structured AuditReports and IssueSpecs
- Recommending ADK best practices and improvements

This agent enforces google-adk patterns, Vertex AI Agent Engine compliance, and department adk iam standards.
"""

    # Capabilities (what iam-adk can do technically)
    capabilities = [
        "adk_pattern_analysis",
        "agentcard_validation",
        "hard_mode_compliance_checking",
        "audit_report_generation",
        "issue_spec_creation"
    ]

    # Skills (specific tasks iam-adk can perform)
    skills = [
        {
            "skill_id": "iam_adk.check_adk_compliance",
            "name": "Check ADK Compliance",
            "description": "Analyze agent code for ADK pattern compliance and Hard Mode rule violations",
            "input_schema": {
                "type": "object",
                "required": ["target"],
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "File path or directory to analyze"
                    },
                    "focus_rules": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
                        },
                        "description": "Specific Hard Mode rules to focus on (optional)"
                    },
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        "default": "LOW",
                        "description": "Only report issues at or above this severity"
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["compliance_status", "violations"],
                "properties": {
                    "compliance_status": {
                        "type": "string",
                        "enum": ["COMPLIANT", "NON_COMPLIANT", "WARNING"]
                    },
                    "violations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["severity", "message"],
                            "properties": {
                                "severity": {
                                    "type": "string",
                                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                                },
                                "rule": {
                                    "type": "string",
                                    "description": "Hard Mode rule violated (R1-R8) or null"
                                },
                                "message": {"type": "string"},
                                "file": {"type": "string"},
                                "line_number": {"type": "integer"}
                            }
                        }
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                    }
                }
            }
        },
        {
            "skill_id": "iam_adk.validate_agentcard",
            "name": "Validate AgentCard",
            "description": "Validate AgentCard structure, schemas, and compliance with A2A standards",
            "input_schema": {
                "type": "object",
                "required": ["agentcard_path"],
                "properties": {
                    "agentcard_path": {
                        "type": "string",
                        "description": "Path to agent directory or agentcard.json file"
                    },
                    "check_skills": {
                        "type": "boolean",
                        "default": True,
                        "description": "Validate skill schemas"
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["valid", "errors"],
                "properties": {
                    "valid": {"type": "boolean"},
                    "errors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["field", "message"],
                            "properties": {
                                "field": {"type": "string"},
                                "message": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["ERROR", "WARNING"]
                                }
                            }
                        }
                    },
                    "warnings": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        {
            "skill_id": "iam_adk.analyze_agent_architecture",
            "name": "Analyze Agent Architecture",
            "description": "Analyze agent architecture for ADK best practices and design patterns",
            "input_schema": {
                "type": "object",
                "required": ["agent_directory"],
                "properties": {
                    "agent_directory": {
                        "type": "string",
                        "description": "Path to agent directory"
                    },
                    "check_lazy_loading": {
                        "type": "boolean",
                        "default": True,
                        "description": "Check 6767-LAZY lazy loading pattern compliance"
                    },
                    "check_memory_wiring": {
                        "type": "boolean",
                        "default": True,
                        "description": "Check R5 dual memory wiring"
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["analysis_status", "findings"],
                "properties": {
                    "analysis_status": {
                        "type": "string",
                        "enum": ["PASS", "FAIL", "WARNING"]
                    },
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["category", "message", "severity"],
                            "properties": {
                                "category": {
                                    "type": "string",
                                    "description": "Finding category (lazy_loading, memory, tools, etc.)"
                                },
                                "message": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
                                },
                                "recommendation": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_adk.generate_audit_report",
            "name": "Generate Audit Report",
            "description": "Generate comprehensive ADK compliance audit report",
            "input_schema": {
                "type": "object",
                "required": ["scope"],
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Audit scope (repo, directory, agent)"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include fix recommendations"
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["audit_summary", "findings_count", "findings"],
                "properties": {
                    "audit_summary": {
                        "type": "object",
                        "required": ["compliant_agents", "non_compliant_agents", "total_agents"],
                        "properties": {
                            "compliant_agents": {"type": "integer"},
                            "non_compliant_agents": {"type": "integer"},
                            "total_agents": {"type": "integer"},
                            "risk_level": {
                                "type": "string",
                                "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                            }
                        }
                    },
                    "findings_count": {"type": "integer"},
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "description": "Individual compliance findings"
                        }
                    }
                }
            }
        }
    ]

    return AgentCard(
        name=app_name,
        version=app_version,
        url=public_url,
        description=description,
        capabilities=capabilities,
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=skills
    )


def get_agent_card_dict() -> Dict[str, Any]:
    """
    Get iam-adk's AgentCard as a dictionary.

    Returns:
        Dict representation of AgentCard with explicit spiffe_id field (R7)
    """
    card = get_agent_card()
    card_dict = card.model_dump()

    # Add explicit SPIFFE ID field (R7 requirement)
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-adk/dev/us-central1/0.10.0")
    card_dict["spiffe_id"] = spiffe_id

    return card_dict


# Module exports
__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
