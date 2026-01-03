"""
Auth module for Bob's MCP server.

Provides OAuth 2.1 token validation with backwards-compatible
header-based authentication fallback, plus origin validation
for DNS rebinding protection.

Usage:
    from src.auth import validate_request, get_auth_info

    # In endpoint handlers:
    caller = await validate_request(request)

    # For debugging:
    auth_info = await get_auth_info(request)
"""

from .validator import validate_request, get_auth_info
from .origin_validator import (
    OriginValidatorMiddleware,
    validate_origin,
    validate_origin_header,
    get_allowed_origins,
)
from .oauth_validator import (
    validate_oauth_token,
    try_oauth_validation,
    is_oauth_enabled,
    get_oauth_status,
    OAuthClaims,
)
from .token_cache import (
    TokenCache,
    get_token_cache,
    reset_token_cache,
)

__all__ = [
    # Main validation entry points
    "validate_request",
    "get_auth_info",
    # Origin validation (DNS rebinding protection)
    "OriginValidatorMiddleware",
    "validate_origin",
    "validate_origin_header",
    "get_allowed_origins",
    # OAuth-specific
    "validate_oauth_token",
    "try_oauth_validation",
    "is_oauth_enabled",
    "get_oauth_status",
    "OAuthClaims",
    # Cache utilities
    "TokenCache",
    "get_token_cache",
    "reset_token_cache",
]
