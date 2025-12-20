"""Search codebase tool."""

import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)
MAX_RESULTS = 50


async def execute(query: str, path: str = ".", file_pattern: str = "*.py") -> dict:
    """Search codebase for a pattern."""
    if not query:
        return {"error": "Query is required", "matches": []}

    logger.info(f"Searching for '{query}' in {path}")

    try:
        result = await _search_with_rg(query, path, file_pattern)
    except FileNotFoundError:
        result = await _search_with_grep(query, path, file_pattern)

    return result


async def _search_with_rg(query: str, path: str, file_pattern: str) -> dict:
    """Search using ripgrep."""
    cmd = ["rg", "--json", "--max-count", "5", "--glob", file_pattern, query, path]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode not in (0, 1):
        raise FileNotFoundError("rg not available")

    matches = _parse_rg_output(stdout.decode())
    return {
        "query": query,
        "path": path,
        "file_pattern": file_pattern,
        "match_count": len(matches),
        "matches": matches[:MAX_RESULTS]
    }


async def _search_with_grep(query: str, path: str, file_pattern: str) -> dict:
    """Fallback search using grep."""
    cmd = ["grep", "-rn", "--include", file_pattern, query, path]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()

    matches = _parse_grep_output(stdout.decode())
    return {
        "query": query,
        "path": path,
        "file_pattern": file_pattern,
        "match_count": len(matches),
        "matches": matches[:MAX_RESULTS]
    }


def _parse_rg_output(output: str) -> List[dict]:
    """Parse ripgrep JSON output."""
    import json
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
