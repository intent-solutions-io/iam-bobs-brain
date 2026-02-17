"""
A2A Protocol Data Types

Defines the core data structures for agent-to-agent communication.

Classes:
- AgentCard: Agent identity and capabilities for A2A discovery
- A2ATask: Request envelope for specialist invocation
- A2AResult: Response envelope from specialist
- A2AError: Exception raised for A2A protocol violations
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """
    AgentCard model for A2A protocol (R7 compliant).

    Represents an agent's identity, capabilities, and skills.
    This is the canonical type for AgentCard - individual agent
    a2a_card.py files should import from here.

    Fields:
        name: Agent name
        version: Agent version
        url: Agent public URL
        description: Agent description (must include SPIFFE ID per R7)
        capabilities: Agent capabilities list
        default_input_modes: Supported input modes (default: ["text"])
        default_output_modes: Supported output modes (default: ["text"])
        skills: Agent skills with input/output schemas
    """
    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent version")
    url: str = Field(..., description="Agent public URL")
    description: str = Field(..., description="Agent description (must include SPIFFE ID per R7)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    default_input_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported input modes")
    default_output_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported output modes")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Agent skills")


class A2ATask(BaseModel):
    """
    Task envelope for agent-to-agent delegation.

    This structure aligns with the foreman's AgentCard skill schemas,
    particularly iam_foreman.delegate_to_specialist.

    Fields:
        specialist: Agent directory name (e.g., "iam_adk")
        skill_id: Full skill identifier (e.g., "iam_adk.check_adk_compliance")
        payload: Input data matching the skill's input_schema
        context: Optional metadata (request_id, correlation_id, etc.)
        spiffe_id: Calling agent's SPIFFE ID (R7 propagation)
        mandate: Optional mandate for budget/authorization tracking (Phase B)
    """
    specialist: str = Field(..., description="Target specialist agent name")
    skill_id: str = Field(..., description="Full skill ID from AgentCard")
    payload: Dict[str, Any] = Field(..., description="Skill input matching input_schema")
    context: Dict[str, Any] = Field(default_factory=dict, description="Request context/metadata")
    spiffe_id: Optional[str] = Field(None, description="Caller's SPIFFE ID (R7)")
    mandate: Optional[Dict[str, Any]] = Field(None, description="Authorization mandate with budget limits (Phase B)")

    class Config:
        json_schema_extra = {
            "example": {
                "specialist": "iam_adk",
                "skill_id": "iam_adk.check_adk_compliance",
                "payload": {
                    "target": "agents/bob/agent.py",
                    "focus_rules": ["R1", "R5", "R7"]
                },
                "context": {
                    "request_id": "req_123",
                    "pipeline_run_id": "pipeline_456"
                },
                "spiffe_id": "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0"
            }
        }


class A2AResult(BaseModel):
    """
    Result envelope from specialist execution.

    This structure provides a consistent response format regardless of
    which specialist or skill was invoked.

    Fields:
        status: Execution status (SUCCESS, FAILED, PARTIAL)
        specialist: Echo of the specialist that was called
        skill_id: Echo of the skill that was invoked
        result: Skill output matching the skill's output_schema
        error: Error message if status is FAILED
        duration_ms: Execution time in milliseconds
        timestamp: ISO 8601 timestamp of completion
    """
    status: Literal["SUCCESS", "FAILED", "PARTIAL"] = Field(..., description="Execution status")
    specialist: str = Field(..., description="Specialist that executed")
    skill_id: str = Field(..., description="Skill that was invoked")
    result: Optional[Dict[str, Any]] = Field(None, description="Skill output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Execution time in ms")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Completion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "SUCCESS",
                "specialist": "iam_adk",
                "skill_id": "iam_adk.check_adk_compliance",
                "result": {
                    "compliance_report": {
                        "status": "COMPLIANT",
                        "violations": [],
                        "recommendations": ["Consider adding type hints"]
                    }
                },
                "duration_ms": 1250,
                "timestamp": "2025-11-22T12:34:56.789Z"
            }
        }


class A2AError(Exception):
    """
    Exception raised for A2A protocol violations or errors.

    Examples:
    - Specialist not found
    - Skill ID doesn't exist in AgentCard
    - Input payload doesn't match skill's input_schema shape
    - Specialist execution failure
    """
    def __init__(self, message: str, specialist: Optional[str] = None, skill_id: Optional[str] = None):
        self.specialist = specialist
        self.skill_id = skill_id
        super().__init__(message)

    def __str__(self):
        parts = [super().__str__()]
        if self.specialist:
            parts.append(f"specialist={self.specialist}")
        if self.skill_id:
            parts.append(f"skill_id={self.skill_id}")
        return " | ".join(parts)
