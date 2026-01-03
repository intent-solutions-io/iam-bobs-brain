"""
Bob's MCP Server

Repository and code operation tools for Bob's Brain agents.
Runs on Cloud Run, registered in Cloud API Registry.

Hard Mode Compliance:
- R3: Gateway on Cloud Run (not Agent Engine)
- R4: Deployed via Terraform + GitHub Actions
- R7: Validates caller identity before processing

Security:
- OAuth 2.1 token validation (google-auth library)
- Origin validation middleware prevents DNS rebinding attacks
- Configurable via environment variables:
  - MCP_OAUTH_ENABLED: Enable OAuth 2.1 validation
  - MCP_SERVER_AUDIENCE: Required audience claim
  - MCP_ALLOWED_ORIGINS: Comma-separated allowed origins
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from src.auth.validator import validate_request, get_auth_info
from src.auth.origin_validator import OriginValidatorMiddleware
from src.auth.oauth_validator import get_oauth_status, is_oauth_enabled
from src.tools import search_codebase, get_file, analyze_deps, check_patterns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Bob's MCP Server starting up")
    oauth_status = get_oauth_status()
    if oauth_status["enabled"]:
        logger.info(f"OAuth 2.1 validation enabled (audience: {oauth_status['audience']})")
    else:
        logger.info("OAuth 2.1 validation disabled (using header-based auth)")
    yield
    logger.info("Bob's MCP Server shutting down")


app = FastAPI(
    title="bobs-mcp",
    description="Bob's MCP server for repository and code operations",
    version="0.2.0",
    lifespan=lifespan
)

# Add Origin validation middleware for DNS rebinding protection
# This must be added early in the middleware stack
app.add_middleware(OriginValidatorMiddleware)


# ============================================================================
# Well-Known Endpoints (RFC-compliant discovery)
# ============================================================================

@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """
    OAuth 2.0 Protected Resource Metadata endpoint.

    Per RFC 8707 and OAuth 2.1 draft, this endpoint advertises the
    resource server's OAuth configuration to clients.

    Returns:
        Protected Resource Metadata document.
    """
    # Get the base URL from environment or request context
    base_url = os.getenv("MCP_SERVER_BASE_URL", "https://bobs-mcp.run.app")
    audience = os.getenv("MCP_SERVER_AUDIENCE", base_url)

    # Authorization server (Google's OAuth)
    authorization_server = "https://accounts.google.com"

    # Build scopes based on available tools
    scopes_supported: List[str] = [
        "openid",
        "email",
        "profile",
        # Tool-specific scopes
        "bobs-mcp:tools:read",
        "bobs-mcp:tools:execute",
        "bobs-mcp:codebase:read",
        "bobs-mcp:codebase:analyze",
    ]

    # Methods required for OAuth 2.1
    token_introspection_endpoint = None  # Not supported yet
    token_revocation_endpoint = None  # Not supported yet

    return {
        # Required fields
        "resource": audience,

        # Authorization server reference
        "authorization_servers": [authorization_server],

        # Supported scopes
        "scopes_supported": scopes_supported,

        # Bearer token profile (RFC 6750)
        "bearer_methods_supported": ["header"],

        # Resource documentation
        "resource_documentation": f"{base_url}/docs",

        # Resource policy (optional)
        "resource_policy_uri": None,

        # Additional metadata
        "resource_name": "Bob's MCP Server",
        "resource_description": "Repository and code operation tools for Bob's Brain agents",

        # JWS algorithms for signed tokens
        "resource_signing_alg_values_supported": ["RS256", "ES256"],

        # Introspection endpoint (if available)
        "introspection_endpoint": token_introspection_endpoint,

        # Revocation endpoint (if available)
        "revocation_endpoint": token_revocation_endpoint,
    }


# ============================================================================
# Health and Status Endpoints
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "bobs-mcp"}


@app.get("/auth/status")
async def auth_status(request: Request):
    """
    Get current authentication status and configuration.

    Useful for debugging and client configuration.
    Does not require authentication.
    """
    oauth_status = get_oauth_status()
    auth_info = await get_auth_info(request)

    return {
        "oauth": oauth_status,
        "current_request": {
            "method": auth_info.get("method"),
            "authenticated": auth_info.get("authenticated"),
            # Don't expose identity in unauthenticated endpoint
        },
        "auth_methods_available": [
            "oauth2" if oauth_status["enabled"] else None,
            "header",
            "local-dev" if os.getenv("ALLOW_LOCAL_DEV") == "true" else None,
        ],
    }


# ============================================================================
# Tool Endpoints
# ============================================================================

@app.get("/tools")
async def list_tools(request: Request):
    """List available tools (MCP discovery)."""
    await validate_request(request)

    return {
        "tools": [
            {
                "name": "search_codebase",
                "description": "Search repository for code patterns",
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "path": {"type": "string", "default": "."},
                    "file_pattern": {"type": "string", "default": "*.py"}
                }
            },
            {
                "name": "get_file",
                "description": "Get contents of a file",
                "parameters": {
                    "path": {"type": "string", "required": True}
                }
            },
            {
                "name": "analyze_dependencies",
                "description": "Analyze project dependencies",
                "parameters": {
                    "path": {"type": "string", "default": "."}
                }
            },
            {
                "name": "check_patterns",
                "description": "Check code against ADK patterns",
                "parameters": {
                    "path": {"type": "string", "default": "."},
                    "rules": {"type": "array", "default": ["R1", "R2", "R3"]}
                }
            }
        ]
    }


@app.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Invoke a tool by name."""
    caller = await validate_request(request)

    try:
        body = await request.json()
    except Exception:
        body = {}

    logger.info(f"Tool invocation: {tool_name} by {caller}")

    if tool_name == "search_codebase":
        result = await search_codebase.execute(
            query=body.get("query", ""),
            path=body.get("path", "."),
            file_pattern=body.get("file_pattern", "*.py")
        )
    elif tool_name == "get_file":
        result = await get_file.execute(path=body.get("path", ""))
    elif tool_name == "analyze_dependencies":
        result = await analyze_deps.execute(path=body.get("path", "."))
    elif tool_name == "check_patterns":
        result = await check_patterns.execute(
            path=body.get("path", "."),
            rules=body.get("rules", ["R1", "R2", "R3"])
        )
    else:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    return {"result": result}


# ============================================================================
# Error Handling
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors securely."""
    # Log the full error internally
    logger.error(f"Unhandled error: {exc}", exc_info=True)

    # Return sanitized error to client
    # Never expose internal details in production
    if os.getenv("ALLOW_LOCAL_DEV") == "true":
        # Development mode: include error details
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": type(exc).__name__}
        )
    else:
        # Production mode: generic error
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
