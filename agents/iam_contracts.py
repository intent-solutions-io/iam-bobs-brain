"""
Shared Contract Definitions for iam-* Agent Communication

This module defines the structured data models that iam-* agents use
to communicate with each other and with the foreman.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


@dataclass
class IssueSpec:
    """
    Specification for a GitHub issue or internal work item.

    Created by: iam-adk (findings), iam-cleanup (hygiene), foreman (aggregated)
    Consumed by: iam-issue (formatting), iam-fix-plan (planning)
    """
    title: str
    description: str
    component: Literal["agents", "service", "infra", "ci", "docs", "general"]
    severity: Literal["low", "medium", "high", "critical"]
    type: Literal["bug", "tech_debt", "improvement", "task", "violation"]

    # Optional fields
    id: Optional[str] = None
    repro_steps: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    milestone: Optional[str] = None
    notes: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "component": self.component,
            "severity": self.severity,
            "type": self.type,
            "repro_steps": self.repro_steps,
            "acceptance_criteria": self.acceptance_criteria,
            "links": self.links,
            "labels": self.labels,
            "assignees": self.assignees,
            "milestone": self.milestone,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class FixPlan:
    """
    Implementation plan for addressing an issue.

    Created by: iam-fix-plan
    Consumed by: iam-fix-impl, iam-qa, foreman
    """
    summary: str
    impacted_areas: List[str]
    steps: List[str]
    risk_level: Literal["low", "medium", "high"]
    testing_strategy: List[str]

    # Optional fields
    issue_id: Optional[str] = None
    estimated_effort: Optional[str] = None  # e.g., "2 hours", "1 day"
    rollout_notes: str = ""
    dependencies: List[str] = field(default_factory=list)
    rollback_plan: Optional[str] = None
    success_metrics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "issue_id": self.issue_id,
            "summary": self.summary,
            "impacted_areas": self.impacted_areas,
            "steps": self.steps,
            "risk_level": self.risk_level,
            "testing_strategy": self.testing_strategy,
            "estimated_effort": self.estimated_effort,
            "rollout_notes": self.rollout_notes,
            "dependencies": self.dependencies,
            "rollback_plan": self.rollback_plan,
            "success_metrics": self.success_metrics
        }


@dataclass
class QAVerdict:
    """
    Testing and quality assurance verdict for implemented fixes.

    Created by: iam-qa
    Consumed by: iam-doc, foreman, Bob
    """
    status: Literal["pass", "fail", "partial", "blocked", "skipped"]
    notes: str
    test_evidence: List[str]

    # Optional fields
    issue_id: Optional[str] = None
    fix_id: Optional[str] = None
    test_types: List[str] = field(default_factory=list)  # ["unit", "integration", "e2e"]
    coverage_report: Optional[Dict[str, Any]] = None
    performance_impact: Optional[str] = None
    security_review: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "issue_id": self.issue_id,
            "fix_id": self.fix_id,
            "status": self.status,
            "notes": self.notes,
            "test_evidence": self.test_evidence,
            "test_types": self.test_types,
            "coverage_report": self.coverage_report,
            "performance_impact": self.performance_impact,
            "security_review": self.security_review,
            "recommendations": self.recommendations,
            "blocking_issues": self.blocking_issues
        }


@dataclass
class AuditReport:
    """
    Pattern compliance and code quality audit report.

    Created by: iam-adk
    Consumed by: iam-issue, iam-fix-plan, foreman
    """
    summary: str
    violations: List[Dict[str, Any]]  # List of violations with details
    compliance_score: float  # 0.0 to 1.0

    # Optional fields
    scan_id: Optional[str] = None
    scanned_paths: List[str] = field(default_factory=list)
    patterns_checked: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliant_areas: List[str] = field(default_factory=list)
    risk_assessment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan_id": self.scan_id,
            "summary": self.summary,
            "violations": self.violations,
            "compliance_score": self.compliance_score,
            "scanned_paths": self.scanned_paths,
            "patterns_checked": self.patterns_checked,
            "recommendations": self.recommendations,
            "compliant_areas": self.compliant_areas,
            "risk_assessment": self.risk_assessment
        }


@dataclass
class DocumentationUpdate:
    """
    Documentation changes and AAR entries.

    Created by: iam-doc
    Consumed by: foreman, Bob
    """
    type: Literal["aar", "readme", "api_doc", "user_guide", "design_doc"]
    title: str
    content: str
    file_path: str

    # Optional fields
    doc_id: Optional[str] = None
    related_issues: List[str] = field(default_factory=list)
    sections_updated: List[str] = field(default_factory=list)
    review_status: Literal["draft", "review", "approved", "published"] = "draft"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_id": self.doc_id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "file_path": self.file_path,
            "related_issues": self.related_issues,
            "sections_updated": self.sections_updated,
            "review_status": self.review_status,
            "metadata": self.metadata
        }


@dataclass
class CleanupTask:
    """
    Repository hygiene and cleanup task specification.

    Created by: iam-cleanup
    Consumed by: iam-issue, foreman
    """
    type: Literal["dead_code", "unused_deps", "naming", "structure", "duplication"]
    description: str
    affected_files: List[str]
    proposed_action: str

    # Optional fields
    task_id: Optional[str] = None
    priority: Literal["low", "medium", "high"] = "low"
    estimated_impact: Optional[str] = None
    safety_notes: Optional[str] = None
    automated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "type": self.type,
            "description": self.description,
            "affected_files": self.affected_files,
            "proposed_action": self.proposed_action,
            "priority": self.priority,
            "estimated_impact": self.estimated_impact,
            "safety_notes": self.safety_notes,
            "automated": self.automated
        }


@dataclass
class IndexEntry:
    """
    Knowledge base and documentation index entry.

    Created by: iam-index
    Consumed by: all agents for knowledge retrieval
    """
    title: str
    source: str  # File path or URL
    content_type: Literal["code", "doc", "config", "test", "example"]
    summary: str

    # Optional fields
    entry_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    relevance_score: Optional[float] = None
    embeddings: Optional[List[float]] = None  # For vector search

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "source": self.source,
            "content_type": self.content_type,
            "summary": self.summary,
            "tags": self.tags,
            "keywords": self.keywords,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "relevance_score": self.relevance_score,
            "embeddings": self.embeddings
        }


# ============================================================================
# Phase P4: Human-in-the-Loop Approval Contracts
# ============================================================================


from enum import Enum
import uuid


class RiskLevel(Enum):
    """
    Risk classification for actions requiring approval.

    Used by the Human-in-the-Loop pattern to determine whether
    an action requires human approval before execution.

    Classification Guidelines:
    - LOW: Safe, reversible, minimal impact (auto-approve)
    - MEDIUM: Limited scope, recoverable (auto-approve with logging)
    - HIGH: Significant scope, requires review (human approval required)
    - CRITICAL: Production impact, security sensitive (human approval + escalation)
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def requires_approval(cls, level: "RiskLevel") -> bool:
        """Check if risk level requires human approval."""
        return level in [cls.HIGH, cls.CRITICAL]

    @classmethod
    def from_string(cls, value: str) -> "RiskLevel":
        """Convert string to RiskLevel, defaulting to HIGH if unknown."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.HIGH  # Safe default: require approval


class ApprovalStatus(Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    """
    Request for human approval of a high-risk action.

    This is sent to the approval system (e.g., Slack) when an agent
    needs permission to execute a potentially dangerous operation.
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.HIGH
    context: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""  # SPIFFE ID or agent name
    requested_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300  # 5 minutes default
    files_affected: List[str] = field(default_factory=list)
    estimated_impact: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "action": self.action,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "context": self.context,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "timeout_seconds": self.timeout_seconds,
            "files_affected": self.files_affected,
            "estimated_impact": self.estimated_impact,
        }


@dataclass
class ApprovalResponse:
    """
    Response from human approval (or auto-approval).

    Returned after the approval workflow completes, either by
    human action or automatic decision based on risk level.
    """

    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved: bool = False
    reason: str = ""
    approved_by: Optional[str] = None  # Human approver or "system"
    approved_at: Optional[datetime] = None
    conditions: List[str] = field(default_factory=list)  # Conditional approval

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "approved": self.approved,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "conditions": self.conditions,
        }


# Type aliases for clarity
SpecialistOutput = IssueSpec | FixPlan | QAVerdict | AuditReport | DocumentationUpdate | CleanupTask | IndexEntry

# Export all contracts including Phase P4 additions
__all__ = [
    # Existing contracts
    "IssueSpec",
    "FixPlan",
    "QAVerdict",
    "AuditReport",
    "DocumentationUpdate",
    "CleanupTask",
    "IndexEntry",
    "SpecialistOutput",
    # Phase P4: Human-in-the-Loop
    "RiskLevel",
    "ApprovalStatus",
    "ApprovalRequest",
    "ApprovalResponse",
]