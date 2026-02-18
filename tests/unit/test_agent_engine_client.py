"""
Unit Tests for Agent Engine Client (AE2)

Tests the agent_engine_client.py module which handles communication
with Vertex AI Agent Engine from the a2a gateway.

Test Coverage:
- Agent configuration retrieval
- Authentication token handling
- Request formatting and routing
- Error handling (HTTP errors, timeouts, auth failures)
- Response parsing and metadata
"""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)


# Test fixtures
@pytest.fixture
def mock_agent_config():
    """Mock AgentEngineConfig."""
    from agents.config.agent_engine import AgentEngineConfig

    return AgentEngineConfig(
        reasoning_engine_id="test-engine-123",
        project_id="test-project",
        location="us-central1",
        spiffe_id="spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.9.0",
        notes="Test config",
    )


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv("DEPLOYMENT_ENV", "dev")
    monkeypatch.setenv("PROJECT_ID", "test-project")
    monkeypatch.setenv("LOCATION", "us-central1")
    monkeypatch.setenv("AGENT_ENGINE_BOB_ID_DEV", "test-engine-bob-123")
    monkeypatch.setenv("AGENT_ENGINE_FOREMAN_ID_DEV", "test-engine-foreman-456")


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================


@patch("google.auth.default")
def test_get_gcp_token_success(mock_default):
    """Test successful token retrieval."""
    from service.a2a_gateway.agent_engine_client import get_gcp_token

    # Mock credentials
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.token = "test-token-abc123"
    mock_default.return_value = (mock_creds, None)

    token = get_gcp_token()

    assert token == "test-token-abc123"
    mock_default.assert_called_once()


@patch("google.auth.default")
def test_get_gcp_token_refresh(mock_default):
    """Test token refresh when not valid."""
    from service.a2a_gateway.agent_engine_client import get_gcp_token

    # Mock credentials needing refresh
    mock_creds = Mock()
    mock_creds.valid = False
    mock_creds.token = "refreshed-token-xyz"
    mock_creds.refresh = Mock()
    mock_default.return_value = (mock_creds, None)

    token = get_gcp_token()

    assert token == "refreshed-token-xyz"
    mock_creds.refresh.assert_called_once()


@patch("google.auth.default")
def test_get_gcp_token_failure(mock_default):
    """Test authentication failure."""
    from service.a2a_gateway.agent_engine_client import get_gcp_token

    mock_default.side_effect = Exception("Auth failed")

    with pytest.raises(RuntimeError, match="Authentication failed"):
        get_gcp_token()


# ==============================================================================
# AGENT ENGINE CALL TESTS
# ==============================================================================


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_success(
    mock_client_class,
    mock_get_token,
    mock_build_config,
    mock_agent_config,
    mock_env_vars,
):
    """Test successful Agent Engine call."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    # Mock config and token
    mock_build_config.return_value = mock_agent_config
    mock_get_token.return_value = "test-token"

    # Mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "response": "Hello from Agent Engine!",
        "session_id": "session-123",
        "metadata": {"tokens_used": 100},
    }
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    # Call function
    result = await call_agent_engine(
        agent_role="bob",
        prompt="Test prompt",
        session_id="session-123",
        correlation_id="corr-456",
    )

    # Assertions
    assert result.response == "Hello from Agent Engine!"
    assert result.session_id == "session-123"
    assert result.error is None
    assert result.metadata["tokens_used"] == 100
    assert result.metadata["agent_role"] == "bob"
    assert result.metadata["correlation_id"] == "corr-456"

    mock_build_config.assert_called_once_with("bob", "dev")
    mock_get_token.assert_called_once()


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
async def test_call_agent_engine_agent_not_configured(mock_build_config, mock_env_vars):
    """Test when agent is not configured."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = None

    result = await call_agent_engine(
        agent_role="unknown-agent",
        prompt="Test prompt",
    )

    assert result.response == ""
    assert result.error is not None
    assert "not configured" in result.error
    assert (
        result.metadata["reason"] == "Agent not configured - set environment variable"
    )


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
async def test_call_agent_engine_auth_failure(
    mock_get_token, mock_build_config, mock_agent_config, mock_env_vars
):
    """Test authentication failure."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = mock_agent_config
    mock_get_token.side_effect = RuntimeError("Auth failed")

    result = await call_agent_engine(
        agent_role="bob",
        prompt="Test prompt",
    )

    assert result.response == ""
    assert result.error is not None
    assert "Authentication failed" in result.error


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_http_error(
    mock_client_class,
    mock_get_token,
    mock_build_config,
    mock_agent_config,
    mock_env_vars,
):
    """Test HTTP error from Agent Engine."""
    import httpx

    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = mock_agent_config
    mock_get_token.return_value = "test-token"

    # Mock HTTP error
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Error", request=Mock(), response=mock_response
        )
    )
    mock_client_class.return_value = mock_client

    result = await call_agent_engine(
        agent_role="bob",
        prompt="Test prompt",
    )

    assert result.response == ""
    assert result.error is not None
    assert "HTTP error" in result.error
    assert result.metadata["status_code"] == 500


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_timeout(
    mock_client_class,
    mock_get_token,
    mock_build_config,
    mock_agent_config,
    mock_env_vars,
):
    """Test timeout error."""
    import httpx

    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = mock_agent_config
    mock_get_token.return_value = "test-token"

    # Mock timeout
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(
        side_effect=httpx.TimeoutException("Timeout")
    )
    mock_client_class.return_value = mock_client

    result = await call_agent_engine(
        agent_role="bob",
        prompt="Test prompt",
        timeout=5.0,
    )

    assert result.response == ""
    assert result.error is not None
    assert "timeout" in result.error.lower()
    assert result.metadata["timeout"] == 5.0


# ==============================================================================
# REQUEST FORMATTING TESTS
# ==============================================================================


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_headers(
    mock_client_class,
    mock_get_token,
    mock_build_config,
    mock_agent_config,
    mock_env_vars,
):
    """Test request headers include correlation ID and SPIFFE ID."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = mock_agent_config
    mock_get_token.return_value = "test-token"

    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"response": "OK"}
    mock_response.raise_for_status = Mock()

    mock_post = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post
    mock_client_class.return_value = mock_client

    await call_agent_engine(
        agent_role="bob",
        prompt="Test",
        correlation_id="corr-123",
    )

    # Check headers
    call_args = mock_post.call_args
    headers = call_args.kwargs["headers"]

    assert headers["Authorization"] == "Bearer test-token"
    assert headers["X-Correlation-ID"] == "corr-123"
    assert headers["X-SPIFFE-ID"] == mock_agent_config.spiffe_id


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_payload(
    mock_client_class,
    mock_get_token,
    mock_build_config,
    mock_agent_config,
    mock_env_vars,
):
    """Test request payload includes query, session_id, and context."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = mock_agent_config
    mock_get_token.return_value = "test-token"

    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"response": "OK"}
    mock_response.raise_for_status = Mock()

    mock_post = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post
    mock_client_class.return_value = mock_client

    test_context = {"repo": "bobs-brain", "files": ["main.py"]}

    await call_agent_engine(
        agent_role="bob",
        prompt="Analyze this repo",
        session_id="session-456",
        context=test_context,
    )

    # Check payload
    call_args = mock_post.call_args
    payload = call_args.kwargs["json"]

    assert payload["query"] == "Analyze this repo"
    assert payload["session_id"] == "session-456"
    assert payload["context"] == test_context


# ==============================================================================
# ENVIRONMENT HANDLING TESTS
# ==============================================================================


@pytest.mark.asyncio
@patch("service.a2a_gateway.agent_engine_client.build_agent_config")
@patch("service.a2a_gateway.agent_engine_client.get_gcp_token")
@patch("service.a2a_gateway.agent_engine_client.httpx.AsyncClient")
async def test_call_agent_engine_env_override(
    mock_client_class, mock_get_token, mock_build_config, mock_env_vars
):
    """Test environment can be explicitly overridden."""
    from service.a2a_gateway.agent_engine_client import call_agent_engine

    mock_build_config.return_value = None  # Will fail if called with wrong env

    await call_agent_engine(
        agent_role="bob",
        prompt="Test",
        env="staging",
    )

    # Should have been called with staging env
    mock_build_config.assert_called_once_with("bob", "staging")
