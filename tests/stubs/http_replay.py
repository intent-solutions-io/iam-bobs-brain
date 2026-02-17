"""
HTTP record/replay utilities using respx for httpx-based tests.

Provides helpers for recording live HTTP interactions and replaying them
deterministically in CI. Built on top of respx (mock transport for httpx).

Usage:
    import httpx
    from tests.stubs.http_replay import mock_agent_engine, mock_a2a_gateway

    # Quick mock for Agent Engine REST API
    async def test_agent_engine_call():
        with mock_agent_engine(response={"status": "SUCCESS"}):
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://us-central1-aiplatform.googleapis.com/query",
                    json={"message": "hello"}
                )
                assert resp.status_code == 200

    # Quick mock for A2A gateway
    async def test_a2a_dispatch():
        with mock_a2a_gateway(specialist="iam_adk", result={"compliance": "PASS"}):
            # ... your code that calls the A2A gateway ...
            pass
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional

try:
    import httpx
    import respx

    HAS_RESPX = True
except ImportError:
    HAS_RESPX = False


def _require_respx():
    if not HAS_RESPX:
        raise ImportError(
            "respx is required for HTTP replay. " "Install with: pip install respx"
        )


@contextmanager
def mock_agent_engine(
    response: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    base_url: str = "https://us-central1-aiplatform.googleapis.com",
):
    """Context manager that mocks Agent Engine REST API calls.

    Args:
        response: JSON response body to return.
        status_code: HTTP status code to return.
        base_url: Base URL pattern to intercept.
    """
    _require_respx()

    if response is None:
        response = {
            "status": "SUCCESS",
            "result": {"message": "Mocked Agent Engine response"},
        }

    with respx.mock(assert_all_called=False) as router:
        router.post(url__startswith=base_url).mock(
            return_value=httpx.Response(
                status_code,
                json=response,
            )
        )
        yield router


@contextmanager
def mock_a2a_gateway(
    specialist: str = "iam_adk",
    result: Optional[Dict[str, Any]] = None,
    status: str = "SUCCESS",
    status_code: int = 200,
    base_url: str = "http://localhost:8080",
):
    """Context manager that mocks A2A gateway HTTP calls.

    Args:
        specialist: Specialist name echoed in response.
        result: Result payload to return.
        status: A2AResult status (SUCCESS, FAILED, PARTIAL).
        status_code: HTTP status code.
        base_url: Gateway base URL to intercept.
    """
    _require_respx()

    if result is None:
        result = {"message": f"Mocked response from {specialist}"}

    a2a_response = {
        "status": status,
        "specialist": specialist,
        "skill_id": f"{specialist}.default",
        "result": result,
        "duration_ms": 42,
        "timestamp": "2025-01-01T00:00:00Z",
    }

    with respx.mock(assert_all_called=False) as router:
        router.post(url__startswith=base_url).mock(
            return_value=httpx.Response(
                status_code,
                json=a2a_response,
            )
        )
        yield router


@contextmanager
def mock_slack_api(
    ok: bool = True,
    channel: str = "C12345",
    ts: str = "1234567890.123456",
):
    """Context manager that mocks Slack Web API calls.

    Args:
        ok: Whether the Slack API returns ok=true.
        channel: Channel ID in response.
        ts: Message timestamp in response.
    """
    _require_respx()

    response = {
        "ok": ok,
        "channel": channel,
        "ts": ts,
        "message": {"text": "mocked"},
    }

    with respx.mock(assert_all_called=False) as router:
        router.post(url__startswith="https://slack.com/api/").mock(
            return_value=httpx.Response(200, json=response)
        )
        yield router
