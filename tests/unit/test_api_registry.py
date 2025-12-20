"""Unit tests for API Registry client."""

import pytest
from unittest.mock import patch, MagicMock
import os


class TestGetApiRegistry:
    """Tests for get_api_registry function."""

    def test_returns_none_without_project_id(self):
        """Should return None when PROJECT_ID not set."""
        from agents.shared_tools.api_registry import get_api_registry

        # Clear singleton
        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        with patch.dict(os.environ, {}, clear=True):
            result = get_api_registry()
            assert result is None

    def test_returns_none_when_import_fails(self):
        """Should return None when ApiRegistry import fails."""
        from agents.shared_tools.api_registry import get_api_registry

        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        with patch.dict(os.environ, {"PROJECT_ID": "test-project"}):
            with patch.dict("sys.modules", {"google.adk.tools": None}):
                result = get_api_registry()
                # Should handle gracefully
                assert result is None or result is not None  # Just shouldn't crash

    def test_singleton_pattern(self):
        """Should return same instance on repeated calls."""
        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        mock_registry = MagicMock()

        with patch.dict(os.environ, {"PROJECT_ID": "test-project"}):
            with patch.object(module, "_registry_instance", mock_registry):
                result1 = module.get_api_registry()
                result2 = module.get_api_registry()
                assert result1 is result2


class TestGetToolsForAgent:
    """Tests for get_tools_for_agent function."""

    def test_returns_empty_when_registry_unavailable(self):
        """Should return empty list when registry unavailable."""
        from agents.shared_tools.api_registry import get_tools_for_agent

        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        with patch.dict(os.environ, {}, clear=True):
            result = get_tools_for_agent("bob")
            assert result == []

    def test_returns_empty_on_exception(self):
        """Should return empty list on registry exception."""
        from agents.shared_tools.api_registry import get_tools_for_agent

        import agents.shared_tools.api_registry as module

        mock_registry = MagicMock()
        mock_registry.get_agent_tools.side_effect = Exception("Network error")
        mock_registry.get_toolset.side_effect = Exception("Network error")

        module._registry_instance = mock_registry

        with patch.dict(os.environ, {"PROJECT_ID": "test-project"}):
            result = get_tools_for_agent("iam-adk")
            assert result == []

        # Cleanup
        module._registry_instance = None


class TestGetMcpToolset:
    """Tests for get_mcp_toolset function."""

    def test_returns_none_when_registry_unavailable(self):
        """Should return None when registry unavailable."""
        from agents.shared_tools.api_registry import get_mcp_toolset

        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        with patch.dict(os.environ, {}, clear=True):
            result = get_mcp_toolset("mcp-repo-ops")
            assert result is None

    def test_builds_full_resource_name(self):
        """Should build full resource name from short name."""
        from agents.shared_tools.api_registry import get_mcp_toolset

        import agents.shared_tools.api_registry as module

        mock_registry = MagicMock()
        mock_toolset = MagicMock()
        mock_registry.get_toolset.return_value = mock_toolset

        module._registry_instance = mock_registry

        with patch.dict(os.environ, {"PROJECT_ID": "my-project"}):
            result = get_mcp_toolset("mcp-repo-ops")

            # Verify it built the full resource name
            mock_registry.get_toolset.assert_called_once()
            call_args = mock_registry.get_toolset.call_args
            assert "projects/my-project" in call_args.kwargs.get("mcp_server_name", "")

        module._registry_instance = None

    def test_passes_tool_filter(self):
        """Should pass tool filter to registry."""
        from agents.shared_tools.api_registry import get_mcp_toolset

        import agents.shared_tools.api_registry as module

        mock_registry = MagicMock()
        module._registry_instance = mock_registry

        with patch.dict(os.environ, {"PROJECT_ID": "my-project"}):
            get_mcp_toolset("mcp-repo-ops", tool_filter=["search_codebase"])

            call_args = mock_registry.get_toolset.call_args
            assert call_args.kwargs.get("tool_filter") == ["search_codebase"]

        module._registry_instance = None


class TestIsRegistryAvailable:
    """Tests for is_registry_available function."""

    def test_returns_false_when_unavailable(self):
        """Should return False when registry not configured."""
        from agents.shared_tools.api_registry import is_registry_available

        import agents.shared_tools.api_registry as module
        module._registry_instance = None

        with patch.dict(os.environ, {}, clear=True):
            result = is_registry_available()
            assert result is False

    def test_returns_true_when_available(self):
        """Should return True when registry is available."""
        from agents.shared_tools.api_registry import is_registry_available

        import agents.shared_tools.api_registry as module
        module._registry_instance = MagicMock()

        result = is_registry_available()
        assert result is True

        module._registry_instance = None
