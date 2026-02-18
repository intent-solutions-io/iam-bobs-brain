"""
iam-cleanup - Repository Hygiene and Cleanup Specialist

Detects dead code, unused dependencies, and structural issues.

Enforces R1 (ADK only), R2 (Agent Engine runtime), R5 (dual memory).

Phase 12 Update: Migrated to google-adk 1.18+ API (App pattern)
"""

from .agent import app, auto_save_session_to_memory, create_agent, create_runner

__all__ = [
    "app",  # Phase 12: App pattern for Agent Engine (was root_agent)
    "auto_save_session_to_memory",
    "create_agent",  # Phase 12: renamed from get_agent
    "create_runner",
]
