"""
Root pytest configuration for Bob's Brain test suite.

Provides shared fixtures, factories, and utilities used across all test tiers:
- tests/unit/
- tests/integration/
- tests/e2e/
- tests/smoke/

Environment toggles (set in .env.test or shell):
    BOB_TEST_MODE=1          - Enable test mode (stub external services)
    BOB_STUB_EXTERNAL=1      - Force stub all external HTTP calls
    BOB_LLM_MODE=stub        - LLM mode: stub|replay|real (default: stub in CI)
"""

import os

import pytest

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

IS_CI = os.getenv("CI", "").lower() in ("true", "1")
BOB_TEST_MODE = os.getenv("BOB_TEST_MODE", "1" if IS_CI else "0") == "1"
BOB_STUB_EXTERNAL = os.getenv("BOB_STUB_EXTERNAL", "1" if IS_CI else "0") == "1"
BOB_LLM_MODE = os.getenv("BOB_LLM_MODE", "stub")


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------


def pytest_configure(config):
    """Register additional custom markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests (critical workflows)")
    config.addinivalue_line("markers", "smoke: Smoke tests (post-deploy health checks)")
    config.addinivalue_line("markers", "contract: Contract tests (schema validation)")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def deterministic_id():
    """Generate deterministic sequential IDs for reproducible tests."""
    counter = 0

    def _next_id(prefix="test"):
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter:04d}"

    return _next_id


@pytest.fixture
def fake_clock():
    """Provide a controllable clock for time-dependent tests.

    Usage:
        def test_expiration(fake_clock):
            clock = fake_clock("2025-01-01T00:00:00+00:00")
            assert clock.now().year == 2025
            clock.advance(hours=2)
            assert clock.now().hour == 2
    """
    from tests.fixtures.clock import FakeClock

    def _make_clock(iso_start="2025-01-01T00:00:00+00:00"):
        return FakeClock.from_iso(iso_start)

    return _make_clock


@pytest.fixture
def mandate_factory():
    """Factory for creating Mandate test objects with sensible defaults.

    Usage:
        def test_something(mandate_factory):
            mandate = mandate_factory(risk_tier="R2", max_iterations=5)
    """
    from tests.fixtures.factories import make_mandate

    return make_mandate


@pytest.fixture
def a2a_task_factory():
    """Factory for creating A2ATask test objects.

    Usage:
        def test_dispatch(a2a_task_factory):
            task = a2a_task_factory(specialist="iam_adk")
    """
    from tests.fixtures.factories import make_a2a_task

    return make_a2a_task


@pytest.fixture
def a2a_result_factory():
    """Factory for creating A2AResult test objects.

    Usage:
        def test_result(a2a_result_factory):
            result = a2a_result_factory(status="SUCCESS", specialist="iam_qa")
    """
    from tests.fixtures.factories import make_a2a_result

    return make_a2a_result


@pytest.fixture
def gate_result_factory():
    """Factory for creating GateResult test objects."""
    from tests.fixtures.factories import make_gate_result

    return make_gate_result


@pytest.fixture
def stub_llm():
    """Provide a stub LLM for tests that need LLM responses.

    Usage:
        def test_with_llm(stub_llm):
            response = stub_llm.generate("hello")
            assert stub_llm.call_count == 1
    """
    from tests.stubs.llm import StubLLM

    return StubLLM()


@pytest.fixture
def stub_agent_engine():
    """Provide a stub Agent Engine client for tests.

    Usage:
        async def test_query(stub_agent_engine):
            response = await stub_agent_engine.query("hello")
            assert response["status"] == "SUCCESS"
    """
    from tests.stubs.agent_engine import StubAgentEngineClient

    return StubAgentEngineClient()
