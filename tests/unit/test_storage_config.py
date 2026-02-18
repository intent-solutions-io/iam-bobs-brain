"""
Test Org Storage Config Module (LIVE1-GCS)

Tests configuration helpers for org-wide knowledge hub GCS bucket.
"""

import os

# Add agents to path
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))

from config.storage import (
    get_org_storage_bucket,
    is_org_storage_write_enabled,
    make_portfolio_run_repo_path,
    make_portfolio_run_summary_path,
    make_swe_agent_run_path,
)


class TestGetOrgStorageBucket:
    """Test get_org_storage_bucket() function"""

    def test_returns_bucket_when_set(self):
        """Test returns bucket name when ORG_STORAGE_BUCKET is set"""
        with patch.dict(os.environ, {"ORG_STORAGE_BUCKET": "test-bucket"}):
            assert get_org_storage_bucket() == "test-bucket"

    def test_returns_none_when_not_set(self):
        """Test returns None when ORG_STORAGE_BUCKET is not set"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_org_storage_bucket() is None

    def test_returns_empty_string_when_empty(self):
        """Test returns empty string when ORG_STORAGE_BUCKET is empty"""
        with patch.dict(os.environ, {"ORG_STORAGE_BUCKET": ""}):
            result = get_org_storage_bucket()
            assert result == "" or result is None


class TestIsOrgStorageWriteEnabled:
    """Test is_org_storage_write_enabled() function"""

    def test_returns_true_when_enabled_lowercase(self):
        """Test returns True when ORG_STORAGE_WRITE_ENABLED='true'"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": "true"}):
            assert is_org_storage_write_enabled() is True

    def test_returns_true_when_enabled_uppercase(self):
        """Test returns True when ORG_STORAGE_WRITE_ENABLED='TRUE'"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": "TRUE"}):
            assert is_org_storage_write_enabled() is True

    def test_returns_true_when_enabled_mixed_case(self):
        """Test returns True when ORG_STORAGE_WRITE_ENABLED='True'"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": "True"}):
            assert is_org_storage_write_enabled() is True

    def test_returns_false_when_disabled(self):
        """Test returns False when ORG_STORAGE_WRITE_ENABLED='false'"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": "false"}):
            assert is_org_storage_write_enabled() is False

    def test_returns_false_when_not_set(self):
        """Test returns False when ORG_STORAGE_WRITE_ENABLED is not set (default)"""
        with patch.dict(os.environ, {}, clear=True):
            assert is_org_storage_write_enabled() is False

    def test_returns_false_when_empty(self):
        """Test returns False when ORG_STORAGE_WRITE_ENABLED is empty"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": ""}):
            assert is_org_storage_write_enabled() is False

    def test_returns_false_when_invalid_value(self):
        """Test returns False when ORG_STORAGE_WRITE_ENABLED has invalid value"""
        with patch.dict(os.environ, {"ORG_STORAGE_WRITE_ENABLED": "yes"}):
            assert is_org_storage_write_enabled() is False


class TestMakePortfolioRunSummaryPath:
    """Test make_portfolio_run_summary_path() function"""

    def test_generates_correct_path(self):
        """Test generates correct GCS path for portfolio summary"""
        run_id = "test-run-123"
        expected = "portfolio/runs/test-run-123/summary.json"
        assert make_portfolio_run_summary_path(run_id) == expected

    def test_handles_uuid_format(self):
        """Test handles UUID format run IDs"""
        run_id = "550e8400-e29b-41d4-a716-446655440000"
        expected = f"portfolio/runs/{run_id}/summary.json"
        assert make_portfolio_run_summary_path(run_id) == expected

    def test_handles_special_characters(self):
        """Test handles run IDs with special characters"""
        run_id = "run-2025-01-20T12:00:00Z"
        expected = f"portfolio/runs/{run_id}/summary.json"
        assert make_portfolio_run_summary_path(run_id) == expected


class TestMakePortfolioRunRepoPath:
    """Test make_portfolio_run_repo_path() function"""

    def test_generates_correct_path(self):
        """Test generates correct GCS path for per-repo results"""
        run_id = "test-run-123"
        repo_id = "bobs-brain"
        expected = "portfolio/runs/test-run-123/per-repo/bobs-brain.json"
        assert make_portfolio_run_repo_path(run_id, repo_id) == expected

    def test_handles_multiple_repos(self):
        """Test generates different paths for different repos"""
        run_id = "test-run-123"
        repo1 = "bobs-brain"
        repo2 = "diagnosticpro"

        path1 = make_portfolio_run_repo_path(run_id, repo1)
        path2 = make_portfolio_run_repo_path(run_id, repo2)

        assert path1 != path2
        assert "bobs-brain.json" in path1
        assert "diagnosticpro.json" in path2

    def test_handles_repo_with_special_characters(self):
        """Test handles repo IDs with special characters"""
        run_id = "test-run-123"
        repo_id = "my-repo_v2.0"
        expected = f"portfolio/runs/{run_id}/per-repo/{repo_id}.json"
        assert make_portfolio_run_repo_path(run_id, repo_id) == expected


class TestMakeSweAgentRunPath:
    """Test make_swe_agent_run_path() function (future use)"""

    def test_generates_correct_path(self):
        """Test generates correct GCS path for single-repo SWE runs"""
        agent_name = "iam-adk"
        run_id = "test-run-456"
        expected = "swe/agents/iam-adk/runs/test-run-456.json"
        assert make_swe_agent_run_path(agent_name, run_id) == expected

    def test_handles_different_agents(self):
        """Test generates different paths for different agents"""
        run_id = "test-run-456"
        agent1 = "iam-adk"
        agent2 = "iam-issue"

        path1 = make_swe_agent_run_path(agent1, run_id)
        path2 = make_swe_agent_run_path(agent2, run_id)

        assert path1 != path2
        assert "iam-adk" in path1
        assert "iam-issue" in path2

    def test_handles_agent_with_special_characters(self):
        """Test handles agent names with special characters"""
        agent_name = "iam-fix_v2"
        run_id = "test-run-456"
        expected = f"swe/agents/{agent_name}/runs/{run_id}.json"
        assert make_swe_agent_run_path(agent_name, run_id) == expected


class TestPathConsistency:
    """Test that all path functions produce consistent formats"""

    def test_all_paths_are_relative(self):
        """Test all path functions return relative paths (no leading slash)"""
        paths = [
            make_portfolio_run_summary_path("run-1"),
            make_portfolio_run_repo_path("run-1", "repo-1"),
            make_swe_agent_run_path("agent-1", "run-1"),
        ]

        for path in paths:
            assert not path.startswith("/"), f"Path should be relative: {path}"

    def test_all_paths_end_with_json(self):
        """Test all path functions return paths ending in .json"""
        paths = [
            make_portfolio_run_summary_path("run-1"),
            make_portfolio_run_repo_path("run-1", "repo-1"),
            make_swe_agent_run_path("agent-1", "run-1"),
        ]

        for path in paths:
            assert path.endswith(".json"), f"Path should end with .json: {path}"

    def test_paths_use_forward_slashes(self):
        """Test all paths use forward slashes (GCS standard)"""
        paths = [
            make_portfolio_run_summary_path("run-1"),
            make_portfolio_run_repo_path("run-1", "repo-1"),
            make_swe_agent_run_path("agent-1", "run-1"),
        ]

        for path in paths:
            assert "\\" not in path, f"Path should use forward slashes: {path}"
            assert "/" in path, f"Path should contain forward slashes: {path}"
