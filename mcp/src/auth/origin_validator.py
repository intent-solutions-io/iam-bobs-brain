"""
Origin validation middleware for DNS rebinding protection.

Prevents DNS rebinding attacks by validating Origin headers against
an allowlist of trusted origins. Server-to-server calls (no Origin
header) are permitted to pass through.

Security Reference:
- DNS rebinding allows attackers to bypass same-origin policy
- By validating Origin headers, we ensure only trusted web clients can call
- Server-to-server calls don't include Origin headers and are handled separately
"""

import logging
import os
from typing import List, Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

# Default allowed origins - configurable via MCP_ALLOWED_ORIGINS env var
# Format: comma-separated list of origins (e.g., "https://example.com,http://localhost:8080")
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]


def get_allowed_origins() -> List[str]:
    """
    Get list of allowed origins from environment or defaults.

    Environment variable MCP_ALLOWED_ORIGINS can override defaults.
    Format: comma-separated origins (e.g., "https://app.example.com,http://localhost:3000")

    Returns:
        List of allowed origin strings.
    """
    env_origins = os.getenv("MCP_ALLOWED_ORIGINS")
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
        logger.info(f"Using custom allowed origins: {origins}")
        return origins
    return DEFAULT_ALLOWED_ORIGINS.copy()


def validate_origin(origin: Optional[str], allowed_origins: List[str]) -> bool:
    """
    Validate an origin against the allowlist.

    Args:
        origin: The Origin header value to validate.
        allowed_origins: List of allowed origin strings.

    Returns:
        True if origin is valid (None or in allowlist), False otherwise.
    """
    # No Origin header = server-to-server call, allow it
    if origin is None:
        return True

    # Normalize origin (strip trailing slash, lowercase)
    normalized = origin.rstrip("/").lower()

    # Check against allowlist (also normalized)
    for allowed in allowed_origins:
        if normalized == allowed.rstrip("/").lower():
            return True

    return False


class OriginValidatorMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Origin header validation.

    Blocks requests with disallowed Origin headers to prevent
    DNS rebinding attacks. Requests without Origin headers
    (server-to-server) are permitted.
    """

    def __init__(self, app, allowed_origins: Optional[List[str]] = None):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI application.
            allowed_origins: Optional custom list of allowed origins.
                           If None, uses get_allowed_origins().
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or get_allowed_origins()
        logger.info(f"OriginValidatorMiddleware initialized with origins: {self.allowed_origins}")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and validate Origin header.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler in the chain.

        Returns:
            Response from the next handler, or 403 if origin is blocked.
        """
        origin = request.headers.get("Origin")

        if not validate_origin(origin, self.allowed_origins):
            logger.warning(
                f"Blocked request from disallowed origin: {origin} "
                f"(path: {request.url.path}, client: {request.client.host if request.client else 'unknown'})"
            )
            # Return JSONResponse directly instead of raising HTTPException
            # Middleware cannot use HTTPException as it's not caught by FastAPI's exception handlers
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin not allowed"}
            )

        # Origin is valid, proceed
        if origin:
            logger.debug(f"Allowed request from origin: {origin}")

        return await call_next(request)


async def validate_origin_header(request: Request) -> None:
    """
    Standalone async function to validate Origin header.

    Can be used as a dependency or called directly in route handlers.
    Raises HTTPException with 403 if origin is not allowed.

    Args:
        request: The FastAPI request object.

    Raises:
        HTTPException: 403 if origin is not in allowlist.
    """
    origin = request.headers.get("Origin")
    allowed_origins = get_allowed_origins()

    if not validate_origin(origin, allowed_origins):
        logger.warning(
            f"Blocked request from disallowed origin: {origin} "
            f"(path: {request.url.path})"
        )
        raise HTTPException(
            status_code=403,
            detail="Origin not allowed"
        )
