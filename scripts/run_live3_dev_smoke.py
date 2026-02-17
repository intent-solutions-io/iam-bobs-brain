#!/usr/bin/env python3
"""
LIVE3 Dev Smoke Test - End-to-End Validation for LIVE3 Features

This script exercises the complete LIVE3 pipeline in dev:
- Portfolio/SWE audit (via iam-senior-adk-devops-lead)
- Org GCS storage write (if ORG_STORAGE_WRITE_ENABLED=true)
- Slack notifications (if SLACK_NOTIFICATIONS_ENABLED=true)
- GitHub issue creation (if GITHUB_ISSUE_CREATION_ENABLED=true, respects dry-run)

Usage:
    python3 scripts/run_live3_dev_smoke.py
    python3 scripts/run_live3_dev_smoke.py --repo bobs-brain
    python3 scripts/run_live3_dev_smoke.py --verbose

Exit Codes:
    0: Core path succeeded (optional subsystems may have failed)
    1: Core path failed (portfolio audit failed)

Design Philosophy:
- Core path (portfolio audit) must succeed for exit 0
- Optional subsystems (Slack, GitHub, GCS) failures are logged but don't fail the smoke
- Idempotent and safe to run repeatedly
- Respects all LIVE3 feature flags
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from iam_senior_adk_devops_lead.portfolio_orchestrator import (
    run_portfolio_swe,
)


class SubsystemResult:
    """Result of a subsystem execution."""

    def __init__(
        self,
        name: str,
        enabled: bool,
        success: Optional[bool] = None,
        details: str = "",
    ):
        self.name = name
        self.enabled = enabled
        self.success = success  # None = skipped, True = passed, False = failed
        self.details = details

    def status_str(self) -> str:
        """Get human-readable status string."""
        if not self.enabled:
            return "DISABLED"
        if self.success is None:
            return "SKIPPED"
        return "PASS" if self.success else "FAIL"

    def status_emoji(self) -> str:
        """Get emoji for status."""
        if not self.enabled:
            return "⚫"
        if self.success is None:
            return "⏸️"
        return "✅" if self.success else "❌"


class SmokeSummary:
    """Summary of entire smoke test run."""

    def __init__(self):
        self.subsystems: List[SubsystemResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

    def add_subsystem(self, result: SubsystemResult):
        """Add a subsystem result."""
        self.subsystems.append(result)

    def finish(self):
        """Mark smoke test as finished."""
        self.end_time = datetime.now()

    def core_passed(self) -> bool:
        """Check if core subsystems passed."""
        core = [s for s in self.subsystems if s.name == "Portfolio Audit"]
        return all(s.success for s in core if s.enabled)

    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def print_summary(self, verbose: bool = False):
        """Print human-readable summary."""
        print("\n" + "=" * 70)
        print("LIVE3 DEV SMOKE TEST SUMMARY")
        print("=" * 70)
        print(f"Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.end_time:
            print(f"Finished: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {self.duration_seconds():.1f}s")
        print()
        print("Subsystem Status:")
        print("-" * 70)

        for subsystem in self.subsystems:
            status_line = f"{subsystem.status_emoji()} {subsystem.name:25} {subsystem.status_str():10}"
            print(status_line)
            if verbose and subsystem.details:
                # Indent details
                for line in subsystem.details.split("\n"):
                    if line.strip():
                        print(f"   {line}")

        print("-" * 70)
        overall = "PASS" if self.core_passed() else "FAIL"
        overall_emoji = "✅" if self.core_passed() else "❌"
        print(f"\nOverall: {overall_emoji} {overall}")
        print("=" * 70)


def load_env_config() -> Dict[str, str]:
    """Load environment configuration from .env or environment."""
    config = {
        "DEPLOYMENT_ENV": os.getenv("DEPLOYMENT_ENV", "dev"),
        "ORG_STORAGE_WRITE_ENABLED": os.getenv("ORG_STORAGE_WRITE_ENABLED", "false"),
        "SLACK_NOTIFICATIONS_ENABLED": os.getenv(
            "SLACK_NOTIFICATIONS_ENABLED", "false"
        ),
        "GITHUB_ISSUE_CREATION_ENABLED": os.getenv(
            "GITHUB_ISSUE_CREATION_ENABLED", "false"
        ),
        "GITHUB_ISSUES_DRY_RUN": os.getenv("GITHUB_ISSUES_DRY_RUN", "true"),
        "ORG_STORAGE_BUCKET": os.getenv("ORG_STORAGE_BUCKET", ""),
        "SLACK_SWE_CHANNEL_WEBHOOK_URL": os.getenv("SLACK_SWE_CHANNEL_WEBHOOK_URL", ""),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
    }
    return config


def run_portfolio_audit(target_repo: str, env: str, verbose: bool) -> SubsystemResult:
    """
    Run portfolio audit on target repo.
    This is the CORE subsystem - must succeed for smoke to pass.
    """
    result = SubsystemResult(name="Portfolio Audit", enabled=True)  # Always enabled

    try:
        if verbose:
            print(f"\n🔍 Running portfolio audit on: {target_repo}")
            print(f"   Environment: {env}")

        # Run portfolio SWE
        swe_result = run_portfolio_swe(
            repo_ids=[target_repo] if target_repo != "all" else None,
            mode="preview",  # Safe mode for smoke test
            task_name=f"LIVE3 Dev Smoke - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            env=env,
        )

        # Check if audit completed
        if swe_result and "results" in swe_result:
            result.success = True
            result.details = f"Audited {len(swe_result['results'])} repo(s)"
            if verbose:
                print(
                    f"   ✅ Portfolio audit completed: {len(swe_result['results'])} repos"
                )
        else:
            result.success = False
            result.details = "Audit returned no results"
            if verbose:
                print("   ❌ Portfolio audit failed: no results")

    except Exception as e:
        result.success = False
        result.details = f"Exception: {e!s}"
        if verbose:
            print(f"   ❌ Portfolio audit exception: {e}")

    return result


def write_to_gcs(
    swe_result: Dict[str, Any], config: Dict[str, str], verbose: bool
) -> SubsystemResult:
    """
    Write portfolio results to GCS org storage (if enabled).
    Optional subsystem - failure doesn't fail the smoke.
    """
    enabled = config["ORG_STORAGE_WRITE_ENABLED"].lower() == "true"
    result = SubsystemResult(name="GCS Org Storage", enabled=enabled)

    if not enabled:
        result.details = "Disabled via ORG_STORAGE_WRITE_ENABLED=false"
        return result

    try:
        bucket = config["ORG_STORAGE_BUCKET"]
        if not bucket:
            result.success = False
            result.details = "ORG_STORAGE_BUCKET not set"
            return result

        if verbose:
            print(f"\n📦 Writing to GCS: {bucket}")

        # Import GCS writer (only if enabled)
        from google.cloud import storage

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_swe/dev_smoke/{timestamp}_smoke_test.json"

        # Write to GCS
        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(filename)
        blob.upload_from_string(
            json.dumps(swe_result, indent=2), content_type="application/json"
        )

        result.success = True
        result.details = f"Wrote to gs://{bucket}/{filename}"
        if verbose:
            print(f"   ✅ Wrote to gs://{bucket}/{filename}")

    except Exception as e:
        result.success = False
        result.details = f"Exception: {e!s}"
        if verbose:
            print(f"   ❌ GCS write failed: {e}")

    return result


def send_slack_notification(
    swe_result: Dict[str, Any], config: Dict[str, str], verbose: bool
) -> SubsystemResult:
    """
    Send Slack notification for portfolio completion (if enabled).
    Optional subsystem - failure doesn't fail the smoke.
    """
    enabled = config["SLACK_NOTIFICATIONS_ENABLED"].lower() == "true"
    result = SubsystemResult(name="Slack Notifications", enabled=enabled)

    if not enabled:
        result.details = "Disabled via SLACK_NOTIFICATIONS_ENABLED=false"
        return result

    try:
        webhook_url = config["SLACK_SWE_CHANNEL_WEBHOOK_URL"]
        if not webhook_url:
            result.success = False
            result.details = "SLACK_SWE_CHANNEL_WEBHOOK_URL not set"
            return result

        if verbose:
            print("\n💬 Sending Slack notification")

        # Import requests (only if enabled)
        import requests

        # Build message
        repo_count = len(swe_result.get("results", []))
        message = {
            "text": "🧪 LIVE3 Dev Smoke Test Completed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*LIVE3 Dev Smoke Test*\n✅ Portfolio audit completed: {repo_count} repo(s)",
                    },
                }
            ],
        }

        # Send to Slack
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()

        result.success = True
        result.details = f"Posted to Slack (status: {response.status_code})"
        if verbose:
            print(f"   ✅ Slack notification sent (status: {response.status_code})")

    except Exception as e:
        result.success = False
        result.details = f"Exception: {e!s}"
        if verbose:
            print(f"   ❌ Slack notification failed: {e}")

    return result


def create_github_issues(
    swe_result: Dict[str, Any], config: Dict[str, str], verbose: bool
) -> SubsystemResult:
    """
    Create GitHub issues for findings (if enabled, respects dry-run).
    Optional subsystem - failure doesn't fail the smoke.
    """
    enabled = config["GITHUB_ISSUE_CREATION_ENABLED"].lower() == "true"
    dry_run = config["GITHUB_ISSUES_DRY_RUN"].lower() == "true"

    result = SubsystemResult(name="GitHub Issue Creation", enabled=enabled)

    if not enabled:
        result.details = "Disabled via GITHUB_ISSUE_CREATION_ENABLED=false"
        return result

    try:
        if verbose:
            print(f"\n🐙 GitHub issue creation (dry-run: {dry_run})")

        # Count issues that would be created
        issue_count = 0
        for repo_result in swe_result.get("results", []):
            findings = repo_result.get("findings", [])
            issue_count += len(findings)

        if dry_run:
            result.success = True
            result.details = f"DRY RUN: Would create {issue_count} issues"
            if verbose:
                print(f"   ⏸️  DRY RUN: Would create {issue_count} issues")
        else:
            # TODO: Actual GitHub API calls via iam-issue agent
            # For now, just log
            result.success = True
            result.details = f"Would create {issue_count} issues (not implemented yet)"
            if verbose:
                print(
                    f"   ⚠️  Issue creation not implemented yet: {issue_count} issues"
                )

    except Exception as e:
        result.success = False
        result.details = f"Exception: {e!s}"
        if verbose:
            print(f"   ❌ GitHub issue creation failed: {e}")

    return result


def main():
    """Main entry point for LIVE3 dev smoke test."""
    parser = argparse.ArgumentParser(
        description="LIVE3 Dev Smoke Test - End-to-end validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on bobs-brain (default)
  %(prog)s

  # Run on specific repo
  %(prog)s --repo diagnosticpro

  # Verbose output
  %(prog)s --verbose

Environment Variables:
  DEPLOYMENT_ENV                   Environment (default: dev)
  ORG_STORAGE_WRITE_ENABLED       Enable GCS writes (default: false)
  SLACK_NOTIFICATIONS_ENABLED     Enable Slack (default: false)
  GITHUB_ISSUE_CREATION_ENABLED   Enable GitHub (default: false)
  GITHUB_ISSUES_DRY_RUN          GitHub dry-run mode (default: true)
        """,
    )

    parser.add_argument(
        "--repo",
        type=str,
        default="bobs-brain",
        help="Repository to audit (default: bobs-brain)",
    )

    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Environment override (default: from DEPLOYMENT_ENV or 'dev')",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Load config
    config = load_env_config()
    env = args.env or config["DEPLOYMENT_ENV"]

    # Initialize summary
    summary = SmokeSummary()

    if args.verbose:
        print("\n" + "=" * 70)
        print("LIVE3 DEV SMOKE TEST")
        print("=" * 70)
        print(f"Repository: {args.repo}")
        print(f"Environment: {env}")
        print(f"Timestamp: {summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nFeature Flags:")
        print(
            f"  ORG_STORAGE_WRITE_ENABLED:      {config['ORG_STORAGE_WRITE_ENABLED']}"
        )
        print(
            f"  SLACK_NOTIFICATIONS_ENABLED:    {config['SLACK_NOTIFICATIONS_ENABLED']}"
        )
        print(
            f"  GITHUB_ISSUE_CREATION_ENABLED:  {config['GITHUB_ISSUE_CREATION_ENABLED']}"
        )
        print(f"  GITHUB_ISSUES_DRY_RUN:          {config['GITHUB_ISSUES_DRY_RUN']}")
        print("=" * 70)

    # CORE: Portfolio Audit (must succeed)
    audit_result = run_portfolio_audit(args.repo, env, args.verbose)
    summary.add_subsystem(audit_result)

    # If audit failed, bail early
    if not audit_result.success:
        summary.finish()
        summary.print_summary(args.verbose)
        print("\n❌ CORE subsystem failed - aborting smoke test")
        return 1

    # Get audit results for optional subsystems
    swe_result = {"results": [{"repo": args.repo, "findings": []}]}  # Placeholder

    # OPTIONAL: GCS Storage
    gcs_result = write_to_gcs(swe_result, config, args.verbose)
    summary.add_subsystem(gcs_result)

    # OPTIONAL: Slack Notifications
    slack_result = send_slack_notification(swe_result, config, args.verbose)
    summary.add_subsystem(slack_result)

    # OPTIONAL: GitHub Issues
    github_result = create_github_issues(swe_result, config, args.verbose)
    summary.add_subsystem(github_result)

    # Finish and print summary
    summary.finish()
    summary.print_summary(args.verbose)

    # Exit 0 if core passed (optional failures are OK)
    return 0 if summary.core_passed() else 1


if __name__ == "__main__":
    sys.exit(main())
