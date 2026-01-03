"""Tests for Pydantic tool output models."""

import pytest
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    ToolResult,
    ComplianceResult,
    SearchResult,
    FileResult,
    DependencyResult,
    Violation,
    SearchMatch,
    PythonDependencies,
    create_success_result,
    create_error_result,
)


class TestToolResult:
    """Test base ToolResult model."""

    def test_success_result(self):
        """Test successful result creation."""
        result = ToolResult(
            success=True,
            data={"key": "value"},
            metadata={"tool_name": "test_tool"},
        )
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.metadata["tool_name"] == "test_tool"

    def test_error_result(self):
        """Test error result creation."""
        result = ToolResult(
            success=False, error="Something went wrong", metadata={"tool_name": "test_tool"}
        )
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.data is None

    def test_json_serialization(self):
        """Test JSON serialization."""
        result = ToolResult(
            success=True,
            data={"test": "data"},
            metadata={"tool_name": "test"},
        )
        json_data = result.model_dump_json()
        assert '"success":true' in json_data
        assert '"test":"data"' in json_data


class TestComplianceResult:
    """Test ComplianceResult model."""

    def test_compliant_result(self):
        """Test COMPLIANT status with no violations."""
        result = create_success_result(
            ComplianceResult,
            "check_patterns",
            status="COMPLIANT",
            violations=[],
            warnings=[],
            passed=["R1", "R2", "R5"],
            compliance_score=100.0,
            risk_level="LOW",
            path="/test/path",
            rules_checked=["R1", "R2", "R5"],
        )

        assert result.success is True
        assert result.status == "COMPLIANT"
        assert len(result.violations) == 0
        assert result.compliance_score == 100.0
        assert result.risk_level == "LOW"
        assert "R1" in result.passed

    def test_violations_found_result(self):
        """Test VIOLATIONS_FOUND status with violations."""
        violation = Violation(
            rule="R1",
            rule_name="ADK-Only",
            type="forbidden_import",
            pattern="langchain",
            file="agents/test.py",
            line=10,
            text="import langchain",
        )

        result = create_success_result(
            ComplianceResult,
            "check_patterns",
            status="VIOLATIONS_FOUND",
            violations=[violation],
            warnings=[],
            passed=["R2"],
            compliance_score=50.0,
            risk_level="CRITICAL",
            path="/test/path",
            rules_checked=["R1", "R2"],
        )

        assert result.success is True
        assert result.status == "VIOLATIONS_FOUND"
        assert len(result.violations) == 1
        assert result.violations[0].rule == "R1"
        assert result.risk_level == "CRITICAL"

    def test_validation_error_on_mismatched_status(self):
        """Test validation fails when status doesn't match violations."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Cannot be COMPLIANT"):
            violation = Violation(
                rule="R1",
                rule_name="Test",
                type="test",
                pattern="test",
                file="test.py",
                line=1,
                text="test",
            )
            ComplianceResult(
                success=True,
                metadata={},
                status="COMPLIANT",  # Wrong - has violations
                violations=[violation],
                warnings=[],
                passed=[],
                compliance_score=0.0,
                risk_level="LOW",
                path="/test",
                rules_checked=["R1"],
            )

    def test_json_schema_generation(self):
        """Test JSON schema generation for AgentCard."""
        schema = ComplianceResult.model_json_schema()

        assert "properties" in schema
        assert "status" in schema["properties"]
        assert "violations" in schema["properties"]
        assert "compliance_score" in schema["properties"]
        assert "Violation" in schema.get("$defs", {})


class TestSearchResult:
    """Test SearchResult model."""

    def test_search_with_matches(self):
        """Test search result with matches."""
        matches = [
            SearchMatch(file="test.py", line_number=10, text="google.adk"),
            SearchMatch(file="test2.py", line_number=20, text="google.adk"),
        ]

        result = create_success_result(
            SearchResult,
            "search_codebase",
            query="google.adk",
            path="/test",
            file_pattern="*.py",
            matches=matches,
            match_count=2,
            file_count=2,
            truncated=False,
        )

        assert result.success is True
        assert result.query == "google.adk"
        assert len(result.matches) == 2
        assert result.match_count == 2
        assert result.file_count == 2
        assert result.truncated is False

    def test_search_truncated(self):
        """Test search result with truncation."""
        result = create_success_result(
            SearchResult,
            "search_codebase",
            query="test",
            path="/test",
            file_pattern="*.py",
            matches=[],
            match_count=100,  # More than returned
            file_count=50,
            truncated=True,
        )

        assert result.truncated is True
        assert result.match_count == 100

    def test_empty_search(self):
        """Test search with no results."""
        result = create_success_result(
            SearchResult,
            "search_codebase",
            query="nonexistent",
            path="/test",
            file_pattern="*.py",
            matches=[],
            match_count=0,
            file_count=0,
            truncated=False,
        )

        assert len(result.matches) == 0
        assert result.match_count == 0


class TestFileResult:
    """Test FileResult model."""

    def test_file_read_success(self):
        """Test successful file read."""
        result = create_success_result(
            FileResult,
            "get_file",
            path="/test/file.py",
            content="import google.adk\n",
            size=19,
            lines=1,
            encoding="utf-8",
        )

        assert result.success is True
        assert result.path == "/test/file.py"
        assert "google.adk" in result.content
        assert result.size == 19
        assert result.lines == 1
        assert result.encoding == "utf-8"

    def test_file_error(self):
        """Test file read error."""
        result = create_error_result(
            FileResult, "get_file", "File not found: /test/missing.py"
        )

        assert result.success is False
        assert "File not found" in result.error
        assert result.path is None
        assert result.content is None


class TestDependencyResult:
    """Test DependencyResult model."""

    def test_python_dependencies(self):
        """Test Python dependency analysis."""
        python = PythonDependencies(
            requirements_txt=["google-adk", "pydantic"],
            pyproject_toml=["pytest"],
        )

        result = create_success_result(
            DependencyResult,
            "analyze_deps",
            path="/test",
            python=python,
            summary={
                "python_packages": 3,
                "node_packages": 0,
                "terraform_providers": 0,
            },
        )

        assert result.success is True
        assert len(result.python.requirements_txt) == 2
        assert "google-adk" in result.python.requirements_txt

    def test_summary_calculation(self):
        """Test dependency summary calculation."""
        from agents.shared_contracts.tool_outputs import DependencySummary

        summary = DependencySummary(
            python_packages=10, node_packages=5, terraform_providers=2
        )

        result = create_success_result(
            DependencyResult,
            "analyze_deps",
            path="/test",
            summary=summary,
        )

        assert result.summary.python_packages == 10
        assert result.summary.node_packages == 5
        assert result.summary.terraform_providers == 2


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_success_result(self):
        """Test success result factory."""
        result = create_success_result(
            ToolResult, "test_tool", data={"key": "value"}
        )

        assert result.success is True
        assert result.metadata["tool_name"] == "test_tool"
        assert "timestamp" in result.metadata

    def test_create_error_result(self):
        """Test error result factory."""
        result = create_error_result(
            ToolResult, "test_tool", "Test error message"
        )

        assert result.success is False
        assert result.error == "Test error message"
        assert result.metadata["tool_name"] == "test_tool"
        assert "timestamp" in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
