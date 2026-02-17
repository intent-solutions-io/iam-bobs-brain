"""
Shared contracts package for Bob's Brain agents.

This package contains:
- agent_identity.py: Canonical agent IDs and alias resolution (252-DR-STND)
- policy_gates.py: Risk tier enforcement and preflight checks (254-DR-STND)
- evidence_bundle.py: Audit trail manifests and artifact hashing (255-DR-STND)
- tool_outputs.py: Pydantic models for MCP tool results
- pipeline_contracts.py: Dataclasses for SWE pipeline agent communication
- (future) a2a_envelopes.py: A2A task/result envelope wrappers

All contracts are designed for:
- Type-safe inter-agent communication
- JSON Schema generation for AgentCard skills
- Validation of inputs/outputs against A2A protocol
- Canonical agent identity management (Phase D)
- Enterprise controls with policy gates (Phase E)
"""

# ============================================================================
# AGENT IDENTITY (Canonical IDs and aliases - 252-DR-STND)
# ============================================================================
from agents.shared_contracts.agent_identity import (
    AGENT_ALIASES,
    # Data
    CANONICAL_AGENTS,
    CANONICAL_TO_DIRECTORY,
    DIRECTORY_TO_CANONICAL,
    AgentDefinition,
    # Types
    AgentTier,
    # Functions
    canonicalize,
    get_definition,
    get_directory,
    get_spiffe_id,
    is_canonical,
    is_valid,
    list_by_tier,
    list_canonical_ids,
    list_specialists,
)

# ============================================================================
# EVIDENCE BUNDLES (Audit trails - 255-DR-STND)
# ============================================================================
from agents.shared_contracts.evidence_bundle import (
    # Types
    ArtifactRecord,
    EvidenceBundle,
    EvidenceBundleManifest,
    ToolCallRecord,
    UnitTestRecord,
    # Functions
    create_evidence_bundle,
)

# ============================================================================
# PIPELINE CONTRACTS (Dataclasses for iam-* agents)
# ============================================================================
from agents.shared_contracts.pipeline_contracts import (
    # Analysis contracts
    AnalysisReport,
    # Cleanup contracts
    CleanupTask,
    # Code change contracts
    CodeChange,
    # Documentation contracts
    DocumentationUpdate,
    # Fix planning contracts
    FixPlan,
    FixStep,
    # Index contracts
    IndexEntry,
    # Issue contracts
    IssueSpec,
    IssueType,
    # Portfolio contracts
    PerRepoResult,
    # Pipeline request/result
    PipelineRequest,
    PipelineResult,
    PortfolioResult,
    QAStatus,
    QAVerdict,
    # Enums
    Severity,
    # QA contracts
    TestResult,
    create_mock_fix_plan,
    # Helper functions
    create_mock_issue,
)

# ============================================================================
# POLICY GATES (Risk tiers and preflight checks - 254-DR-STND)
# ============================================================================
from agents.shared_contracts.policy_gates import (
    # Data
    RISK_TIER_DESCRIPTIONS,
    GateResult,
    PolicyGate,
    # Types
    RiskTier,
    # Functions
    preflight_check,
)

# ============================================================================
# TOOL OUTPUTS (MCP/Pydantic models)
# ============================================================================
from agents.shared_contracts.tool_outputs import (
    # Specific result types
    ComplianceResult,
    DependencyResult,
    DependencySummary,
    FileResult,
    NodeDependencies,
    PythonDependencies,
    SearchMatch,
    SearchResult,
    TerraformDependencies,
    # Base models
    ToolResult,
    # Nested models
    Violation,
    create_error_result,
    # Helper functions
    create_success_result,
)

__all__ = [
    "AGENT_ALIASES",
    "CANONICAL_AGENTS",
    "CANONICAL_TO_DIRECTORY",
    "DIRECTORY_TO_CANONICAL",
    "RISK_TIER_DESCRIPTIONS",
    "AgentDefinition",
    "AgentTier",
    "AnalysisReport",
    "ArtifactRecord",
    "CleanupTask",
    "CodeChange",
    "ComplianceResult",
    "DependencyResult",
    "DependencySummary",
    "DocumentationUpdate",
    "EvidenceBundle",
    "EvidenceBundleManifest",
    "FileResult",
    "FixPlan",
    "FixStep",
    "GateResult",
    "IndexEntry",
    "IssueSpec",
    "IssueType",
    "NodeDependencies",
    "PerRepoResult",
    "PipelineRequest",
    "PipelineResult",
    "PolicyGate",
    "PortfolioResult",
    "PythonDependencies",
    "QAStatus",
    "QAVerdict",
    "RiskTier",
    "SearchMatch",
    "SearchResult",
    "Severity",
    "TerraformDependencies",
    "TestResult",
    "ToolCallRecord",
    "ToolResult",
    "UnitTestRecord",
    "Violation",
    "canonicalize",
    "create_error_result",
    "create_evidence_bundle",
    "create_mock_fix_plan",
    "create_mock_issue",
    "create_success_result",
    "get_definition",
    "get_directory",
    "get_spiffe_id",
    "is_canonical",
    "is_valid",
    "list_by_tier",
    "list_canonical_ids",
    "list_specialists",
    "preflight_check",
]
