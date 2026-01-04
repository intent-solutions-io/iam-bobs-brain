"""GitHub API tool for repository operations.

Provides GitHub operations for Bob's MCP server:
- List issues
- Create issues
- Get pull requests
- Create pull requests

Requires GITHUB_TOKEN environment variable.
Uses PyGithub library for API access.

Phase H: Universal Tool Access
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    ToolResult,
    create_success_result,
    create_error_result,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# GitHub token from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


# ============================================================================
# OUTPUT MODELS
# ============================================================================


class GitHubIssue(BaseModel):
    """GitHub issue information."""
    number: int = Field(description="Issue number")
    title: str = Field(description="Issue title")
    state: str = Field(description="Issue state (open/closed)")
    body: Optional[str] = Field(default=None, description="Issue body")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    created_at: str = Field(description="Creation timestamp")
    html_url: str = Field(description="URL to issue on GitHub")


class GitHubPR(BaseModel):
    """GitHub pull request information."""
    number: int = Field(description="PR number")
    title: str = Field(description="PR title")
    state: str = Field(description="PR state (open/closed/merged)")
    body: Optional[str] = Field(default=None, description="PR body")
    head: str = Field(description="Head branch")
    base: str = Field(description="Base branch")
    created_at: str = Field(description="Creation timestamp")
    html_url: str = Field(description="URL to PR on GitHub")


class GitHubResult(ToolResult):
    """Structured output from GitHub API tool."""

    operation: str = Field(default="", description="Operation performed")
    repo: str = Field(default="", description="Repository (owner/repo)")
    issues: List[GitHubIssue] = Field(default_factory=list, description="Issues")
    pull_requests: List[GitHubPR] = Field(default_factory=list, description="PRs")
    created_issue: Optional[GitHubIssue] = Field(default=None, description="Created issue")
    created_pr: Optional[GitHubPR] = Field(default=None, description="Created PR")


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================


async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    labels: Optional[List[str]] = None,
    limit: int = 10
) -> GitHubResult:
    """
    List issues in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state filter (open/closed/all)
        labels: Filter by labels
        limit: Maximum issues to return

    Returns:
        GitHubResult with issues list
    """
    if not GITHUB_TOKEN:
        return create_error_result(
            GitHubResult, "github_list_issues",
            "GITHUB_TOKEN environment variable not set"
        )

    try:
        from github import Github
        g = Github(GITHUB_TOKEN)
        repository = g.get_repo(f"{owner}/{repo}")

        kwargs = {"state": state}
        if labels:
            kwargs["labels"] = labels

        issues_list = []
        for issue in repository.get_issues(**kwargs)[:limit]:
            # Skip PRs (they show up as issues in the API)
            if issue.pull_request is None:
                issues_list.append(GitHubIssue(
                    number=issue.number,
                    title=issue.title,
                    state=issue.state,
                    body=issue.body[:500] if issue.body else None,
                    labels=[l.name for l in issue.labels],
                    created_at=issue.created_at.isoformat(),
                    html_url=issue.html_url,
                ))

        return create_success_result(
            GitHubResult,
            "github_list_issues",
            operation="list_issues",
            repo=f"{owner}/{repo}",
            issues=issues_list,
        )

    except ImportError:
        return create_error_result(
            GitHubResult, "github_list_issues",
            "PyGithub library not installed. Run: pip install PyGithub"
        )
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return create_error_result(
            GitHubResult, "github_list_issues", str(e)
        )


async def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None
) -> GitHubResult:
    """
    Create an issue in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue body (markdown supported)
        labels: Labels to add

    Returns:
        GitHubResult with created issue
    """
    if not GITHUB_TOKEN:
        return create_error_result(
            GitHubResult, "github_create_issue",
            "GITHUB_TOKEN environment variable not set"
        )

    try:
        from github import Github
        g = Github(GITHUB_TOKEN)
        repository = g.get_repo(f"{owner}/{repo}")

        issue = repository.create_issue(
            title=title,
            body=body,
            labels=labels or [],
        )

        created = GitHubIssue(
            number=issue.number,
            title=issue.title,
            state=issue.state,
            body=issue.body,
            labels=[l.name for l in issue.labels],
            created_at=issue.created_at.isoformat(),
            html_url=issue.html_url,
        )

        return create_success_result(
            GitHubResult,
            "github_create_issue",
            operation="create_issue",
            repo=f"{owner}/{repo}",
            created_issue=created,
        )

    except ImportError:
        return create_error_result(
            GitHubResult, "github_create_issue",
            "PyGithub library not installed. Run: pip install PyGithub"
        )
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return create_error_result(
            GitHubResult, "github_create_issue", str(e)
        )


async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10
) -> GitHubResult:
    """
    List pull requests in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state filter (open/closed/all)
        limit: Maximum PRs to return

    Returns:
        GitHubResult with pull requests list
    """
    if not GITHUB_TOKEN:
        return create_error_result(
            GitHubResult, "github_list_prs",
            "GITHUB_TOKEN environment variable not set"
        )

    try:
        from github import Github
        g = Github(GITHUB_TOKEN)
        repository = g.get_repo(f"{owner}/{repo}")

        prs_list = []
        for pr in repository.get_pulls(state=state)[:limit]:
            prs_list.append(GitHubPR(
                number=pr.number,
                title=pr.title,
                state=pr.state,
                body=pr.body[:500] if pr.body else None,
                head=pr.head.ref,
                base=pr.base.ref,
                created_at=pr.created_at.isoformat(),
                html_url=pr.html_url,
            ))

        return create_success_result(
            GitHubResult,
            "github_list_prs",
            operation="list_pull_requests",
            repo=f"{owner}/{repo}",
            pull_requests=prs_list,
        )

    except ImportError:
        return create_error_result(
            GitHubResult, "github_list_prs",
            "PyGithub library not installed. Run: pip install PyGithub"
        )
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return create_error_result(
            GitHubResult, "github_list_prs", str(e)
        )


async def execute(
    operation: str,
    owner: str,
    repo: str,
    **kwargs
) -> GitHubResult:
    """
    Execute a GitHub operation.

    Args:
        operation: Operation to perform (list_issues, create_issue, list_prs)
        owner: Repository owner
        repo: Repository name
        **kwargs: Operation-specific parameters

    Returns:
        GitHubResult
    """
    if operation == "list_issues":
        return await list_issues(owner, repo, **kwargs)
    elif operation == "create_issue":
        return await create_issue(owner, repo, **kwargs)
    elif operation == "list_prs":
        return await list_pull_requests(owner, repo, **kwargs)
    else:
        return create_error_result(
            GitHubResult, "github_api",
            f"Unknown operation: {operation}. Valid: list_issues, create_issue, list_prs"
        )
