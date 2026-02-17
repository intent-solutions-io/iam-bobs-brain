"""
GitHub Client for Repository Access

Minimal GitHub REST API client for SWE pipeline operations:
- Read operations: Fetch repository contents and metadata
- Write operations: Create issues (requires authentication and feature flags)

Write operations are guarded by authentication requirements and
feature flags for safety.
"""

import os

# Import structured logging (Phase RC2)
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging import get_logger

# Create logger
logger = get_logger(__name__)


@dataclass
class RepoFile:
    """Represents a file in a GitHub repository."""

    path: str
    type: str  # "file" or "dir"
    size: int
    sha: str
    download_url: Optional[str] = None
    content: Optional[str] = None  # Populated when fetched


@dataclass
class RepoTree:
    """Represents a repository file tree."""

    owner: str
    repo: str
    ref: str
    files: List[RepoFile] = field(default_factory=list)
    total_size: int = 0


@dataclass
class CreatedIssue:
    """Represents a newly created GitHub issue."""

    number: int
    html_url: str
    title: str
    state: str
    body: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""


class GitHubAuthError(GitHubClientError):
    """Authentication/authorization error."""


class GitHubRateLimitError(GitHubClientError):
    """API rate limit exceeded."""


class GitHubClient:
    """
    GitHub API client with read and guarded write operations.

    Read operations:
    - Fetch repository metadata and file contents
    - List repository files and trees
    - Check authentication status

    Write operations (require authentication + feature flags):
    - Create issues
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (from env if not provided)
            base_url: GitHub API base URL (default: public GitHub)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        # Set headers
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })

        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (will be appended to base_url)
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            GitHubAuthError: Authentication failed
            GitHubRateLimitError: Rate limit exceeded
            GitHubClientError: Other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, **kwargs)

            # Check for rate limiting
            if response.status_code == 403 and "rate limit" in response.text.lower():
                logger.log_error(
                    "github_rate_limit_exceeded",
                    endpoint=endpoint,
                    reset_at=response.headers.get('X-RateLimit-Reset'),
                    remaining=response.headers.get('X-RateLimit-Remaining')
                )
                raise GitHubRateLimitError(f"GitHub API rate limit exceeded. Reset at: {response.headers.get('X-RateLimit-Reset')}")

            # Check for auth errors
            if response.status_code in (401, 403):
                logger.log_error(
                    "github_auth_failed",
                    endpoint=endpoint,
                    status_code=response.status_code
                )
                raise GitHubAuthError(f"GitHub authentication failed: {response.status_code} - {response.text[:200]}")

            # Raise for other HTTP errors
            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            logger.log_error(
                "github_request_failed",
                endpoint=endpoint,
                error=str(e)
            )
            raise GitHubClientError(f"GitHub API request failed: {e}")

    def list_repo_files(
        self,
        owner: str,
        repo: str,
        ref: str = "main",
        path: str = "",
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_size_bytes: Optional[int] = None
    ) -> List[RepoFile]:
        """
        List files in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch, tag, or commit SHA
            path: Path within repo (empty for root)
            recursive: Recursively list all files
            file_patterns: Include only matching patterns (e.g., ["*.py", "*.md"])
            exclude_patterns: Exclude matching patterns (e.g., ["*.pyc"])
            max_size_bytes: Skip files larger than this

        Returns:
            List of RepoFile objects
        """
        endpoint = f"/repos/{owner}/{repo}/git/trees/{ref}"
        if recursive:
            endpoint += "?recursive=1"

        response = self._request("GET", endpoint)
        tree_data = response.json()

        files = []
        for item in tree_data.get("tree", []):
            # Skip directories in file list
            if item["type"] != "blob":  # blob = file, tree = directory
                continue

            file_path = item["path"]

            # Apply file pattern filters
            if file_patterns:
                import fnmatch
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in file_patterns):
                    continue

            # Apply exclude patterns
            if exclude_patterns:
                import fnmatch
                if any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
                    continue

            # Apply size filter
            if max_size_bytes and item.get("size", 0) > max_size_bytes:
                continue

            repo_file = RepoFile(
                path=file_path,
                type="file",
                size=item.get("size", 0),
                sha=item["sha"],
                download_url=None  # Not provided in tree API
            )
            files.append(repo_file)

        return files

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main"
    ) -> str:
        """
        Get raw file content from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path within repo
            ref: Branch, tag, or commit SHA

        Returns:
            File content as string

        Raises:
            GitHubClientError: If file cannot be fetched
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}

        response = self._request("GET", endpoint, params=params)
        data = response.json()

        # GitHub returns content base64-encoded
        import base64
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        else:
            raise GitHubClientError(f"No content returned for {path}")

    def get_repo_tree(
        self,
        owner: str,
        repo: str,
        ref: str = "main",
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: Optional[int] = None,
        max_total_size: Optional[int] = None,
        fetch_content: bool = False
    ) -> RepoTree:
        """
        Get complete repository tree with optional content fetching.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch, tag, or commit SHA
            file_patterns: Include only matching patterns
            exclude_patterns: Exclude matching patterns
            max_file_size: Max size per file in bytes
            max_total_size: Max total size in bytes (stops when exceeded)
            fetch_content: Whether to fetch actual file contents

        Returns:
            RepoTree object with files (and optionally contents)
        """
        # List all matching files
        files = self.list_repo_files(
            owner=owner,
            repo=repo,
            ref=ref,
            recursive=True,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns,
            max_size_bytes=max_file_size
        )

        tree = RepoTree(
            owner=owner,
            repo=repo,
            ref=ref,
            files=[]
        )

        # Fetch content if requested
        for file in files:
            # Check total size limit
            if max_total_size and tree.total_size + file.size > max_total_size:
                print(f"⚠️ Stopping at {len(tree.files)} files (total size limit reached)")
                break

            if fetch_content:
                try:
                    file.content = self.get_file_content(owner, repo, file.path, ref)
                except GitHubClientError as e:
                    print(f"⚠️ Could not fetch {file.path}: {e}")
                    file.content = None

            tree.files.append(file)
            tree.total_size += file.size

        return tree

    def check_auth(self) -> Dict[str, Any]:
        """
        Check if authentication is working.

        Returns:
            Dictionary with rate limit and user info

        Raises:
            GitHubAuthError: If authentication fails
        """
        if not self.token:
            return {
                "authenticated": False,
                "message": "No GITHUB_TOKEN provided - using unauthenticated access",
                "rate_limit": "60 requests/hour"
            }

        try:
            # Check rate limit endpoint (doesn't count against limit)
            response = self._request("GET", "/rate_limit")
            data = response.json()

            # Get user info
            user_response = self._request("GET", "/user")
            user_data = user_response.json()

            return {
                "authenticated": True,
                "user": user_data.get("login"),
                "rate_limit_remaining": data["rate"]["remaining"],
                "rate_limit_total": data["rate"]["limit"],
                "message": "✅ GitHub authentication successful"
            }

        except GitHubAuthError as e:
            return {
                "authenticated": False,
                "error": str(e),
                "message": "❌ GitHub authentication failed"
            }

    def create_issue(
        self,
        owner: str,
        repo: str,
        payload: Dict[str, Any]
    ) -> CreatedIssue:
        """
        Create a new issue in a GitHub repository.

        IMPORTANT: This is a WRITE operation. Requires authentication
        and appropriate permissions. Use with caution.

        Args:
            owner: Repository owner
            repo: Repository name
            payload: Issue payload dict with:
                - title (required): Issue title
                - body (optional): Issue description
                - labels (optional): List of label names
                - assignees (optional): List of GitHub usernames
                - milestone (optional): Milestone number

        Returns:
            CreatedIssue object with issue details

        Raises:
            GitHubAuthError: If no token or insufficient permissions
            GitHubClientError: If creation fails
        """
        # SAFETY: Require authentication for write operations
        if not self.token:
            raise GitHubAuthError(
                "GitHub issue creation requires authentication. "
                "Set GITHUB_TOKEN environment variable or provide token to client."
            )

        # Validate required fields
        if "title" not in payload or not payload["title"]:
            raise GitHubClientError("Issue payload must include 'title' field")

        # Make POST request to create issue
        endpoint = f"/repos/{owner}/{repo}/issues"

        try:
            response = self._request("POST", endpoint, json=payload)
            issue_data = response.json()

            # Extract issue details
            return CreatedIssue(
                number=issue_data["number"],
                html_url=issue_data["html_url"],
                title=issue_data["title"],
                state=issue_data["state"],
                body=issue_data.get("body"),
                labels=[label["name"] if isinstance(label, dict) else label
                       for label in issue_data.get("labels", [])],
                assignees=[user["login"] if isinstance(user, dict) else user
                          for user in issue_data.get("assignees", [])]
            )

        except GitHubAuthError:
            # Re-raise auth errors with context
            raise GitHubAuthError(
                f"Failed to create issue in {owner}/{repo}: "
                "Check that GITHUB_TOKEN has 'repo' or 'public_repo' scope"
            )
        except GitHubClientError as e:
            # Re-raise with context
            raise GitHubClientError(f"Failed to create issue in {owner}/{repo}: {e}")


# Convenience functions
def get_client(token: Optional[str] = None) -> GitHubClient:
    """
    Get a GitHub client instance.

    Args:
        token: Optional token (uses GITHUB_TOKEN env var if not provided)

    Returns:
        GitHubClient instance
    """
    return GitHubClient(token=token)


# Example usage
if __name__ == "__main__":
    # Demo the GitHub client
    client = get_client()

    print("🐙 GitHub Client Demo")
    print("=" * 60)

    # Check authentication
    auth_info = client.check_auth()
    print(f"\n{auth_info['message']}")
    if auth_info['authenticated']:
        print(f"User: {auth_info['user']}")
        print(f"Rate Limit: {auth_info['rate_limit_remaining']}/{auth_info['rate_limit_total']}")

    # Try listing files (will fail gracefully if no token)
    try:
        print("\n📂 Listing files in jeremylongshore/bobs-brain...")
        files = client.list_repo_files(
            owner="jeremylongshore",
            repo="bobs-brain",
            ref="main",
            file_patterns=["*.md", "*.py"],
            exclude_patterns=["*__pycache__*"],
            max_size_bytes=100000  # 100KB limit
        )

        print(f"Found {len(files)} files")
        for i, file in enumerate(files[:10], 1):
            print(f"  {i}. {file.path} ({file.size} bytes)")

        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")

    except GitHubClientError as e:
        print(f"⚠️ Could not list files: {e}")
        print("Tip: Set GITHUB_TOKEN environment variable for authenticated access")
