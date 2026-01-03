"""
Pydantic models for MCP tool outputs and A2A contract serialization.

This module provides structured output models for Bob's Brain MCP tools,
enabling:
- Type-safe tool responses
- JSON Schema generation for A2A AgentCard skills
- Validation of tool outputs before returning to agents
- Consistent error handling across all tools

All models use Pydantic V2 patterns and are designed to serialize cleanly
to JSON for A2A protocol transport.

Architecture Pattern:
- MCP tools use these models as return types
- Models provide .model_json_schema() for AgentCard generation
- Foreman and specialists validate inputs/outputs against schemas
- Consistent metadata (tool_name, timestamp) across all results

See: 000-docs/6767-115-DR-STND-prompt-design-and-a2a-contracts-for-department-adk-iam.md
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# BASE MODELS
# ============================================================================


class ToolResult(BaseModel):
    """
    Base model for all MCP tool outputs.

    Provides consistent structure across all tools:
    - success: Whether tool execution succeeded
    - data: Tool-specific output data
    - error: Error message if failed
    - metadata: Additional context (timestamps, versions, etc.)

    All tool result models should inherit from this.
    """

    success: bool = Field(
        description="Whether the tool execution completed successfully"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool-specific output data (null on error)"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if success=false"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (tool name, timestamp, execution time, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"key": "value"},
                    "error": None,
                    "metadata": {
                        "tool_name": "example_tool",
                        "timestamp": "2025-12-20T15:00:00Z",
                        "execution_time_ms": 150,
                    },
                }
            ]
        }
    }


# ============================================================================
# COMPLIANCE CHECKING (check_patterns.py)
# ============================================================================


class Violation(BaseModel):
    """Single compliance violation found during pattern checking."""

    rule: str = Field(description="Rule ID that was violated (e.g., 'R1', 'R2')")
    rule_name: str = Field(description="Human-readable rule name")
    type: str = Field(
        description="Violation type (e.g., 'forbidden_import', 'forbidden_in_service')"
    )
    pattern: str = Field(description="Pattern that triggered the violation")
    file: str = Field(description="File path where violation was found")
    line: int = Field(description="Line number of violation")
    text: str = Field(description="Code snippet containing violation (truncated)")


class ComplianceResult(ToolResult):
    """
    Structured output from ADK compliance checking tool.

    Used by check_patterns.py to return compliance verification results.
    Validates code against Hard Mode rules (R1-R8).

    Fields:
    - status: COMPLIANT (no violations) or VIOLATIONS_FOUND
    - violations: List of detected violations with location details
    - warnings: Non-blocking warnings (e.g., unknown rules)
    - passed: List of rule IDs that passed checks
    - compliance_score: Percentage of rules passed (0.0-100.0)
    - risk_level: Overall risk assessment based on violations
    """

    status: Optional[Literal["COMPLIANT", "VIOLATIONS_FOUND"]] = Field(
        default=None, description="Overall compliance status (None on error)"
    )
    violations: List[Violation] = Field(
        default_factory=list,
        description="List of compliance violations found (empty if COMPLIANT)",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings (e.g., unknown rules checked)",
    )
    passed: List[str] = Field(
        default_factory=list, description="Rule IDs that passed checks"
    )
    compliance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentage of rules passed (0.0 = all failed, 100.0 = all passed, None on error)",
    )
    risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = Field(
        default=None, description="Overall risk level based on violation severity (None on error)"
    )

    # Override data field with structured compliance data
    path: Optional[str] = Field(default=None, description="Path that was checked (None on error)")
    rules_checked: List[str] = Field(
        default_factory=list, description="List of rule IDs checked"
    )

    @model_validator(mode="after")
    def validate_status_matches_violations(self):
        """Ensure status matches violations list."""
        # Allow None for error cases
        if self.status is None:
            return self

        if self.violations and self.status == "COMPLIANT":
            raise ValueError("Cannot be COMPLIANT with violations present")
        if not self.violations and self.status == "VIOLATIONS_FOUND":
            raise ValueError("Cannot have VIOLATIONS_FOUND with empty violations list")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": None,
                    "error": None,
                    "metadata": {"tool_name": "check_patterns", "timestamp": "2025-12-20T15:00:00Z"},
                    "status": "COMPLIANT",
                    "violations": [],
                    "warnings": [],
                    "passed": ["R1", "R2", "R5"],
                    "compliance_score": 100.0,
                    "risk_level": "LOW",
                    "path": "/home/user/project",
                    "rules_checked": ["R1", "R2", "R5"],
                }
            ]
        }
    }


# ============================================================================
# CODEBASE SEARCH (search_codebase.py)
# ============================================================================


class SearchMatch(BaseModel):
    """Single search result match."""

    file: str = Field(description="File path where match was found")
    line_number: int = Field(description="Line number of match")
    text: str = Field(description="Matched line content (stripped/truncated)")


class SearchResult(ToolResult):
    """
    Structured output from codebase search tool.

    Used by search_codebase.py to return code search results.
    Supports both ripgrep and grep backends.

    Fields:
    - query: Search pattern used
    - path: Directory searched
    - file_pattern: File glob pattern (e.g., '*.py')
    - matches: List of search matches with file/line/text
    - match_count: Total matches found (before truncation)
    - file_count: Number of unique files with matches
    - truncated: Whether results were truncated due to MAX_RESULTS limit
    """

    query: str = Field(default="", description="Search pattern used")
    path: str = Field(default="", description="Directory path searched")
    file_pattern: str = Field(default="", description="File glob pattern (e.g., '*.py', '*.md')")
    matches: List[SearchMatch] = Field(
        default_factory=list, description="List of search matches found"
    )
    match_count: int = Field(
        default=0, ge=0, description="Total number of matches (before truncation)"
    )
    file_count: int = Field(
        default=0, ge=0, description="Number of unique files containing matches"
    )
    truncated: bool = Field(
        default=False, description="Whether results were truncated (match_count > len(matches))"
    )

    @field_validator("file_count")
    @classmethod
    def calculate_file_count(cls, v: int, info) -> int:
        """Calculate unique file count from matches if not provided."""
        if v == 0 and info.data.get("matches"):
            unique_files = set(m.file for m in info.data["matches"])
            return len(unique_files)
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": None,
                    "error": None,
                    "metadata": {"tool_name": "search_codebase", "timestamp": "2025-12-20T15:00:00Z"},
                    "query": "google.adk",
                    "path": "/home/user/project",
                    "file_pattern": "*.py",
                    "matches": [
                        {
                            "file": "agents/bob/agent.py",
                            "line_number": 10,
                            "text": "from google.adk.agents import LlmAgent",
                        }
                    ],
                    "match_count": 1,
                    "file_count": 1,
                    "truncated": False,
                }
            ]
        }
    }


# ============================================================================
# FILE OPERATIONS (get_file.py)
# ============================================================================


class FileResult(ToolResult):
    """
    Structured output from file reading tool.

    Used by get_file.py to return file contents with metadata.
    Enforces security (allowed extensions, denied paths, size limits).

    Fields:
    - path: Absolute path to file (None on error)
    - content: File contents as UTF-8 text (None on error)
    - size: File size in bytes (None on error)
    - lines: Number of lines in file (None on error)
    - encoding: Character encoding (always 'utf-8' for now)
    """

    path: Optional[str] = Field(default=None, description="Absolute file path")
    content: Optional[str] = Field(default=None, description="File contents as UTF-8 text")
    size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    lines: Optional[int] = Field(default=None, ge=0, description="Number of lines in file")
    encoding: Literal["utf-8"] = Field(
        default="utf-8", description="Character encoding"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": None,
                    "error": None,
                    "metadata": {"tool_name": "get_file", "timestamp": "2025-12-20T15:00:00Z"},
                    "path": "/home/user/project/agents/bob/agent.py",
                    "content": "from google.adk.agents import LlmAgent\n\napp = LlmAgent(...)\n",
                    "size": 512,
                    "lines": 3,
                    "encoding": "utf-8",
                }
            ]
        }
    }


# ============================================================================
# DEPENDENCY ANALYSIS (analyze_deps.py)
# ============================================================================


class PythonDependencies(BaseModel):
    """Python dependency information."""

    requirements_txt: List[str] = Field(
        default_factory=list, description="Dependencies from requirements.txt"
    )
    pyproject_toml: List[str] = Field(
        default_factory=list, description="Dependencies from pyproject.toml"
    )


class NodeDependencies(BaseModel):
    """Node.js dependency information."""

    dependencies: Dict[str, str] = Field(
        default_factory=dict, description="Production dependencies from package.json"
    )
    dev_dependencies: Dict[str, str] = Field(
        default_factory=dict, description="Dev dependencies from package.json"
    )


class TerraformDependencies(BaseModel):
    """Terraform provider information."""

    providers: List[str] = Field(
        default_factory=list, description="Terraform providers found in *.tf files"
    )


class DependencySummary(BaseModel):
    """Summary of all dependencies."""

    python_packages: int = Field(
        ge=0, description="Total Python packages (requirements + pyproject)"
    )
    node_packages: int = Field(
        ge=0, description="Total Node packages (prod + dev)"
    )
    terraform_providers: int = Field(ge=0, description="Total Terraform providers")


class DependencyResult(ToolResult):
    """
    Structured output from dependency analysis tool.

    Used by analyze_deps.py to return project dependency information.
    Scans requirements.txt, pyproject.toml, package.json, and *.tf files.

    Fields:
    - path: Project path analyzed
    - python: Python dependency details
    - node: Node.js dependency details
    - terraform: Terraform provider details
    - summary: Aggregated counts
    - issues: Detected dependency issues (e.g., vulnerabilities, duplicates)
    """

    path: str = Field(description="Project path analyzed")
    python: PythonDependencies = Field(
        default_factory=PythonDependencies, description="Python dependencies"
    )
    node: NodeDependencies = Field(
        default_factory=NodeDependencies, description="Node.js dependencies"
    )
    terraform: TerraformDependencies = Field(
        default_factory=TerraformDependencies, description="Terraform providers"
    )
    summary: DependencySummary = Field(
        default_factory=DependencySummary, description="Dependency counts summary"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Detected dependency issues (e.g., vulnerabilities, duplicates)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": None,
                    "error": None,
                    "metadata": {"tool_name": "analyze_deps", "timestamp": "2025-12-20T15:00:00Z"},
                    "path": "/home/user/project",
                    "python": {
                        "requirements_txt": ["google-adk", "pydantic"],
                        "pyproject_toml": [],
                    },
                    "node": {"dependencies": {}, "dev_dependencies": {}},
                    "terraform": {"providers": ["google"]},
                    "summary": {
                        "python_packages": 2,
                        "node_packages": 0,
                        "terraform_providers": 1,
                    },
                    "issues": [],
                }
            ]
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_success_result(
    model_class: type[ToolResult], tool_name: str, **kwargs
) -> ToolResult:
    """
    Factory for creating successful tool results.

    Args:
        model_class: ToolResult subclass to instantiate
        tool_name: Name of the tool (for metadata)
        **kwargs: Model-specific fields

    Returns:
        Instantiated tool result with success=True and metadata
    """
    metadata = {
        "tool_name": tool_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Add execution_time_ms if provided
    if "execution_time_ms" in kwargs:
        metadata["execution_time_ms"] = kwargs.pop("execution_time_ms")

    return model_class(success=True, metadata=metadata, **kwargs)


def create_error_result(
    model_class: type[ToolResult], tool_name: str, error: str
) -> ToolResult:
    """
    Factory for creating error tool results.

    Args:
        model_class: ToolResult subclass to instantiate
        tool_name: Name of the tool (for metadata)
        error: Error message

    Returns:
        Instantiated tool result with success=False and error message
    """
    metadata = {
        "tool_name": tool_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    return model_class(success=False, error=error, metadata=metadata)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Base models
    "ToolResult",
    # Specific result types
    "ComplianceResult",
    "Violation",
    "SearchResult",
    "SearchMatch",
    "FileResult",
    "DependencyResult",
    "PythonDependencies",
    "NodeDependencies",
    "TerraformDependencies",
    "DependencySummary",
    # Helper functions
    "create_success_result",
    "create_error_result",
]
