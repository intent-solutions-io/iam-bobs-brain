#!/usr/bin/env python3
"""
Demo script to run the SWE pipeline once.

This script provides a CLI interface to trigger the IAM SWE pipeline
for testing and demonstration purposes.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.iam_senior_adk_devops_lead.orchestrator import run_swe_pipeline
from agents.shared_contracts import PipelineRequest, PipelineResult, QAStatus, Severity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def format_issue_summary(result: PipelineResult) -> str:
    """Format issues for display."""
    if not result.issues:
        return "No issues found."

    lines = [f"\n📋 Issues Found ({len(result.issues)}):"]
    for i, issue in enumerate(result.issues, 1):
        severity_icon = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🟢",
            Severity.INFO: "ℹ️"
        }.get(issue.severity, "❓")

        lines.append(f"  {i}. {severity_icon} [{issue.severity.value}] {issue.title}")
        lines.append(f"     Type: {issue.type.value}")
        if issue.file_path:
            lines.append(f"     File: {issue.file_path}")
        lines.append(f"     Description: {issue.description[:100]}...")

    return "\n".join(lines)


def format_fix_summary(result: PipelineResult) -> str:
    """Format fixes for display."""
    if not result.plans:
        return "No fixes planned."

    lines = [f"\n🔧 Fixes Applied ({len(result.plans)}):"]
    for i, plan in enumerate(result.plans, 1):
        risk_icon = {
            "low": "✅",
            "medium": "⚠️",
            "high": "⚡"
        }.get(plan.overall_risk, "❓")

        lines.append(f"  {i}. {risk_icon} {plan.approach}")
        lines.append(f"     Risk: {plan.overall_risk}")
        lines.append(f"     Steps: {len(plan.steps)}")

        # Show implementation status
        impl = next((c for c in result.implementations if c.plan_id == plan.plan_id), None)
        if impl:
            lines.append(f"     Implementation: ✅ {impl.change_type} {impl.file_path}")

        # Show QA status
        qa = next((q for q in result.qa_report if q.change_id == plan.plan_id), None)
        if qa:
            status_icon = {
                QAStatus.PASSED: "✅",
                QAStatus.FAILED: "❌",
                QAStatus.PARTIAL: "⚠️",
                QAStatus.SKIPPED: "⏭️"
            }.get(qa.status, "❓")
            lines.append(f"     QA: {status_icon} {qa.status.value}")
            if qa.safe_to_apply:
                lines.append("     Safe to Apply: ✅")
            else:
                lines.append("     Safe to Apply: ❌")

    return "\n".join(lines)


def format_metrics_summary(result: PipelineResult) -> str:
    """Format metrics for display."""
    lines = [
        "\n📊 Pipeline Metrics:",
        f"  Total Issues Found: {result.total_issues_found}",
        f"  Issues Fixed: {result.issues_fixed}",
        f"  Issues Documented: {result.issues_documented}",
        f"  Pipeline Duration: {result.pipeline_duration_seconds:.2f} seconds",
        f"  Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    ]

    if result.cleanup:
        lines.append(f"  Cleanup Tasks: {len(result.cleanup)}")

    if result.index_updates:
        lines.append(f"  Index Updates: {len(result.index_updates)}")

    return "\n".join(lines)


def save_result_to_file(result: PipelineResult, output_path: Path) -> None:
    """Save pipeline result to JSON file."""
    # Convert to dict (simple serialization)
    result_dict = {
        "timestamp": result.timestamp.isoformat(),
        "total_issues_found": result.total_issues_found,
        "issues_fixed": result.issues_fixed,
        "issues_documented": result.issues_documented,
        "pipeline_duration_seconds": result.pipeline_duration_seconds,
        "issues_count": len(result.issues),
        "plans_count": len(result.plans),
        "implementations_count": len(result.implementations),
        "qa_passed": sum(1 for qa in result.qa_report if qa.status == QAStatus.PASSED),
        "qa_failed": sum(1 for qa in result.qa_report if qa.status == QAStatus.FAILED),
    }

    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2)

    logger.info(f"Result saved to {output_path}")


def main():
    """Main entry point for the pipeline demo."""
    parser = argparse.ArgumentParser(
        description="Run the IAM SWE Pipeline on a repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on synthetic test repo
  %(prog)s --repo-path tests/data/synthetic_repo

  # Run with custom task
  %(prog)s --repo-path . --task "Find and fix security issues"

  # Run in staging environment with more fixes
  %(prog)s --repo-path . --env staging --max-issues 5

  # Include cleanup and save results
  %(prog)s --repo-path . --cleanup --output pipeline_result.json
        """
    )

    parser.add_argument(
        "--repo-path",
        type=str,
        default="tests/data/synthetic_repo",
        help="Path to the repository to analyze (default: tests/data/synthetic_repo)"
    )

    parser.add_argument(
        "--task",
        type=str,
        default="Audit ADK compliance and fix violations",
        help="Task description for the pipeline"
    )

    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment to run in (default: dev)"
    )

    parser.add_argument(
        "--max-issues",
        type=int,
        default=2,
        help="Maximum number of issues to fix (default: 2)"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Include cleanup phase to identify tech debt"
    )

    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip knowledge indexing phase"
    )

    parser.add_argument(
        "--mode",
        choices=["preview", "dry-run", "create"],
        default="preview",
        help="GitHub issue creation mode: preview (default, no creation), dry-run (show payloads), create (actually create issues)"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Save result to JSON file"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print request without running pipeline"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve repository path
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        sys.exit(1)

    # Create pipeline request
    request = PipelineRequest(
        repo_hint=str(repo_path),
        task_description=args.task,
        env=args.env,
        max_issues_to_fix=args.max_issues,
        include_cleanup=args.cleanup,
        include_indexing=not args.no_index,
        mode=args.mode,  # Phase GHC: GitHub issue creation mode
        metadata={
            "triggered_by": "CLI",
            "script": "run_swe_pipeline_once.py"
        }
    )

    # Print request
    print("\n" + "="*60)
    print("🚀 IAM SWE Pipeline Demo")
    print("="*60)
    print(f"\n📁 Repository: {repo_path}")
    print(f"📝 Task: {request.task_description}")
    print(f"🌍 Environment: {request.env}")
    print(f"🔧 Max Issues to Fix: {request.max_issues_to_fix}")
    print(f"🧹 Include Cleanup: {request.include_cleanup}")
    print(f"📚 Include Indexing: {request.include_indexing}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - Not executing pipeline")
        print("\nRequest object:")
        print(json.dumps({
            "repo_hint": request.repo_hint,
            "task_description": request.task_description,
            "env": request.env,
            "max_issues_to_fix": request.max_issues_to_fix,
            "include_cleanup": request.include_cleanup,
            "include_indexing": request.include_indexing,
            "metadata": request.metadata
        }, indent=2))
        return

    print("\n⏳ Running pipeline...")
    print("-" * 60)

    try:
        # Run the pipeline
        result = run_swe_pipeline(request)

        # Print results
        print("\n" + "="*60)
        print("✅ Pipeline Completed Successfully!")
        print("="*60)

        # Show issue summary
        print(format_issue_summary(result))

        # Show fix summary
        print(format_fix_summary(result))

        # Show metrics
        print(format_metrics_summary(result))

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            save_result_to_file(result, output_path)

        # Exit code based on issues found
        if result.total_issues_found > 0 and result.issues_fixed < result.total_issues_found:
            print(f"\n⚠️  {result.total_issues_found - result.issues_fixed} issues remain unfixed")
            sys.exit(1)
        else:
            print("\n✅ All detected issues have been addressed")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline Failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
