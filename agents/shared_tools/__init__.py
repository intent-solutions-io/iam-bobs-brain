"""
Shared ADK Tools Layer for Bob's Brain Department

This module provides centralized tool profiles for all agents in the department.
Each agent gets a specific tool profile based on the principle of least privilege.

Tool Loading Strategy (Hybrid):
1. Static tools: ADK builtins, custom tools, Vertex Search (always loaded)
2. Dynamic tools: MCP tools from Cloud API Registry (when available)

The API Registry provides centralized governance for MCP-based tools while
static tools provide reliable fallback functionality.

Enforces:
- R1: ADK-only tools (no custom frameworks)
- R3: Gateway separation (tools don't access Runner directly)
- R7: Auth context propagation via header provider
- Security: No credentials or secrets in tool definitions
"""

from typing import List, Any
import logging

logger = logging.getLogger(__name__)

# Import tool constructors
from .adk_builtin import (
    get_google_search_tool,
    get_code_execution_tool,
    get_repo_search_tool_stub,
    get_bigquery_toolset,
    get_mcp_toolset,
)

from .custom_tools import (
    get_adk_docs_tools,
    get_vertex_search_tools,
    get_analysis_tools,
    get_issue_management_tools,
    get_planning_tools,
    get_implementation_tools,
    get_qa_tools,
    get_documentation_tools,
    get_cleanup_tools,
    get_indexing_tools,
    get_delegation_tools,
)

# Import org knowledge hub Vertex Search tools
from .vertex_search import (
    get_bob_vertex_search_tool,
    get_foreman_vertex_search_tool,
)

# Import API Registry for dynamic MCP tool discovery
from .api_registry import (
    get_tools_for_agent,
    get_mcp_toolset as get_registry_mcp_toolset,
    is_registry_available,
)


# ============================================================================
# TOOL PROFILES - Define which tools each agent can access
# ============================================================================


def _load_mcp_tools(agent_name: str) -> List[Any]:
    """
    Load MCP tools from Cloud API Registry for an agent.

    Tools are loaded dynamically at runtime based on registry configuration.
    This provides centralized governance - admins control tool access in the
    registry, not in agent code.

    Args:
        agent_name: Agent name (e.g., "bob", "iam-adk")

    Returns:
        List of MCP tool handles from registry, or empty list if unavailable
    """
    if not is_registry_available():
        logger.debug(f"API Registry not available for {agent_name}")
        return []

    try:
        mcp_tools = get_tools_for_agent(agent_name)
        if mcp_tools:
            logger.info(f"✅ Loaded {len(mcp_tools)} MCP tools for {agent_name} from registry")
        return mcp_tools
    except Exception as e:
        logger.warning(f"Could not load MCP tools for {agent_name}: {e}")
        return []


def get_bob_tools() -> List[Any]:
    """
    Bob's tool profile - Orchestrator with broad access.

    Bob needs:
    - Search capabilities (Google, ADK docs, Vertex AI)
    - Knowledge access via org knowledge hub
    - MCP tools from registry (repo ops, etc.)
    - Future: delegation to iam-* agents
    """
    tools = []

    # Core web search
    tools.append(get_google_search_tool())

    # ADK documentation tools
    tools.extend(get_adk_docs_tools())

    # Org Knowledge Hub RAG (new centralized approach)
    vertex_tool = get_bob_vertex_search_tool()
    if vertex_tool:
        tools.append(vertex_tool)
        logger.info("✅ Added org knowledge hub Vertex Search for Bob")

    # Legacy Vertex Search (backwards compatibility)
    tools.extend(get_vertex_search_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("bob"))

    logger.info(f"Loaded {len(tools)} tools for Bob")
    return tools


def get_foreman_tools() -> List[Any]:
    """
    iam-senior-adk-devops-lead tool profile - Departmental foreman.

    Foreman needs:
    - Delegation to specialists
    - Repository analysis
    - Compliance checking
    - RAG access to org knowledge hub
    - MCP tools from registry
    """
    tools = []

    # Delegation and management
    tools.extend(get_delegation_tools())

    # Analysis capabilities
    tools.append(get_google_search_tool())

    # Org Knowledge Hub RAG (same as Bob)
    vertex_tool = get_foreman_vertex_search_tool()
    if vertex_tool:
        tools.append(vertex_tool)
        logger.info("✅ Added org knowledge hub Vertex Search for Foreman")

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-senior-adk-devops-lead"))

    logger.info(f"Loaded {len(tools)} tools for Foreman")
    return tools


def get_iam_adk_tools() -> List[Any]:
    """
    iam-adk tool profile - ADK pattern specialist.

    Needs:
    - Code analysis
    - Pattern validation
    - ADK documentation access
    - MCP tools (repo ops, pattern checking)
    """
    tools = []

    # Core analysis tools
    tools.extend(get_analysis_tools())

    # Documentation access
    tools.extend(get_adk_docs_tools())
    tools.append(get_google_search_tool())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-adk"))

    logger.info(f"Loaded {len(tools)} tools for iam-adk")
    return tools


def get_iam_issue_tools() -> List[Any]:
    """
    iam-issue tool profile - Issue management specialist.

    Needs:
    - Issue creation and formatting
    - Problem analysis
    - Basic search
    - MCP tools (GitHub integration)
    """
    tools = []

    # Issue management
    tools.extend(get_issue_management_tools())

    # Basic search
    tools.append(get_google_search_tool())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-issue"))

    logger.info(f"Loaded {len(tools)} tools for iam-issue")
    return tools


def get_iam_fix_plan_tools() -> List[Any]:
    """
    iam-fix-plan tool profile - Solution planning specialist.

    Needs:
    - Planning and design tools
    - Dependency analysis
    - Documentation access
    - MCP tools (repo analysis)
    """
    tools = []

    # Planning tools
    tools.extend(get_planning_tools())

    # Research capabilities
    tools.append(get_google_search_tool())
    tools.extend(get_adk_docs_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-fix-plan"))

    logger.info(f"Loaded {len(tools)} tools for iam-fix-plan")
    return tools


def get_iam_fix_impl_tools() -> List[Any]:
    """
    iam-fix-impl tool profile - Implementation specialist.

    Needs:
    - Code generation and modification
    - Testing helpers
    - Documentation reference
    - MCP tools (repo ops, GitHub)
    """
    tools = []

    # Implementation tools
    tools.extend(get_implementation_tools())

    # Reference access
    tools.extend(get_adk_docs_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-fix-impl"))

    logger.info(f"Loaded {len(tools)} tools for iam-fix-impl")
    return tools


def get_iam_qa_tools() -> List[Any]:
    """
    iam-qa tool profile - Quality assurance specialist.

    Needs:
    - Test execution
    - Validation tools
    - Regression checking
    - MCP tools (pattern checking)
    """
    tools = []

    # QA tools
    tools.extend(get_qa_tools())

    # Documentation for validation
    tools.extend(get_adk_docs_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-qa"))

    logger.info(f"Loaded {len(tools)} tools for iam-qa")
    return tools


def get_iam_doc_tools() -> List[Any]:
    """
    iam-doc tool profile - Documentation specialist.

    Needs:
    - Documentation generation
    - Markdown formatting
    - Reference materials
    - MCP tools (repo search)
    """
    tools = []

    # Documentation tools
    tools.extend(get_documentation_tools())

    # Research and reference
    tools.append(get_google_search_tool())
    tools.extend(get_adk_docs_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-doc"))

    logger.info(f"Loaded {len(tools)} tools for iam-doc")
    return tools


def get_iam_cleanup_tools() -> List[Any]:
    """
    iam-cleanup tool profile - Technical debt specialist.

    Needs:
    - Code analysis for debt
    - Dependency checking
    - Archive tools
    - MCP tools (dependency analysis)
    """
    tools = []

    # Cleanup tools
    tools.extend(get_cleanup_tools())

    # Analysis support
    tools.append(get_google_search_tool())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-cleanup"))

    logger.info(f"Loaded {len(tools)} tools for iam-cleanup")
    return tools


def get_iam_index_tools() -> List[Any]:
    """
    iam-index tool profile - Knowledge management specialist.

    Needs:
    - Indexing and cataloging
    - Search integration
    - Knowledge base management
    - MCP tools (repo indexing)
    """
    tools = []

    # Indexing tools
    tools.extend(get_indexing_tools())

    # Search and retrieval
    tools.append(get_google_search_tool())
    tools.extend(get_vertex_search_tools())

    # MCP tools from Cloud API Registry (dynamic governance)
    tools.extend(_load_mcp_tools("iam-index"))

    logger.info(f"Loaded {len(tools)} tools for iam-index")
    return tools


# ============================================================================
# PROFILE EXPORTS - Easy imports for agents
# ============================================================================

# Export tool profiles
BOB_TOOLS = get_bob_tools()
FOREMAN_TOOLS = get_foreman_tools()
IAM_ADK_TOOLS = get_iam_adk_tools()
IAM_ISSUE_TOOLS = get_iam_issue_tools()
IAM_FIX_PLAN_TOOLS = get_iam_fix_plan_tools()
IAM_FIX_IMPL_TOOLS = get_iam_fix_impl_tools()
IAM_QA_TOOLS = get_iam_qa_tools()
IAM_DOC_TOOLS = get_iam_doc_tools()
IAM_CLEANUP_TOOLS = get_iam_cleanup_tools()
IAM_INDEX_TOOLS = get_iam_index_tools()

# Export functions for dynamic loading
__all__ = [
    # Tool getters
    "get_bob_tools",
    "get_foreman_tools",
    "get_iam_adk_tools",
    "get_iam_issue_tools",
    "get_iam_fix_plan_tools",
    "get_iam_fix_impl_tools",
    "get_iam_qa_tools",
    "get_iam_doc_tools",
    "get_iam_cleanup_tools",
    "get_iam_index_tools",
    # Direct profiles
    "BOB_TOOLS",
    "FOREMAN_TOOLS",
    "IAM_ADK_TOOLS",
    "IAM_ISSUE_TOOLS",
    "IAM_FIX_PLAN_TOOLS",
    "IAM_FIX_IMPL_TOOLS",
    "IAM_QA_TOOLS",
    "IAM_DOC_TOOLS",
    "IAM_CLEANUP_TOOLS",
    "IAM_INDEX_TOOLS",
    # API Registry exports
    "get_tools_for_agent",
    "get_registry_mcp_toolset",
    "is_registry_available",
]