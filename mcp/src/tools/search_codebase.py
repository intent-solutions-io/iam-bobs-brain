"""Search codebase tool."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    SearchResult,
    SearchMatch,
    create_success_result,
    create_error_result,
)

logger = logging.getLogger(__name__)
MAX_RESULTS = 50


async def execute(query: str, path: str = ".", file_pattern: str = "*.py") -> SearchResult:
    """
    Search codebase for a pattern.

    Args:
        query: Search pattern (regex supported by rg/grep)
        path: Directory to search (default: current directory)
        file_pattern: File glob pattern (default: *.py)

    Returns:
        SearchResult with matches, metadata, and truncation info
    """
    if not query:
        return create_error_result(
            SearchResult, "search_codebase", "Query is required"
        )

    logger.info(f"Searching for '{query}' in {path}")

    try:
        matches = await _search_with_rg(query, path, file_pattern)
    except FileNotFoundError:
        matches = await _search_with_grep(query, path, file_pattern)

    # Convert dict matches to SearchMatch models
    search_matches = [
        SearchMatch(
            file=m["file"], line_number=m["line_number"], text=m["text"]
        )
        for m in matches
    ]

    # Calculate metrics
    total_matches = len(search_matches)
    truncated = total_matches > MAX_RESULTS
    if truncated:
        search_matches = search_matches[:MAX_RESULTS]

    unique_files = set(m.file for m in search_matches)

    return create_success_result(
        SearchResult,
        "search_codebase",
        query=query,
        path=path,
        file_pattern=file_pattern,
        matches=search_matches,
        match_count=total_matches,
        file_count=len(unique_files),
        truncated=truncated,
    )


async def _search_with_rg(query: str, path: str, file_pattern: str) -> List[dict]:
    """Search using ripgrep."""
    cmd = ["rg", "--json", "--max-count", "5", "--glob", file_pattern, query, path]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode not in (0, 1):
        raise FileNotFoundError("rg not available")

    return _parse_rg_output(stdout.decode())


async def _search_with_grep(query: str, path: str, file_pattern: str) -> List[dict]:
    """Fallback search using grep."""
    cmd = ["grep", "-rn", "--include", file_pattern, query, path]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()

    return _parse_grep_output(stdout.decode())


def _parse_rg_output(output: str) -> List[dict]:
    """Parse ripgrep JSON output."""
    matches = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "match":
                match_data = data.get("data", {})
                matches.append({
                    "file": match_data.get("path", {}).get("text", ""),
                    "line_number": match_data.get("line_number", 0),
                    "text": match_data.get("lines", {}).get("text", "").strip()
                })
        except json.JSONDecodeError:
            continue
    return matches


def _parse_grep_output(output: str) -> List[dict]:
    """Parse grep output."""
    matches = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":", 2)
        if len(parts) >= 3:
            matches.append({
                "file": parts[0],
                "line_number": int(parts[1]) if parts[1].isdigit() else 0,
                "text": parts[2].strip()
            })
    return matches
