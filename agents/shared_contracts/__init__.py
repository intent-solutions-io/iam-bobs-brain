"""
Shared contracts package for Bob's Brain agents.

This package contains:
- tool_outputs.py: Pydantic models for MCP tool results
- pipeline_contracts.py: Dataclasses for SWE pipeline agent communication
- (future) a2a_envelopes.py: A2A task/result envelope wrappers

All contracts are designed for:
- Type-safe inter-agent communication
- JSON Schema generation for AgentCard skills
- Validation of inputs/outputs against A2A protocol
"""

# ============================================================================
# TOOL OUTPUTS (MCP/Pydantic models)
# ============================================================================
from agents.shared_contracts.tool_outputs import (
    # Base models
    ToolResult,
    # Specific result types
    ComplianceResult,
    SearchResult,
    FileResult,
    DependencyResult,
    # Nested models
    Violation,
    SearchMatch,
    PythonDependencies,
    NodeDependencies,
    TerraformDependencies,
    DependencySummary,
    # Helper functions
    create_success_result,
    create_error_result,
)

# ============================================================================
# PIPELINE CONTRACTS (Dataclasses for iam-* agents)
# ============================================================================
from agents.shared_contracts.pipeline_contracts import (
    # Enums
    Severity,
    IssueType,
    QAStatus,
    # Pipeline request/result
    PipelineRequest,
    PipelineResult,
    # Portfolio contracts
    PerRepoResult,
    PortfolioResult,
    # Analysis contracts
    AnalysisReport,
    # Issue contracts
    IssueSpec,
    # Fix planning contracts
    FixPlan,
    FixStep,
    # Code change contracts
    CodeChange,
    # QA contracts
    TestResult,
    QAVerdict,
    # Documentation contracts
    DocumentationUpdate,
    # Cleanup contracts
    CleanupTask,
    # Index contracts
    IndexEntry,
    # Helper functions
    create_mock_issue,
    create_mock_fix_plan,
)

__all__ = [
    # Tool outputs (MCP/Pydantic)
    "ToolResult",
    "ComplianceResult",
    "SearchResult",
    "FileResult",
    "DependencyResult",
    "Violation",
    "SearchMatch",
    "PythonDependencies",
    "NodeDependencies",
    "TerraformDependencies",
    "DependencySummary",
    "create_success_result",
    "create_error_result",
    # Pipeline contracts (dataclasses)
    "Severity",
    "IssueType",
    "QAStatus",
    "PipelineRequest",
    "PipelineResult",
    "PerRepoResult",
    "PortfolioResult",
    "AnalysisReport",
    "IssueSpec",
    "FixPlan",
    "FixStep",
    "CodeChange",
    "TestResult",
    "QAVerdict",
    "DocumentationUpdate",
    "CleanupTask",
    "IndexEntry",
    "create_mock_issue",
    "create_mock_fix_plan",
]
