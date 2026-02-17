#!/usr/bin/env python3
"""
Test suite for GitHub feature flags and safety configuration.

Tests the Phase GHC feature flag system that controls GitHub issue creation.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.config.github_features import (
    GitHubFeatureConfig,
    can_create_issues_for_repo,
    get_feature_status_summary,
    load_github_feature_config,
)


class TestGitHubFeatureConfig(unittest.TestCase):
    """Test GitHubFeatureConfig dataclass."""

    def test_is_repo_allowed_with_wildcard(self):
        """Test wildcard allows all repos."""
        config = GitHubFeatureConfig(issue_creation_enabled=True, allowed_repos={"*"})

        self.assertTrue(config.is_repo_allowed("bobs-brain"))
        self.assertTrue(config.is_repo_allowed("any-repo"))
        self.assertTrue(config.is_repo_allowed("unknown"))

    def test_is_repo_allowed_with_specific_repos(self):
        """Test specific repo allowlist."""
        config = GitHubFeatureConfig(
            issue_creation_enabled=True, allowed_repos={"bobs-brain", "test-repo"}
        )

        self.assertTrue(config.is_repo_allowed("bobs-brain"))
        self.assertTrue(config.is_repo_allowed("test-repo"))
        self.assertFalse(config.is_repo_allowed("other-repo"))
        self.assertFalse(config.is_repo_allowed("unknown"))

    def test_is_repo_allowed_with_empty_list(self):
        """Test empty allowlist blocks all repos."""
        config = GitHubFeatureConfig(issue_creation_enabled=True, allowed_repos=set())

        self.assertFalse(config.is_repo_allowed("bobs-brain"))
        self.assertFalse(config.is_repo_allowed("any-repo"))


class TestLoadGitHubFeatureConfig(unittest.TestCase):
    """Test loading configuration from environment variables."""

    def test_default_config_disabled(self):
        """Test default configuration (disabled)."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_github_feature_config()

            self.assertFalse(config.issue_creation_enabled)
            self.assertEqual(config.allowed_repos, set())

    def test_enabled_with_specific_repos(self):
        """Test enabled with specific repo list."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "bobs-brain,test-repo",
            },
        ):
            config = load_github_feature_config()

            self.assertTrue(config.issue_creation_enabled)
            self.assertEqual(config.allowed_repos, {"bobs-brain", "test-repo"})

    def test_enabled_with_wildcard(self):
        """Test enabled with wildcard (all repos)."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "*",
            },
        ):
            config = load_github_feature_config()

            self.assertTrue(config.issue_creation_enabled)
            self.assertEqual(config.allowed_repos, {"*"})

    def test_enabled_with_spaces_in_repos(self):
        """Test handling of spaces in repo list."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "repo1, repo2 , repo3",
            },
        ):
            config = load_github_feature_config()

            self.assertTrue(config.issue_creation_enabled)
            self.assertEqual(config.allowed_repos, {"repo1", "repo2", "repo3"})

    def test_enabled_variations(self):
        """Test different variations of 'enabled' value."""
        enabled_values = ["true", "True", "TRUE", "1", "yes", "on"]

        for value in enabled_values:
            with patch.dict(os.environ, {"GITHUB_ISSUE_CREATION_ENABLED": value}):
                config = load_github_feature_config()
                self.assertTrue(
                    config.issue_creation_enabled, f"Failed for value: {value}"
                )

    def test_disabled_variations(self):
        """Test different variations of 'disabled' value."""
        disabled_values = ["false", "False", "FALSE", "0", "no", "off", ""]

        for value in disabled_values:
            with patch.dict(os.environ, {"GITHUB_ISSUE_CREATION_ENABLED": value}):
                config = load_github_feature_config()
                self.assertFalse(
                    config.issue_creation_enabled, f"Failed for value: {value}"
                )


class TestCanCreateIssuesForRepo(unittest.TestCase):
    """Test the main safety gate function."""

    def test_disabled_blocks_all_repos(self):
        """Test that disabled flag blocks all repos."""
        config = GitHubFeatureConfig(
            issue_creation_enabled=False, allowed_repos={"*"}  # Even with wildcard
        )

        self.assertFalse(can_create_issues_for_repo("bobs-brain", config))
        self.assertFalse(can_create_issues_for_repo("any-repo", config))

    def test_enabled_with_specific_repo_allowed(self):
        """Test enabled with repo in allowlist."""
        config = GitHubFeatureConfig(
            issue_creation_enabled=True, allowed_repos={"bobs-brain", "test-repo"}
        )

        self.assertTrue(can_create_issues_for_repo("bobs-brain", config))
        self.assertTrue(can_create_issues_for_repo("test-repo", config))

    def test_enabled_with_repo_not_allowed(self):
        """Test enabled but repo not in allowlist."""
        config = GitHubFeatureConfig(
            issue_creation_enabled=True, allowed_repos={"bobs-brain"}
        )

        self.assertFalse(can_create_issues_for_repo("other-repo", config))
        self.assertFalse(can_create_issues_for_repo("unknown", config))

    def test_enabled_with_wildcard(self):
        """Test enabled with wildcard allows all."""
        config = GitHubFeatureConfig(issue_creation_enabled=True, allowed_repos={"*"})

        self.assertTrue(can_create_issues_for_repo("bobs-brain", config))
        self.assertTrue(can_create_issues_for_repo("any-repo", config))
        self.assertTrue(can_create_issues_for_repo("unknown", config))

    def test_loads_config_from_env_when_not_provided(self):
        """Test that config is loaded from env when not provided."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "bobs-brain",
            },
        ):
            # Don't pass config - should load from env
            self.assertTrue(can_create_issues_for_repo("bobs-brain"))
            self.assertFalse(can_create_issues_for_repo("other-repo"))


class TestGetFeatureStatusSummary(unittest.TestCase):
    """Test the status summary function."""

    def test_disabled_summary(self):
        """Test summary when feature is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            status = get_feature_status_summary()

            self.assertFalse(status["enabled"])
            self.assertEqual(status["allowed_repos"], [])
            self.assertIn("DISABLED", status["message"])
            self.assertIn("recommendation", status)

    def test_enabled_with_specific_repos_summary(self):
        """Test summary when enabled for specific repos."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "bobs-brain,test-repo",
            },
        ):
            status = get_feature_status_summary()

            self.assertTrue(status["enabled"])
            self.assertEqual(
                sorted(status["allowed_repos"]), ["bobs-brain", "test-repo"]
            )
            self.assertIn("ENABLED for", status["message"])
            self.assertNotIn("warning", status)

    def test_enabled_with_wildcard_summary(self):
        """Test summary when enabled for all repos."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_ISSUE_CREATION_ENABLED": "true",
                "GITHUB_ISSUE_CREATION_ALLOWED_REPOS": "*",
            },
        ):
            status = get_feature_status_summary()

            self.assertTrue(status["enabled"])
            self.assertEqual(status["allowed_repos"], ["*"])
            self.assertIn("ALL REPOS", status["message"])
            self.assertIn("warning", status)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
