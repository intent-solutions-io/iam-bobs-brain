"""
Integration tests for Agent Engine smoke tests.

Phase 18: Pytest wrapper for smoke test script.

These tests verify that deployed agents in Vertex AI Agent Engine are responding.
They require:
- Agents deployed to Agent Engine
- Valid GCP credentials with access to Agent Engine
- Environment variables configured (PROJECT_ID, LOCATION, AGENT_ENGINE_ID)

Run with:
    pytest tests/integration/test_agent_engine_smoke.py -v

Or with environment variables:
    PROJECT_ID=bobs-brain-dev \
    LOCATION=us-central1 \
    AGENT_NAME=bob \
    AGENT_ENGINE_ID=bob-dev \
    pytest tests/integration/test_agent_engine_smoke.py::test_bob_smoke -v

Skip if not deployed:
    pytest tests/integration/test_agent_engine_smoke.py -v -m "not requires_deployment"
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# Check if GCP libraries available
try:
    import google.cloud.aiplatform  # noqa: F401
    GCP_AVAILABLE = True
except Exception:
    GCP_AVAILABLE = False

# Check if deployed (has required env vars)
DEPLOYED = all([
    os.getenv("PROJECT_ID"),
    os.getenv("AGENT_ENGINE_ID"),
])

# Pytest markers
requires_deployment = pytest.mark.skipif(
    not DEPLOYED,
    reason="Requires deployed agent (set PROJECT_ID and AGENT_ENGINE_ID env vars)"
)

requires_gcp = pytest.mark.skipif(
    not GCP_AVAILABLE,
    reason="Requires google-cloud-aiplatform (pip install google-cloud-aiplatform)"
)


class TestAgentEngineSmoke:
    """Smoke tests for deployed agents."""

    def _run_smoke_test(self, agent_name: str, agent_engine_id: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Run smoke test script and return result.

        Args:
            agent_name: Agent to test (bob, iam-senior-adk-devops-lead, etc.)
            agent_engine_id: Optional override for AGENT_ENGINE_ID

        Returns:
            CompletedProcess with returncode and output
        """
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "smoke_test_agent_engine.py"),
            "--agent", agent_name,
        ]

        # Add optional parameters
        if agent_engine_id:
            cmd.extend(["--agent-engine-id", agent_engine_id])

        # Use environment variables for project and location
        env = os.environ.copy()

        result = subprocess.run(
            cmd,
            check=False, env=env,
            capture_output=True,
            text=True
        )

        return result

    @requires_deployment
    @requires_gcp
    def test_bob_smoke(self):
        """Test bob responds to smoke test request."""
        agent_name = os.getenv("AGENT_NAME", "bob")
        agent_engine_id = os.getenv("AGENT_ENGINE_ID")

        result = self._run_smoke_test(agent_name, agent_engine_id)

        # Print output for debugging
        if result.returncode != 0:
            print(f"\nSmoke test stdout:\n{result.stdout}")
            print(f"\nSmoke test stderr:\n{result.stderr}")

        assert result.returncode == 0, f"Smoke test failed with exit code {result.returncode}"

    @requires_deployment
    @requires_gcp
    @pytest.mark.skip(reason="Foreman not deployed yet in Phase 18")
    def test_foreman_smoke(self):
        """Test foreman responds to smoke test request."""
        agent_name = "iam-senior-adk-devops-lead"
        agent_engine_id = os.getenv("FOREMAN_AGENT_ENGINE_ID")

        result = self._run_smoke_test(agent_name, agent_engine_id)

        # Print output for debugging
        if result.returncode != 0:
            print(f"\nSmoke test stdout:\n{result.stdout}")
            print(f"\nSmoke test stderr:\n{result.stderr}")

        assert result.returncode == 0, f"Smoke test failed with exit code {result.returncode}"

    def test_smoke_test_script_exists(self):
        """Verify smoke test script exists and is executable."""
        script_path = REPO_ROOT / "scripts" / "smoke_test_agent_engine.py"

        assert script_path.exists(), f"Smoke test script not found at {script_path}"
        assert os.access(script_path, os.X_OK), f"Smoke test script not executable: {script_path}"

    def test_smoke_test_script_help(self):
        """Verify smoke test script shows help without errors."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "smoke_test_agent_engine.py"), "--help"],
            check=False, capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Smoke test script --help failed"
        assert "usage:" in result.stdout.lower(), "Help output missing usage info"
        assert "--project" in result.stdout, "Help output missing --project option"
        assert "--env" in result.stdout, "Help output missing --env option"


class TestSmokeTestConfiguration:
    """Tests for smoke test configuration and environment variables."""

    def test_smoke_test_accepts_env_vars(self):
        """Verify smoke test script reads environment variables."""
        # This test runs even without deployment
        env = os.environ.copy()
        env["PROJECT_ID"] = "test-project"
        env["LOCATION"] = "us-central1"
        env["AGENT_NAME"] = "bob"
        env["AGENT_ENGINE_ID"] = "test-agent-engine-id"

        # Run with --help to avoid actual invocation
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "smoke_test_agent_engine.py"), "--help"],
            check=False, env=env,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Script failed to read environment variables"

    def test_smoke_test_requires_project_id(self):
        """Verify smoke test fails gracefully without PROJECT_ID."""
        # Run without PROJECT_ID (expect failure)
        env = os.environ.copy()
        env.pop("PROJECT_ID", None)  # Remove if present

        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "smoke_test_agent_engine.py"), "--agent", "bob"],
            check=False, env=env,
            capture_output=True,
            text=True
        )

        # Should exit with error code 2 (configuration error)
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
