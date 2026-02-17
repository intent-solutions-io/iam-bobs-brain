"""
Portfolio SWE Orchestrator for Multi-Repo Audits (Phase PORT2)

This module extends the single-repo SWE pipeline to operate across
an entire portfolio of repositories, producing aggregated quality reports.

Future: Can be parallelized for faster execution across many repos.
"""

# Import shared contracts
import sys
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.github_features import can_create_issues_for_repo, get_github_mode
from config.notifications import should_send_slack_notifications

# Import repo registry
from config.repos import get_repo_by_id, list_repos
from config.storage import get_org_storage_bucket, is_org_storage_write_enabled

# Import GitHub issue creation (LIVE3B/LIVE3C-GITHUB-ISSUES)
from iam_issue.github_issue_adapter import batch_create_github_issues

# Import notifications (LIVE3A)
from notifications import send_portfolio_notification

from shared_contracts import IssueSpec, PerRepoResult, PortfolioResult

# Import single-repo orchestrator (relative import to avoid module path issues)
from .orchestrator import run_swe_pipeline_for_repo

# Import org storage writer (LIVE1-GCS)
from .storage_writer import write_portfolio_result_to_gcs


def run_portfolio_swe(
    repo_ids: Optional[List[str]] = None,
    mode: str = "preview",
    task: str = "Portfolio quality audit",
    env: str = "dev",
    parallel: bool = False
) -> PortfolioResult:
    """
    Run SWE pipeline across multiple repositories and aggregate results.

    This is the main entry point for portfolio-level audits. It coordinates
    running individual repo audits and producing a comprehensive portfolio report.

    Args:
        repo_ids: List of repo IDs to audit. If None, audits all local repos.
        mode: Pipeline mode ("preview", "dry-run", "create")
        task: Task description for all repos
        env: Environment ("dev", "staging", "prod")
        parallel: If True, run repos in parallel (future enhancement)

    Returns:
        PortfolioResult with aggregated metrics and per-repo results
    """
    start_time = time.time()
    portfolio_run_id = str(uuid.uuid4())

    print("\n" + "=" * 70)
    print("PORTFOLIO SWE ORCHESTRATOR")
    print("=" * 70)
    print(f"Portfolio Run ID: {portfolio_run_id}")
    print(f"Mode: {mode}")
    print(f"Task: {task}")
    print(f"Environment: {env}")
    print("=" * 70 + "\n")

    # Step 1: Determine which repos to analyze
    if repo_ids:
        print(f"📋 Running on {len(repo_ids)} specified repos: {', '.join(repo_ids)}")
        repos_to_analyze = [get_repo_by_id(rid) for rid in repo_ids]
        # Filter out None values (repos not found)
        repos_to_analyze = [r for r in repos_to_analyze if r is not None]
    else:
        print("📋 Running on all local repos...")
        all_repos = list_repos()
        repos_to_analyze = [r for r in all_repos if r.is_local]
        print(f"   Found {len(repos_to_analyze)} local repos")

    if not repos_to_analyze:
        print("⚠️  No repos to analyze!")
        return PortfolioResult(
            portfolio_run_id=portfolio_run_id,
            repos=[],
            portfolio_duration_seconds=time.time() - start_time
        )

    print()

    # Step 2: Run pipeline for each repo
    per_repo_results: List[PerRepoResult] = []

    for i, repo in enumerate(repos_to_analyze, 1):
        print(f"\n{'=' * 70}")
        print(f"REPO {i}/{len(repos_to_analyze)}: {repo.id} ({repo.display_name})")
        print(f"{'=' * 70}")

        repo_start = time.time()

        try:
            # Run the single-repo pipeline
            pipeline_result = run_swe_pipeline_for_repo(
                repo_id=repo.id,
                mode=mode,
                task=task,
                env=env
            )

            # Determine status from pipeline result
            status = "completed"
            error_msg = None

            if pipeline_result.request.metadata.get("error"):
                status = "error"
                error_msg = f"Error: {pipeline_result.request.metadata['error']}"
            elif pipeline_result.request.metadata.get("status") == "skipped":
                status = "skipped"

            # Create per-repo result
            per_repo_result = PerRepoResult(
                repo_id=repo.id,
                display_name=repo.display_name,
                status=status,
                pipeline_result=pipeline_result,
                duration_seconds=time.time() - repo_start,
                error_message=error_msg
            )

            per_repo_results.append(per_repo_result)

            # Print summary for this repo
            if status == "completed":
                print(f"\n✅ {repo.id}: {pipeline_result.total_issues_found} issues, "
                      f"{pipeline_result.issues_fixed} fixed")
            elif status == "skipped":
                print(f"\n⏭️  {repo.id}: SKIPPED (no local path)")
            elif status == "error":
                print(f"\n❌ {repo.id}: ERROR - {error_msg}")

        except Exception as e:
            print(f"\n❌ {repo.id}: EXCEPTION - {e}")
            import traceback
            traceback.print_exc()

            # Create error result
            per_repo_result = PerRepoResult(
                repo_id=repo.id,
                display_name=repo.display_name,
                status="error",
                pipeline_result=None,
                duration_seconds=time.time() - repo_start,
                error_message=str(e)
            )
            per_repo_results.append(per_repo_result)

    # Step 3: Aggregate results
    print(f"\n{'=' * 70}")
    print("AGGREGATING PORTFOLIO RESULTS")
    print(f"{'=' * 70}\n")

    portfolio_result = _aggregate_results(
        portfolio_run_id=portfolio_run_id,
        per_repo_results=per_repo_results,
        total_duration=time.time() - start_time
    )

    # Step 4: Print portfolio summary
    _print_portfolio_summary(portfolio_result)

    # Step 5: Create GitHub issues from findings (LIVE3B/LIVE3C-GITHUB-ISSUES)
    github_owner = "jeremylongshore"  # TODO: Make configurable
    issue_specs = _convert_findings_to_issue_specs(portfolio_result, github_owner)

    if issue_specs:
        portfolio_result.issues_planned = len(issue_specs)

        print(f"\n{'=' * 70}")
        print("CREATING GITHUB ISSUES FROM FINDINGS")
        print(f"{'=' * 70}")
        print(f"Issues planned: {portfolio_result.issues_planned}")

        # Group by repo for batch creation
        issues_by_repo: Dict[Tuple[str, str], List[IssueSpec]] = {}
        for repo_id, github_repo, issue_spec in issue_specs:
            key = (repo_id, github_repo)
            if key not in issues_by_repo:
                issues_by_repo[key] = []
            issues_by_repo[key].append(issue_spec)

        # Create issues for each repo
        for (repo_id, github_repo), issues in issues_by_repo.items():
            mode = get_github_mode(repo_id)
            print(f"\n  Repo: {github_owner}/{github_repo} (mode: {mode.value})")

            results = batch_create_github_issues(
                issues=issues,
                repo_id=repo_id,
                github_owner=github_owner,
                github_repo=github_repo
            )

            # Count successes
            for result in results:
                if result.success and result.mode == "real":
                    portfolio_result.issues_created += 1
                    print(f"    ✅ Created issue #{result.issue_number}: {result.issue_url}")
                elif result.success and result.mode == "dry_run":
                    print("    📝 DRY-RUN: Would create issue")
                elif result.mode == "disabled":
                    print("    ⏭️  DISABLED: Skipped issue creation")
                else:
                    print(f"    ❌ FAILED: {result.error}")

        print(f"\nSummary: {portfolio_result.issues_created} issues created "
              f"(out of {portfolio_result.issues_planned} planned)")
        print(f"{'=' * 70}\n")
    else:
        print("\n📋 No GitHub issues planned (all repos disabled or no findings)\n")

    # Step 6: Write to org-wide knowledge hub (LIVE1-GCS)
    if is_org_storage_write_enabled() and get_org_storage_bucket():
        print(f"\n{'=' * 70}")
        print("WRITING TO ORG KNOWLEDGE HUB")
        print(f"{'=' * 70}")
        print(f"Bucket: {get_org_storage_bucket()}")
        print(f"Run ID: {portfolio_run_id}")
        write_portfolio_result_to_gcs(portfolio_result, env=env)
        print(f"{'=' * 70}\n")
    else:
        if not is_org_storage_write_enabled():
            print("\n📊 Org storage write disabled (set ORG_STORAGE_WRITE_ENABLED=true to enable)")
        elif not get_org_storage_bucket():
            print("\n⚠️  Org storage write enabled but ORG_STORAGE_BUCKET not set")

    # Step 7: Send Slack notifications (LIVE3A)
    if should_send_slack_notifications():
        print(f"\n{'=' * 70}")
        print("SENDING SLACK NOTIFICATION")
        print(f"{'=' * 70}")
        success = send_portfolio_notification(portfolio_result, env=env)
        if success:
            print("✅ Slack notification sent successfully")
        else:
            print("⚠️  Slack notification failed (see logs)")
        print(f"{'=' * 70}\n")
    else:
        print("\n💬 Slack notifications disabled (set SLACK_NOTIFICATIONS_ENABLED=true to enable)")

    return portfolio_result


def _aggregate_results(
    portfolio_run_id: str,
    per_repo_results: List[PerRepoResult],
    total_duration: float
) -> PortfolioResult:
    """
    Aggregate per-repo results into a portfolio-level summary.

    Calculates totals, breakdowns, and rankings.
    """
    # Count repos by status
    status_counts = Counter(r.status for r in per_repo_results)

    # Aggregate issue counts
    total_issues = sum(r.issues_found for r in per_repo_results if r.status == "completed")
    total_fixes = sum(r.issues_fixed for r in per_repo_results if r.status == "completed")

    # Aggregate issues by severity
    severity_counts: Dict[str, int] = {}
    for repo_result in per_repo_results:
        if repo_result.status == "completed" and repo_result.pipeline_result:
            for issue in repo_result.pipeline_result.issues:
                severity = issue.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Aggregate issues by type
    type_counts: Dict[str, int] = {}
    for repo_result in per_repo_results:
        if repo_result.status == "completed" and repo_result.pipeline_result:
            for issue in repo_result.pipeline_result.issues:
                issue_type = issue.type.value
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

    # Rank repos by issue count (descending)
    repos_with_issues = [
        (r.repo_id, r.issues_found)
        for r in per_repo_results
        if r.status == "completed"
    ]
    repos_by_issue_count = sorted(repos_with_issues, key=lambda x: x[1], reverse=True)

    # Rank repos by compliance score (ascending - lower is worse)
    repos_with_compliance = []
    for r in per_repo_results:
        if r.status == "completed" and r.pipeline_result:
            # Get compliance score from analysis metadata if available
            # For now, use a simple heuristic: 1 - (issues / 100)
            # In real implementation, would come from AnalysisReport
            estimated_compliance = max(0.0, 1.0 - (r.issues_found / 100.0))
            repos_with_compliance.append((r.repo_id, estimated_compliance))

    repos_by_compliance_score = sorted(repos_with_compliance, key=lambda x: x[1])

    return PortfolioResult(
        portfolio_run_id=portfolio_run_id,
        repos=per_repo_results,
        total_repos_analyzed=status_counts.get("completed", 0),
        total_repos_skipped=status_counts.get("skipped", 0),
        total_repos_errored=status_counts.get("error", 0),
        total_issues_found=total_issues,
        total_issues_fixed=total_fixes,
        issues_by_severity=severity_counts,
        issues_by_type=type_counts,
        repos_by_issue_count=repos_by_issue_count,
        repos_by_compliance_score=repos_by_compliance_score,
        portfolio_duration_seconds=total_duration,
        timestamp=datetime.now()
    )


def _print_portfolio_summary(result: PortfolioResult):
    """Print a formatted summary of the portfolio audit results."""
    print("\n" + "=" * 70)
    print("PORTFOLIO SUMMARY")
    print("=" * 70)

    # Overall stats
    print(f"Portfolio Run ID: {result.portfolio_run_id}")
    print(f"Duration: {result.portfolio_duration_seconds:.2f} seconds")
    print()

    # Repo counts
    print("📊 Repository Status:")
    print(f"  ✅ Analyzed: {result.total_repos_analyzed}")
    print(f"  ⏭️  Skipped: {result.total_repos_skipped}")
    print(f"  ❌ Errored: {result.total_repos_errored}")
    print(f"  📦 Total: {len(result.repos)}")
    print()

    # Issue stats
    print("🔍 Issues Found:")
    print(f"  Total Issues: {result.total_issues_found}")
    print(f"  Issues Fixed: {result.total_issues_fixed}")
    print(f"  Fix Rate: {result.total_issues_fixed / result.total_issues_found * 100:.1f}%"
          if result.total_issues_found > 0 else "  Fix Rate: N/A")
    print()

    # Issues by severity
    if result.issues_by_severity:
        print("📈 Issues by Severity:")
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = result.issues_by_severity.get(severity, 0)
            if count > 0:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "⚪"}.get(severity, "•")
                print(f"  {icon} {severity.title()}: {count}")
        print()

    # Issues by type
    if result.issues_by_type:
        print("🏷️  Issues by Type:")
        for issue_type, count in sorted(result.issues_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {issue_type}: {count}")
        print()

    # Top repos by issue count
    if result.repos_by_issue_count:
        print("🔝 Repos by Issue Count (Top 5):")
        for repo_id, issue_count in result.repos_by_issue_count[:5]:
            icon = "🔴" if issue_count > 10 else "🟡" if issue_count > 5 else "🟢"
            print(f"  {icon} {repo_id}: {issue_count} issues")
        print()

    # Bottom repos by compliance
    if result.repos_by_compliance_score:
        print("⚠️  Repos Needing Attention (by compliance):")
        for repo_id, compliance_score in result.repos_by_compliance_score[:5]:
            icon = "🔴" if compliance_score < 0.7 else "🟡" if compliance_score < 0.9 else "🟢"
            print(f"  {icon} {repo_id}: {compliance_score:.2f} compliance")
        print()

    print("=" * 70 + "\n")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_portfolio_local_repos() -> List[str]:
    """
    Get list of repo IDs that are locally available.

    Convenience function for filtering to only local repos.

    Returns:
        List of repo IDs with local_path != "external"
    """
    return [r.id for r in list_repos() if r.is_local]


def get_portfolio_repos_by_tag(tag: str) -> List[str]:
    """
    Get list of repo IDs filtered by tag.

    Args:
        tag: Tag to filter by (e.g., "production", "adk", "product")

    Returns:
        List of repo IDs with the specified tag
    """
    return [r.id for r in list_repos(tag=tag)]


def _convert_findings_to_issue_specs(
    portfolio_result: PortfolioResult,
    github_owner: str,
    max_issues_per_repo: int = 10
) -> List[Tuple[str, str, IssueSpec]]:
    """
    Convert portfolio findings to GitHub IssueSpecs.

    Args:
        portfolio_result: Portfolio result with findings
        github_owner: GitHub owner/org name
        max_issues_per_repo: Maximum issues to create per repo (default 10)

    Returns:
        List of tuples: (repo_id, github_repo_name, IssueSpec)
    """
    issue_specs = []

    for repo_result in portfolio_result.repos:
        if repo_result.status != "completed" or not repo_result.pipeline_result:
            continue

        repo_config = get_repo_by_id(repo_result.repo_id)
        if not repo_config:
            continue

        # Check if we can create issues for this repo
        if not can_create_issues_for_repo(repo_result.repo_id):
            continue

        # Get issues from pipeline result (limit per repo)
        issues = repo_result.pipeline_result.issues[:max_issues_per_repo]

        for issue in issues:
            # Convert to IssueSpec format (issue is already an IssueSpec from pipeline)
            issue_specs.append((
                repo_result.repo_id,
                repo_config.display_name,  # Use as GitHub repo name
                issue
            ))

    return issue_specs


if __name__ == "__main__":
    # Demo: Run portfolio audit on all local repos
    print("Running portfolio demo...")
    result = run_portfolio_swe(mode="preview")
    print(f"\nDemo complete! Analyzed {result.total_repos_analyzed} repos, "
          f"found {result.total_issues_found} issues.")
