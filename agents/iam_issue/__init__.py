"""
iam-issue - Issue Tracking Specialist

Creates structured IssueSpec from problem descriptions.

Enforces R1 (ADK only), R2 (Agent Engine runtime), R5 (dual memory).

Phase 12 Update: Migrated to google-adk 1.18+ API (App pattern)
"""

from .agent import get_agent, create_runner, auto_save_session_to_memory, root_agent

__all__ = [
    "get_agent",  # Creates the LlmAgent instance
    "create_runner",
    "auto_save_session_to_memory",
    "root_agent",  # Module-level agent for ADK deployment
]
