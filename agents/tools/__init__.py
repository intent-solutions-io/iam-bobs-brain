"""
Agent tools for GitHub integration, approval workflows, and other utilities.
"""

from .github_client import (
    GitHubClient,
    GitHubClientError,
    GitHubAuthError,
    GitHubRateLimitError,
    RepoFile,
    RepoTree,
    get_client
)

from .approval_tool import (
    # Core functions
    classify_risk_level,
    create_approval_request,
    requires_approval,
    request_approval,
    handle_approval_callback,
    get_pending_approvals,
    get_approval_status,
    # Tool functions for agents
    request_human_approval,
    check_approval_status,
)

__all__ = [
    # GitHub tools
    'GitHubClient',
    'GitHubClientError',
    'GitHubAuthError',
    'GitHubRateLimitError',
    'RepoFile',
    'RepoTree',
    'get_client',
    # Approval tools (Phase P4)
    'classify_risk_level',
    'create_approval_request',
    'requires_approval',
    'request_approval',
    'handle_approval_callback',
    'get_pending_approvals',
    'get_approval_status',
    'request_human_approval',
    'check_approval_status',
]