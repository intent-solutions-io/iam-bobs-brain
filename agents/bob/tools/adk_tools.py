"""
ADK Documentation Tools

Tools for searching and retrieving information from local ADK documentation.

These tools enable Bob to access comprehensive Google ADK documentation
without requiring external API calls or internet connectivity.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Documentation directory path
DOCS_BASE_PATH = (
    Path(__file__).parent.parent.parent / "000-docs" / "google-reference" / "adk"
)


def search_adk_docs(query: str, max_results: int = 5, context_lines: int = 3) -> str:
    """
    Search local ADK documentation for relevant information.

    Searches across all ADK documentation files for keyword matches and returns
    the most relevant sections with context. Useful for finding specific ADK
    concepts, API references, patterns, or examples.

    Args:
        query: Search query string (keywords or phrases to search for)
        max_results: Maximum number of results to return (default: 5)
        context_lines: Number of context lines to include around each match (default: 3)

    Returns:
        Formatted string with search results including:
        - File name
        - Section heading (if available)
        - Matched content with context
        - Line numbers for reference

    Examples:
        >>> search_adk_docs("LlmAgent")
        >>> search_adk_docs("deploy agent_engine", max_results=3)
        >>> search_adk_docs("VertexAiSessionService")
    """
    try:
        if not DOCS_BASE_PATH.exists():
            return f"❌ Documentation directory not found: {DOCS_BASE_PATH}"

        # Get all markdown files
        doc_files = list(DOCS_BASE_PATH.glob("*.md"))

        if not doc_files:
            return f"❌ No documentation files found in {DOCS_BASE_PATH}"

        # Search query preprocessing
        search_terms = query.lower().split()
        results = []

        # Search each file
        for doc_file in doc_files:
            try:
                with open(doc_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Search for matches
                for i, line in enumerate(lines):
                    line_lower = line.lower()

                    # Check if any search term matches
                    if any(term in line_lower for term in search_terms):
                        # Extract context
                        start_idx = max(0, i - context_lines)
                        end_idx = min(len(lines), i + context_lines + 1)
                        context = lines[start_idx:end_idx]

                        # Find nearest heading (go backwards to find section)
                        heading = None
                        for j in range(i, -1, -1):
                            if lines[j].startswith("#"):
                                heading = lines[j].strip()
                                break

                        # Calculate relevance score (simple: count of matching terms)
                        score = sum(1 for term in search_terms if term in line_lower)

                        results.append(
                            {
                                "file": doc_file.name,
                                "line_num": i + 1,
                                "heading": heading or "N/A",
                                "context": "".join(context),
                                "score": score,
                                "matched_line": line.strip(),
                            }
                        )

            except Exception as e:
                logger.error(f"Error reading {doc_file}: {e}")
                continue

        if not results:
            return f"ℹ️ No matches found for query: '{query}'"

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Format top N results
        formatted_results = [
            f"📄 **Search Results for: '{query}'**\n",
            f"Found {len(results)} matches. Showing top {min(max_results, len(results))}:\n",
        ]

        for idx, result in enumerate(results[:max_results], 1):
            formatted_results.append(
                f"\n**Result {idx}:**\n"
                f"- **File:** `{result['file']}`\n"
                f"- **Section:** {result['heading']}\n"
                f"- **Line:** {result['line_num']}\n"
                f"- **Match:** `{result['matched_line'][:100]}{'...' if len(result['matched_line']) > 100 else ''}`\n"
                f"\n**Context:**\n```\n{result['context'].strip()}\n```\n"
            )

        return "".join(formatted_results)

    except Exception as e:
        logger.error(f"Error in search_adk_docs: {e}", exc_info=True)
        return f"❌ Error searching documentation: {e!s}"


def get_adk_api_reference(topic: str) -> str:
    """
    Get comprehensive API reference for a specific ADK topic.

    Retrieves detailed API information from the Python API reference documentation,
    including class definitions, methods, parameters, and usage examples.

    Args:
        topic: Topic to look up (e.g., "LlmAgent", "Runner", "VertexAiSessionService",
               "FunctionTool", "SequentialAgent", "InMemoryRunner")

    Returns:
        Formatted API reference with:
        - Class signature
        - Constructor parameters
        - Methods and properties
        - Usage examples (if available)
        - Related references

    Examples:
        >>> get_adk_api_reference("LlmAgent")
        >>> get_adk_api_reference("Runner")
        >>> get_adk_api_reference("VertexAiMemoryBankService")
    """
    try:
        api_ref_path = DOCS_BASE_PATH / "GOOGLE_ADK_PYTHON_API_REFERENCE.md"

        if not api_ref_path.exists():
            return f"❌ API reference not found: {api_ref_path}"

        with open(api_ref_path, encoding="utf-8") as f:
            content = f.read()

        # Search for topic (case-insensitive heading search)
        pattern = rf"^#+\s+{re.escape(topic)}(?:\s+Class)?.*$"
        match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

        if not match:
            # Try searching in content
            if topic.lower() in content.lower():
                # Find context around the match
                idx = content.lower().find(topic.lower())
                start = max(0, idx - 500)
                end = min(len(content), idx + 1500)
                snippet = content[start:end]

                return (
                    f"📚 **Partial Match for '{topic}':**\n\n"
                    f"Found reference in documentation. Showing relevant context:\n\n"
                    f"```\n{snippet.strip()}\n```\n\n"
                    f"💡 For complete details, search for: `search_adk_docs('{topic}')`"
                )
            else:
                return (
                    f"ℹ️ No API reference found for '{topic}'.\n\n"
                    f"Try searching with: `search_adk_docs('{topic}')` for related information."
                )

        # Extract section (from heading to next same-level heading or end)
        start_pos = match.start()
        heading_level = len(match.group().split()[0])  # Count # characters

        # Find next heading of same or higher level
        next_heading_pattern = rf"^#{{{1,{heading_level}}}}\s+"
        remaining_content = content[start_pos:]
        next_match = re.search(
            next_heading_pattern, remaining_content[1:], re.MULTILINE
        )

        if next_match:
            section = remaining_content[: next_match.start() + 1]
        else:
            section = remaining_content

        # Limit length (max 2000 chars for readability)
        if len(section) > 2000:
            section = section[:2000] + "\n\n...(content truncated)..."

        return (
            f"📚 **API Reference: {topic}**\n\n"
            f"{section.strip()}\n\n"
            f"---\n"
            f"💡 **Source:** GOOGLE_ADK_PYTHON_API_REFERENCE.md"
        )

    except Exception as e:
        logger.error(f"Error in get_adk_api_reference: {e}", exc_info=True)
        return f"❌ Error retrieving API reference: {e!s}"


def list_adk_documentation() -> str:
    """
    List all available ADK documentation files.

    Returns a formatted list of all available documentation files in the
    local ADK documentation directory, including file names, sizes, and
    brief descriptions (extracted from file headers).

    Returns:
        Formatted list of available documentation files

    Example:
        >>> list_adk_documentation()
    """
    try:
        if not DOCS_BASE_PATH.exists():
            return f"❌ Documentation directory not found: {DOCS_BASE_PATH}"

        doc_files = sorted(DOCS_BASE_PATH.glob("*.md"))

        if not doc_files:
            return f"❌ No documentation files found in {DOCS_BASE_PATH}"

        result = [
            "📚 **Available ADK Documentation:**\n",
            f"**Location:** `{DOCS_BASE_PATH}`\n\n",
        ]

        for doc_file in doc_files:
            size_kb = doc_file.stat().st_size / 1024

            # Try to extract first heading as description
            try:
                with open(doc_file, encoding="utf-8") as f:
                    first_lines = [next(f) for _ in range(5)]
                    description = None
                    for line in first_lines:
                        if line.startswith("#"):
                            description = line.strip("# \n")
                            break
                    if not description:
                        description = "ADK Documentation"
            except Exception:
                description = "ADK Documentation"

            result.append(
                f"- **{doc_file.name}** ({size_kb:.1f} KB)\n" f"  {description}\n"
            )

        result.append(
            "\n💡 **Usage:**\n"
            "- Search: `search_adk_docs('your query')`\n"
            "- API Reference: `get_adk_api_reference('ClassName')`\n"
        )

        return "".join(result)

    except Exception as e:
        logger.error(f"Error in list_adk_documentation: {e}", exc_info=True)
        return f"❌ Error listing documentation: {e!s}"


# Tool metadata for ADK agent integration
__all__ = ["get_adk_api_reference", "list_adk_documentation", "search_adk_docs"]
