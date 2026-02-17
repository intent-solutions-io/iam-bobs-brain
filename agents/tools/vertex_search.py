"""
Vertex AI Search Tool Factory

Provides tool factory functions for creating Vertex AI Search tools for
Bob (orchestrator) and iam-senior-adk-devops-lead (foreman).

Uses centralized RAG configuration from agents.config.rag.
"""

import sys
from pathlib import Path
from typing import Literal, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.rag import (
    VertexSearchConfig,
    get_bob_vertex_search_config,
    get_current_env,
    get_foreman_vertex_search_config,
)


class VertexSearchToolStub:
    """
    Stub for Vertex AI Search tool.

    TODO: Replace with actual ADK Vertex Search tool when wiring to real datastores.
    For now, this provides the interface and configuration structure.
    """

    def __init__(self, config: VertexSearchConfig, agent_name: str):
        """
        Initialize Vertex Search tool stub.

        Args:
            config: VertexSearchConfig with project, location, datastore
            agent_name: Name of the agent using this tool (for logging)
        """
        self.config = config
        self.agent_name = agent_name

    def search(self, query: str, max_results: int = 10) -> dict:
        """
        Search the configured Vertex AI Search datastore.

        TODO: Replace with actual Vertex AI Search API call.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            Dictionary with search results
        """
        # Stub implementation
        return {
            "query": query,
            "results": [],
            "datastore": self.config.datastore_id,
            "env": self.config.env,
            "message": "TODO: Wire to real Vertex AI Search API"
        }

    def __repr__(self) -> str:
        return (
            f"VertexSearchToolStub("
            f"agent={self.agent_name}, "
            f"env={self.config.env}, "
            f"datastore={self.config.datastore_id})"
        )


def get_bob_vertex_search_tool(
    env: Optional[Literal["dev", "staging", "prod"]] = None
) -> VertexSearchToolStub:
    """
    Get Vertex AI Search tool for Bob (orchestrator).

    Uses centralized RAG configuration with environment-specific datastore.

    Args:
        env: Environment (auto-detected from DEPLOYMENT_ENV if not provided)

    Returns:
        VertexSearchToolStub configured for Bob

    Raises:
        ValueError: If RAG configuration is invalid

    Example:
        # Auto-detect environment
        tool = get_bob_vertex_search_tool()

        # Explicit environment
        tool = get_bob_vertex_search_tool(env="staging")

        # Use the tool
        results = tool.search("ADK agent patterns")
    """
    if env is None:
        env = get_current_env()

    config = get_bob_vertex_search_config(env)

    return VertexSearchToolStub(
        config=config,
        agent_name="bob"
    )


def get_foreman_vertex_search_tool(
    env: Optional[Literal["dev", "staging", "prod"]] = None
) -> VertexSearchToolStub:
    """
    Get Vertex AI Search tool for iam-senior-adk-devops-lead (foreman).

    Uses centralized RAG configuration with environment-specific datastore.

    Args:
        env: Environment (auto-detected from DEPLOYMENT_ENV if not provided)

    Returns:
        VertexSearchToolStub configured for foreman

    Raises:
        ValueError: If RAG configuration is invalid

    Example:
        # Auto-detect environment
        tool = get_foreman_vertex_search_tool()

        # Use the tool
        results = tool.search("ADK memory bank patterns")
    """
    if env is None:
        env = get_current_env()

    config = get_foreman_vertex_search_config(env)

    return VertexSearchToolStub(
        config=config,
        agent_name="iam-senior-adk-devops-lead"
    )


def get_vertex_search_tool_for_env(
    agent_name: str,
    env: Literal["dev", "staging", "prod"]
) -> VertexSearchToolStub:
    """
    Get Vertex AI Search tool for any agent in a specific environment.

    Generic factory function for custom agent configurations.

    Args:
        agent_name: Name of the agent (for logging)
        env: Explicit environment (dev/staging/prod)

    Returns:
        VertexSearchToolStub configured for the specified agent and environment

    Example:
        tool = get_vertex_search_tool_for_env("iam-adk", "staging")
    """
    # Use the same config source (extensible if agents need different configs)
    if agent_name == "bob":
        config = get_bob_vertex_search_config(env)
    elif agent_name == "iam-senior-adk-devops-lead":
        config = get_foreman_vertex_search_config(env)
    else:
        # Default: use base config
        from config.rag import get_vertex_search_config
        config = get_vertex_search_config(env)

    return VertexSearchToolStub(
        config=config,
        agent_name=agent_name
    )


# TODO: When wiring to real Vertex AI Search
# ============================================
#
# Replace VertexSearchToolStub with:
#
# from google.cloud import discoveryengine_v1alpha as discoveryengine
# from google.adk.tools import Tool
#
# def create_vertex_search_adk_tool(config: VertexSearchConfig) -> Tool:
#     """
#     Create actual ADK tool for Vertex AI Search.
#
#     Args:
#         config: VertexSearchConfig with project, location, datastore
#
#     Returns:
#         ADK Tool instance for Vertex AI Search
#     """
#     client = discoveryengine.SearchServiceClient()
#
#     serving_config = (
#         f"projects/{config.project_id}/locations/{config.location}/"
#         f"collections/default_collection/dataStores/{config.datastore_id}/"
#         f"servingConfigs/default_config"
#     )
#
#     def search(query: str, max_results: int = 10) -> dict:
#         request = discoveryengine.SearchRequest(
#             serving_config=serving_config,
#             query=query,
#             page_size=max_results
#         )
#         response = client.search(request)
#         return {"results": [r for r in response.results]}
#
#     return Tool(
#         name="vertex_search",
#         description="Search ADK documentation using Vertex AI Search",
#         func=search
#     )


# Example usage and testing
if __name__ == "__main__":
    print("🔍 Vertex AI Search Tool Factory Demo")
    print("=" * 60)

    try:
        # Get current environment
        env = get_current_env()
        print(f"\nCurrent Environment: {env}")

        # Create tools for Bob and foreman
        print("\n📦 Creating Vertex Search Tools...")

        bob_tool = get_bob_vertex_search_tool()
        print(f"✅ Bob tool: {bob_tool}")

        foreman_tool = get_foreman_vertex_search_tool()
        print(f"✅ Foreman tool: {foreman_tool}")

        # Test tool usage (stub)
        print("\n🔎 Testing search (stub)...")
        result = bob_tool.search("ADK agent patterns", max_results=5)
        print(f"Query: {result['query']}")
        print(f"Datastore: {result['datastore']}")
        print(f"Message: {result['message']}")

        print("\n✅ Tool factory working correctly")

    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\n💡 Set required environment variables:")
        print("   - VERTEX_SEARCH_PROJECT_ID")
        print("   - VERTEX_SEARCH_DATASTORE_ID_DEV (or _STAGING, _PROD)")

    print("\n" + "=" * 60)
