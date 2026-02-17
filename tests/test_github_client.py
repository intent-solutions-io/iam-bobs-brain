#!/usr/bin/env python3
"""
Test suite for GitHub client (read-only operations).

Tests work with and without GITHUB_TOKEN:
- Without token: Mocked tests only
- With token: Optional live tests (not run by default)
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.tools.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubRateLimitError,
    RepoFile,
    RepoTree,
    get_client,
)


class TestGitHubClient(unittest.TestCase):
    """Test GitHub client with mocked responses."""

    def setUp(self):
        """Set up test client."""
        self.client = GitHubClient(token="fake_token")

    def test_client_initialization(self):
        """Test client initialization."""
        # With token
        client = GitHubClient(token="test_token")
        self.assertEqual(client.token, "test_token")
        self.assertIn("Authorization", client.session.headers)

        # Without token (from env)
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            client = GitHubClient()
            self.assertEqual(client.token, "env_token")

        # No token at all
        with patch.dict(os.environ, {}, clear=True):
            client = GitHubClient()
            self.assertIsNone(client.token)

    @patch("requests.Session.request")
    def test_list_repo_files(self, mock_request):
        """Test listing repository files."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 1024, "sha": "abc123"},
                {"path": "src/main.py", "type": "blob", "size": 2048, "sha": "def456"},
                {"path": "tests", "type": "tree", "size": 0, "sha": "ghi789"},
            ]
        }
        mock_request.return_value = mock_response

        # List files
        files = self.client.list_repo_files(owner="test", repo="repo", ref="main")

        # Should have 2 files (excluding directory)
        self.assertEqual(len(files), 2)
        self.assertIsInstance(files[0], RepoFile)
        self.assertEqual(files[0].path, "README.md")
        self.assertEqual(files[0].size, 1024)

    @patch("requests.Session.request")
    def test_list_repo_files_with_filters(self, mock_request):
        """Test listing files with pattern filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 100, "sha": "a"},
                {"path": "main.py", "type": "blob", "size": 200, "sha": "b"},
                {"path": "test.pyc", "type": "blob", "size": 50, "sha": "c"},
                {"path": "large.bin", "type": "blob", "size": 2000000, "sha": "d"},
            ]
        }
        mock_request.return_value = mock_response

        # Filter by patterns
        files = self.client.list_repo_files(
            owner="test",
            repo="repo",
            ref="main",
            file_patterns=["*.py", "*.md"],
            exclude_patterns=["*.pyc"],
            max_size_bytes=1000000,
        )

        # Should have 2 files (README.md, main.py)
        self.assertEqual(len(files), 2)
        paths = [f.path for f in files]
        self.assertIn("README.md", paths)
        self.assertIn("main.py", paths)
        self.assertNotIn("test.pyc", paths)
        self.assertNotIn("large.bin", paths)

    @patch("requests.Session.request")
    def test_get_file_content(self, mock_request):
        """Test fetching file content."""
        import base64

        # Mock API response
        content = "Hello, World!"
        encoded_content = base64.b64encode(content.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_request.return_value = mock_response

        # Get file content
        result = self.client.get_file_content(
            owner="test", repo="repo", path="README.md", ref="main"
        )

        self.assertEqual(result, content)

    @patch("requests.Session.request")
    def test_get_repo_tree(self, mock_request):
        """Test getting complete repo tree."""
        # Mock list files response
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "tree": [
                {"path": "file1.py", "type": "blob", "size": 100, "sha": "a"},
                {"path": "file2.py", "type": "blob", "size": 200, "sha": "b"},
            ]
        }

        mock_request.return_value = list_response

        # Get tree
        tree = self.client.get_repo_tree(
            owner="test", repo="repo", ref="main", fetch_content=False
        )

        self.assertIsInstance(tree, RepoTree)
        self.assertEqual(tree.owner, "test")
        self.assertEqual(tree.repo, "repo")
        self.assertEqual(len(tree.files), 2)
        self.assertEqual(tree.total_size, 300)

    @patch("requests.Session.request")
    def test_auth_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with self.assertRaises(GitHubAuthError):
            self.client.list_repo_files("test", "repo", "main")

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "rate limit exceeded"
        mock_response.headers = {"X-RateLimit-Reset": "1234567890"}
        mock_request.return_value = mock_response

        with self.assertRaises(GitHubRateLimitError):
            self.client.list_repo_files("test", "repo", "main")

    @patch("requests.Session.request")
    def test_check_auth_success(self, mock_request):
        """Test authentication check."""
        # Mock responses
        rate_limit_response = Mock()
        rate_limit_response.status_code = 200
        rate_limit_response.json.return_value = {
            "rate": {"remaining": 5000, "limit": 5000}
        }

        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {"login": "testuser"}

        mock_request.side_effect = [rate_limit_response, user_response]

        # Check auth
        result = self.client.check_auth()

        self.assertTrue(result["authenticated"])
        self.assertEqual(result["user"], "testuser")
        self.assertEqual(result["rate_limit_remaining"], 5000)

    def test_check_auth_no_token(self):
        """Test auth check without token."""
        client = GitHubClient(token=None)
        result = client.check_auth()

        self.assertFalse(result["authenticated"])
        self.assertIn("No GITHUB_TOKEN", result["message"])

    def test_get_client_helper(self):
        """Test get_client convenience function."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            client = get_client()
            self.assertIsInstance(client, GitHubClient)
            self.assertEqual(client.token, "test_token")


class TestRepoFileDataclass(unittest.TestCase):
    """Test RepoFile dataclass."""

    def test_repo_file_creation(self):
        """Test creating RepoFile."""
        file = RepoFile(path="test.py", type="file", size=1024, sha="abc123")

        self.assertEqual(file.path, "test.py")
        self.assertEqual(file.size, 1024)
        self.assertIsNone(file.content)


class TestRepoTreeDataclass(unittest.TestCase):
    """Test RepoTree dataclass."""

    def test_repo_tree_creation(self):
        """Test creating RepoTree."""
        file1 = RepoFile(path="f1.py", type="file", size=100, sha="a")
        file2 = RepoFile(path="f2.py", type="file", size=200, sha="b")

        tree = RepoTree(
            owner="test", repo="repo", ref="main", files=[file1, file2], total_size=300
        )

        self.assertEqual(tree.owner, "test")
        self.assertEqual(len(tree.files), 2)
        self.assertEqual(tree.total_size, 300)


@unittest.skipUnless(
    os.getenv("GITHUB_TOKEN") and os.getenv("RUN_LIVE_TESTS"),
    "Set GITHUB_TOKEN and RUN_LIVE_TESTS=1 to run live tests",
)
class TestGitHubClientLive(unittest.TestCase):
    """
    Live tests against real GitHub API.

    Only run when GITHUB_TOKEN and RUN_LIVE_TESTS are set.
    Uses public repo to avoid requiring write access.
    """

    def setUp(self):
        """Set up live client."""
        self.client = get_client()

    def test_live_list_files(self):
        """Test listing files from a real public repo."""
        files = self.client.list_repo_files(
            owner="jeremylongshore",
            repo="bobs-brain",
            ref="main",
            file_patterns=["*.md"],
            max_size_bytes=100000,
        )

        self.assertGreater(len(files), 0)
        self.assertTrue(all(f.path.endswith(".md") for f in files))

    def test_live_get_file(self):
        """Test fetching file content from a real public repo."""
        content = self.client.get_file_content(
            owner="jeremylongshore", repo="bobs-brain", path="README.md", ref="main"
        )

        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)

    def test_live_get_tree(self):
        """Test getting repo tree from a real public repo."""
        tree = self.client.get_repo_tree(
            owner="jeremylongshore",
            repo="bobs-brain",
            ref="main",
            file_patterns=["*.py"],
            max_file_size=100000,
            max_total_size=1000000,
            fetch_content=False,
        )

        self.assertIsInstance(tree, RepoTree)
        self.assertGreater(len(tree.files), 0)
        self.assertGreater(tree.total_size, 0)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
