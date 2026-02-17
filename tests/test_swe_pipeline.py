#!/usr/bin/env python3
"""
Test suite for IAM SWE Pipeline orchestration.

Tests the complete end-to-end pipeline flow with synthetic data.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import pipeline components
# Import orchestrator
from agents.iam_senior_adk_devops_lead.orchestrator import (
    iam_adk_analyze,
    iam_doc_update,
    iam_fix_impl_execute,
    iam_fix_plan_create,
    iam_issue_create,
    iam_qa_verify,
    run_swe_pipeline,
)
from agents.shared_contracts import (
    CleanupTask,
    CodeChange,
    DocumentationUpdate,
    FixPlan,
    IndexEntry,
    IssueSpec,
    IssueType,
    PipelineRequest,
    PipelineResult,
    QAVerdict,
    create_mock_fix_plan,
    create_mock_issue,
)


class TestSWEPipeline(unittest.TestCase):
    """Test the complete SWE pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_repo_path = Path(__file__).parent / "data" / "synthetic_repo"
        self.assertTrue(self.test_repo_path.exists(), f"Test repo not found at {self.test_repo_path}")

    @unittest.expectedFailure  # Phase H+: Async A2A infrastructure complete, but requires LLM credentials
    def test_pipeline_end_to_end(self):
        """Test complete pipeline flow from request to result.

        NOTE: This test is marked as expectedFailure because:
        - Phase H+ async A2A dispatch infrastructure is COMPLETE
        - Uses InMemoryRunner.run_debug() for async execution
        - BUT: Requires valid GCP credentials to call Gemini LLM
        - Without credentials, falls back to mock execution which
          returns placeholder data that doesn't match test expectations
        - Will pass when run with valid GOOGLE_APPLICATION_CREDENTIALS
        """
        # Create request
        request = PipelineRequest(
            repo_hint=str(self.test_repo_path),
            task_description="Audit ADK compliance and fix violations",
            env="dev",
            max_issues_to_fix=2,
            include_cleanup=True,
            include_indexing=True
        )

        # Run pipeline
        result = run_swe_pipeline(request)

        # Assertions on result structure
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(result.request, request)

        # Check that issues were found
        self.assertGreater(len(result.issues), 0, "Should find at least one issue")
        self.assertGreater(result.total_issues_found, 0, "Total issues should be > 0")

        # Check issue quality
        for issue in result.issues:
            self.assertIsInstance(issue, IssueSpec)
            self.assertIsNotNone(issue.id)
            self.assertIsNotNone(issue.type)
            self.assertIsNotNone(issue.severity)
            self.assertIsNotNone(issue.title)
            self.assertIsNotNone(issue.description)

        # Check that plans were created for issues
        self.assertGreater(len(result.plans), 0, "Should create fix plans")
        self.assertLessEqual(len(result.plans), request.max_issues_to_fix,
                            "Should not exceed max_issues_to_fix")

        # Check plan quality
        for plan in result.plans:
            self.assertIsInstance(plan, FixPlan)
            self.assertIsNotNone(plan.plan_id)
            self.assertIsNotNone(plan.issue_id)
            self.assertIsNotNone(plan.approach)
            self.assertGreater(len(plan.steps), 0, "Plan should have steps")

        # Check implementations
        self.assertEqual(len(result.implementations), len(result.plans),
                        "Should implement all plans")

        for impl in result.implementations:
            self.assertIsInstance(impl, CodeChange)
            self.assertIsNotNone(impl.plan_id)
            self.assertIsNotNone(impl.file_path)
            self.assertIsNotNone(impl.change_type)

        # Check QA results
        self.assertEqual(len(result.qa_report), len(result.implementations),
                        "Should verify all implementations")

        for qa in result.qa_report:
            self.assertIsInstance(qa, QAVerdict)
            self.assertIsNotNone(qa.status)
            self.assertIsNotNone(qa.safe_to_apply)

        # Check documentation
        self.assertGreater(len(result.docs), 0, "Should generate documentation")

        for doc in result.docs:
            self.assertIsInstance(doc, DocumentationUpdate)
            self.assertIsNotNone(doc.doc_id)
            self.assertIsNotNone(doc.doc_type)

        # Check cleanup (if enabled)
        if request.include_cleanup:
            self.assertGreater(len(result.cleanup), 0, "Should identify cleanup tasks")
            for task in result.cleanup:
                self.assertIsInstance(task, CleanupTask)

        # Check indexing (if enabled)
        if request.include_indexing:
            self.assertGreater(len(result.index_updates), 0, "Should update index")
            for entry in result.index_updates:
                self.assertIsInstance(entry, IndexEntry)

        # Check metrics
        self.assertEqual(result.issues_fixed, min(len(result.plans), request.max_issues_to_fix))
        self.assertGreater(result.pipeline_duration_seconds, 0, "Should track duration")

    def test_pipeline_no_issues(self):
        """Test pipeline when no issues are found (except doc issue)."""
        # Create request for a "clean" repo
        request = PipelineRequest(
            repo_hint="/nonexistent/clean/repo",
            task_description="Audit perfect code",
            env="dev"
        )

        # Mock the analyze function to return no violations
        with patch('agents.iam_senior_adk_devops_lead.orchestrator.iam_adk_analyze') as mock_analyze:
            mock_analyze.return_value = MagicMock(violations_found=[], compliance_score=1.0)

            result = run_swe_pipeline(request)

            # Should handle gracefully - iam_issue_create always adds one doc issue
            # even with no violations, so expect 1 issue (the doc issue)
            self.assertLessEqual(len(result.issues), 1)
            # No ADK violation issues should be created
            adk_issues = [i for i in result.issues if i.type == IssueType.ADK_VIOLATION]
            self.assertEqual(len(adk_issues), 0, "No ADK violations should be found")
            # No fixes should be implemented for the doc issue
            self.assertEqual(result.issues_fixed, 0)

    @unittest.expectedFailure  # Phase H+: Async A2A infrastructure complete, but requires LLM credentials
    def test_pipeline_with_cleanup(self):
        """Test optional cleanup phase.

        NOTE: This test is marked as expectedFailure because:
        - Phase H+ async A2A dispatch infrastructure is COMPLETE
        - Uses InMemoryRunner.run_debug() for async execution
        - BUT: Requires valid GCP credentials to call Gemini LLM
        - Without credentials, cleanup identification returns mock data
        - Will pass when run with valid GOOGLE_APPLICATION_CREDENTIALS
        """
        request = PipelineRequest(
            repo_hint=str(self.test_repo_path),
            task_description="Find tech debt",
            env="dev",
            include_cleanup=True,
            include_indexing=False  # Disable indexing
        )

        result = run_swe_pipeline(request)

        # Should include cleanup tasks
        self.assertGreater(len(result.cleanup), 0, "Should find cleanup tasks")

        # Should not include index updates
        self.assertEqual(len(result.index_updates), 0, "Should skip indexing")

    def test_pipeline_staging_env(self):
        """Test pipeline with staging environment settings."""
        request = PipelineRequest(
            repo_hint=str(self.test_repo_path),
            task_description="Staging audit",
            env="staging",
            max_issues_to_fix=5  # Higher limit for staging
        )

        result = run_swe_pipeline(request)

        # Should respect staging limits
        self.assertLessEqual(len(result.plans), 5, "Should respect staging limits")

    def test_individual_agent_stubs(self):
        """Test individual agent stub functions."""
        # Initialize variables for later use
        plans = []
        qa_results = []

        # Test iam-adk
        analysis = iam_adk_analyze(str(self.test_repo_path), "Test")
        self.assertIsNotNone(analysis.compliance_score)
        self.assertIsInstance(analysis.violations_found, list)

        # Test iam-issue
        issues = iam_issue_create(analysis)
        self.assertIsInstance(issues, list)
        if issues:
            self.assertIsInstance(issues[0], IssueSpec)

        # Test iam-fix-plan
        if issues:
            plans = iam_fix_plan_create(issues[:1], max_fixes=1)
            self.assertIsInstance(plans, list)
            if plans:
                self.assertIsInstance(plans[0], FixPlan)

                # Test iam-fix-impl
                impls = iam_fix_impl_execute(plans)
                self.assertIsInstance(impls, list)
                if impls:
                    self.assertIsInstance(impls[0], CodeChange)

                    # Test iam-qa
                    qa_results = iam_qa_verify(impls)
                    self.assertIsInstance(qa_results, list)
                    if qa_results:
                        self.assertIsInstance(qa_results[0], QAVerdict)

        # Test iam-doc
        docs = iam_doc_update(issues, plans, qa_results)
        self.assertIsInstance(docs, list)
        if docs:
            self.assertIsInstance(docs[0], DocumentationUpdate)

    def test_contract_serialization(self):
        """Test that all contracts can be serialized (for A2A)."""
        request = PipelineRequest(
            repo_hint=str(self.test_repo_path),
            task_description="Test serialization",
            env="dev"
        )

        result = run_swe_pipeline(request)

        # Try to convert result to dict (simulating A2A serialization)
        # In real implementation, would use dataclasses.asdict or similar
        self.assertIsNotNone(result.timestamp)
        self.assertIsInstance(result.total_issues_found, int)
        self.assertIsInstance(result.issues_fixed, int)
        self.assertIsInstance(result.pipeline_duration_seconds, float)

    def test_mock_helpers(self):
        """Test the mock helper functions."""
        # Test create_mock_issue
        issue = create_mock_issue(IssueType.ADK_VIOLATION)
        self.assertIsInstance(issue, IssueSpec)
        self.assertEqual(issue.type, IssueType.ADK_VIOLATION)

        # Test create_mock_fix_plan
        plan = create_mock_fix_plan(issue.id)
        self.assertIsInstance(plan, FixPlan)
        self.assertEqual(plan.issue_id, issue.id)
        self.assertGreater(len(plan.steps), 0)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for pipeline with external systems."""

    @unittest.skip("Requires actual Vertex AI setup")
    def test_vertex_search_integration(self):
        """Test integration with Vertex AI Search."""
        # Would test actual Vertex AI Search calls

    @unittest.skip("Requires actual A2A setup")
    def test_a2a_protocol(self):
        """Test A2A protocol with Agent Engine."""
        # Would test actual A2A communication


class TestPipelinePerformance(unittest.TestCase):
    """Performance tests for the pipeline."""

    def test_pipeline_performance(self):
        """Test pipeline completes within performance targets."""
        import time

        request = PipelineRequest(
            repo_hint=Path(__file__).parent / "data" / "synthetic_repo",
            task_description="Performance test",
            env="dev",
            max_issues_to_fix=1
        )

        start = time.time()
        result = run_swe_pipeline(request)
        duration = time.time() - start

        # Should complete quickly with stubs
        self.assertLess(duration, 10, "Pipeline should complete within 10 seconds with stubs")
        self.assertAlmostEqual(result.pipeline_duration_seconds, duration, places=1)


def run_single_test(test_name: str = None):
    """Run a single test or all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    if test_name:
        # Run specific test
        suite.addTest(TestSWEPipeline(test_name))
    else:
        # Run all tests
        suite.addTest(loader.loadTestsFromTestCase(TestSWEPipeline))
        suite.addTest(loader.loadTestsFromTestCase(TestPipelineIntegration))
        suite.addTest(loader.loadTestsFromTestCase(TestPipelinePerformance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    # Allow running specific test: python test_swe_pipeline.py test_pipeline_end_to_end
    test_name = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_single_test(test_name)
    sys.exit(0 if success else 1)
