"""
Bob's Brain - ADK Agent Implementation

This module contains the core agent implementation using Google ADK
with dual memory wiring (Session + Memory Bank).

Enforces R1 (ADK only), R2 (Agent Engine runtime), R5 (dual memory).

Phase 12 Update: Migrated to google-adk 1.18+ API (App pattern)
"""

from .agent import create_agent, create_runner, auto_save_session_to_memory, app

# NOTE: a2a_card import removed for Agent Engine deployment compatibility
# AgentCard is only needed by service/a2a_gateway/, not by the agent itself
# from .a2a_card import get_agent_card

__all__ = [
    "create_agent",  # Phase 12: renamed from get_agent
    "create_runner",
    "auto_save_session_to_memory",
    "app",  # Phase 12: App pattern for Agent Engine (was root_agent)
    # "get_agent_card",  # Only needed for gateway service
]
