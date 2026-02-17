"""
Portfolio Storage Writer (LIVE1-GCS)

Writes portfolio SWE audit results to org-wide GCS knowledge hub.
All writes are opt-in via feature flags (default: disabled).

Behavior:
    - If ORG_STORAGE_WRITE_ENABLED is false or bucket not set: skip silently
    - If enabled: write JSON to GCS using Application Default Credentials
    - Failures are logged but do NOT crash the portfolio pipeline

Layout:
    gs://{bucket}/portfolio/runs/{run_id}/summary.json
    gs://{bucket}/portfolio/runs/{run_id}/per-repo/{repo_id}.json

BigQuery:
    - Deferred to future LIVE-BQ phase
    - This module does NOT include BigQuery writers
"""

import json
import logging
from datetime import datetime

# Import GCS client
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# Import config helpers
# Import contracts
from agents.shared_contracts import PortfolioResult

from ..config.storage import (
    get_org_storage_bucket,
    is_org_storage_write_enabled,
    make_portfolio_run_repo_path,
    make_portfolio_run_summary_path,
)

logger = logging.getLogger(__name__)


def write_portfolio_result_to_gcs(
    result: PortfolioResult,
    *,
    env: str
) -> None:
    """
    Write portfolio result to org-wide GCS bucket if enabled.

    This function is called after portfolio orchestrator completes.
    It writes:
        1. Summary JSON at portfolio/runs/{run_id}/summary.json
        2. Per-repo JSON at portfolio/runs/{run_id}/per-repo/{repo_id}.json

    Args:
        result: PortfolioResult with aggregated metrics
        env: Environment name (dev/staging/prod)

    Behavior:
        - If disabled or misconfigured: logs and returns (no error)
        - If enabled: attempts GCS write with error handling
        - Failures are logged but do NOT raise exceptions

    Environment Variables:
        ORG_STORAGE_BUCKET: Bucket name
        ORG_STORAGE_WRITE_ENABLED: Must be "true" to write

    Example:
        result = run_portfolio_swe(...)
        write_portfolio_result_to_gcs(result, env="dev")
    """
    # Check if GCS client library is available
    if not GCS_AVAILABLE:
        logger.warning(
            "google-cloud-storage not installed; skipping org storage write"
        )
        return

    # Check if org storage writes are enabled
    if not is_org_storage_write_enabled():
        logger.info(
            "Org storage write disabled (ORG_STORAGE_WRITE_ENABLED not true); "
            "skipping GCS write"
        )
        return

    # Get bucket name
    bucket_name = get_org_storage_bucket()
    if not bucket_name:
        logger.warning(
            "Org storage write enabled but ORG_STORAGE_BUCKET not set; "
            "skipping GCS write"
        )
        return

    # Prepare payload
    try:
        summary_data = _build_portfolio_summary_json(result, env)
    except Exception as e:
        logger.error(
            f"Failed to serialize portfolio result: {e}",
            exc_info=True
        )
        return

    # Write to GCS
    try:
        _upload_to_gcs(
            bucket_name=bucket_name,
            result=result,
            summary_data=summary_data
        )
        logger.info(
            f"✅ Portfolio result written to org storage: "
            f"gs://{bucket_name}/portfolio/runs/{result.portfolio_run_id}/"
        )
    except Exception as e:
        logger.error(
            f"Failed to write portfolio result to GCS bucket {bucket_name}: {e}",
            exc_info=True
        )
        # Do NOT raise; allow portfolio pipeline to complete


def _build_portfolio_summary_json(result: PortfolioResult, env: str) -> dict:
    """
    Build portfolio summary JSON structure.

    Args:
        result: PortfolioResult
        env: Environment name

    Returns:
        Dictionary with portfolio summary data
    """
    return {
        "portfolio_run_id": result.portfolio_run_id,
        "timestamp": result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else str(result.timestamp),
        "environment": env,
        "duration_seconds": result.portfolio_duration_seconds,
        "summary": {
            "total_repos_analyzed": result.total_repos_analyzed,
            "total_repos_skipped": result.total_repos_skipped,
            "total_repos_errored": result.total_repos_errored,
            "total_issues_found": result.total_issues_found,
            "total_issues_fixed": result.total_issues_fixed,
            "fix_rate": (
                (result.total_issues_fixed / result.total_issues_found * 100)
                if result.total_issues_found > 0
                else 0.0
            ),
        },
        "issues_by_severity": result.issues_by_severity,
        "issues_by_type": result.issues_by_type,
        "repos_by_issue_count": [
            {"repo_id": repo_id, "issues": count}
            for repo_id, count in result.repos_by_issue_count
        ],
        "repos_by_compliance_score": [
            {"repo_id": repo_id, "compliance_score": score}
            for repo_id, score in result.repos_by_compliance_score
        ],
        "repos": [
            {
                "repo_id": r.repo_id,
                "display_name": r.display_name,
                "status": r.status,
                "duration_seconds": r.duration_seconds,
                "issues_found": r.issues_found,
                "issues_fixed": r.issues_fixed,
                "error_message": r.error_message,
            }
            for r in result.repos
        ],
    }


def _upload_to_gcs(
    bucket_name: str,
    result: PortfolioResult,
    summary_data: dict
) -> None:
    """
    Upload portfolio result to GCS bucket.

    Args:
        bucket_name: GCS bucket name
        result: PortfolioResult
        summary_data: Pre-serialized summary data

    Raises:
        Exception on GCS errors (caller catches)
    """
    # Initialize GCS client (uses Application Default Credentials)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Upload summary JSON
    summary_path = make_portfolio_run_summary_path(result.portfolio_run_id)
    summary_blob = bucket.blob(summary_path)
    summary_blob.upload_from_string(
        json.dumps(summary_data, indent=2),
        content_type="application/json"
    )
    logger.info(f"  Wrote summary: gs://{bucket_name}/{summary_path}")

    # Upload per-repo JSON files
    for repo_result in result.repos:
        if repo_result.status == "completed":
            repo_path = make_portfolio_run_repo_path(
                result.portfolio_run_id,
                repo_result.repo_id
            )
            repo_data = {
                "repo_id": repo_result.repo_id,
                "display_name": repo_result.display_name,
                "status": repo_result.status,
                "duration_seconds": repo_result.duration_seconds,
                "issues_found": repo_result.issues_found,
                "issues_fixed": repo_result.issues_fixed,
                "pipeline_result": (
                    _serialize_pipeline_result(repo_result.pipeline_result)
                    if repo_result.pipeline_result
                    else None
                ),
            }

            repo_blob = bucket.blob(repo_path)
            repo_blob.upload_from_string(
                json.dumps(repo_data, indent=2),
                content_type="application/json"
            )
            logger.debug(f"  Wrote per-repo: gs://{bucket_name}/{repo_path}")


def _serialize_pipeline_result(pipeline_result) -> dict:
    """
    Serialize PipelineResult to JSON-safe dict.

    Args:
        pipeline_result: PipelineResult object

    Returns:
        Dictionary with pipeline result data
    """
    return {
        "repo_hint": pipeline_result.request.repo_hint,
        "task_description": pipeline_result.request.task_description,
        "total_issues_found": pipeline_result.total_issues_found,
        "issues_fixed": pipeline_result.issues_fixed,
        "pipeline_duration_seconds": pipeline_result.pipeline_duration_seconds,
        "issues": [
            {
                "severity": issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                "type": issue.type.value if hasattr(issue.type, 'value') else str(issue.type),
                "title": getattr(issue, 'title', 'N/A'),
                "description": getattr(issue, 'description', 'N/A'),
            }
            for issue in pipeline_result.issues
        ] if pipeline_result.issues else [],
    }


# ==============================================================================
# BigQuery Writer (Future - LIVE-BQ Phase)
# ==============================================================================
# BigQuery writes are deferred to a future phase.
# When implementing, add:
#   - def append_portfolio_result_to_bigquery(result, *, env) -> None
#   - Config: ORG_AUDIT_BIGQUERY_ENABLED, ORG_AUDIT_DATASET
#   - Insert rows into portfolio_swe_runs table
# ==============================================================================
