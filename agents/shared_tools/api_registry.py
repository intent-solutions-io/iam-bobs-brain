"""
Cloud API Registry Client for Bob's Brain

This module provides runtime tool discovery via Google Cloud API Registry.
Agents fetch their approved tools from the registry instead of hardcoding them.

Key benefits:
- Centralized tool governance
- Dynamic discovery (no redeploy to add tools)
- Audit trail of tool access
- IAM-based access control

Hard Mode Compliance:
- R1: Uses google.adk.tools.ApiRegistry (ADK native)
- R7: Header provider propagates auth context
"""

from typing import Optional, Any, List, Callable
import logging
import os

logger = logging.getLogger(__name__)

# Lazy singleton for registry client
_registry_instance: Optional[Any] = None


def get_api_registry() -> Optional[Any]:
    """
    Get or initialize the Cloud API Registry client.

    Uses lazy singleton pattern (6767-LAZY compliant).
    Returns None if registry is not available or not configured.

    Returns:
        ApiRegistry instance or None
    """
    global _registry_instance

    if _registry_instance is not None:
        return _registry_instance

    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        logger.warning("PROJECT_ID not set - ApiRegistry disabled")
        return None

    try:
        from google.adk.tools import ApiRegistry

        header_provider = _get_header_provider()

        _registry_instance = ApiRegistry(
            project_id=project_id,
            header_provider=header_provider
        )
        logger.info(f"Initialized ApiRegistry for project: {project_id}")
        return _registry_instance

    except ImportError:
        logger.info("ApiRegistry not available in this ADK version - using fallback")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize ApiRegistry: {e}")
        return None


def _get_header_provider() -> Optional[Callable[[], dict]]:
    """
    Get header provider for auth context propagation.

    R7 compliance: Propagates caller identity to MCP servers.

    Returns:
        Callable that returns auth headers, or None
    """
    try:
        from google.auth import default
        from google.auth.transport.requests import Request

        credentials, _ = default()

        def header_provider() -> dict:
            credentials.refresh(Request())
            return {"Authorization": f"Bearer {credentials.token}"}

        return header_provider
    except Exception as e:
        logger.warning(f"Could not create header provider: {e}")
        return None


def get_tools_for_agent(agent_name: str) -> List[Any]:
    """
    Fetch all approved tools for a specific agent from the registry.

    The registry determines which MCP servers this agent can access
    based on IAM bindings. Agent code does NOT hardcode tool lists.

    Args:
        agent_name: The agent requesting tools (e.g., "iam-adk", "bob")

    Returns:
        List of tool handles from approved MCP servers, or empty list
    """
    registry = get_api_registry()
    if registry is None:
        logger.info(f"Registry unavailable for {agent_name} - returning empty tools")
        return []

    try:
        # Registry returns tools this agent is authorized to use
        tools = registry.get_agent_tools(agent_name)
        logger.info(f"Loaded {len(tools)} tools for {agent_name} from registry")
        return tools
    except AttributeError:
        # API might be different - try alternative method
        logger.info(f"get_agent_tools not available, trying get_toolset")
        return _get_tools_via_toolset(registry, agent_name)
    except Exception as e:
        logger.error(f"Failed to get tools for {agent_name}: {e}")
        return []


def _get_tools_via_toolset(registry: Any, agent_name: str) -> List[Any]:
    """
    Alternative method to get tools using get_toolset.

    Some API versions use MCP server names instead of agent names.
    """
    try:
        # Map agent names to their allowed MCP servers
        # bobs-mcp is the main MCP server in this repo (mcp/ directory)
        agent_mcp_mapping = {
            "bob": ["bobs-mcp"],
            "iam-senior-adk-devops-lead": ["bobs-mcp"],
            "iam-adk": ["bobs-mcp"],
            "iam-issue": ["bobs-mcp"],
            "iam-fix-plan": ["bobs-mcp"],
            "iam-fix-impl": ["bobs-mcp"],
            "iam-qa": ["bobs-mcp"],
            "iam-doc": ["bobs-mcp"],
            "iam-cleanup": ["bobs-mcp"],
            "iam-index": ["bobs-mcp"],
        }

        mcp_servers = agent_mcp_mapping.get(agent_name, [])
        if not mcp_servers:
            logger.warning(f"No MCP servers mapped for agent: {agent_name}")
            return []

        project_id = os.getenv("PROJECT_ID", "")
        tools = []

        for server_name in mcp_servers:
            try:
                server_resource = f"projects/{project_id}/locations/global/mcpServers/{server_name}"
                toolset = registry.get_toolset(mcp_server_name=server_resource)
                tools.append(toolset)
                logger.info(f"Loaded toolset from {server_name} for {agent_name}")
            except Exception as e:
                logger.warning(f"Could not load {server_name}: {e}")

        return tools
    except Exception as e:
        logger.error(f"Failed in _get_tools_via_toolset: {e}")
        return []


def get_mcp_toolset(
    mcp_server_name: str,
    tool_filter: Optional[List[str]] = None
) -> Optional[Any]:
    """
    Fetch tools from a specific registered MCP server.

    Args:
        mcp_server_name: Short name (e.g., "mcp-repo-ops") or full resource name
        tool_filter: Optional list of specific tool names to fetch

    Returns:
        Toolset from the MCP server, or None
    """
    registry = get_api_registry()
    if registry is None:
        return None

    project_id = os.getenv("PROJECT_ID", "")

    # Build full resource name if needed
    if not mcp_server_name.startswith("projects/"):
        mcp_server_name = f"projects/{project_id}/locations/global/mcpServers/{mcp_server_name}"

    try:
        if tool_filter:
            toolset = registry.get_toolset(
                mcp_server_name=mcp_server_name,
                tool_filter=tool_filter
            )
        else:
            toolset = registry.get_toolset(mcp_server_name=mcp_server_name)

        logger.info(f"Fetched toolset from {mcp_server_name}")
        return toolset
    except Exception as e:
        logger.error(f"Failed to fetch toolset from {mcp_server_name}: {e}")
        return None


# Registry availability check for health endpoints
def is_registry_available() -> bool:
    """Check if API Registry is available and configured."""
    return get_api_registry() is not None
