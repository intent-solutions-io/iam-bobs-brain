"""
Shared Contract Objects for IAM Department SWE Pipeline

This module defines the data contracts passed between iam-* agents
in the SWE pipeline orchestrated by iam-senior-adk-devops-lead.

All contracts are serializable dataclasses with clear type annotations.

Validation Strategy:
- These contracts define the data structures for internal agent communication
- AgentCard JSON schemas (in .well-known/agent-card.json) define the A2A protocol interface
- Two-layer validation ensures contract compliance:
  1. Static validation (scripts/check_a2a_contracts.py):
     - Validates AgentCard structure before runtime
     - Ensures skill schemas match these contract types
     - Runs in CI/CD for fast feedback
  2. Runtime validation (a2a-inspector web UI):
     - Validates actual agent behavior and protocol compliance
     - Tests task envelope handling matches AgentCard specifications
     - Optional for dev/test, used for debugging

See: tools/a2a-inspector/README.md for validation strategy details

TODO (A2A-1/2/3): Add A2ATaskEnvelope and A2AResultEnvelope wrappers
- When implemented, these will wrap the contracts below for A2A protocol messages
- Validation helpers will check envelopes against AgentCard schemas
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Types of issues that can be detected."""
    ADK_VIOLATION = "adk_violation"
    PATTERN_DRIFT = "pattern_drift"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TECH_DEBT = "tech_debt"
    MISSING_DOC = "missing_doc"
    CONFIG_ERROR = "config_error"


class QAStatus(Enum):
    """QA verdict outcomes."""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


# ============================================================================
# PIPELINE REQUEST AND RESULT
# ============================================================================

@dataclass
class PipelineRequest:
    """
    Request to run the SWE pipeline on a target repository.

    This is the entry point for the foreman's orchestration.
    """
    repo_hint: str  # Path or identifier for the target repo (local path or fallback)
    task_description: str  # High-level task (e.g., "audit ADK patterns")

    # Correlation ID for tracing this pipeline run (Phase RC2)
    pipeline_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    env: Literal["dev", "staging", "prod"] = "dev"
    max_issues_to_fix: int = 2  # How many issues to attempt fixing
    include_cleanup: bool = False  # Whether to run cleanup phase
    include_indexing: bool = True  # Whether to update knowledge index

    # GitHub integration (Phase GH1+)
    repo_id: Optional[str] = None  # Registry ID for GitHub repos (e.g., "bobs-brain")
    github_owner: Optional[str] = None  # Resolved from registry or explicit
    github_repo: Optional[str] = None  # Resolved from registry or explicit
    github_ref: Optional[str] = None  # Branch/tag/commit (defaults to default_branch)

    # GitHub issue creation mode (Phase GHC)
    mode: Literal["preview", "dry-run", "create"] = "preview"
    # - "preview": No issue creation (safe default)
    # - "dry-run": Log what would be created but don't create
    # - "create": Actually create issues (requires feature flags + allowlist)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """
    Aggregated result from running the complete SWE pipeline.

    Contains outputs from all iam-* agents involved.
    """
    request: PipelineRequest
    pipeline_run_id: str  # Correlation ID (copied from request for tracing)
    issues: List["IssueSpec"]
    plans: List["FixPlan"]
    implementations: List["CodeChange"]
    qa_report: List["QAVerdict"]
    docs: List["DocumentationUpdate"]
    cleanup: List["CleanupTask"]
    index_updates: List["IndexEntry"]

    # Summary metrics
    total_issues_found: int = 0
    issues_fixed: int = 0
    issues_documented: int = 0
    pipeline_duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# PORTFOLIO CONTRACTS (PHASE PORT2)
# ============================================================================

@dataclass
class PerRepoResult:
    """
    Results for a single repository in a portfolio-wide SWE run.

    Used by portfolio orchestrator to track results per repo.
    """
    repo_id: str
    display_name: str
    status: Literal["completed", "skipped", "error"]
    pipeline_result: Optional[PipelineResult]
    duration_seconds: float
    error_message: Optional[str] = None

    @property
    def issues_found(self) -> int:
        """Quick access to issue count."""
        return self.pipeline_result.total_issues_found if self.pipeline_result else 0

    @property
    def issues_fixed(self) -> int:
        """Quick access to fixes count."""
        return self.pipeline_result.issues_fixed if self.pipeline_result else 0


@dataclass
class PortfolioResult:
    """
    Aggregated results from portfolio-wide SWE pipeline run.

    Contains results for all repositories analyzed in a single portfolio sweep.
    """
    portfolio_run_id: str  # UUID for this portfolio run
    repos: List[PerRepoResult]

    # Aggregated metrics
    total_repos_analyzed: int = 0
    total_repos_skipped: int = 0
    total_repos_errored: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0

    # GitHub issue creation (LIVE3B/LIVE3C-GITHUB-ISSUES)
    issues_planned: int = 0
    issues_created: int = 0

    # Issue breakdown
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)

    # Repo rankings
    repos_by_issue_count: List[tuple[str, int]] = field(default_factory=list)
    repos_by_compliance_score: List[tuple[str, float]] = field(default_factory=list)

    # Timing
    portfolio_duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# IAM-ADK: ANALYSIS CONTRACTS
# ============================================================================

@dataclass
class AnalysisReport:
    """Output from iam-adk agent's analysis phase."""
    repo_path: str
    patterns_checked: List[str]
    violations_found: List[Dict[str, Any]]
    compliance_score: float  # 0.0 to 1.0
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# IAM-ISSUE: ISSUE MANAGEMENT CONTRACTS
# ============================================================================

@dataclass
class IssueSpec:
    """
    Structured issue specification created by iam-issue agent.

    Represents a single issue found during analysis.
    """
    id: str  # Unique identifier
    type: IssueType
    severity: Severity
    title: str
    description: str

    # Location information
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    # Context
    pattern_violated: Optional[str] = None
    expected_pattern: Optional[str] = None

    # Metadata
    detected_by: str = "iam-adk"
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


# ============================================================================
# IAM-FIX-PLAN: PLANNING CONTRACTS
# ============================================================================

@dataclass
class FixStep:
    """Single step in a fix plan."""
    order: int
    action: str  # e.g., "edit", "create", "delete", "move"
    target: str  # File or resource
    description: str
    estimated_risk: Literal["low", "medium", "high"]


@dataclass
class FixPlan:
    """
    Fix plan created by iam-fix-plan agent for an issue.

    Describes how to resolve the issue step by step.
    """
    issue_id: str  # References IssueSpec.id
    plan_id: str

    # Plan details
    approach: str  # High-level approach description
    steps: List[FixStep]

    # Risk assessment
    overall_risk: Literal["low", "medium", "high"]
    requires_human_review: bool = False

    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other plan IDs
    conflicts_with: List[str] = field(default_factory=list)

    # Metadata
    created_by: str = "iam-fix-plan"
    estimated_duration_minutes: float = 0.0


# ============================================================================
# IAM-FIX-IMPL: IMPLEMENTATION CONTRACTS
# ============================================================================

@dataclass
class CodeChange:
    """
    Code change proposed by iam-fix-impl agent.

    Represents actual code modifications to implement a fix plan.
    """
    plan_id: str  # References FixPlan.plan_id
    file_path: str

    # Change details
    change_type: Literal["create", "modify", "delete"]
    original_content: Optional[str] = None  # For modify/delete
    new_content: Optional[str] = None  # For create/modify
    diff_text: Optional[str] = None  # Unified diff format

    # Validation
    syntax_valid: bool = True
    imports_resolved: bool = True

    # Metadata
    implemented_by: str = "iam-fix-impl"
    confidence: float = 0.0  # 0.0 to 1.0


# ============================================================================
# IAM-QA: QUALITY ASSURANCE CONTRACTS
# ============================================================================

@dataclass
class TestResult:
    """Result of a single test."""
    test_name: str
    passed: bool
    message: str
    duration_ms: float = 0.0


@dataclass
class QAVerdict:
    """
    QA verdict from iam-qa agent on implemented fixes.

    Determines if changes are safe to apply.
    """
    change_id: str  # References CodeChange or plan_id
    status: QAStatus

    # Test results
    tests_run: List[TestResult]
    tests_passed: int = 0
    tests_failed: int = 0

    # Quality metrics
    code_coverage_delta: float = 0.0  # Change in coverage
    complexity_delta: int = 0  # Change in cyclomatic complexity

    # Verdict
    safe_to_apply: bool = False
    requires_manual_review: bool = True
    blocking_issues: List[str] = field(default_factory=list)

    # Metadata
    verified_by: str = "iam-qa"


# ============================================================================
# IAM-DOC: DOCUMENTATION CONTRACTS
# ============================================================================

@dataclass
class DocumentationUpdate:
    """
    Documentation update proposed by iam-doc agent.

    Updates to docs based on fixes and changes.
    """
    doc_id: str
    related_to: List[str]  # Issue/plan/change IDs

    # Documentation details
    doc_type: Literal["api", "readme", "changelog", "comment", "docstring"]
    file_path: str

    # Content (required field)
    updated_text: str

    # Optional content fields
    section: Optional[str] = None  # Section within document
    original_text: Optional[str] = None

    # Metadata
    auto_generated: bool = True
    created_by: str = "iam-doc"


# ============================================================================
# IAM-CLEANUP: TECH DEBT CONTRACTS
# ============================================================================

@dataclass
class CleanupTask:
    """
    Cleanup task identified by iam-cleanup agent.

    Tech debt and cleanup opportunities.
    """
    task_id: str
    category: Literal["dead_code", "unused_deps", "duplicate", "deprecated", "refactor"]

    # Task details
    title: str
    description: str
    file_paths: List[str]

    # Impact
    estimated_loc_reduction: int = 0
    estimated_complexity_reduction: int = 0

    # Priority
    priority: Literal["low", "medium", "high"] = "low"
    safe_to_automate: bool = False

    # Metadata
    identified_by: str = "iam-cleanup"


# ============================================================================
# IAM-INDEX: KNOWLEDGE INDEXING CONTRACTS
# ============================================================================

@dataclass
class IndexEntry:
    """
    Knowledge index entry created by iam-index agent.

    Updates to knowledge base from pipeline results.
    """
    entry_id: str
    knowledge_type: Literal["pattern", "issue", "fix", "learning", "decision"]

    # Content
    title: str
    summary: str
    full_content: Optional[str] = None

    # Categorization
    tags: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)

    # Storage hint
    storage_path: str = "knowledge/general/"  # Where to store in knowledge hub

    # Metadata
    indexed_by: str = "iam-index"
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_days: Optional[int] = None  # Time to live


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_mock_issue(issue_type: IssueType = IssueType.ADK_VIOLATION) -> IssueSpec:
    """Create a mock issue for testing."""
    return IssueSpec(
        id=f"issue-{datetime.now().timestamp()}",
        type=issue_type,
        severity=Severity.MEDIUM,
        title="Mock ADK pattern violation",
        description="This is a mock issue for testing the pipeline",
        file_path="agents/example.py",
        line_start=10,
        line_end=15,
        pattern_violated="ADK LlmAgent pattern",
        expected_pattern="Use google.adk.agents.LlmAgent"
    )


def create_mock_fix_plan(issue_id: str) -> FixPlan:
    """Create a mock fix plan for testing."""
    return FixPlan(
        issue_id=issue_id,
        plan_id=f"plan-{datetime.now().timestamp()}",
        approach="Replace custom agent with ADK LlmAgent",
        steps=[
            FixStep(
                order=1,
                action="edit",
                target="agents/example.py",
                description="Import ADK LlmAgent",
                estimated_risk="low"
            ),
            FixStep(
                order=2,
                action="edit",
                target="agents/example.py",
                description="Refactor agent class to use LlmAgent",
                estimated_risk="medium"
            )
        ],
        overall_risk="medium",
        requires_human_review=True
    )