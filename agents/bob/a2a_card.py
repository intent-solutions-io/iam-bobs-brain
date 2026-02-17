"""
Bob's Brain - A2A AgentCard

Provides AgentCard for Bob, the ADK expert agent.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """
    AgentCard model for A2A protocol.

    Represents Bob's identity, capabilities, and skills.
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
    Get Bob's AgentCard.

    Returns:
        AgentCard with Bob's identity, capabilities, and skills

    Environment Variables Required:
        - APP_NAME: Application name (default: "bobs-brain")
        - APP_VERSION: Application version (default: "0.10.0")
        - PUBLIC_URL: Public URL for this agent (default: "https://bob.intent.solutions")
        - AGENT_SPIFFE_ID: SPIFFE ID (required per R7)
    """
    app_name = os.getenv("APP_NAME", "bobs-brain")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://bob.intent.solutions")
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0",
    )

    # Description with SPIFFE ID (R7 requirement)
    description = f"""Bob's Brain - Expert Google ADK Agent

**Identity:** {spiffe_id}

Bob is an expert Google Agent Development Kit (ADK) specialist who helps developers:
- Design and build AI agents using Google ADK
- Understand ADK architecture patterns and best practices
- Implement tools, multi-agent systems, and workflows
- Deploy agents to Vertex AI Agent Engine
- Debug agent issues and optimize performance
- Integrate with Google Cloud services (BigQuery, Vertex AI Search, Memory Bank)

Bob has access to comprehensive ADK documentation and can provide expert guidance with accurate code examples, deployment commands, and architectural recommendations based on official Google patterns.
"""

    # Capabilities (what Bob can do technically)
    capabilities = [
        "adk_expertise",
        "documentation_search",
        "code_examples",
        "deployment_guidance",
        "architecture_review",
    ]

    # Skills (specific tasks Bob can perform)
    skills = [
        {
            "skill_id": "bob.answer_adk_question",
            "name": "Answer ADK Question",
            "description": "Provide expert answers about Google ADK using documentation and examples",
            "input_schema": {
                "type": "object",
                "required": ["question"],
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about Google ADK",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context (optional)",
                    },
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["answer"],
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Expert answer with code examples and references",
                    },
                    "references": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Relevant documentation references",
                    },
                },
            },
        },
        {
            "skill_id": "bob.search_adk_docs",
            "name": "Search ADK Documentation",
            "description": "Search local and Vertex AI Search documentation for ADK information",
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum results to return",
                    },
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["results"],
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "source": {"type": "string"},
                            },
                        },
                    }
                },
            },
        },
        {
            "skill_id": "bob.provide_deployment_guidance",
            "name": "Provide Deployment Guidance",
            "description": "Guide users through deploying agents to Vertex AI Agent Engine",
            "input_schema": {
                "type": "object",
                "required": ["deployment_scenario"],
                "properties": {
                    "deployment_scenario": {
                        "type": "string",
                        "description": "Description of what needs to be deployed",
                    },
                    "current_setup": {
                        "type": "string",
                        "description": "Current environment setup (optional)",
                    },
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["steps", "commands"],
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Step-by-step deployment instructions",
                    },
                    "commands": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exact commands to run",
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
    Get Bob's AgentCard as a dictionary.

    Returns:
        Dict representation of AgentCard with explicit spiffe_id field (R7)
    """
    card = get_agent_card()
    card_dict = card.model_dump()

    # Add explicit SPIFFE ID field (R7 requirement)
    spiffe_id = os.getenv(
        "AGENT_SPIFFE_ID",
        "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.10.0",
    )
    card_dict["spiffe_id"] = spiffe_id

    return card_dict


# Module exports
__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
