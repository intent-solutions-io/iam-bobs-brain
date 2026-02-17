"""
Repository Target Registry

Provides centralized configuration for target repositories that
the SWE pipeline and agents can operate on.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class ARVProfile:
    """Agent Readiness Verification profile for a repository."""

    requires_rag: bool = False
    requires_iam_dept: bool = False
    requires_tests: bool = False
    requires_dual_memory: bool = False


@dataclass
class RepoConfig:
    """Configuration for a target repository."""

    id: str
    display_name: str
    description: str
    local_path: (
        str  # "." for current repo, "external" if not checked out, or relative path
    )
    github_owner: str
    github_repo: str
    default_branch: str
    tags: List[str] = field(default_factory=list)
    allow_write: bool = False
    arv_profile: Optional[ARVProfile] = None
    slack_channel: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full repository name (owner/repo)."""
        return f"{self.github_owner}/{self.github_repo}"

    @property
    def github_url(self) -> str:
        """Get GitHub web URL."""
        return f"https://github.com/{self.full_name}"

    @property
    def api_url(self) -> str:
        """Get GitHub API URL."""
        return f"https://api.github.com/repos/{self.full_name}"

    @property
    def is_local(self) -> bool:
        """Check if repository is available locally."""
        return self.local_path != "external"

    @property
    def is_current_repo(self) -> bool:
        """Check if this is the current repository."""
        return self.local_path == "."

    def has_tag(self, tag: str) -> bool:
        """Check if repo has a specific tag."""
        return tag in self.tags


@dataclass
class RegistrySettings:
    """Global registry settings."""

    default_allow_write: bool = False
    require_explicit_write_permission: bool = True
    github_api_rate_limit: int = 100
    analysis_file_patterns: List[str] = field(default_factory=list)
    analysis_exclude_patterns: List[str] = field(default_factory=list)
    max_file_size_bytes: int = 1048576
    max_total_size_bytes: int = 10485760


class RepoRegistry:
    """Central registry of target repositories."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize registry from YAML config.

        Args:
            config_path: Path to repos.yaml. If None, uses default location.
        """
        if config_path is None:
            # Default to config/repos.yaml relative to repo root
            repo_root = Path(__file__).parent.parent.parent
            config_path = repo_root / "config" / "repos.yaml"

        self.config_path = config_path
        self._repos: Dict[str, RepoConfig] = {}
        self.settings: RegistrySettings = RegistrySettings()

        if config_path.exists():
            self._load()
        else:
            raise FileNotFoundError(f"Repo registry not found at {config_path}")

    def _load(self):
        """Load registry from YAML file."""
        with open(self.config_path) as f:
            data = yaml.safe_load(f)

        # Load repos
        for repo_data in data.get("repos", []):
            # Parse ARV profile if present
            arv_profile = None
            arv_data = repo_data.get("arv_profile")
            if arv_data:
                arv_profile = ARVProfile(
                    requires_rag=arv_data.get("requires_rag", False),
                    requires_iam_dept=arv_data.get("requires_iam_dept", False),
                    requires_tests=arv_data.get("requires_tests", False),
                    requires_dual_memory=arv_data.get("requires_dual_memory", False),
                )

            repo = RepoConfig(
                id=repo_data["id"],
                display_name=repo_data.get("display_name", repo_data["id"]),
                description=repo_data["description"],
                local_path=repo_data.get("local_path", "external"),
                github_owner=repo_data["github_owner"],
                github_repo=repo_data["github_repo"],
                default_branch=repo_data["default_branch"],
                tags=repo_data.get("tags", []),
                allow_write=repo_data.get("allow_write", False),
                arv_profile=arv_profile,
                slack_channel=repo_data.get("slack_channel"),
            )
            self._repos[repo.id] = repo

        # Load settings
        settings_data = data.get("settings", {})
        self.settings = RegistrySettings(
            default_allow_write=settings_data.get("default_allow_write", False),
            require_explicit_write_permission=settings_data.get(
                "require_explicit_write_permission", True
            ),
            github_api_rate_limit=settings_data.get("github_api_rate_limit", 100),
            analysis_file_patterns=settings_data.get("analysis_file_patterns", []),
            analysis_exclude_patterns=settings_data.get(
                "analysis_exclude_patterns", []
            ),
            max_file_size_bytes=settings_data.get("max_file_size_bytes", 1048576),
            max_total_size_bytes=settings_data.get("max_total_size_bytes", 10485760),
        )

    def get_repo_by_id(self, repo_id: str) -> Optional[RepoConfig]:
        """
        Get repository configuration by ID.

        Args:
            repo_id: Repository identifier

        Returns:
            RepoConfig if found, None otherwise
        """
        return self._repos.get(repo_id)

    def list_repos(self, tag: Optional[str] = None) -> List[RepoConfig]:
        """
        List all repositories, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by

        Returns:
            List of matching RepoConfig objects
        """
        repos = list(self._repos.values())

        if tag:
            repos = [r for r in repos if r.has_tag(tag)]

        return sorted(repos, key=lambda r: r.id)

    def get_all_tags(self) -> List[str]:
        """Get all unique tags across all repos."""
        tags = set()
        for repo in self._repos.values():
            tags.update(repo.tags)
        return sorted(tags)


# Module-level registry instance (lazy loaded)
_registry_instance: Optional[RepoRegistry] = None


def get_registry() -> RepoRegistry:
    """
    Get the singleton registry instance.

    Returns:
        RepoRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = RepoRegistry()
    return _registry_instance


def get_repo_by_id(repo_id: str) -> Optional[RepoConfig]:
    """
    Convenience function to get repo by ID.

    Args:
        repo_id: Repository identifier

    Returns:
        RepoConfig if found, None otherwise
    """
    return get_registry().get_repo_by_id(repo_id)


def list_repos(tag: Optional[str] = None) -> List[RepoConfig]:
    """
    Convenience function to list repos.

    Args:
        tag: Optional tag to filter by

    Returns:
        List of matching RepoConfig objects
    """
    return get_registry().list_repos(tag)


# Example usage
if __name__ == "__main__":
    # Demo the registry
    registry = get_registry()

    print("📚 Repository Registry")
    print("=" * 60)

    # List all repos
    print("\nAll Repositories:")
    for repo in registry.list_repos():
        print(f"  • {repo.id}")
        print(f"    {repo.description}")
        print(f"    {repo.full_name} [{repo.default_branch}]")
        print(f"    Tags: {', '.join(repo.tags)}")
        print(f"    Write: {'✅' if repo.allow_write else '❌'}")
        print()

    # Filter by tag
    print("\nADK Repos:")
    for repo in registry.list_repos(tag="adk"):
        print(f"  • {repo.id} - {repo.full_name}")

    # Get specific repo
    print("\nBob's Brain Details:")
    bobs_brain = registry.get_repo_by_id("bobs-brain")
    if bobs_brain:
        print(f"  ID: {bobs_brain.id}")
        print(f"  Full Name: {bobs_brain.full_name}")
        print(f"  GitHub URL: {bobs_brain.github_url}")
        print(f"  API URL: {bobs_brain.api_url}")
        print(f"  Allow Write: {bobs_brain.allow_write}")

    # Show settings
    print("\nRegistry Settings:")
    print(f"  Max file size: {registry.settings.max_file_size_bytes / 1024:.0f}KB")
    print(
        f"  Max total size: {registry.settings.max_total_size_bytes / 1024 / 1024:.0f}MB"
    )
    print(f"  File patterns: {len(registry.settings.analysis_file_patterns)}")
    print(f"  Exclude patterns: {len(registry.settings.analysis_exclude_patterns)}")
