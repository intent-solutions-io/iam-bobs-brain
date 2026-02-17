"""
GitHub Feature Flags and Safety Configuration

Controls which GitHub write operations are enabled and for which repositories.
All write operations are disabled by default for safety.

ENVIRONMENT-AWARE BEHAVIOR (Phase LIVE3-STAGE-PROD-SAFETY):
- dev: DRY_RUN by default; REAL if DRY_RUN=false + token + allowlist
- staging: DRY_RUN only unless GITHUB_ENABLE_STAGING=true
- prod: DISABLED unless GITHUB_ENABLE_PROD=true

Environment Variables:
- GITHUB_ISSUE_CREATION_ENABLED: Enable GitHub issue creation (default: false)
- GITHUB_ISSUE_CREATION_ALLOWED_REPOS: Comma-separated repo IDs or "*"
- GITHUB_ISSUES_DRY_RUN: Dry-run mode (log only, no API calls) (default: true)
- GITHUB_ENABLE_STAGING: Allow real issues in staging (default: false)
- GITHUB_ENABLE_PROD: Allow real issues in prod (default: false)
- GITHUB_TOKEN: GitHub Personal Access Token (required for real creation)
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional, Set

logger = logging.getLogger(__name__)


class GitHubMode(Enum):
    """GitHub issue creation mode based on environment and flags."""

    DISABLED = "disabled"  # Feature off or blocked
    DRY_RUN = "dry_run"  # Log only, no API calls
    REAL = "real"  # Create actual issues


def _get_current_environment() -> Literal["dev", "staging", "prod"]:
    """Get current environment (imported from features module to avoid circular imports)."""
    from agents.config.features import get_current_environment

    return get_current_environment()


def get_github_mode(repo_id: Optional[str] = None) -> GitHubMode:
    """
    Determine GitHub issue creation mode based on environment and flags.

    Behavior matrix:
    - dev: DRY_RUN (default); REAL if DRY_RUN=false + token + repo in allowlist
    - staging: DRY_RUN only unless GITHUB_ENABLE_STAGING=true
    - prod: DISABLED unless GITHUB_ENABLE_PROD=true

    Args:
        repo_id: Optional repository ID to check against allowlist

    Returns:
        GitHubMode (DISABLED, DRY_RUN, or REAL)

    Examples:
        >>> # Dev environment, dry-run mode
        >>> os.environ["DEPLOYMENT_ENV"] = "dev"
        >>> os.environ["GITHUB_ISSUE_CREATION_ENABLED"] = "true"
        >>> os.environ["GITHUB_ISSUES_DRY_RUN"] = "true"
        >>> get_github_mode()
        GitHubMode.DRY_RUN

        >>> # Staging with explicit override
        >>> os.environ["DEPLOYMENT_ENV"] = "staging"
        >>> os.environ["GITHUB_ENABLE_STAGING"] = "true"
        >>> os.environ["GITHUB_ISSUES_DRY_RUN"] = "false"
        >>> get_github_mode("bobs-brain")
        GitHubMode.REAL
    """
    # Load config
    config = load_github_feature_config()

    # Check if feature is enabled globally
    if not config.issue_creation_enabled:
        logger.debug("GitHub mode: DISABLED (feature flag off)")
        return GitHubMode.DISABLED

    # Check repo allowlist if repo_id provided
    if repo_id and not config.is_repo_allowed(repo_id):
        logger.info(f"GitHub mode: DISABLED (repo {repo_id} not in allowlist)")
        return GitHubMode.DISABLED

    # Get environment and DRY_RUN flag
    env = _get_current_environment()
    dry_run_str = os.getenv("GITHUB_ISSUES_DRY_RUN", "true").lower()
    dry_run = dry_run_str in ("true", "1", "yes")

    # DEV: DRY_RUN by default, REAL if explicitly disabled + token present
    if env == "dev":
        if dry_run:
            logger.info("GitHub mode: DRY_RUN (dev environment, default)")
            return GitHubMode.DRY_RUN
        else:
            # Check if token is available for real creation
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                logger.warning("GitHub mode: DRY_RUN (dev, DRY_RUN=false but no token)")
                return GitHubMode.DRY_RUN

            logger.warning("⚠️  GitHub mode: REAL (dev environment, DRY_RUN=false)")
            return GitHubMode.REAL

    # STAGING: DRY_RUN only unless explicit override
    elif env == "staging":
        enable_staging = os.getenv("GITHUB_ENABLE_STAGING", "false").lower() == "true"
        if not enable_staging:
            logger.info(
                "GitHub mode: DRY_RUN (staging, requires GITHUB_ENABLE_STAGING=true for real)"
            )
            return GitHubMode.DRY_RUN

        # Staging enabled - check DRY_RUN flag
        if dry_run:
            logger.info("GitHub mode: DRY_RUN (staging, DRY_RUN=true)")
            return GitHubMode.DRY_RUN
        else:
            # Check token for real creation
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                logger.warning(
                    "GitHub mode: DRY_RUN (staging enabled, DRY_RUN=false but no token)"
                )
                return GitHubMode.DRY_RUN

            logger.warning("⚠️  GitHub mode: REAL (STAGING - explicit override)")
            return GitHubMode.REAL

    # PROD: DISABLED unless explicit override
    elif env == "prod":
        enable_prod = os.getenv("GITHUB_ENABLE_PROD", "false").lower() == "true"
        if not enable_prod:
            logger.info("GitHub mode: DISABLED (prod requires GITHUB_ENABLE_PROD=true)")
            return GitHubMode.DISABLED

        # Prod enabled - check DRY_RUN flag
        if dry_run:
            logger.warning(
                "⚠️  GitHub mode: DRY_RUN (PRODUCTION enabled, DRY_RUN=true)"
            )
            return GitHubMode.DRY_RUN
        else:
            # Check token for real creation
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                logger.error(
                    "GitHub mode: DISABLED (prod enabled, DRY_RUN=false but no token)"
                )
                return GitHubMode.DISABLED

            logger.error(
                "🚨 GitHub mode: REAL (PRODUCTION - explicit override - USE WITH EXTREME CAUTION)"
            )
            return GitHubMode.REAL

    # Unknown environment: disable for safety
    logger.warning(f"GitHub mode: DISABLED (unknown environment: {env})")
    return GitHubMode.DISABLED


@dataclass
class GitHubFeatureConfig:
    """Configuration for GitHub feature flags."""

    issue_creation_enabled: bool
    allowed_repos: Set[str]  # Set of repo_ids, or {"*"} for all repos

    def is_repo_allowed(self, repo_id: str) -> bool:
        """
        Check if a repo is in the allowed list.

        Args:
            repo_id: Repository ID to check

        Returns:
            True if repo is allowed, False otherwise
        """
        # "*" means all repos are allowed
        if "*" in self.allowed_repos:
            return True

        # Check if specific repo_id is in allowlist
        return repo_id in self.allowed_repos


def load_github_feature_config() -> GitHubFeatureConfig:
    """
    Load GitHub feature configuration from environment variables.

    Environment Variables:
        GITHUB_ISSUE_CREATION_ENABLED: "true" or "false" (default: "false")
        GITHUB_ISSUE_CREATION_ALLOWED_REPOS: Comma-separated repo IDs or "*" (default: "")

    Returns:
        GitHubFeatureConfig object

    Examples:
        # Disabled (default)
        export GITHUB_ISSUE_CREATION_ENABLED=false

        # Enabled for specific repos
        export GITHUB_ISSUE_CREATION_ENABLED=true
        export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=bobs-brain,test-repo

        # Enabled for all repos (use with caution!)
        export GITHUB_ISSUE_CREATION_ENABLED=true
        export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=*
    """
    # Load feature flag (default: disabled)
    enabled_str = os.getenv("GITHUB_ISSUE_CREATION_ENABLED", "false").lower()
    issue_creation_enabled = enabled_str in ("true", "1", "yes", "on")

    # Load allowed repos list (default: empty)
    allowed_str = os.getenv("GITHUB_ISSUE_CREATION_ALLOWED_REPOS", "")
    if not allowed_str:
        # Empty = no repos allowed
        allowed_repos = set()
    elif allowed_str.strip() == "*":
        # "*" = all repos allowed
        allowed_repos = {"*"}
    else:
        # Parse comma-separated list
        allowed_repos = {
            repo.strip() for repo in allowed_str.split(",") if repo.strip()
        }

    return GitHubFeatureConfig(
        issue_creation_enabled=issue_creation_enabled, allowed_repos=allowed_repos
    )


def can_create_issues_for_repo(
    repo_id: str, config: Optional[GitHubFeatureConfig] = None
) -> bool:
    """
    Check if GitHub issue creation is allowed for a specific repository.

    This is the main safety gate for issue creation. Both conditions must be true:
    1. Issue creation feature must be globally enabled
    2. The specific repo must be in the allowlist

    Args:
        repo_id: Repository ID (from repo registry)
        config: Optional pre-loaded config (loads from env if not provided)

    Returns:
        True if issue creation is allowed, False otherwise

    Examples:
        >>> # Check if can create issues for bobs-brain
        >>> if can_create_issues_for_repo("bobs-brain"):
        ...     client.create_issue(...)
        ... else:
        ...     print("Issue creation disabled for this repo")
    """
    if config is None:
        config = load_github_feature_config()

    # Both must be true: feature enabled + repo allowed
    return config.issue_creation_enabled and config.is_repo_allowed(repo_id)


def get_feature_status_summary() -> dict:
    """
    Get human-readable summary of GitHub feature configuration.

    Returns:
        Dictionary with status information

    Example:
        >>> status = get_feature_status_summary()
        >>> print(status['message'])
        ✅ GitHub issue creation ENABLED for: bobs-brain, test-repo
    """
    config = load_github_feature_config()

    if not config.issue_creation_enabled:
        return {
            "enabled": False,
            "allowed_repos": [],
            "message": "🚫 GitHub issue creation is DISABLED (safe mode)",
            "recommendation": "Set GITHUB_ISSUE_CREATION_ENABLED=true to enable",
        }

    if "*" in config.allowed_repos:
        return {
            "enabled": True,
            "allowed_repos": ["*"],
            "message": "⚠️  GitHub issue creation ENABLED for ALL REPOS",
            "warning": "Use with caution - this allows creation in any repository",
        }

    repos_list = sorted(config.allowed_repos)
    return {
        "enabled": True,
        "allowed_repos": repos_list,
        "message": f"✅ GitHub issue creation ENABLED for: {', '.join(repos_list)}",
        "info": f"Allowed repos: {len(repos_list)}",
    }


# Example usage and testing
if __name__ == "__main__":
    print("🔐 GitHub Feature Configuration")
    print("=" * 60)

    # Load current config
    config = load_github_feature_config()

    print(
        f"\nFeature Flag: GITHUB_ISSUE_CREATION_ENABLED = {config.issue_creation_enabled}"
    )
    print(f"Allowed Repos: {config.allowed_repos}")

    # Show status
    status = get_feature_status_summary()
    print(f"\n{status['message']}")

    if "warning" in status:
        print(f"⚠️  {status['warning']}")
    if "recommendation" in status:
        print(f"💡 {status['recommendation']}")

    # Test specific repos
    test_repos = ["bobs-brain", "test-repo", "unknown-repo"]
    print("\nRepository Access Checks:")
    for repo_id in test_repos:
        allowed = can_create_issues_for_repo(repo_id, config)
        icon = "✅" if allowed else "❌"
        print(f"  {icon} {repo_id}: {'ALLOWED' if allowed else 'BLOCKED'}")

    print("\n" + "=" * 60)
    print("Configuration loaded from environment variables:")
    print("  - GITHUB_ISSUE_CREATION_ENABLED")
    print("  - GITHUB_ISSUE_CREATION_ALLOWED_REPOS")
