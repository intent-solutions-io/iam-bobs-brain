"""
Request validation for Bob's MCP server.

R7: SPIFFE ID propagation - validate caller identity and log it.

Authentication Strategy (OAuth 2.1 with backwards compatibility):
1. Try OAuth 2.1 validation first (if enabled and token present)
2. Fall back to header-based validation for backwards compatibility
3. Log which method was used for debugging/auditing

Environment variables:
- MCP_OAUTH_ENABLED: Set to "true" to enable OAuth validation
- MCP_SERVER_AUDIENCE: Required audience claim for OAuth tokens
- ALLOW_LOCAL_DEV: Set to "true" to allow unauthenticated local requests
"""

import logging
import os
from typing import Optional

from fastapi import Request, HTTPException

from .oauth_validator import (
    try_oauth_validation,
    is_oauth_enabled,
    OAuthClaims,
)

logger = logging.getLogger(__name__)

# Allowed callers for header-based authentication (legacy)
ALLOWED_CALLERS = [
    "bob-agent",
    "iam-senior-adk-devops-lead",
    "iam-adk-agent",
    "iam-issue-agent",
    "iam-fix-plan-agent",
    "iam-fix-impl-agent",
    "iam-qa-agent",
    "iam-doc-agent",
    "iam-cleanup-agent",
    "iam-index-agent",
    "api-registry",
    "local-dev",
]


async def validate_request(request: Request) -> str:
    """
    Validate incoming request and extract caller identity.

    Authentication flow:
    1. Try OAuth 2.1 validation first (if enabled)
    2. Fall back to header-based validation for backwards compatibility
    3. Allow local-dev bypass if ALLOW_LOCAL_DEV=true

    R7: Every request must have valid identity.

    Args:
        request: The FastAPI request object.

    Returns:
        Caller identity string for logging and authorization.

    Raises:
        HTTPException(401): If no valid identity found.
        HTTPException(403): If identity is not authorized.
    """
    # Try OAuth validation first
    oauth_claims = await try_oauth_validation(request)

    if oauth_claims is not None:
        caller_identity = oauth_claims.get_identity()
        logger.info(f"Authenticated via OAuth: {caller_identity}")
        return caller_identity

    # Fall back to header-based validation
    caller_identity = await _validate_header_auth(request)

    if caller_identity:
        if is_oauth_enabled():
            # Log that we fell back when OAuth is enabled
            logger.info(f"Authenticated via headers (OAuth fallback): {caller_identity}")
        else:
            logger.info(f"Authenticated via headers: {caller_identity}")
        return caller_identity

    # No valid identity found
    logger.warning("Request rejected - no valid authentication method")
    raise HTTPException(status_code=401, detail="Authentication required")


async def _validate_header_auth(request: Request) -> Optional[str]:
    """
    Validate request using header-based authentication (legacy method).

    Checks for identity in:
    1. X-Goog-Authenticated-User-Email (GCP IAP)
    2. X-Forwarded-User (custom proxy)
    3. Authorization header (service account extraction)

    Args:
        request: The FastAPI request object.

    Returns:
        Caller identity if valid, None otherwise.

    Raises:
        HTTPException(403): If identity is found but not authorized.
    """
    caller_identity = (
        request.headers.get("X-Goog-Authenticated-User-Email")
        or request.headers.get("X-Forwarded-User")
        or _extract_sa_from_auth(request.headers.get("Authorization"))
    )

    # Local dev bypass
    if os.getenv("ALLOW_LOCAL_DEV") == "true":
        if not caller_identity:
            caller_identity = "local-dev"
            logger.warning("Local dev mode - using default identity")

    if not caller_identity:
        return None

    # Check authorization
    if not _is_allowed(caller_identity):
        logger.warning(f"Request rejected - unauthorized: {caller_identity}")
        raise HTTPException(status_code=403, detail="Not authorized")

    return caller_identity


def _extract_sa_from_auth(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract service account from Authorization header.

    For non-OAuth Bearer tokens (e.g., service account tokens),
    this could parse the JWT to extract the service account email.
    Currently returns None as OAuth handles this case.
    """
    if not auth_header:
        return None

    # OAuth validation handles Bearer tokens
    # This is kept for potential future non-OAuth auth methods
    return None


def _is_allowed(identity: str) -> bool:
    """
    Check if caller is allowed based on identity.

    Checks:
    1. Identity matches an allowed caller prefix
    2. Identity is a service account in the project

    Args:
        identity: The caller identity string.

    Returns:
        True if authorized, False otherwise.
    """
    identity_lower = identity.lower()

    # Check against allowed callers list
    for allowed in ALLOWED_CALLERS:
        if allowed.lower() in identity_lower:
            return True

    # Allow service accounts from the same project
    project_id = os.getenv("PROJECT_ID", "")
    if project_id and f"@{project_id}.iam.gserviceaccount.com" in identity:
        return True

    return False


async def get_auth_info(request: Request) -> dict:
    """
    Get authentication information without enforcing authorization.

    Useful for debugging and health check endpoints.

    Args:
        request: The FastAPI request object.

    Returns:
        Dictionary with authentication method and identity info.
    """
    result = {
        "oauth_enabled": is_oauth_enabled(),
        "method": None,
        "identity": None,
        "authenticated": False,
    }

    # Check OAuth
    oauth_claims = await try_oauth_validation(request)
    if oauth_claims:
        result["method"] = "oauth"
        result["identity"] = oauth_claims.get_identity()
        result["authenticated"] = True
        result["oauth_claims"] = oauth_claims.to_dict()
        return result

    # Check headers
    caller = (
        request.headers.get("X-Goog-Authenticated-User-Email")
        or request.headers.get("X-Forwarded-User")
    )

    if caller:
        result["method"] = "header"
        result["identity"] = caller
        result["authenticated"] = _is_allowed(caller)
        return result

    # Check local dev
    if os.getenv("ALLOW_LOCAL_DEV") == "true":
        result["method"] = "local-dev"
        result["identity"] = "local-dev"
        result["authenticated"] = True

    return result
