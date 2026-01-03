"""
Shared ADK Tools Layer for Bob's Brain Department

This module provides centralized tool profiles for all agents in the department.
Each agent gets a specific tool profile based on the principle of least privilege.

Enforces:
- R1: ADK-only tools (no custom frameworks)
- R3: Gateway separation (tools don't access Runner directly)
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
    get_workflow_tools,  # Phase P1: Sequential workflow tools
)

# Import org knowledge hub Vertex Search tools
from .vertex_search import (
    get_bob_vertex_search_tool,
    get_foreman_vertex_search_tool,
)


# ============================================================================
# TOOL PROFILES - Define which tools each agent can access
# ============================================================================

def get_bob_tools() -> List[Any]:
    """
    Bob's tool profile - Orchestrator with broad access.

    Bob needs:
    - Search capabilities (Google, ADK docs, Vertex AI)
    - Knowledge access via org knowledge hub
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

    # Future expansions (stubbed for now)
    # tools.append(get_repo_search_tool_stub())  # TODO: Wire when ready

    logger.info(f"Loaded {len(tools)} tools for Bob")
    return tools


def get_foreman_tools() -> List[Any]:
    """
    iam-senior-adk-devops-lead tool profile - Departmental foreman.

    Foreman needs:
    - Delegation to specialists
    - Workflow orchestration (Phase P1: SequentialAgent)
    - Repository analysis
    - Compliance checking
    - RAG access to org knowledge hub
    """
    tools = []

    # Delegation and management
    tools.extend(get_delegation_tools())

    # Phase P1: Workflow orchestration tools (SequentialAgent)
    tools.extend(get_workflow_tools())

    # Analysis capabilities
    tools.append(get_google_search_tool())

    # Org Knowledge Hub RAG (same as Bob)
    vertex_tool = get_foreman_vertex_search_tool()
    if vertex_tool:
        tools.append(vertex_tool)
        logger.info("✅ Added org knowledge hub Vertex Search for Foreman")

    # Future: repo tools when ready
    # tools.append(get_repo_search_tool_stub())

    logger.info(f"Loaded {len(tools)} tools for Foreman (includes workflow tools)")
    return tools


def get_iam_adk_tools() -> List[Any]:
    """
    iam-adk tool profile - ADK pattern specialist.

    Needs:
    - Code analysis
    - Pattern validation
    - ADK documentation access
    """
    tools = []

    # Core analysis tools
    tools.extend(get_analysis_tools())

    # Documentation access
    tools.extend(get_adk_docs_tools())
    tools.append(get_google_search_tool())

    logger.info(f"Loaded {len(tools)} tools for iam-adk")
    return tools


def get_iam_issue_tools() -> List[Any]:
    """
    iam-issue tool profile - Issue management specialist.

    Needs:
    - Issue creation and formatting
    - Problem analysis
    - Basic search
    """
    tools = []

    # Issue management
    tools.extend(get_issue_management_tools())

    # Basic search
    tools.append(get_google_search_tool())

    logger.info(f"Loaded {len(tools)} tools for iam-issue")
    return tools


def get_iam_fix_plan_tools() -> List[Any]:
    """
    iam-fix-plan tool profile - Solution planning specialist.

    Needs:
    - Planning and design tools
    - Dependency analysis
    - Documentation access
    """
    tools = []

    # Planning tools
    tools.extend(get_planning_tools())

    # Research capabilities
    tools.append(get_google_search_tool())
    tools.extend(get_adk_docs_tools())

    logger.info(f"Loaded {len(tools)} tools for iam-fix-plan")
    return tools


def get_iam_fix_impl_tools() -> List[Any]:
    """
    iam-fix-impl tool profile - Implementation specialist.

    Needs:
    - Code generation and modification
    - Testing helpers
    - Documentation reference
    """
    tools = []

    # Implementation tools
    tools.extend(get_implementation_tools())

    # Reference access
    tools.extend(get_adk_docs_tools())

    # Future: code execution when sandboxed
    # tools.append(get_code_execution_tool_stub())

    logger.info(f"Loaded {len(tools)} tools for iam-fix-impl")
    return tools


def get_iam_qa_tools() -> List[Any]:
    """
    iam-qa tool profile - Quality assurance specialist.

    Needs:
    - Test execution
    - Validation tools
    - Regression checking
    """
    tools = []

    # QA tools
    tools.extend(get_qa_tools())

    # Documentation for validation
    tools.extend(get_adk_docs_tools())

    logger.info(f"Loaded {len(tools)} tools for iam-qa")
    return tools


def get_iam_doc_tools() -> List[Any]:
    """
    iam-doc tool profile - Documentation specialist.

    Needs:
    - Documentation generation
    - Markdown formatting
    - Reference materials
    """
    tools = []

    # Documentation tools
    tools.extend(get_documentation_tools())

    # Research and reference
    tools.append(get_google_search_tool())
    tools.extend(get_adk_docs_tools())

    logger.info(f"Loaded {len(tools)} tools for iam-doc")
    return tools


def get_iam_cleanup_tools() -> List[Any]:
    """
    iam-cleanup tool profile - Technical debt specialist.

    Needs:
    - Code analysis for debt
    - Dependency checking
    - Archive tools
    """
    tools = []

    # Cleanup tools
    tools.extend(get_cleanup_tools())

    # Analysis support
    tools.append(get_google_search_tool())

    logger.info(f"Loaded {len(tools)} tools for iam-cleanup")
    return tools


def get_iam_index_tools() -> List[Any]:
    """
    iam-index tool profile - Knowledge management specialist.

    Needs:
    - Indexing and cataloging
    - Search integration
    - Knowledge base management
    """
    tools = []

    # Indexing tools
    tools.extend(get_indexing_tools())

    # Search and retrieval
    tools.append(get_google_search_tool())
    tools.extend(get_vertex_search_tools())

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
]