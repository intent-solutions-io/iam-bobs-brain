"""Unit tests for Origin validation middleware (DNS rebinding protection)."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from src.auth.origin_validator import (
    validate_origin,
    get_allowed_origins,
    OriginValidatorMiddleware,
    validate_origin_header,
    DEFAULT_ALLOWED_ORIGINS,
)


class TestValidateOriginFunction:
    """Tests for the validate_origin function."""

    def test_none_origin_passes(self):
        """No Origin header (server-to-server) should pass."""
        allowed = ["http://localhost:3000"]
        assert validate_origin(None, allowed) is True

    def test_allowed_origin_passes(self):
        """Origin in allowlist should pass."""
        allowed = ["http://localhost:3000", "https://app.example.com"]
        assert validate_origin("http://localhost:3000", allowed) is True
        assert validate_origin("https://app.example.com", allowed) is True

    def test_blocked_origin_fails(self):
        """Origin not in allowlist should fail."""
        allowed = ["http://localhost:3000"]
        assert validate_origin("http://evil.com", allowed) is False
        assert validate_origin("https://attacker.example.com", allowed) is False

    def test_origin_matching_is_case_insensitive(self):
        """Origin matching should be case-insensitive."""
        allowed = ["http://localhost:3000"]
        assert validate_origin("HTTP://LOCALHOST:3000", allowed) is True
        assert validate_origin("Http://LocalHost:3000", allowed) is True

    def test_origin_trailing_slash_handling(self):
        """Trailing slashes should be normalized."""
        allowed = ["http://localhost:3000/"]
        assert validate_origin("http://localhost:3000", allowed) is True
        assert validate_origin("http://localhost:3000/", allowed) is True

    def test_empty_allowlist_blocks_all(self):
        """Empty allowlist should block all origins (but allow None)."""
        allowed = []
        assert validate_origin(None, allowed) is True
        assert validate_origin("http://localhost:3000", allowed) is False


class TestGetAllowedOrigins:
    """Tests for get_allowed_origins function."""

    def test_returns_defaults_when_no_env(self):
        """Should return default origins when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove MCP_ALLOWED_ORIGINS if it exists
            os.environ.pop("MCP_ALLOWED_ORIGINS", None)
            origins = get_allowed_origins()
            assert origins == DEFAULT_ALLOWED_ORIGINS

    def test_custom_origins_from_env(self):
        """Should parse custom origins from MCP_ALLOWED_ORIGINS env var."""
        custom = "https://app.example.com,https://api.example.com"
        with patch.dict(os.environ, {"MCP_ALLOWED_ORIGINS": custom}):
            origins = get_allowed_origins()
            assert origins == ["https://app.example.com", "https://api.example.com"]

    def test_custom_origins_with_whitespace(self):
        """Should handle whitespace in env var."""
        custom = "  https://app.example.com , https://api.example.com  "
        with patch.dict(os.environ, {"MCP_ALLOWED_ORIGINS": custom}):
            origins = get_allowed_origins()
            assert origins == ["https://app.example.com", "https://api.example.com"]

    def test_empty_env_returns_defaults(self):
        """Empty env var should return defaults."""
        with patch.dict(os.environ, {"MCP_ALLOWED_ORIGINS": ""}):
            origins = get_allowed_origins()
            assert origins == DEFAULT_ALLOWED_ORIGINS


class TestOriginValidatorMiddleware:
    """Integration tests for OriginValidatorMiddleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create a test app with the middleware."""
        app = FastAPI()
        app.add_middleware(
            OriginValidatorMiddleware,
            allowed_origins=["http://localhost:3000", "https://trusted.example.com"]
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware, raise_server_exceptions=False)

    def test_allowed_origin_passes(self, client):
        """Request with allowed Origin header should pass."""
        response = client.get("/test", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_blocked_origin_returns_403(self, client):
        """Request with blocked Origin header should return 403."""
        response = client.get("/test", headers={"Origin": "http://evil.com"})
        assert response.status_code == 403
        response_data = response.json()
        assert "detail" in response_data
        assert "not allowed" in response_data["detail"].lower()

    def test_no_origin_header_passes(self, client):
        """Request without Origin header (server-to-server) should pass."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_multiple_allowed_origins(self, client):
        """All allowed origins should pass."""
        response1 = client.get("/test", headers={"Origin": "http://localhost:3000"})
        assert response1.status_code == 200

        response2 = client.get("/test", headers={"Origin": "https://trusted.example.com"})
        assert response2.status_code == 200


class TestOriginValidatorMiddlewareWithEnv:
    """Tests for middleware using environment variable configuration."""

    def test_middleware_uses_env_origins(self):
        """Middleware should use origins from MCP_ALLOWED_ORIGINS env var."""
        with patch.dict(os.environ, {"MCP_ALLOWED_ORIGINS": "https://custom.example.com"}):
            app = FastAPI()
            # Middleware gets origins from env when allowed_origins not specified
            app.add_middleware(OriginValidatorMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"status": "ok"}

            client = TestClient(app, raise_server_exceptions=False)

            # Custom origin should pass
            response = client.get("/test", headers={"Origin": "https://custom.example.com"})
            assert response.status_code == 200

            # Default origin should now fail
            response = client.get("/test", headers={"Origin": "http://localhost:3000"})
            assert response.status_code == 403


class TestOriginValidationLogging:
    """Tests for logging behavior."""

    def test_blocked_request_is_logged(self, caplog):
        """Blocked requests should be logged with warning level."""
        import logging
        caplog.set_level(logging.WARNING)

        app = FastAPI()
        app.add_middleware(
            OriginValidatorMiddleware,
            allowed_origins=["http://localhost:3000"]
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app, raise_server_exceptions=False)
        client.get("/test", headers={"Origin": "http://evil.com"})

        # Check that blocked request was logged
        assert any("Blocked request" in record.message for record in caplog.records)
        assert any("evil.com" in record.message for record in caplog.records)


class TestValidateOriginHeaderFunction:
    """Tests for the standalone validate_origin_header function."""

    @pytest.mark.asyncio
    async def test_allowed_origin_no_exception(self):
        """Allowed origin should not raise exception."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "http://localhost:3000"
        mock_request.url.path = "/test"

        # Should not raise
        await validate_origin_header(mock_request)

    @pytest.mark.asyncio
    async def test_blocked_origin_raises_403(self):
        """Blocked origin should raise HTTPException with 403."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "http://evil.com"
        mock_request.url.path = "/test"

        with pytest.raises(HTTPException) as exc_info:
            await validate_origin_header(mock_request)

        assert exc_info.value.status_code == 403
        assert "not allowed" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_origin_no_exception(self):
        """No Origin header should not raise exception."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.url.path = "/test"

        # Should not raise
        await validate_origin_header(mock_request)
