"""Web search tool for internet research.

Provides web search capabilities for Bob's MCP server:
- Search the web using search APIs
- Fetch and summarize web pages

Supports multiple backends:
- Google Custom Search API (requires GOOGLE_CSE_ID and GOOGLE_API_KEY)
- DuckDuckGo (no API key required, uses ddg library)

Phase H: Universal Tool Access
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    ToolResult,
    create_success_result,
    create_error_result,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")


# ============================================================================
# OUTPUT MODELS
# ============================================================================


class WebSearchResult(BaseModel):
    """Single web search result."""
    title: str = Field(description="Page title")
    url: str = Field(description="Page URL")
    snippet: str = Field(description="Result snippet/description")


class WebSearchOutput(ToolResult):
    """Structured output from web search tool."""

    query: str = Field(default="", description="Search query")
    results: List[WebSearchResult] = Field(
        default_factory=list, description="Search results"
    )
    result_count: int = Field(default=0, description="Number of results")
    backend: str = Field(default="", description="Search backend used")


# ============================================================================
# SEARCH BACKENDS
# ============================================================================


async def _search_google(query: str, limit: int = 10) -> List[WebSearchResult]:
    """Search using Google Custom Search API."""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID required")

    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": query,
                "num": min(limit, 10),
            }
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("items", []):
        results.append(WebSearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
        ))

    return results


async def _search_duckduckgo(query: str, limit: int = 10) -> List[WebSearchResult]:
    """Search using DuckDuckGo (no API key required)."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError("duckduckgo-search library not installed. Run: pip install duckduckgo-search")

    # Run in thread pool since ddgs is synchronous
    def do_search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=limit))

    loop = asyncio.get_event_loop()
    ddg_results = await loop.run_in_executor(None, do_search)

    results = []
    for item in ddg_results:
        results.append(WebSearchResult(
            title=item.get("title", ""),
            url=item.get("href", ""),
            snippet=item.get("body", ""),
        ))

    return results


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


async def execute(
    query: str,
    limit: int = 10,
    backend: Optional[str] = None
) -> WebSearchOutput:
    """
    Search the web for a query.

    Args:
        query: Search query string
        limit: Maximum results to return (default: 10)
        backend: Search backend to use ("google" or "duckduckgo", auto-detected if not specified)

    Returns:
        WebSearchOutput with search results
    """
    if not query:
        return create_error_result(
            WebSearchOutput, "web_search", "Query is required"
        )

    logger.info(f"Web search: {query}")

    # Auto-detect backend if not specified
    if backend is None:
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            backend = "google"
        else:
            backend = "duckduckgo"

    try:
        if backend == "google":
            results = await _search_google(query, limit)
        elif backend == "duckduckgo":
            results = await _search_duckduckgo(query, limit)
        else:
            return create_error_result(
                WebSearchOutput, "web_search",
                f"Unknown backend: {backend}. Valid: google, duckduckgo"
            )

        return create_success_result(
            WebSearchOutput,
            "web_search",
            query=query,
            results=results,
            result_count=len(results),
            backend=backend,
        )

    except ImportError as e:
        return create_error_result(WebSearchOutput, "web_search", str(e))
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return create_error_result(WebSearchOutput, "web_search", str(e))
