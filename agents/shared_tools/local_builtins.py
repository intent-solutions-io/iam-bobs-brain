"""
Local Built-in Tools Module

This module contains ADK built-in tools that run inside the agent runtime.
These tools are executed in-process by the Runner/Agent Engine.

No external services or Cloud Run deployments required.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# ADK BUILT-IN TOOLS - Run inside agent runtime
# ============================================================================

def get_google_search_tool() -> Any:
    """
    Get the Google Search tool from ADK.

    This is an ADK built-in tool that runs in the agent runtime.
    No external service required.
    """
    try:
        from google.adk.toolsets import GoogleSearchToolset
        toolset = GoogleSearchToolset()
        logger.info("✅ Loaded ADK GoogleSearchToolset (in-process)")
        return toolset
    except ImportError:
        logger.warning("GoogleSearchToolset not available, using stub")
        from .adk_builtin import create_tool_stub
        return create_tool_stub(
            "google_search",
            "Search the web using Google",
            "GoogleSearchToolset requires: pip install google-adk[search]"
        )


def get_code_execution_tool() -> Any:
    """
    Get the Code Execution tool from ADK.

    This tool runs in a sandboxed environment within Agent Engine.
    No separate Cloud Run service needed.
    """
    try:
        from google.adk.toolsets import CodeExecutionToolset
        toolset = CodeExecutionToolset()
        logger.info("✅ Loaded ADK CodeExecutionToolset (sandboxed in-engine)")
        return toolset
    except ImportError:
        logger.warning("CodeExecutionToolset not available, using stub")
        from .adk_builtin import create_tool_stub
        return create_tool_stub(
            "code_execution",
            "Execute Python code in sandbox",
            "CodeExecutionToolset requires Agent Engine deployment"
        )


def get_bigquery_toolset() -> Any:
    """
    Get the BigQuery toolset from ADK.

    This tool runs in the agent runtime but connects to BigQuery API.
    The tool itself is local; BigQuery is the remote service.
    """
    try:
        from google.adk.toolsets import BigQueryToolset
        project_id = os.getenv("PROJECT_ID")
        if project_id:
            toolset = BigQueryToolset(project_id=project_id)
            logger.info("✅ Loaded ADK BigQueryToolset (API client in-process)")
            return toolset
        else:
            logger.warning("PROJECT_ID not set for BigQuery")
            return None
    except ImportError:
        logger.warning("BigQueryToolset not available")
        return None


def get_vertex_ai_search_tool() -> Any:
    """
    Get the Vertex AI Search tool.

    This tool runs in the agent runtime but queries Vertex AI Search API.
    The tool is local; Vertex AI Search is the remote service.
    """
    try:
        from google.adk.toolsets import VertexAiSearchToolset

        # Support both old and new datastore configurations
        use_datahub = os.getenv("USE_DATAHUB", "false") == "true"

        if use_datahub:
            # Use new datahub configuration
            project_id = os.getenv("DATAHUB_PROJECT_ID", "datahub-intent")
            datastore_id = os.getenv("DATAHUB_DATASTORE_ID", "universal-knowledge-store")
        else:
            # Use existing Bob datastore
            project_id = os.getenv("PROJECT_ID", "bobs-brain")
            datastore_id = os.getenv("VERTEX_SEARCH_DATASTORE_ID", "bob-vertex-agent-datastore")

        location = os.getenv("LOCATION", "us")

        toolset = VertexAiSearchToolset(
            project_id=project_id,
            location=location,
            datastore_id=datastore_id
        )
        logger.info(f"✅ Loaded VertexAiSearchToolset (queries {datastore_id})")
        return toolset
    except ImportError:
        logger.warning("VertexAiSearchToolset not available")
        return None


# ============================================================================
# POLICY: All built-in tools run in the agent runtime
# ============================================================================
# These tools are:
# - Imported as Python libraries
# - Executed in the same process as the agent
# - Do NOT require separate Cloud Run services
# - May call external APIs (BigQuery, Vertex AI) but the tool itself is local
