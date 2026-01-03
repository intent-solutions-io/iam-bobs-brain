"""
Unit tests for OAuth 2.1 token validation.

Tests cover:
- Token cache functionality (TTL, thread-safety)
- OAuth token validation (with mocked google-auth)
- Integration with existing header-based auth
- Protected Resource Metadata endpoint
- Graceful degradation when OAuth not configured
"""

import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Token Cache Tests
# ============================================================================

class TestTokenCache:
    """Tests for the token cache module."""

    def test_cache_set_and_get(self):
        """Should store and retrieve values."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache(ttl_seconds=60)
        cache.set("token123", {"email": "test@example.com"})

        result = cache.get("token123")
        assert result is not None
        assert result["email"] == "test@example.com"

    def test_cache_miss_returns_none(self):
        """Should return None for missing keys."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """Should expire entries after TTL."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache(ttl_seconds=1)
        cache.set("token123", {"email": "test@example.com"})

        # Should exist immediately
        assert cache.get("token123") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be gone
        assert cache.get("token123") is None

    def test_cache_custom_ttl_per_entry(self):
        """Should support custom TTL per entry."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache(ttl_seconds=60)

        # Set with short TTL
        cache.set("short", "value", ttl_seconds=1)
        cache.set("long", "value", ttl_seconds=60)

        time.sleep(1.1)

        assert cache.get("short") is None
        assert cache.get("long") is not None

    def test_cache_invalidate(self):
        """Should remove specific entries."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        cache.set("token1", "value1")
        cache.set("token2", "value2")

        result = cache.invalidate("token1")

        assert result is True
        assert cache.get("token1") is None
        assert cache.get("token2") is not None

    def test_cache_invalidate_nonexistent(self):
        """Should return False for nonexistent entries."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        result = cache.invalidate("nonexistent")
        assert result is False

    def test_cache_clear(self):
        """Should clear all entries."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        cache.set("token1", "value1")
        cache.set("token2", "value2")

        count = cache.clear()

        assert count == 2
        assert cache.size() == 0

    def test_cache_cleanup_expired(self):
        """Should clean up expired entries."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache(ttl_seconds=1)
        cache.set("token1", "value1")
        cache.set("token2", "value2")

        time.sleep(1.1)

        removed = cache.cleanup_expired()

        assert removed == 2
        assert cache.size() == 0

    def test_cache_stats(self):
        """Should return accurate statistics."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache(ttl_seconds=60)
        cache.set("token1", "value1")
        cache.set("token2", "value2")

        stats = cache.stats()

        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["ttl_seconds"] == 60

    def test_cache_thread_safety(self):
        """Should handle concurrent access safely."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"token{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"token{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_cache_hashes_tokens(self):
        """Should not store raw tokens as keys."""
        from src.auth.token_cache import TokenCache

        cache = TokenCache()
        token = "sensitive_token_12345"
        cache.set(token, "value")

        # Check internal storage doesn't contain raw token
        assert token not in cache._cache

    def test_global_cache_singleton(self):
        """Should return same instance for global cache."""
        from src.auth.token_cache import get_token_cache, reset_token_cache

        reset_token_cache()

        cache1 = get_token_cache()
        cache2 = get_token_cache()

        assert cache1 is cache2

        reset_token_cache()


# ============================================================================
# OAuth Validator Tests
# ============================================================================

class TestOAuthValidator:
    """Tests for OAuth token validation."""

    def setup_method(self):
        """Reset state before each test."""
        from src.auth.token_cache import reset_token_cache
        reset_token_cache()

        # Clear environment
        for key in ["MCP_OAUTH_ENABLED", "MCP_SERVER_AUDIENCE"]:
            if key in os.environ:
                del os.environ[key]

    def test_oauth_disabled_by_default(self):
        """OAuth should be disabled when not configured."""
        from src.auth.oauth_validator import is_oauth_enabled

        assert is_oauth_enabled() is False

    def test_oauth_enabled_requires_audience(self):
        """OAuth should require audience to be enabled."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"

        from src.auth.oauth_validator import is_oauth_enabled

        # Should still be disabled without audience
        assert is_oauth_enabled() is False

    def test_oauth_enabled_with_full_config(self):
        """OAuth should be enabled with full configuration."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import is_oauth_enabled

        assert is_oauth_enabled() is True

    def test_get_oauth_status(self):
        """Should return OAuth configuration status."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import get_oauth_status

        status = get_oauth_status()

        assert status["enabled"] is True
        assert status["audience"] == "https://bobs-mcp.run.app"
        assert status["google_auth_available"] is True

    def test_extract_bearer_token(self):
        """Should extract Bearer token from Authorization header."""
        from src.auth.oauth_validator import _extract_bearer_token

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer token123"}

        token = _extract_bearer_token(mock_request)

        assert token == "token123"

    def test_extract_bearer_token_no_header(self):
        """Should return None when no Authorization header."""
        from src.auth.oauth_validator import _extract_bearer_token

        mock_request = Mock()
        mock_request.headers = {}

        token = _extract_bearer_token(mock_request)

        assert token is None

    def test_extract_bearer_token_wrong_scheme(self):
        """Should return None for non-Bearer schemes."""
        from src.auth.oauth_validator import _extract_bearer_token

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}

        token = _extract_bearer_token(mock_request)

        assert token is None

    def test_extract_bearer_token_malformed(self):
        """Should return None for malformed header."""
        from src.auth.oauth_validator import _extract_bearer_token

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer"}

        token = _extract_bearer_token(mock_request)

        assert token is None

    @pytest.mark.asyncio
    async def test_validate_oauth_token_no_config(self):
        """Should raise 500 when OAuth not configured."""
        from src.auth.oauth_validator import validate_oauth_token
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer token123"}

        # OAuth not configured (no audience)
        os.environ["MCP_OAUTH_ENABLED"] = "true"

        with pytest.raises(HTTPException) as exc_info:
            await validate_oauth_token(mock_request)

        assert exc_info.value.status_code == 500
        assert "MCP_SERVER_AUDIENCE" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_oauth_token_no_token(self):
        """Should raise 401 when no token provided."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import validate_oauth_token
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await validate_oauth_token(mock_request)

        assert exc_info.value.status_code == 401
        assert "Bearer token required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_oauth_token_invalid_token(self):
        """Should raise 401 for invalid token."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import validate_oauth_token
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer invalid_token"}

        # Mock google-auth to raise error
        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            from google.auth import exceptions
            mock_verify.side_effect = exceptions.GoogleAuthError("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await validate_oauth_token(mock_request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_oauth_token_success(self):
        """Should return claims for valid token."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import validate_oauth_token

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}

        mock_claims = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "https://bobs-mcp.run.app",
            "iss": "https://accounts.google.com",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = mock_claims

            claims = await validate_oauth_token(mock_request)

            assert claims.subject == "user123"
            assert claims.email == "test@example.com"
            assert claims.get_identity() == "test@example.com"

    @pytest.mark.asyncio
    async def test_validate_oauth_token_caches_result(self):
        """Should cache validated tokens."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import validate_oauth_token
        from src.auth.token_cache import get_token_cache

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer cached_token"}

        mock_claims = {
            "sub": "user123",
            "email": "cached@example.com",
            "aud": "https://bobs-mcp.run.app",
            "iss": "https://accounts.google.com",
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = mock_claims

            # First call
            await validate_oauth_token(mock_request)

            # Second call should use cache
            await validate_oauth_token(mock_request)

            # verify_oauth2_token should only be called once
            assert mock_verify.call_count == 1

    @pytest.mark.asyncio
    async def test_try_oauth_validation_graceful_failure(self):
        """Should return None on failure instead of raising."""
        from src.auth.oauth_validator import try_oauth_validation

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer bad_token"}

        # OAuth not configured
        result = await try_oauth_validation(mock_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_oauth_token_wrong_issuer(self):
        """Should reject tokens from wrong issuer."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.oauth_validator import validate_oauth_token
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer wrong_issuer_token"}

        mock_claims = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "https://bobs-mcp.run.app",
            "iss": "https://evil-issuer.com",  # Wrong issuer
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = mock_claims

            with pytest.raises(HTTPException) as exc_info:
                await validate_oauth_token(mock_request)

            assert exc_info.value.status_code == 401
            assert "issuer" in exc_info.value.detail.lower()


# ============================================================================
# Validator Integration Tests
# ============================================================================

class TestValidatorIntegration:
    """Tests for the main validator with OAuth integration."""

    def setup_method(self):
        """Reset state before each test."""
        from src.auth.token_cache import reset_token_cache
        reset_token_cache()

        # Clear environment
        for key in ["MCP_OAUTH_ENABLED", "MCP_SERVER_AUDIENCE", "ALLOW_LOCAL_DEV", "PROJECT_ID"]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_oauth_takes_precedence(self):
        """OAuth validation should take precedence over headers."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.validator import validate_request

        mock_request = Mock()
        mock_request.headers = {
            "Authorization": "Bearer valid_token",
            "X-Forwarded-User": "header-user",  # Should be ignored
        }

        mock_claims = {
            "sub": "oauth-user",
            "email": "oauth@example.com",
            "aud": "https://bobs-mcp.run.app",
            "iss": "https://accounts.google.com",
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = mock_claims

            identity = await validate_request(mock_request)

            assert identity == "oauth@example.com"

    @pytest.mark.asyncio
    async def test_fallback_to_headers_when_oauth_fails(self):
        """Should fall back to header auth when OAuth fails."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.validator import validate_request

        mock_request = Mock()
        mock_request.headers = {
            "Authorization": "Bearer invalid_token",
            "X-Forwarded-User": "bob-agent",
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            from google.auth import exceptions
            mock_verify.side_effect = exceptions.GoogleAuthError("Invalid")

            identity = await validate_request(mock_request)

            assert identity == "bob-agent"

    @pytest.mark.asyncio
    async def test_fallback_to_headers_when_oauth_disabled(self):
        """Should use header auth when OAuth not enabled."""
        # OAuth disabled (default)
        from src.auth.validator import validate_request

        mock_request = Mock()
        mock_request.headers = {
            "X-Goog-Authenticated-User-Email": "bob-agent@project.iam.gserviceaccount.com",
        }

        identity = await validate_request(mock_request)

        assert "bob-agent" in identity

    @pytest.mark.asyncio
    async def test_local_dev_fallback(self):
        """Should allow local-dev when configured."""
        os.environ["ALLOW_LOCAL_DEV"] = "true"

        from src.auth.validator import validate_request

        mock_request = Mock()
        mock_request.headers = {}

        identity = await validate_request(mock_request)

        assert identity == "local-dev"

    @pytest.mark.asyncio
    async def test_no_auth_raises_401(self):
        """Should raise 401 when no auth method succeeds."""
        from src.auth.validator import validate_request
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await validate_request(mock_request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthorized_header_raises_403(self):
        """Should raise 403 for unauthorized header identity."""
        from src.auth.validator import validate_request
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.headers = {
            "X-Forwarded-User": "unauthorized-user",
        }

        with pytest.raises(HTTPException) as exc_info:
            await validate_request(mock_request)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_auth_info_oauth(self):
        """get_auth_info should report OAuth status."""
        os.environ["MCP_OAUTH_ENABLED"] = "true"
        os.environ["MCP_SERVER_AUDIENCE"] = "https://bobs-mcp.run.app"

        from src.auth.validator import get_auth_info

        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}

        mock_claims = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "https://bobs-mcp.run.app",
            "iss": "https://accounts.google.com",
        }

        with patch("src.auth.oauth_validator.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = mock_claims

            info = await get_auth_info(mock_request)

            assert info["method"] == "oauth"
            assert info["authenticated"] is True
            assert info["identity"] == "test@example.com"


# ============================================================================
# Server Endpoint Tests
# ============================================================================

class TestServerEndpoints:
    """Tests for server OAuth endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from src.server import app

        return TestClient(app)

    def test_protected_resource_metadata(self, client):
        """Should return OAuth Protected Resource Metadata."""
        response = client.get("/.well-known/oauth-protected-resource")

        assert response.status_code == 200
        data = response.json()

        assert "resource" in data
        assert "authorization_servers" in data
        assert "scopes_supported" in data
        assert "bearer_methods_supported" in data
        assert data["bearer_methods_supported"] == ["header"]

    def test_protected_resource_metadata_scopes(self, client):
        """Should include expected scopes."""
        response = client.get("/.well-known/oauth-protected-resource")
        data = response.json()

        scopes = data["scopes_supported"]

        assert "openid" in scopes
        assert "email" in scopes
        assert "bobs-mcp:tools:read" in scopes
        assert "bobs-mcp:tools:execute" in scopes

    def test_auth_status_endpoint(self, client):
        """Should return authentication status."""
        response = client.get("/auth/status")

        assert response.status_code == 200
        data = response.json()

        assert "oauth" in data
        assert "current_request" in data
        assert "auth_methods_available" in data

    def test_health_endpoint_unchanged(self, client):
        """Health endpoint should remain accessible."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ============================================================================
# OAuthClaims Tests
# ============================================================================

class TestOAuthClaims:
    """Tests for OAuthClaims dataclass."""

    def test_get_identity_with_email(self):
        """Should return email when present."""
        from src.auth.oauth_validator import OAuthClaims

        claims = OAuthClaims(
            subject="user123",
            email="test@example.com",
            audience="https://api.example.com",
            issuer="https://accounts.google.com",
            expires_at=None,
            issued_at=None,
            raw_claims={},
        )

        assert claims.get_identity() == "test@example.com"

    def test_get_identity_without_email(self):
        """Should return subject when email not present."""
        from src.auth.oauth_validator import OAuthClaims

        claims = OAuthClaims(
            subject="user123",
            email=None,
            audience="https://api.example.com",
            issuer="https://accounts.google.com",
            expires_at=None,
            issued_at=None,
            raw_claims={},
        )

        assert claims.get_identity() == "user123"

    def test_to_dict(self):
        """Should serialize to dictionary."""
        from src.auth.oauth_validator import OAuthClaims

        claims = OAuthClaims(
            subject="user123",
            email="test@example.com",
            audience="https://api.example.com",
            issuer="https://accounts.google.com",
            expires_at=1234567890,
            issued_at=1234567800,
            raw_claims={"extra": "data"},
        )

        d = claims.to_dict()

        assert d["subject"] == "user123"
        assert d["email"] == "test@example.com"
        assert d["audience"] == "https://api.example.com"
        assert d["issuer"] == "https://accounts.google.com"
        assert d["expires_at"] == 1234567890
        assert d["issued_at"] == 1234567800
        # raw_claims not included in to_dict
        assert "raw_claims" not in d
