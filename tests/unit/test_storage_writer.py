"""
Test Org Storage Writer Module (LIVE1-GCS)

Tests GCS writer for portfolio results with mocking.
"""

# Add agents to path (as a proper package)
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Insert repo root so "agents" becomes a proper top-level package
repo_root = str(Path(__file__).parent.parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Now import from agents package properly
# Import the storage_writer module through proper package path
# This ensures relative imports work correctly
from agents.iam_senior_adk_devops_lead import storage_writer
from agents.shared_contracts import PerRepoResult, PortfolioResult

# Register the module under the path that @patch decorators expect
sys.modules["iam_senior_adk_devops_lead.storage_writer"] = storage_writer


class TestWritePortfolioResultToGCS:
    """Test write_portfolio_result_to_gcs() function"""

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", False)
    def test_skips_when_gcs_not_available(self, caplog):
        """Test skips write when google-cloud-storage not installed"""
        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should log warning and return without error
        assert "google-cloud-storage not installed" in caplog.text

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", True)
    @patch("iam_senior_adk_devops_lead.storage_writer.is_org_storage_write_enabled")
    def test_skips_when_writes_disabled(self, mock_enabled, caplog):
        """Test skips write when ORG_STORAGE_WRITE_ENABLED is false"""
        import logging

        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        caplog.set_level(
            logging.INFO, logger="agents.iam_senior_adk_devops_lead.storage_writer"
        )
        mock_enabled.return_value = False

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should log info and return without error
        assert "Org storage write disabled" in caplog.text

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", True)
    @patch("iam_senior_adk_devops_lead.storage_writer.is_org_storage_write_enabled")
    @patch("iam_senior_adk_devops_lead.storage_writer.get_org_storage_bucket")
    def test_skips_when_bucket_not_set(self, mock_bucket, mock_enabled, caplog):
        """Test skips write when ORG_STORAGE_BUCKET not set"""
        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        mock_enabled.return_value = True
        mock_bucket.return_value = None

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should log warning and return without error
        assert "ORG_STORAGE_BUCKET not set" in caplog.text

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", True)
    @patch("iam_senior_adk_devops_lead.storage_writer.is_org_storage_write_enabled")
    @patch("iam_senior_adk_devops_lead.storage_writer.get_org_storage_bucket")
    @patch("iam_senior_adk_devops_lead.storage_writer._build_portfolio_summary_json")
    def test_handles_serialization_errors_gracefully(
        self, mock_build_json, mock_bucket, mock_enabled, caplog
    ):
        """Test handles serialization errors without crashing"""
        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        mock_enabled.return_value = True
        mock_bucket.return_value = "test-bucket"
        mock_build_json.side_effect = Exception("Serialization failed")

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should log error and return without raising
        assert "Failed to serialize portfolio result" in caplog.text

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", True)
    @patch("iam_senior_adk_devops_lead.storage_writer.is_org_storage_write_enabled")
    @patch("iam_senior_adk_devops_lead.storage_writer.get_org_storage_bucket")
    @patch("iam_senior_adk_devops_lead.storage_writer._upload_to_gcs")
    @patch("iam_senior_adk_devops_lead.storage_writer._build_portfolio_summary_json")
    def test_handles_gcs_upload_errors_gracefully(
        self, mock_build_json, mock_upload, mock_bucket, mock_enabled, caplog
    ):
        """Test handles GCS upload errors without crashing"""
        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        mock_enabled.return_value = True
        mock_bucket.return_value = "test-bucket"
        mock_build_json.return_value = {"test": "data"}
        mock_upload.side_effect = Exception("Upload failed")

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should log error and return without raising
        assert "Failed to write portfolio result to GCS" in caplog.text

    @patch("iam_senior_adk_devops_lead.storage_writer.GCS_AVAILABLE", True)
    @patch("iam_senior_adk_devops_lead.storage_writer.is_org_storage_write_enabled")
    @patch("iam_senior_adk_devops_lead.storage_writer.get_org_storage_bucket")
    @patch("iam_senior_adk_devops_lead.storage_writer._upload_to_gcs")
    @patch("iam_senior_adk_devops_lead.storage_writer._build_portfolio_summary_json")
    def test_successful_write(
        self, mock_build_json, mock_upload, mock_bucket, mock_enabled, caplog
    ):
        """Test successful write to GCS"""
        import logging

        from iam_senior_adk_devops_lead.storage_writer import (
            write_portfolio_result_to_gcs,
        )

        caplog.set_level(
            logging.INFO, logger="agents.iam_senior_adk_devops_lead.storage_writer"
        )
        mock_enabled.return_value = True
        mock_bucket.return_value = "test-bucket"
        mock_build_json.return_value = {"test": "data"}

        result = self._create_sample_portfolio_result()
        write_portfolio_result_to_gcs(result, env="dev")

        # Should call upload and log success
        mock_upload.assert_called_once()
        assert "Portfolio result written to org storage" in caplog.text

    @staticmethod
    def _create_sample_portfolio_result():
        """Create a sample PortfolioResult for testing"""
        repo_result = PerRepoResult(
            repo_id="test-repo",
            display_name="Test Repo",
            status="completed",
            pipeline_result=None,
            duration_seconds=10.0,
            error_message=None,
        )

        return PortfolioResult(
            portfolio_run_id="test-run-123",
            timestamp=datetime.now(),
            total_repos_analyzed=1,
            total_repos_skipped=0,
            total_repos_errored=0,
            total_issues_found=5,
            total_issues_fixed=3,
            portfolio_duration_seconds=10.0,
            issues_by_severity={"high": 2, "medium": 3},
            issues_by_type={"security": 2, "quality": 3},
            repos_by_issue_count=[("test-repo", 5)],
            repos_by_compliance_score=[("test-repo", 0.6)],
            repos=[repo_result],
        )


class TestBuildPortfolioSummaryJson:
    """Test _build_portfolio_summary_json() helper function"""

    def test_serializes_portfolio_result(self):
        """Test serializes PortfolioResult to JSON-safe dict"""
        from iam_senior_adk_devops_lead.storage_writer import (
            _build_portfolio_summary_json,
        )

        result = self._create_sample_portfolio_result()
        json_data = _build_portfolio_summary_json(result, env="dev")

        # Check required fields
        assert json_data["portfolio_run_id"] == "test-run-123"
        assert json_data["environment"] == "dev"
        assert json_data["summary"]["total_repos_analyzed"] == 1
        assert json_data["summary"]["total_issues_found"] == 5
        assert json_data["summary"]["total_issues_fixed"] == 3

    def test_calculates_fix_rate(self):
        """Test calculates fix rate correctly"""
        from iam_senior_adk_devops_lead.storage_writer import (
            _build_portfolio_summary_json,
        )

        result = self._create_sample_portfolio_result()
        json_data = _build_portfolio_summary_json(result, env="dev")

        # 3 fixed out of 5 = 60%
        assert json_data["summary"]["fix_rate"] == 60.0

    def test_handles_zero_issues(self):
        """Test handles zero issues (no division by zero)"""
        from iam_senior_adk_devops_lead.storage_writer import (
            _build_portfolio_summary_json,
        )

        result = self._create_sample_portfolio_result()
        result.total_issues_found = 0
        result.total_issues_fixed = 0

        json_data = _build_portfolio_summary_json(result, env="dev")

        # Should default to 0.0 when no issues
        assert json_data["summary"]["fix_rate"] == 0.0

    def test_serializes_datetime(self):
        """Test serializes datetime to ISO format"""
        from iam_senior_adk_devops_lead.storage_writer import (
            _build_portfolio_summary_json,
        )

        result = self._create_sample_portfolio_result()
        result.timestamp = datetime(2025, 1, 20, 12, 0, 0)

        json_data = _build_portfolio_summary_json(result, env="dev")

        # Should be ISO format string
        assert json_data["timestamp"] == "2025-01-20T12:00:00"

    def test_includes_per_repo_results(self):
        """Test includes per-repo results in JSON"""
        from iam_senior_adk_devops_lead.storage_writer import (
            _build_portfolio_summary_json,
        )

        result = self._create_sample_portfolio_result()
        json_data = _build_portfolio_summary_json(result, env="dev")

        # Should include repos array
        assert "repos" in json_data
        assert len(json_data["repos"]) == 1
        assert json_data["repos"][0]["repo_id"] == "test-repo"

    @staticmethod
    def _create_sample_portfolio_result():
        """Create a sample PortfolioResult for testing"""
        repo_result = PerRepoResult(
            repo_id="test-repo",
            display_name="Test Repo",
            status="completed",
            pipeline_result=None,
            duration_seconds=10.0,
            error_message=None,
        )

        return PortfolioResult(
            portfolio_run_id="test-run-123",
            timestamp=datetime.now(),
            total_repos_analyzed=1,
            total_repos_skipped=0,
            total_repos_errored=0,
            total_issues_found=5,
            total_issues_fixed=3,
            portfolio_duration_seconds=10.0,
            issues_by_severity={"high": 2, "medium": 3},
            issues_by_type={"security": 2, "quality": 3},
            repos_by_issue_count=[("test-repo", 5)],
            repos_by_compliance_score=[("test-repo", 0.6)],
            repos=[repo_result],
        )


class TestUploadToGCS:
    """Test _upload_to_gcs() helper function"""

    @patch("iam_senior_adk_devops_lead.storage_writer.storage")
    @patch("iam_senior_adk_devops_lead.storage_writer.make_portfolio_run_summary_path")
    @patch("iam_senior_adk_devops_lead.storage_writer.make_portfolio_run_repo_path")
    def test_uploads_summary_json(
        self, mock_repo_path, mock_summary_path, mock_storage
    ):
        """Test uploads summary JSON to GCS"""
        from iam_senior_adk_devops_lead.storage_writer import _upload_to_gcs

        # Mock GCS client
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        mock_summary_path.return_value = "portfolio/runs/test-run/summary.json"

        result = self._create_sample_portfolio_result()
        summary_data = {"test": "data"}

        _upload_to_gcs("test-bucket", result, summary_data)

        # Should upload summary
        mock_bucket.blob.assert_any_call("portfolio/runs/test-run/summary.json")
        mock_blob.upload_from_string.assert_called()

    @patch("iam_senior_adk_devops_lead.storage_writer.storage")
    @patch("iam_senior_adk_devops_lead.storage_writer.make_portfolio_run_summary_path")
    @patch("iam_senior_adk_devops_lead.storage_writer.make_portfolio_run_repo_path")
    def test_uploads_per_repo_json_for_completed_repos(
        self, mock_repo_path, mock_summary_path, mock_storage
    ):
        """Test uploads per-repo JSON only for completed repos"""
        from iam_senior_adk_devops_lead.storage_writer import _upload_to_gcs

        # Mock GCS client
        mock_client = MagicMock()
        mock_bucket = MagicMock()

        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket

        mock_summary_path.return_value = "portfolio/runs/test-run/summary.json"
        mock_repo_path.return_value = "portfolio/runs/test-run/per-repo/test-repo.json"

        result = self._create_sample_portfolio_result()
        summary_data = {"test": "data"}

        _upload_to_gcs("test-bucket", result, summary_data)

        # Should call make_portfolio_run_repo_path for completed repos
        mock_repo_path.assert_called_with("test-run-123", "test-repo")

    @patch("iam_senior_adk_devops_lead.storage_writer.storage")
    @patch("iam_senior_adk_devops_lead.storage_writer.make_portfolio_run_summary_path")
    def test_skips_per_repo_json_for_failed_repos(
        self, mock_summary_path, mock_storage
    ):
        """Test skips per-repo JSON for failed/skipped repos"""
        from iam_senior_adk_devops_lead.storage_writer import _upload_to_gcs

        # Mock GCS client
        mock_client = MagicMock()
        mock_bucket = MagicMock()

        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket

        mock_summary_path.return_value = "portfolio/runs/test-run/summary.json"

        result = self._create_sample_portfolio_result()
        result.repos[0].status = "error"  # Set to error status
        summary_data = {"test": "data"}

        _upload_to_gcs("test-bucket", result, summary_data)

        # Should only upload summary, not per-repo (only 1 blob call)
        assert mock_bucket.blob.call_count == 1

    @staticmethod
    def _create_sample_portfolio_result():
        """Create a sample PortfolioResult for testing"""
        repo_result = PerRepoResult(
            repo_id="test-repo",
            display_name="Test Repo",
            status="completed",
            pipeline_result=None,
            duration_seconds=10.0,
            error_message=None,
        )

        return PortfolioResult(
            portfolio_run_id="test-run-123",
            timestamp=datetime.now(),
            total_repos_analyzed=1,
            total_repos_skipped=0,
            total_repos_errored=0,
            total_issues_found=5,
            total_issues_fixed=3,
            portfolio_duration_seconds=10.0,
            issues_by_severity={"high": 2, "medium": 3},
            issues_by_type={"security": 2, "quality": 3},
            repos_by_issue_count=[("test-repo", 5)],
            repos_by_compliance_score=[("test-repo", 0.6)],
            repos=[repo_result],
        )
