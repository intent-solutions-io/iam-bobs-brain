"""
Unit tests for iam-adk lazy loading pattern (6774).

Tests the lazy-loading App pattern to ensure:
- No heavy work at import time
- Agent created lazily on first use
- Environment validation happens lazily
- App can be called multiple times safely
"""

import pytest
import os
import sys
from unittest.mock import patch
from pathlib import Path


class TestLazyImport:
    """Tests for lazy import behavior."""

    def test_module_imports_without_env_vars(self):
        """Test module can be imported without full environment setup."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            # Should NOT raise on import (lazy validation)
            try:
                # Remove from sys.modules if already imported
                if 'agents.iam_adk.agent' in sys.modules:
                    del sys.modules['agents.iam_adk.agent']

                import agents.iam_adk.agent

                # Module should have expected symbols
                assert hasattr(agents.iam_adk.agent, 'create_agent')
                assert hasattr(agents.iam_adk.agent, 'create_app')
                assert hasattr(agents.iam_adk.agent, 'app')
            except Exception as e:
                pytest.fail(f"Import should not fail without env vars: {e}")

    def test_import_time_is_fast(self):
        """Test import time is fast (no heavy initialization)."""
        import time

        # Clear cache
        if 'agents.iam_adk.agent' in sys.modules:
            del sys.modules['agents.iam_adk.agent']

        # Measure import time
        start = time.time()
        import agents.iam_adk.agent
        elapsed = time.time() - start

        # Import should be under 1 second (target: 50-200ms, allowing buffer)
        assert elapsed < 1.0, f"Import took {elapsed:.3f}s (should be < 1s)"


class TestCreateAgent:
    """Tests for create_agent() function."""

    def test_create_agent_without_project_id(self):
        """Test create_agent() succeeds even if PROJECT_ID missing (6767-LAZY)."""
        # Minimal env (missing PROJECT_ID) - should NOT raise at creation
        env = {
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_agent

            # Agent creation is cheap and does NOT validate env (6767-LAZY)
            # Validation happens when agent is invoked by Runner/Agent Engine
            agent = create_agent()
            assert agent is not None
            assert agent.name == "iam_adk"

    def test_create_agent_without_location(self):
        """Test create_agent() succeeds even if LOCATION missing (6767-LAZY)."""
        env = {
            'PROJECT_ID': 'test-project',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_agent

            # Agent creation is cheap and does NOT validate env (6767-LAZY)
            agent = create_agent()
            assert agent is not None
            assert agent.name == "iam_adk"

    def test_create_agent_without_agent_engine_id(self):
        """Test create_agent() succeeds even if AGENT_ENGINE_ID missing (6767-LAZY)."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_SPIFFE_ID': 'spiffe://test'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_agent

            # Agent creation is cheap and does NOT validate env (6767-LAZY)
            agent = create_agent()
            assert agent is not None
            assert agent.name == "iam_adk"

    def test_create_agent_with_valid_env(self):
        """Test create_agent() succeeds with valid environment."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_agent

            agent = create_agent()

            # Verify agent is correctly configured
            assert agent is not None
            assert agent.name == "iam_adk"
            assert agent.model == "gemini-2.0-flash-exp"
            # Tools should be wired (non-empty list)
            assert hasattr(agent, 'tools')


class TestCreateApp:
    """Tests for create_app() function."""

    def test_create_app_without_project_id(self):
        """Test create_app() succeeds even if PROJECT_ID missing (6767-LAZY)."""
        env = {
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_app

            # App creation is cheap and does NOT validate env (6767-LAZY)
            # Validation happens when app is invoked by Agent Engine
            app = create_app()
            assert app is not None

    def test_create_app_without_agent_engine_id(self):
        """Test create_app() succeeds even if AGENT_ENGINE_ID missing (6767-LAZY)."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_SPIFFE_ID': 'spiffe://test'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_app

            # App creation is cheap and does NOT validate env (6767-LAZY)
            app = create_app()
            assert app is not None

    def test_create_app_with_valid_env(self):
        """Test create_app() succeeds with valid environment."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_app

            app = create_app()

            # Verify app is created
            assert app is not None
            # App has 'name' attribute (from google.adk.apps.App)
            assert hasattr(app, 'name')
            assert app.name == 'bobs-brain'


class TestAppEntrypoint:
    """Tests for module-level app entrypoint."""

    def test_app_symbol_exists(self):
        """Test module has 'app' symbol for Agent Engine."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            # Clear cache
            if 'agents.iam_adk.agent' in sys.modules:
                del sys.modules['agents.iam_adk.agent']

            import agents.iam_adk.agent

            # Module should have 'app' symbol
            assert hasattr(agents.iam_adk.agent, 'app')
            assert agents.iam_adk.agent.app is not None

    def test_app_is_not_agent(self):
        """Test module-level symbol is 'app' not 'agent' (6774 pattern)."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            # Clear cache
            if 'agents.iam_adk.agent' in sys.modules:
                del sys.modules['agents.iam_adk.agent']

            import agents.iam_adk.agent

            # Should have 'app', NOT 'root_agent'
            assert hasattr(agents.iam_adk.agent, 'app')
            # Old pattern (root_agent) should not exist at module level
            assert not hasattr(agents.iam_adk.agent, 'root_agent')


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with old pattern."""

    def test_create_runner_still_exists(self):
        """Test create_runner() still exists for backwards compatibility."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_runner

            # Function should exist (deprecated but not removed)
            assert callable(create_runner)

    def test_create_runner_is_deprecated(self):
        """Test create_runner() logs deprecation warning."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test',
            'APP_NAME': 'bobs-brain'
        }

        with patch.dict(os.environ, env, clear=True):
            from agents.iam_adk.agent import create_runner
            import logging

            # Capture logs
            with patch('agents.iam_adk.agent.logger') as mock_logger:
                runner = create_runner()

                # Should log deprecation warning
                assert mock_logger.warning.called
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "deprecated" in warning_msg.lower()
                assert "create_app" in warning_msg


class TestSmokeTest:
    """Comprehensive smoke test for lazy loading behavior."""

    def test_full_lazy_loading_cycle(self):
        """Test complete lazy loading cycle from import to usage."""
        env = {
            'PROJECT_ID': 'test-project',
            'LOCATION': 'us-central1',
            'AGENT_ENGINE_ID': 'test-engine',
            'AGENT_SPIFFE_ID': 'spiffe://test/iam-adk',
            'APP_NAME': 'bobs-brain'
        }

        # Step 1: Import module (should be fast, no exceptions)
        with patch.dict(os.environ, env, clear=True):
            # Clear cache
            if 'agents.iam_adk.agent' in sys.modules:
                del sys.modules['agents.iam_adk.agent']

            import time
            start = time.time()
            import agents.iam_adk.agent
            import_time = time.time() - start

            # Import should be fast
            assert import_time < 1.0, f"Import took {import_time:.3f}s"

            # Step 2: Access app (lazy initialization happens here)
            app = agents.iam_adk.agent.app
            assert app is not None

            # Step 3: Call create_agent directly
            agent = agents.iam_adk.agent.create_agent()
            assert agent is not None
            assert agent.name == "iam_adk"

            # Step 4: Call create_app multiple times (idempotent)
            app1 = agents.iam_adk.agent.create_app()
            app2 = agents.iam_adk.agent.create_app()
            # Both should be valid app instances
            assert app1 is not None
            assert app2 is not None
            # Note: They may be different instances (that's OK)
            # The key is both are valid and functional
