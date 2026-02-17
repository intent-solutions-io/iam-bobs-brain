"""
Remote MCP Tools Module - Bob's MCP Client

This module connects to Bob's MCP server deployed on Cloud Run.
The server provides repository and universal operation tools.

Phase H: Universal Tool Access via MCP Protocol

Tools available from bobs-mcp server:

Core repository tools:
- search_codebase: Search repository for code patterns
- get_file: Get contents of a file
- analyze_dependencies: Analyze project dependencies
- check_patterns: Check code against ADK patterns (R1-R8)

Universal tools (Phase H):
- github_api: GitHub operations (issues, PRs)
- web_search: Web search
- write_file: File writing
- shell_exec: Command execution (allowlisted)

Configuration (environment variables):
- BOBS_MCP_URL: Full URL to MCP server (e.g., https://bobs-brain-mcp-dev.run.app)
- MCP_AUTH_TOKEN: Optional auth token for header-based authentication

Hard Mode Compliance:
- R3: Uses Cloud Run MCP server (not running in Agent Engine)
- R7: Passes SPIFFE ID in X-Agent-SPIFFE-ID header
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Configuration
BOBS_MCP_URL = os.getenv("BOBS_MCP_URL", "")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/unknown/dev/us-central1/0.10.0"
)

# HTTP client timeout (seconds)
MCP_TIMEOUT = float(os.getenv("MCP_TIMEOUT", "30"))


# ============================================================================
# MCP Client - Bob's MCP Server
# ============================================================================

class BobsMCPClient:
    """
    Client for Bob's MCP server on Cloud Run.

    Provides access to repository and universal operation tools:

    Core tools:
    - search_codebase
    - get_file
    - analyze_dependencies
    - check_patterns

    Universal tools (Phase H):
    - github_api
    - web_search
    - write_file
    - shell_exec
    """

    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            base_url: MCP server URL (defaults to BOBS_MCP_URL env var)
            auth_token: Auth token (defaults to MCP_AUTH_TOKEN env var)
        """
        self.base_url = (base_url or BOBS_MCP_URL).rstrip("/")
        self.auth_token = auth_token or MCP_AUTH_TOKEN

        if not self.base_url:
            logger.warning("BOBS_MCP_URL not configured - MCP tools unavailable")

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with auth and identity."""
        headers = {
            "Content-Type": "application/json",
            "X-Agent-SPIFFE-ID": AGENT_SPIFFE_ID,  # R7: SPIFFE ID propagation
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    @property
    def is_available(self) -> bool:
        """Check if MCP server is configured."""
        return bool(self.base_url)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check MCP server health.

        Returns:
            Health status dict or error
        """
        if not self.is_available:
            return {"status": "unavailable", "reason": "BOBS_MCP_URL not configured"}

        async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"MCP health check failed: {e}")
                return {"status": "error", "error": str(e)}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        if not self.is_available:
            return []

        async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tools",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("tools", [])
            except Exception as e:
                logger.error(f"Failed to list MCP tools: {e}")
                return []

    async def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a tool on the MCP server.

        Args:
            tool_name: Name of the tool (search_codebase, get_file, etc.)
            params: Tool parameters

        Returns:
            Tool result or error
        """
        if not self.is_available:
            return {"error": "MCP server not configured", "tool": tool_name}

        async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/tools/{tool_name}",
                    json=params,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"MCP tool {tool_name} HTTP error: {e.response.status_code}")
                return {"error": f"HTTP {e.response.status_code}", "tool": tool_name}
            except Exception as e:
                logger.error(f"MCP tool {tool_name} failed: {e}")
                return {"error": str(e), "tool": tool_name}

    # Convenience methods for specific tools

    async def search_codebase(
        self,
        query: str,
        path: str = ".",
        file_pattern: str = "*.py"
    ) -> Dict[str, Any]:
        """
        Search repository for code patterns.

        Args:
            query: Search pattern (regex supported)
            path: Directory to search in
            file_pattern: File glob pattern

        Returns:
            Search results with matching files and snippets
        """
        return await self.invoke_tool("search_codebase", {
            "query": query,
            "path": path,
            "file_pattern": file_pattern
        })

    async def get_file(self, path: str) -> Dict[str, Any]:
        """
        Get contents of a file.

        Args:
            path: Path to file

        Returns:
            File contents
        """
        return await self.invoke_tool("get_file", {"path": path})

    async def analyze_dependencies(self, path: str = ".") -> Dict[str, Any]:
        """
        Analyze project dependencies.

        Args:
            path: Project root path

        Returns:
            Dependency analysis results
        """
        return await self.invoke_tool("analyze_dependencies", {"path": path})

    async def check_patterns(
        self,
        path: str = ".",
        rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check code against ADK patterns (Hard Mode R1-R8).

        Args:
            path: Directory to check
            rules: List of rules to check (default: ["R1", "R2", "R3"])

        Returns:
            Pattern check results with violations
        """
        return await self.invoke_tool("check_patterns", {
            "path": path,
            "rules": rules or ["R1", "R2", "R3"]
        })

    # =========================================================================
    # Universal tools (Phase H)
    # =========================================================================

    async def github_api(
        self,
        operation: str,
        owner: str,
        repo: str,
        state: str = "open",
        title: Optional[str] = None,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Perform GitHub API operations.

        Args:
            operation: Operation to perform (list_issues, create_issue, list_prs)
            owner: Repository owner
            repo: Repository name
            state: Issue/PR state filter (open/closed/all)
            title: Issue title (for create_issue)
            body: Issue body (for create_issue)
            labels: Labels to apply
            limit: Maximum results to return

        Returns:
            GitHub operation results
        """
        params: Dict[str, Any] = {
            "operation": operation,
            "owner": owner,
            "repo": repo,
            "state": state,
            "limit": limit,
        }
        if title:
            params["title"] = title
        if body:
            params["body"] = body
        if labels:
            params["labels"] = labels
        return await self.invoke_tool("github_api", params)

    async def web_search(
        self,
        query: str,
        limit: int = 10,
        backend: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search the web.

        Args:
            query: Search query
            limit: Maximum results to return
            backend: Search backend (google, duckduckgo, auto)

        Returns:
            Search results
        """
        params: Dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if backend:
            params["backend"] = backend
        return await self.invoke_tool("web_search", params)

    async def write_file(
        self,
        path: str,
        content: str,
        mode: str = "write",
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to a file.

        Args:
            path: File path to write
            content: Content to write
            mode: Write mode (write = overwrite, append = append)
            create_dirs: Create parent directories if needed

        Returns:
            Write operation result
        """
        return await self.invoke_tool("write_file", {
            "path": path,
            "content": content,
            "mode": mode,
            "create_dirs": create_dirs,
        })

    async def shell_exec(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a shell command.

        Args:
            command: Command to execute (must be in allowlist)
            cwd: Working directory
            timeout: Timeout in seconds
            env: Additional environment variables

        Returns:
            Command execution result (stdout, stderr, exit_code)
        """
        params: Dict[str, Any] = {
            "command": command,
            "timeout": timeout,
        }
        if cwd:
            params["cwd"] = cwd
        if env:
            params["env"] = env
        return await self.invoke_tool("shell_exec", params)


# Singleton client instance
_mcp_client: Optional[BobsMCPClient] = None


def get_mcp_client() -> BobsMCPClient:
    """
    Get the singleton MCP client instance.

    Returns:
        BobsMCPClient instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = BobsMCPClient()
    return _mcp_client


# ============================================================================
# Legacy compatibility functions
# ============================================================================

def get_mcp_filesystem_tool() -> Optional[BobsMCPClient]:
    """
    Get MCP filesystem tools (via bobs-mcp server).

    The bobs-mcp server provides get_file and search_codebase tools
    for filesystem operations.

    Returns:
        BobsMCPClient if configured, None otherwise
    """
    client = get_mcp_client()
    if client.is_available:
        logger.info(f"MCP filesystem tools available at {client.base_url}")
        return client
    logger.info("MCP filesystem tools not configured (BOBS_MCP_URL not set)")
    return None


def get_mcp_database_tool() -> Optional[Any]:
    """
    Get MCP database tool (FUTURE).

    Not yet implemented - would connect to a database MCP server.
    """
    logger.info("MCP database tool not yet implemented")
    return None


def get_mcp_github_tool() -> Optional[BobsMCPClient]:
    """
    Get MCP GitHub tool (via bobs-mcp server).

    The bobs-mcp server provides github_api tool for GitHub operations.

    Returns:
        BobsMCPClient if configured, None otherwise
    """
    client = get_mcp_client()
    if client.is_available:
        logger.info(f"MCP GitHub tool available at {client.base_url}")
        return client
    logger.info("MCP GitHub tool not configured (BOBS_MCP_URL not set)")
    return None


def list_available_mcp_servers() -> List[str]:
    """
    List currently available MCP servers.

    Returns:
        List of configured MCP server names
    """
    servers = []

    client = get_mcp_client()
    if client.is_available:
        servers.append("bobs-mcp")

    return servers


# ============================================================================
# Tool Registration for Agents
# ============================================================================

def get_mcp_tools_for_agent(agent_name: str) -> List[Any]:
    """
    Get MCP-backed tools appropriate for a specific agent.

    This function returns tool wrappers that agents can use.
    The actual implementation uses the BobsMCPClient to call
    the MCP server.

    Args:
        agent_name: Name of the agent requesting tools

    Returns:
        List of tool functions/objects
    """
    client = get_mcp_client()
    if not client.is_available:
        logger.info(f"No MCP tools available for {agent_name}")
        return []

    # All agents get access to the core MCP tools
    # Future: Filter based on agent permissions/roles
    logger.info(f"Providing MCP tools to {agent_name} from {client.base_url}")

    # Core repository tools
    tools = [
        client.search_codebase,
        client.get_file,
        client.analyze_dependencies,
        client.check_patterns,
    ]

    # Universal tools (Phase H) - available to all agents
    tools.extend([
        client.github_api,
        client.web_search,
        client.write_file,
        client.shell_exec,
    ])

    return tools
