#!/usr/bin/env python3
"""
LIVE3 Readiness Check for ARV

Validates LIVE3 configuration readiness across environments (dev/staging/prod).
Checks that environment-aware safety gates are properly configured.

This is a NON-BLOCKING check - it reports status but doesn't fail the build.

Usage:
    python3 scripts/check_live3_readiness.py

Exit Codes:
    0: Check completed successfully (even if features disabled)
    1: Critical error during check execution (infrastructure issue)

Part of: LIVE3-STAGE-PROD-SAFETY / L3P3 (ARV extension)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.config.features import get_current_environment
from agents.config.github_features import (
    GitHubMode,
    get_github_mode,
    load_github_feature_config,
)
from agents.config.notifications import (
    SlackMode,
    are_slack_notifications_enabled,
    get_slack_mode,
    get_swe_slack_destination,
)


def check_slack_readiness() -> Tuple[str, str, List[str]]:
    """
    Check Slack notification readiness.

    Returns:
        Tuple of (status, mode_str, warnings)
        status: "ENABLED", "DISABLED", "MISCONFIGURED"
        mode_str: Human-readable mode description
        warnings: List of warning messages
    """
    warnings = []
    env = get_current_environment()

    enabled = are_slack_notifications_enabled()
    mode = get_slack_mode()
    dest = get_swe_slack_destination()

    if not enabled:
        return "DISABLED", "Feature flag off", []

    if mode == SlackMode.DISABLED:
        # Feature enabled but mode is disabled (staging/prod without override)
        if env == "staging":
            warnings.append(
                "⚠️  Slack enabled but SLACK_ENABLE_STAGING=false - no messages will be sent"
            )
            return "DISABLED", "Staging gate active (override not set)", warnings
        elif env == "prod":
            warnings.append(
                "⚠️  Slack enabled but SLACK_ENABLE_PROD=false - no messages will be sent"
            )
            return "DISABLED", "Production gate active (override not set)", warnings
        else:
            warnings.append("⚠️  Slack enabled but no valid destination configured")
            return "MISCONFIGURED", "No valid webhook/channel", warnings

    if mode == SlackMode.ENABLED:
        # Feature enabled and mode is enabled
        if not dest or not dest.is_valid():
            warnings.append("⚠️  Slack mode ENABLED but no valid destination")
            return "MISCONFIGURED", "Mode enabled, no destination", warnings

        # Success - report environment and destination type
        dest_type = "webhook" if dest.webhook_url else "channel"
        mode_str = f"ENABLED ({env} - {dest_type})"

        if env in ("staging", "prod"):
            warnings.append(
                f"⚠️  Slack ENABLED in {env.upper()} - explicit override granted"
            )

        return "ENABLED", mode_str, warnings

    return "MISCONFIGURED", f"Unknown mode: {mode}", warnings


def check_github_readiness() -> Tuple[str, str, List[str]]:
    """
    Check GitHub issue creation readiness.

    Returns:
        Tuple of (status, mode_str, warnings)
        status: "ENABLED", "DRY_RUN", "DISABLED", "MISCONFIGURED"
        mode_str: Human-readable mode description
        warnings: List of warning messages
    """
    warnings = []
    env = get_current_environment()

    config = load_github_feature_config()

    if not config.issue_creation_enabled:
        return "DISABLED", "Feature flag off", []

    # Get mode for bobs-brain repo (primary repo)
    mode = get_github_mode("bobs-brain")

    if mode == GitHubMode.DISABLED:
        if env == "staging":
            warnings.append(
                "ℹ️  GitHub enabled but staging requires GITHUB_ENABLE_STAGING=true for real issues"
            )
            return "DISABLED", "Staging gate active (override not set)", warnings
        elif env == "prod":
            warnings.append(
                "ℹ️  GitHub enabled but prod requires GITHUB_ENABLE_PROD=true"
            )
            return "DISABLED", "Production gate active (override not set)", warnings
        else:
            # Dev but disabled - check why
            if not config.allowed_repos and "*" not in config.allowed_repos:
                warnings.append("⚠️  GitHub enabled but no repos in allowlist")
                return "DISABLED", "No repos allowed", warnings
            return "DISABLED", "Feature enabled but mode disabled", warnings

    if mode == GitHubMode.DRY_RUN:
        mode_str = f"DRY_RUN ({env} - logs only)"

        if env == "dev":
            warnings.append("ℹ️  GitHub DRY_RUN in dev (set DRY_RUN=false for real issues)")
        elif env == "staging":
            warnings.append(
                "ℹ️  GitHub DRY_RUN in staging (safe default - override with GITHUB_ENABLE_STAGING=true)"
            )

        return "DRY_RUN", mode_str, warnings

    if mode == GitHubMode.REAL:
        # Real mode - check token is available
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            warnings.append("❌  GitHub REAL mode but no GITHUB_TOKEN set")
            return "MISCONFIGURED", "REAL mode, no token", warnings

        mode_str = f"REAL ({env} - creates actual issues)"

        if env == "dev":
            warnings.append("⚠️  GitHub REAL mode in dev - issues will be created")
        elif env == "staging":
            warnings.append(
                "⚠️  GitHub REAL mode in STAGING - explicit override granted"
            )
        elif env == "prod":
            warnings.append(
                "🚨 GitHub REAL mode in PRODUCTION - extreme caution advised"
            )

        # Check allowlist
        if not config.allowed_repos:
            warnings.append("❌  No repos in allowlist - issues cannot be created")
            return "MISCONFIGURED", "REAL mode, no allowlist", warnings

        return "ENABLED", mode_str, warnings

    return "MISCONFIGURED", f"Unknown mode: {mode}", warnings


def check_org_storage_readiness() -> Tuple[str, str, List[str]]:
    """
    Check org-wide GCS storage readiness.

    Returns:
        Tuple of (status, mode_str, warnings)
        status: "ENABLED", "DISABLED"
        mode_str: Human-readable description
        warnings: List of warning messages
    """
    warnings = []
    env = get_current_environment()

    enabled_str = os.getenv("ORG_STORAGE_WRITE_ENABLED", "false").lower()
    enabled = enabled_str in ("true", "1", "yes")

    if not enabled:
        return "DISABLED", "Feature flag off", []

    bucket = os.getenv("ORG_STORAGE_BUCKET", "")
    if not bucket:
        warnings.append("⚠️  ORG_STORAGE_WRITE_ENABLED=true but no bucket configured")
        return "MISCONFIGURED", "Enabled, no bucket", warnings

    # Check bucket name matches environment
    expected_suffix = f"-{env}"
    if expected_suffix not in bucket:
        warnings.append(
            f"⚠️  Bucket name '{bucket}' doesn't contain '{expected_suffix}' - verify environment"
        )

    mode_str = f"ENABLED ({env} - {bucket})"
    return "ENABLED", mode_str, warnings


def format_status_symbol(status: str) -> str:
    """Get symbol for status."""
    symbols = {
        "ENABLED": "✅",
        "DRY_RUN": "🔵",
        "DISABLED": "⚫",
        "MISCONFIGURED": "❌",
    }
    return symbols.get(status, "❓")


def main():
    """Main entry point for LIVE3 readiness check."""
    print("=" * 80)
    print("LIVE3 CONFIGURATION READINESS CHECK")
    print("=" * 80)

    env = get_current_environment()
    print(f"\nEnvironment: {env.upper()}")
    print()

    # Check each LIVE3 subsystem
    results: Dict[str, Tuple[str, str, List[str]]] = {
        "Slack Notifications": check_slack_readiness(),
        "GitHub Issue Creation": check_github_readiness(),
        "Org-Wide GCS Storage": check_org_storage_readiness(),
    }

    # Print subsystem status
    print("LIVE3 Subsystem Status:")
    print("-" * 80)

    all_warnings = []
    for subsystem, (status, mode_str, warnings) in results.items():
        symbol = format_status_symbol(status)
        print(f"{symbol} {subsystem:25} {status:15} {mode_str}")
        all_warnings.extend(warnings)

    print("-" * 80)

    # Print warnings/info
    if all_warnings:
        print("\nMessages:")
        for warning in all_warnings:
            print(f"  {warning}")
        print()

    # Summary
    enabled_count = sum(
        1 for status, _, _ in results.values() if status in ("ENABLED", "DRY_RUN")
    )
    disabled_count = sum(1 for status, _, _ in results.values() if status == "DISABLED")
    misconfigured_count = sum(
        1 for status, _, _ in results.values() if status == "MISCONFIGURED"
    )

    print("Summary:")
    print(f"  Enabled/Active: {enabled_count}/3")
    print(f"  Disabled: {disabled_count}/3")
    print(f"  Misconfigured: {misconfigured_count}/3")

    # Environment-specific guidance
    print()
    if env == "dev":
        print("💡 Dev environment: All features can be enabled with basic config")
        print("   Next step: Test in staging with explicit overrides")
    elif env == "staging":
        print("💡 Staging environment: Features require explicit override flags")
        print("   Required: SLACK_ENABLE_STAGING=true, GITHUB_ENABLE_STAGING=true")
        print("   See: 115-RB-OPS-live3-slack-and-github-rollout-guide.md")
    elif env == "prod":
        print("💡 Production environment: Features LOCKED by default")
        print("   Required: SLACK_ENABLE_PROD=true, GITHUB_ENABLE_PROD=true")
        print("   ⚠️  Extreme caution required - follow rollout guide")
        print("   See: 115-RB-OPS-live3-slack-and-github-rollout-guide.md")

    print()
    print("=" * 80)

    # Non-blocking check - always exit 0 (success)
    # Even if features are misconfigured, this is informational only
    if misconfigured_count > 0:
        print("ℹ️  This is a NON-BLOCKING check - misconfigured features won't fail build")
        print("   Fix configuration issues before enabling features in production")

    print("\n✅ LIVE3 readiness check completed\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("\n❌ ERROR: LIVE3 readiness check failed with exception:", file=sys.stderr)
        print(f"   {type(e).__name__}: {e}", file=sys.stderr)
        print("\nThis indicates an infrastructure or import issue, not a config problem.")
        print("Check that all dependencies are installed and imports are correct.\n")
        sys.exit(1)
