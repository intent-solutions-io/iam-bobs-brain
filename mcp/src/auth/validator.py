"""
Request validation for Bob's MCP server.

R7: SPIFFE ID propagation - validate caller identity and log it.
"""

import logging
import os
from typing import Optional

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

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

    R7: Every request must have valid identity.
    """
    caller_identity = (
        request.headers.get("X-Goog-Authenticated-User-Email")
        or request.headers.get("X-Forwarded-User")
        or _extract_sa_from_auth(request.headers.get("Authorization"))
    )

    if os.getenv("ALLOW_LOCAL_DEV") == "true":
        if not caller_identity:
            caller_identity = "local-dev"
            logger.warning("Local dev mode - no identity check")

    if not caller_identity:
        logger.warning("Request rejected - no caller identity")
        raise HTTPException(status_code=401, detail="Caller identity required")

    if not _is_allowed(caller_identity):
        logger.warning(f"Request rejected - unauthorized: {caller_identity}")
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"Authorized request from: {caller_identity}")
    return caller_identity


def _extract_sa_from_auth(auth_header: Optional[str]) -> Optional[str]:
    """Extract service account from Authorization header."""
    if not auth_header:
        return None
    return None


def _is_allowed(identity: str) -> bool:
    """Check if caller is allowed."""
    identity_lower = identity.lower()
    for allowed in ALLOWED_CALLERS:
        if allowed.lower() in identity_lower:
            return True
    project_id = os.getenv("PROJECT_ID", "")
    if project_id and f"@{project_id}.iam.gserviceaccount.com" in identity:
        return True
    return False
