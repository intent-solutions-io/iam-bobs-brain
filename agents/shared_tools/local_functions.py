"""
Local Function Tools Module

This module contains function tools that are pure Python code running
in the same process as the agent. These are custom tools we've defined
that do not require any external services.

All tools here run in-process within the Runner/Agent Engine.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ============================================================================
# LOCAL FUNCTION TOOLS - Pure Python running in agent process
# ============================================================================

# Re-export existing function tool collections
# These are all local Python functions with no external dependencies

def get_adk_docs_tools() -> List[Any]:
    """ADK documentation search tools (local functions)."""
    from .custom_tools import get_adk_docs_tools as _get_tools
    return _get_tools()


def get_analysis_tools() -> List[Any]:
    """Code analysis tools (local functions)."""
    from .custom_tools import get_analysis_tools as _get_tools
    return _get_tools()


def get_issue_management_tools() -> List[Any]:
    """Issue creation and formatting tools (local functions)."""
    from .custom_tools import get_issue_management_tools as _get_tools
    return _get_tools()


def get_planning_tools() -> List[Any]:
    """Fix planning tools (local functions)."""
    from .custom_tools import get_planning_tools as _get_tools
    return _get_tools()


def get_implementation_tools() -> List[Any]:
    """Code implementation tools (local functions)."""
    from .custom_tools import get_implementation_tools as _get_tools
    return _get_tools()


def get_qa_tools() -> List[Any]:
    """QA and testing tools (local functions)."""
    from .custom_tools import get_qa_tools as _get_tools
    return _get_tools()


def get_documentation_tools() -> List[Any]:
    """Documentation generation tools (local functions)."""
    from .custom_tools import get_documentation_tools as _get_tools
    return _get_tools()


def get_cleanup_tools() -> List[Any]:
    """Code cleanup and tech debt tools (local functions)."""
    from .custom_tools import get_cleanup_tools as _get_tools
    return _get_tools()


def get_indexing_tools() -> List[Any]:
    """Knowledge indexing tools (local functions)."""
    from .custom_tools import get_indexing_tools as _get_tools
    return _get_tools()


def get_delegation_tools() -> List[Any]:
    """Agent delegation tools (local functions)."""
    from .custom_tools import get_delegation_tools as _get_tools
    return _get_tools()


def get_vertex_search_status_tools() -> List[Any]:
    """Vertex Search status tools (local functions)."""
    from .custom_tools import get_vertex_search_tools as _get_tools
    return _get_tools()


# ============================================================================
# Example of a pure local function tool
# ============================================================================

def calculate_tool_metrics(agent_name: str) -> Dict[str, Any]:
    """
    Example local function tool that calculates metrics.

    This runs entirely in-process with no external dependencies.

    Args:
        agent_name: Name of the agent to analyze

    Returns:
        Metrics dictionary
    """
    # Pure Python logic - no external services
    metrics = {
        "agent": agent_name,
        "tools_loaded": 0,
        "local_tools": 0,
        "remote_tools": 0,
        "status": "calculated_locally"
    }

    # This is just an example - real implementation would count actual tools
    return metrics


# ============================================================================
# POLICY: All function tools here are in-process Python code
# ============================================================================
# These tools:
# - Are pure Python functions
# - Run in the same process as the agent
# - Do NOT make external service calls (except through ADK APIs)
# - Do NOT require Cloud Run or MCP servers
# - Can access local files, environment variables, and in-memory data
