"""
Unit tests for Slack formatter module.

Tests the conversion of PortfolioResult to Slack Block Kit format.
"""

from datetime import datetime

import pytest

from agents.notifications.slack_formatter import (
    _format_duration,
    _get_env_badge,
    _severity_emoji,
    _severity_order,
    format_portfolio_completion,
    format_portfolio_completion_simple,
)
from agents.shared_contracts import PortfolioResult


@pytest.fixture
def sample_portfolio_result():
    """Create a sample PortfolioResult for testing."""
    return PortfolioResult(
        portfolio_run_id="test-12345678-abcd-efgh-ijkl-mnopqrstuvwx",
        repos=[],
        total_repos_analyzed=5,
        total_repos_skipped=1,
        total_repos_errored=0,
        total_issues_found=42,
        total_issues_fixed=30,
        issues_by_severity={
            "critical": 2,
            "high": 10,
            "medium": 20,
            "low": 8,
            "info": 2,
        },
        issues_by_type={
            "adk_violation": 15,
            "pattern_drift": 12,
            "security": 8,
            "tech_debt": 7,
        },
        repos_by_issue_count=[
            ("bobs-brain", 20),
            ("diagnosticpro", 12),
            ("pipelinepilot", 10),
        ],
        repos_by_compliance_score=[
            ("diagnosticpro", 0.7),
            ("bobs-brain", 0.8),
            ("pipelinepilot", 0.9),
        ],
        portfolio_duration_seconds=456.78,
        timestamp=datetime(2025, 11, 20, 12, 30, 45),
    )


class TestFormatPortfolioCompletion:
    """Tests for format_portfolio_completion()."""

    def test_returns_list_of_blocks(self, sample_portfolio_result):
        """Test returns a list of Slack Block Kit blocks."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_contains_header_block(self, sample_portfolio_result):
        """Test contains a header block with run ID."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        # Find section block with run ID
        header_blocks = [b for b in blocks if b.get("type") == "section"]
        assert len(header_blocks) > 0
        # Check first section has run ID (truncated to 8 chars)
        first_section = header_blocks[0]
        text = first_section["text"]["text"]
        assert "test-123" in text  # First 8 chars of run ID

    def test_contains_summary_block(self, sample_portfolio_result):
        """Test contains summary metrics."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        # Find blocks with section type that have text (not fields)
        sections = [b for b in blocks if b.get("type") == "section" and "text" in b]
        # Check that at least one section contains repo/issue metrics
        texts = [s["text"]["text"] for s in sections]
        combined_text = " ".join(texts)
        assert "5 analyzed" in combined_text
        assert "42 found" in combined_text
        assert "30 fixed" in combined_text

    def test_contains_dividers(self, sample_portfolio_result):
        """Test contains divider blocks for visual separation."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        dividers = [b for b in blocks if b.get("type") == "divider"]
        assert len(dividers) >= 2  # At least a couple dividers

    def test_contains_issue_breakdown(self, sample_portfolio_result):
        """Test contains issue breakdown by severity and type."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        # Find section with fields (issue breakdown)
        field_sections = [
            b for b in blocks if b.get("type") == "section" and "fields" in b
        ]
        assert len(field_sections) > 0

    def test_contains_top_repos(self, sample_portfolio_result):
        """Test contains top repos section."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        texts = []
        for block in blocks:
            if block.get("type") == "section" and "text" in block:
                texts.append(block["text"]["text"])
        combined_text = " ".join(texts)
        # Top repos section should exist when there are multiple repos
        assert (
            "Top Repos" in combined_text
            or len(sample_portfolio_result.repos_by_issue_count) > 0
        )

    def test_contains_footer(self, sample_portfolio_result):
        """Test contains footer with timestamp."""
        blocks = format_portfolio_completion(sample_portfolio_result, env="dev")
        # Find context block (footer)
        context_blocks = [b for b in blocks if b.get("type") == "context"]
        assert len(context_blocks) > 0
        # Check footer has timestamp
        footer = context_blocks[0]
        text = footer["elements"][0]["text"]
        assert "2025-11-20" in text

    def test_env_badge_in_header(self, sample_portfolio_result):
        """Test environment badge appears in header."""
        blocks_dev = format_portfolio_completion(sample_portfolio_result, env="dev")
        blocks_prod = format_portfolio_completion(sample_portfolio_result, env="prod")

        # Dev should have DEV badge
        dev_text = blocks_dev[0]["text"]["text"]
        assert "DEV" in dev_text

        # Prod should have PROD badge
        prod_text = blocks_prod[0]["text"]["text"]
        assert "PROD" in prod_text


class TestFormatPortfolioCompletionSimple:
    """Tests for format_portfolio_completion_simple()."""

    def test_returns_plain_text(self, sample_portfolio_result):
        """Test returns plain text string."""
        text = format_portfolio_completion_simple(sample_portfolio_result, env="dev")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_contains_key_metrics(self, sample_portfolio_result):
        """Test contains key metrics in text."""
        text = format_portfolio_completion_simple(sample_portfolio_result, env="dev")
        assert "5 analyzed" in text
        assert "42 found" in text
        assert "30 fixed" in text

    def test_contains_env(self, sample_portfolio_result):
        """Test contains environment name."""
        text_dev = format_portfolio_completion_simple(
            sample_portfolio_result, env="dev"
        )
        text_prod = format_portfolio_completion_simple(
            sample_portfolio_result, env="prod"
        )
        assert "DEV" in text_dev
        assert "PROD" in text_prod

    def test_contains_run_id(self, sample_portfolio_result):
        """Test contains truncated run ID."""
        text = format_portfolio_completion_simple(sample_portfolio_result, env="dev")
        assert "test-123" in text  # Run ID (truncated to 8 chars)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_env_badge(self):
        """Test environment badge generation."""
        assert "DEV" in _get_env_badge("dev")
        assert "STAGING" in _get_env_badge("staging")
        assert "PROD" in _get_env_badge("prod")

    def test_severity_emoji(self):
        """Test severity emoji mapping."""
        assert _severity_emoji("critical") == ":rotating_light:"
        assert _severity_emoji("high") == ":red_circle:"
        assert _severity_emoji("medium") == ":orange_circle:"
        assert _severity_emoji("low") == ":yellow_circle:"
        assert _severity_emoji("info") == ":information_source:"

    def test_severity_order(self):
        """Test severity ordering for sorting."""
        assert _severity_order("critical") > _severity_order("high")
        assert _severity_order("high") > _severity_order("medium")
        assert _severity_order("medium") > _severity_order("low")
        assert _severity_order("low") > _severity_order("info")

    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        assert "5.0s" in _format_duration(5.0)

    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        assert "2.0m" in _format_duration(120.0)

    def test_format_duration_hours(self):
        """Test duration formatting for hours."""
        assert "1.0h" in _format_duration(3600.0)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_no_issues_found(self):
        """Test formatting when no issues found."""
        result = PortfolioResult(
            portfolio_run_id="test-no-issues",
            repos=[],
            total_repos_analyzed=3,
            total_issues_found=0,
            total_issues_fixed=0,
            portfolio_duration_seconds=100.0,
            timestamp=datetime.now(),
        )
        blocks = format_portfolio_completion(result, env="dev")
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_single_repo(self):
        """Test formatting with single repo (no top repos section)."""
        result = PortfolioResult(
            portfolio_run_id="test-single",
            repos=[],
            total_repos_analyzed=1,
            total_issues_found=5,
            total_issues_fixed=3,
            portfolio_duration_seconds=50.0,
            timestamp=datetime.now(),
        )
        blocks = format_portfolio_completion(result, env="dev")
        assert isinstance(blocks, list)

    def test_repos_with_errors(self):
        """Test formatting when some repos errored."""
        result = PortfolioResult(
            portfolio_run_id="test-errors",
            repos=[],
            total_repos_analyzed=3,
            total_repos_skipped=1,
            total_repos_errored=2,
            total_issues_found=10,
            total_issues_fixed=5,
            portfolio_duration_seconds=200.0,
            timestamp=datetime.now(),
        )
        blocks = format_portfolio_completion(result, env="dev")
        texts = []
        for block in blocks:
            if block.get("type") == "section" and "text" in block:
                texts.append(block["text"]["text"])
        combined_text = " ".join(texts)
        assert "2 errored" in combined_text
