"""
Bob's MCP Server

Repository and code operation tools for Bob's Brain agents.
Runs on Cloud Run, registered in Cloud API Registry.

Hard Mode Compliance:
- R3: Gateway on Cloud Run (not Agent Engine)
- R4: Deployed via Terraform + GitHub Actions
- R7: Validates caller identity before processing
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from src.auth.validator import validate_request
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
    yield
    logger.info("Bob's MCP Server shutting down")


app = FastAPI(
    title="bobs-mcp",
    description="Bob's MCP server for repository and code operations",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "bobs-mcp"}


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
