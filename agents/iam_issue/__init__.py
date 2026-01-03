"""
iam-issue - Issue Tracking Specialist

Creates structured IssueSpec from problem descriptions.

Enforces R1 (ADK only), R2 (Agent Engine runtime), R5 (dual memory).

Phase 12 Update: Migrated to google-adk 1.18+ API (App pattern)

6767-LAZY compliant: ADK imports are lazy-loaded to allow non-ADK modules
(like github_issue_adapter) to be imported without triggering ADK dependencies.
"""

__all__ = [
    "get_agent",  # Creates the LlmAgent instance
    "create_runner",
    "auto_save_session_to_memory",
    "root_agent",  # Module-level agent for ADK deployment
]


def __getattr__(name):
    """Lazy-load ADK-dependent exports (6767-LAZY pattern)."""
    if name in __all__:
        from . import agent
        return getattr(agent, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
