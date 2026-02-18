"""
Vertex AI Search Tool for ADK Documentation

Provides semantic search capabilities over ADK documentation using
Google Cloud Vertex AI Search (free 5GB tier).

This tool enables Bob to perform intelligent semantic searches that
understand meaning and context, not just keyword matching.
"""

import logging
import os

from google.cloud import discoveryengine_v1 as discoveryengine

logger = logging.getLogger(__name__)

# Environment configuration
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "global")  # Vertex AI Search uses 'global'
DATASTORE_ID = os.getenv("VERTEX_SEARCH_DATASTORE_ID", "adk-documentation")


def search_vertex_ai(
    query: str, max_results: int = 5, extract_answers: bool = True
) -> str:
    """
    Search ADK documentation using Vertex AI Search with semantic understanding.

    Uses Google Cloud Vertex AI Search (Discovery Engine) to perform intelligent
    semantic search over ADK documentation. Understands meaning and context beyond
    simple keyword matching.

    Args:
        query: Natural language search query (e.g., "How do I create a multi-agent system?")
        max_results: Maximum number of results to return (default: 5)
        extract_answers: Whether to extract direct answers from content (default: True)

    Returns:
        Formatted string with search results including:
        - Extracted answers (if extract_answers=True)
        - Relevant document snippets
        - Source file references
        - Relevance scores

    Examples:
        >>> search_vertex_ai("What is LlmAgent?")
        >>> search_vertex_ai("How to deploy to Vertex AI Agent Engine?", max_results=3)
        >>> search_vertex_ai("Multi-agent coordination patterns")

    Note:
        Requires:
        - PROJECT_ID environment variable
        - Vertex AI Search datastore created and indexed
        - google-cloud-discoveryengine package installed
        - Proper GCP authentication configured
    """
    try:
        # Validate configuration
        if not PROJECT_ID:
            return (
                "❌ **Configuration Error**\n\n"
                "PROJECT_ID environment variable not set.\n"
                "Required for Vertex AI Search.\n\n"
                "Set with: `export PROJECT_ID=your-project-id`"
            )

        # Create search client
        client = discoveryengine.SearchServiceClient()

        # Build serving config path
        # Format: projects/{project}/locations/{location}/collections/default_collection/dataStores/{datastore}/servingConfigs/default_config
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location=LOCATION,
            data_store=DATASTORE_ID,
            serving_config="default_config",
        )

        # Configure search request
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True, max_snippet_count=3
            ),
            summary_spec=(
                discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=max_results, include_citations=True
                )
                if extract_answers
                else None
            ),
            extractive_content_spec=(
                discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                    max_extractive_answer_count=1, max_extractive_segment_count=3
                )
                if extract_answers
                else None
            ),
        )

        # Create search request
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=max_results,
            content_search_spec=content_search_spec,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )

        # Execute search
        response = client.search(request)

        # Format results
        results = [
            f"🔍 **Vertex AI Search Results for:** '{query}'\n",
            f"**Datastore:** {DATASTORE_ID}\n\n",
        ]

        # Extract summary/answers if available
        if extract_answers and hasattr(response, "summary") and response.summary:
            summary_text = (
                response.summary.summary_text
                if hasattr(response.summary, "summary_text")
                else None
            )
            if summary_text:
                results.append(
                    f"📌 **AI-Generated Answer:**\n" f"{summary_text}\n\n" f"---\n\n"
                )

        # Process search results
        result_count = 0
        for result in response.results:
            result_count += 1
            document = result.document

            # Extract document metadata
            title = document.derived_struct_data.get("title", "Untitled")
            snippet = document.derived_struct_data.get("snippets", [{}])[0].get(
                "snippet", ""
            )
            link = document.derived_struct_data.get("link", "N/A")

            # Extract relevance score
            relevance_score = getattr(result, "relevance_score", None)
            score_display = (
                f" (score: {relevance_score:.3f})" if relevance_score else ""
            )

            results.append(
                f"**Result {result_count}:**{score_display}\n"
                f"- **Title:** {title}\n"
                f"- **Source:** `{link}`\n"
                f"- **Snippet:**\n"
                f"```\n{snippet}\n```\n\n"
            )

            # Add extractive answers if available
            if extract_answers and hasattr(document, "derived_struct_data"):
                extractive_answers = document.derived_struct_data.get(
                    "extractive_answers", []
                )
                for idx, answer in enumerate(
                    extractive_answers[:2], 1
                ):  # Max 2 answers per result
                    answer_text = answer.get("content", "")
                    if answer_text:
                        results.append(
                            f"  💡 **Extracted Answer {idx}:** {answer_text}\n\n"
                        )

        if result_count == 0:
            return (
                f"ℹ️ **No results found for:** '{query}'\n\n"
                f"Try:\n"
                f"- Rephrasing your query\n"
                f"- Using different keywords\n"
                f"- Checking if the datastore is properly indexed\n\n"
                f"💡 **Tip:** Vertex AI Search works best with natural language questions."
            )

        results.append(
            f"---\n\n"
            f"**Total Results:** {result_count}\n"
            f"**Query Understanding:** Semantic search with AI-powered relevance\n\n"
            f"💡 **Tip:** For keyword-only search, use `search_adk_docs()` instead."
        )

        return "".join(results)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in search_vertex_ai: {e}", exc_info=True)

        # Provide helpful error messages
        if "NOT_FOUND" in error_msg or "datastore" in error_msg.lower():
            return (
                f"❌ **Datastore Not Found**\n\n"
                f"The Vertex AI Search datastore '{DATASTORE_ID}' does not exist.\n\n"
                f"**Setup Required:**\n"
                f"1. Run setup script: `bash scripts/setup_vertex_search.sh`\n"
                f"2. Wait for indexing to complete (~10-15 minutes)\n"
                f"3. Verify datastore in GCP Console\n\n"
                f"**Error Details:** {error_msg}"
            )
        elif "PERMISSION_DENIED" in error_msg:
            return (
                f"❌ **Permission Denied**\n\n"
                f"Missing permissions for Vertex AI Search.\n\n"
                f"**Required IAM Roles:**\n"
                f"- Discovery Engine Viewer\n"
                f"- Discovery Engine Editor (for setup)\n\n"
                f"**Error Details:** {error_msg}"
            )
        else:
            return (
                f"❌ **Search Error**\n\n"
                f"An error occurred during Vertex AI Search:\n\n"
                f"```\n{error_msg}\n```\n\n"
                f"**Troubleshooting:**\n"
                f"- Check PROJECT_ID: {PROJECT_ID or 'NOT SET'}\n"
                f"- Check datastore: {DATASTORE_ID}\n"
                f"- Verify GCP authentication\n"
                f"- Check Cloud Console for datastore status"
            )


def get_vertex_search_status() -> str:
    """
    Check the status of Vertex AI Search datastore.

    Returns status information about the ADK documentation datastore including:
    - Datastore existence
    - Index status
    - Document count
    - Configuration details

    Returns:
        Formatted status report

    Example:
        >>> get_vertex_search_status()
    """
    try:
        if not PROJECT_ID:
            return (
                "❌ **Configuration Error**\n\n"
                "PROJECT_ID environment variable not set."
            )

        # Create client
        client = discoveryengine.DataStoreServiceClient()

        # Build datastore path
        datastore_path = client.data_store_path(
            project=PROJECT_ID, location=LOCATION, data_store=DATASTORE_ID
        )

        # Get datastore info
        datastore = client.get_data_store(name=datastore_path)

        # Format status
        result = [
            "📊 **Vertex AI Search Status**\n\n",
            f"**Datastore:** {datastore.display_name}\n",
            f"**ID:** {DATASTORE_ID}\n",
            f"**Project:** {PROJECT_ID}\n",
            f"**Location:** {LOCATION}\n",
            f"**Content Config:** {datastore.content_config}\n",
            "**Status:** ✅ Active\n\n",
        ]

        # Try to get document count (requires additional API call)
        try:
            doc_client = discoveryengine.DocumentServiceClient()
            parent = doc_client.branch_path(
                project=PROJECT_ID,
                location=LOCATION,
                data_store=DATASTORE_ID,
                branch="default_branch",
            )
            _documents = doc_client.list_documents(parent=parent, page_size=1)
            # Note: Getting exact count requires iterating all results
            result.append("**Documents:** Indexed (use GCP Console for exact count)\n")
        except Exception:
            result.append("**Documents:** Status unknown (check GCP Console)\n")

        result.append(
            "\n💡 **Next Steps:**\n"
            "- Search: `search_vertex_ai('your query')`\n"
            "- View in Console: https://console.cloud.google.com/gen-app-builder/engines\n"
        )

        return "".join(result)

    except Exception as e:
        error_msg = str(e)
        if "NOT_FOUND" in error_msg:
            return (
                f"ℹ️ **Datastore Not Found**\n\n"
                f"The datastore '{DATASTORE_ID}' does not exist yet.\n\n"
                f"**Setup Required:**\n"
                f"Run: `bash scripts/setup_vertex_search.sh`"
            )
        else:
            return f"❌ **Error checking status:** {error_msg}"


# Tool metadata for ADK agent integration
__all__ = ["get_vertex_search_status", "search_vertex_ai"]
