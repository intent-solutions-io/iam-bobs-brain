"""
OAuth 2.1 token validation for Bob's MCP server.

Uses google-auth library for validating OAuth 2.0/2.1 tokens issued by
Google's authorization servers. Supports both ID tokens and access tokens.

Security features:
- Audience claim validation (prevents token misuse across services)
- Issuer verification (Google's OAuth endpoints only)
- Expiration checking (built into google-auth)
- Token caching with TTL (reduces validation overhead)

Environment variables:
- MCP_SERVER_AUDIENCE: Required audience claim for token validation
- MCP_OAUTH_ENABLED: Set to "true" to enable OAuth validation
- GOOGLE_APPLICATION_CREDENTIALS: Path to service account key (optional)
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional, Any

from fastapi import Request, HTTPException

# google-auth imports - graceful handling if not installed
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from google.auth import exceptions as google_auth_exceptions
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    id_token = None
    google_requests = None
    google_auth_exceptions = None

from .token_cache import get_token_cache

logger = logging.getLogger(__name__)

# Environment configuration
MCP_SERVER_AUDIENCE_ENV = "MCP_SERVER_AUDIENCE"
MCP_OAUTH_ENABLED_ENV = "MCP_OAUTH_ENABLED"

# Google OAuth issuers (accounts.google.com and https variant)
GOOGLE_ISSUERS = [
    "https://accounts.google.com",
    "accounts.google.com",
]


@dataclass
class OAuthClaims:
    """
    Validated OAuth token claims.

    Contains the identity and authorization information extracted
    from a validated OAuth token.
    """
    subject: str  # 'sub' claim - unique user/service identifier
    email: Optional[str]  # 'email' claim if present
    audience: str  # 'aud' claim
    issuer: str  # 'iss' claim
    expires_at: Optional[int]  # 'exp' claim (Unix timestamp)
    issued_at: Optional[int]  # 'iat' claim (Unix timestamp)
    raw_claims: Dict[str, Any]  # All claims from token

    def get_identity(self) -> str:
        """Return the best identifier for logging/authorization."""
        return self.email or self.subject

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "subject": self.subject,
            "email": self.email,
            "audience": self.audience,
            "issuer": self.issuer,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
        }


class OAuthValidationError(Exception):
    """Raised when OAuth token validation fails."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def is_oauth_enabled() -> bool:
    """
    Check if OAuth validation is enabled.

    Returns True if:
    - MCP_OAUTH_ENABLED is set to "true"
    - google-auth library is available
    - MCP_SERVER_AUDIENCE is configured
    """
    if not GOOGLE_AUTH_AVAILABLE:
        logger.debug("OAuth disabled: google-auth library not available")
        return False

    enabled = os.getenv(MCP_OAUTH_ENABLED_ENV, "").lower() == "true"
    if not enabled:
        logger.debug("OAuth disabled: MCP_OAUTH_ENABLED not set to 'true'")
        return False

    audience = os.getenv(MCP_SERVER_AUDIENCE_ENV)
    if not audience:
        logger.warning("OAuth enabled but MCP_SERVER_AUDIENCE not configured")
        return False

    return True


def get_configured_audience() -> Optional[str]:
    """Get the configured audience for token validation."""
    return os.getenv(MCP_SERVER_AUDIENCE_ENV)


def _extract_bearer_token(request: Request) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        request: The FastAPI request object.

    Returns:
        The token string if present and valid format, None otherwise.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    parts = auth_header.split()

    if len(parts) != 2:
        return None

    scheme, token = parts

    if scheme.lower() != "bearer":
        return None

    return token


def _validate_token_with_google(token: str, audience: str) -> Dict[str, Any]:
    """
    Validate an OAuth token using google-auth library.

    Args:
        token: The OAuth token to validate.
        audience: The expected audience claim.

    Returns:
        Dictionary of validated claims.

    Raises:
        OAuthValidationError: If validation fails.
    """
    if not GOOGLE_AUTH_AVAILABLE:
        raise OAuthValidationError(
            "OAuth validation unavailable: google-auth library not installed",
            status_code=500
        )

    try:
        # Create a request object for token verification
        request = google_requests.Request()

        # Verify the ID token
        # This handles:
        # - Signature verification
        # - Issuer verification (accounts.google.com)
        # - Expiration checking
        # - Audience validation
        claims = id_token.verify_oauth2_token(
            token,
            request,
            audience=audience,
        )

        return claims

    except google_auth_exceptions.GoogleAuthError as e:
        logger.warning(f"OAuth token validation failed: {e}")
        raise OAuthValidationError(f"Invalid OAuth token: {e}")

    except ValueError as e:
        # verify_oauth2_token raises ValueError for invalid tokens
        logger.warning(f"OAuth token format error: {e}")
        raise OAuthValidationError(f"Malformed OAuth token: {e}")

    except Exception as e:
        # Catch unexpected errors but don't expose internals
        logger.error(f"Unexpected OAuth validation error: {e}")
        raise OAuthValidationError("Token validation failed")


def _claims_dict_to_oauth_claims(claims: Dict[str, Any]) -> OAuthClaims:
    """
    Convert raw claims dictionary to OAuthClaims dataclass.

    Args:
        claims: Raw claims from token verification.

    Returns:
        Structured OAuthClaims object.
    """
    return OAuthClaims(
        subject=claims.get("sub", ""),
        email=claims.get("email"),
        audience=claims.get("aud", ""),
        issuer=claims.get("iss", ""),
        expires_at=claims.get("exp"),
        issued_at=claims.get("iat"),
        raw_claims=claims,
    )


async def validate_oauth_token(request: Request) -> OAuthClaims:
    """
    Validate OAuth 2.1 token from request and return caller identity claims.

    This is the main entry point for OAuth validation. It:
    1. Extracts Bearer token from Authorization header
    2. Checks token cache for previously validated tokens
    3. Validates token with Google's verification endpoint
    4. Caches successful validation results
    5. Returns structured claims on success

    Args:
        request: The FastAPI request object.

    Returns:
        OAuthClaims containing validated identity information.

    Raises:
        HTTPException(401): If token is missing, invalid, or expired.
        HTTPException(500): If OAuth is misconfigured.
    """
    # Check if OAuth is properly configured
    if not GOOGLE_AUTH_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="OAuth validation unavailable: google-auth not installed"
        )

    audience = get_configured_audience()
    if not audience:
        raise HTTPException(
            status_code=500,
            detail="OAuth misconfigured: MCP_SERVER_AUDIENCE not set"
        )

    # Extract token from request
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authorization header with Bearer token required"
        )

    # Check cache first
    cache = get_token_cache()
    cached_claims = cache.get(token)

    if cached_claims is not None:
        logger.debug("OAuth token validated from cache")
        return cached_claims

    # Validate with Google
    try:
        raw_claims = _validate_token_with_google(token, audience)
    except OAuthValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Convert to structured claims
    claims = _claims_dict_to_oauth_claims(raw_claims)

    # Verify issuer is Google
    if claims.issuer not in GOOGLE_ISSUERS:
        logger.warning(f"OAuth token from unexpected issuer: {claims.issuer}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token issuer: {claims.issuer}"
        )

    # Cache the validated claims
    cache.set(token, claims)

    logger.info(f"OAuth token validated for: {claims.get_identity()}")
    return claims


async def try_oauth_validation(request: Request) -> Optional[OAuthClaims]:
    """
    Attempt OAuth validation without raising exceptions.

    Used for graceful fallback when OAuth is optional.

    Args:
        request: The FastAPI request object.

    Returns:
        OAuthClaims if validation succeeds, None if it fails or is disabled.
    """
    if not is_oauth_enabled():
        return None

    token = _extract_bearer_token(request)
    if not token:
        return None

    try:
        return await validate_oauth_token(request)
    except HTTPException:
        return None
    except Exception as e:
        logger.debug(f"OAuth validation attempt failed: {e}")
        return None


def get_oauth_status() -> Dict[str, Any]:
    """
    Get current OAuth configuration status.

    Useful for debugging and health checks.

    Returns:
        Dictionary with OAuth configuration details.
    """
    return {
        "enabled": is_oauth_enabled(),
        "google_auth_available": GOOGLE_AUTH_AVAILABLE,
        "audience_configured": bool(get_configured_audience()),
        "audience": get_configured_audience() if is_oauth_enabled() else None,
    }
