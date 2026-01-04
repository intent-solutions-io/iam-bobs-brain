"""Repository and universal operation tools.

Phase H: Universal Tool Access via MCP Protocol.

Core repository tools:
- search_codebase: Search code patterns
- get_file: Read file contents
- analyze_deps: Analyze dependencies
- check_patterns: Check ADK compliance

Universal tools (Phase H):
- github_api: GitHub operations (issues, PRs)
- web_search: Web search
- write_file: File writing
- shell_exec: Command execution
"""
from . import (
    search_codebase,
    get_file,
    analyze_deps,
    check_patterns,
    github_api,
    web_search,
    write_file,
    shell_exec,
)

__all__ = [
    # Core repository tools
    "search_codebase",
    "get_file",
    "analyze_deps",
    "check_patterns",
    # Universal tools (Phase H)
    "github_api",
    "web_search",
    "write_file",
    "shell_exec",
]
