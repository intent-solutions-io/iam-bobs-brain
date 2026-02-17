"""
Bob's Brain - A2A AgentCard

Provides AgentCard for Agent-to-Agent (A2A) protocol discovery.

Enforces:
- R7: SPIFFE ID included in description
"""

import logging
import os

from a2a.types import AgentCapabilities, AgentCard

logger = logging.getLogger(__name__)

# Environment variables
APP_NAME = os.getenv("APP_NAME", "bobs-brain")
APP_VERSION = os.getenv("APP_VERSION", "0.6.0")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://example.com")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/unknown/unknown/unknown",
)


def get_agent_card() -> AgentCard:
    """
    Create AgentCard for A2A protocol discovery.

    The AgentCard provides metadata about this agent to other agents
    in multi-agent systems, enabling A2A protocol communication.

    Enforces R7: SPIFFE ID must be included in description.

    Returns:
        AgentCard: Agent metadata for discovery

    Example:
        >>> card = get_agent_card()
        >>> print(card.name)
        'bobs-brain'
        >>> print(card.url)
        'https://a2a-gateway.example.com'
    """
    logger.info(
        f"Creating AgentCard for {APP_NAME} v{APP_VERSION}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # R7: Include SPIFFE ID in description
    description = f"""Bob's Brain - AI Assistant

Identity: {AGENT_SPIFFE_ID}

Capabilities:
- General question answering
- Information lookup
- Task execution via tools
- Multi-turn conversations with memory

This agent uses dual memory (Session + Memory Bank) for context retention
and is deployed on Vertex AI Agent Engine.

A2A Protocol: This agent can be invoked by other agents using the
Agent-to-Agent protocol for multi-agent orchestration.
"""

    card = AgentCard(
        name=APP_NAME,
        description=description.strip(),
        url=PUBLIC_URL,  # A2A gateway URL (service/a2a_gateway/)
        version=APP_VERSION,
        capabilities=AgentCapabilities(),  # Default capabilities
        defaultInputModes=["text"],  # Accept text input
        defaultOutputModes=["text"],  # Return text output
        skills=[],  # Define available skills/capabilities here
    )

    logger.info(
        f"✅ AgentCard created: {APP_NAME} v{APP_VERSION}",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "url": PUBLIC_URL,
            "skills_count": len(card.skills),
        },
    )

    return card


def get_agent_card_dict() -> dict:
    """
    Get AgentCard as dictionary (for HTTP responses).

    Returns:
        dict: AgentCard serialized as JSON-compatible dict

    Example:
        >>> card_dict = get_agent_card_dict()
        >>> print(card_dict["name"])
        'bobs-brain'
    """
    card = get_agent_card()

    return {
        "name": card.name,
        "description": card.description,
        "url": card.url,
        "version": card.version,
        "skills": card.skills,
        "spiffe_id": AGENT_SPIFFE_ID,  # R7: Explicit SPIFFE field
    }


# For testing
if __name__ == "__main__":
    import json

    card = get_agent_card()
    card_dict = get_agent_card_dict()

    print("=" * 80)
    print("AgentCard for Bob's Brain")
    print("=" * 80)
    print(json.dumps(card_dict, indent=2))
    print("=" * 80)
