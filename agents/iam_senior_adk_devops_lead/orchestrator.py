"""
SWE Pipeline Orchestrator for iam-senior-adk-devops-lead (Foreman)

This module implements the end-to-end Software Engineering pipeline that
coordinates all iam-* specialist agents to analyze, fix, and improve code.

Currently uses local stub functions. Future: real A2A calls to agents.
"""

# Import shared contracts
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add agents directory to path for consistent imports
_agents_dir = str(Path(__file__).parent.parent.parent)
if _agents_dir not in sys.path:
    sys.path.insert(0, _agents_dir)

# Import structured logging (Phase RC2)
# Import GitHub feature flags (Phase GHC)
from agents.config.github_features import (
    can_create_issues_for_repo,
    get_feature_status_summary,
)

# Import repo registry (Phase GH1)
from agents.config.repos import get_registry, get_repo_by_id

# Import GitHub issue adapter (Phase GH3)
from agents.iam_issue.github_issue_adapter import (
    issue_spec_to_github_payload,
    preview_issue_payload,
)
from agents.shared_contracts import (
    AnalysisReport,
    CleanupTask,
    CodeChange,
    DocumentationUpdate,
    FixPlan,
    IndexEntry,
    IssueSpec,
    IssueType,
    PipelineRequest,
    PipelineResult,
    QAStatus,
    QAVerdict,
    Severity,
)

# Import GitHub client (Phase GH2)
from agents.tools.github_client import GitHubClientError, RepoTree, get_client
from agents.utils.logging import (
    get_logger,
    log_agent_step,
    log_github_operation,
    log_pipeline_complete,
    log_pipeline_start,
)

# Import A2A delegation (Phase H - Real A2A Wiring)
from .tools.delegation import delegate_to_specialist

# Create logger for orchestrator (Phase RC2)
logger = get_logger(__name__)


# ============================================================================
# IAM-* AGENT A2A DELEGATION FUNCTIONS (Phase H - Real A2A Wiring)
# ============================================================================


def iam_adk_analyze(repo_hint: str, task: str) -> AnalysisReport:
    """
    Delegate ADK compliance analysis to iam-adk specialist via A2A.

    Phase H: Real A2A call to iam-adk agent using AgentCard contract.
    """
    logger.log_info("a2a_delegation", agent="iam-adk", action="analyze", repo=repo_hint)

    result = delegate_to_specialist(
        specialist="iam-adk",
        skill_id="iam_adk.check_adk_compliance",
        payload={
            "target": repo_hint,
            "focus_rules": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
            "severity_threshold": "LOW",
        },
        context={"task_description": task},
    )

    # Handle delegation result
    if result.get("status") == "failure":
        logger.log_warning("a2a_failed", agent="iam-adk", error=result.get("error"))
        # Return minimal report on failure
        return AnalysisReport(
            repo_path=repo_hint,
            patterns_checked=["ADK compliance check (failed)"],
            violations_found=[],
            compliance_score=0.0,
            recommendations=[f"A2A delegation failed: {result.get('error')}"],
        )

    # Map A2A result to AnalysisReport
    a2a_result = result.get("result", {})
    violations = a2a_result.get("violations", [])

    # Convert A2A violations format to AnalysisReport format
    violations_found = [
        {
            "pattern": v.get("rule", "Unknown"),
            "file": v.get("file", "unknown"),
            "line": v.get("line_number", 0),
            "message": v.get("message", ""),
        }
        for v in violations
    ]

    # Calculate compliance score based on violations
    compliance_status = a2a_result.get("compliance_status", "WARNING")
    compliance_score = (
        1.0
        if compliance_status == "COMPLIANT"
        else (0.5 if compliance_status == "WARNING" else 0.0)
    )

    return AnalysisReport(
        repo_path=repo_hint,
        patterns_checked=[
            "ADK LlmAgent usage (R1)",
            "Agent Engine runtime (R2)",
            "Gateway separation (R3)",
            "CI-only deployments (R4)",
            "Dual memory wiring (R5)",
            "Single doc folder (R6)",
            "SPIFFE ID propagation (R7)",
            "Drift detection (R8)",
        ],
        violations_found=violations_found,
        compliance_score=compliance_score,
        recommendations=[
            f"Risk level: {a2a_result.get('risk_level', 'UNKNOWN')}",
            f"Status: {compliance_status}",
        ],
    )


def iam_issue_create(analysis: AnalysisReport) -> List[IssueSpec]:
    """
    Delegate issue creation to iam-issue specialist via A2A.

    Phase H: Real A2A call to iam-issue agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation",
        agent="iam-issue",
        action="create_issues",
        violations_count=len(analysis.violations_found),
    )

    issues = []

    # Create an issue for each violation via A2A
    for i, violation in enumerate(analysis.violations_found):
        result = delegate_to_specialist(
            specialist="iam-issue",
            skill_id="iam_issue.convert_finding_to_issue",
            payload={
                "finding": {
                    "message": violation.get(
                        "message",
                        f"Violation of {violation.get('pattern', 'unknown')} pattern",
                    ),
                    "severity": "MEDIUM" if i == 0 else "LOW",
                    "file": violation.get("file", "unknown"),
                    "rule": violation.get("pattern", "unknown"),
                    "recommendation": f"Fix {violation.get('pattern', 'unknown')} pattern violation",
                },
                "repo_context": {"repo_name": analysis.repo_path, "branch": "main"},
            },
        )

        if result.get("status") == "failure":
            logger.log_warning(
                "a2a_failed",
                agent="iam-issue",
                violation_index=i,
                error=result.get("error"),
            )
            continue

        # Map A2A result to IssueSpec
        a2a_result = result.get("result", {})
        issue_spec = a2a_result.get("issue_spec", {})

        issue = IssueSpec(
            id=f"ISS-{datetime.now().strftime('%Y%m%d')}-{i:03d}",
            type=IssueType.ADK_VIOLATION,
            severity=Severity.MEDIUM if i == 0 else Severity.LOW,
            title=issue_spec.get(
                "title", f"Pattern violation: {violation.get('pattern', 'unknown')}"
            ),
            description=issue_spec.get(
                "body", f"Found violation in {violation.get('file', 'unknown')}"
            ),
            file_path=violation.get("file"),
            line_start=violation.get("line"),
            pattern_violated=violation.get("pattern"),
            expected_pattern=f"ADK-compliant {violation.get('pattern', '')}",
            tags=issue_spec.get("labels", []),
        )
        issues.append(issue)
        logger.log_info(
            "a2a_result",
            agent="iam-issue",
            action="created",
            issue_id=issue.id,
            title=issue.title,
        )

    return issues


def iam_fix_plan_create(issues: List[IssueSpec], max_fixes: int) -> List[FixPlan]:
    """
    Delegate fix planning to iam-fix-plan specialist via A2A.

    Phase H: Real A2A call to iam-fix-plan agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation",
        agent="iam-fix-plan",
        action="plan_fixes",
        issues_count=len(issues),
        max_fixes=max_fixes,
    )

    plans = []

    # Create fix plans for top priority issues via A2A
    for issue in issues[:max_fixes]:
        if issue.type != IssueType.ADK_VIOLATION:
            continue

        result = delegate_to_specialist(
            specialist="iam-fix-plan",
            skill_id="iam_fix_plan.create_fix_plan",
            payload={
                "issue_spec": {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "severity": (
                        issue.severity.value
                        if hasattr(issue.severity, "value")
                        else str(issue.severity)
                    ),
                    "file_path": issue.file_path,
                    "pattern_violated": issue.pattern_violated,
                    "expected_pattern": issue.expected_pattern,
                },
                "constraints": {"max_duration_minutes": 30, "require_tests": True},
            },
        )

        if result.get("status") == "failure":
            logger.log_warning(
                "a2a_failed",
                agent="iam-fix-plan",
                issue_id=issue.id,
                error=result.get("error"),
            )
            continue

        # Map A2A result to FixPlan
        a2a_result = result.get("result", {})
        fix_plan = a2a_result.get("fix_plan", {})

        # Convert steps from A2A format to internal format
        steps = []
        for i, step in enumerate(fix_plan.get("steps", [])):
            steps.append(
                {
                    "order": i + 1,
                    "action": "execute",
                    "target": issue.file_path or "unknown",
                    "description": step if isinstance(step, str) else str(step),
                    "estimated_risk": fix_plan.get("risk_level", "medium").lower(),
                }
            )

        plan = FixPlan(
            issue_id=issue.id,
            plan_id=f"FP-{issue.id}",
            approach=fix_plan.get("strategy", f"Refactor to fix: {issue.title}"),
            steps=(
                steps
                if steps
                else [
                    {
                        "order": 1,
                        "action": "analyze",
                        "target": issue.file_path or "unknown",
                        "description": "Analyze",
                        "estimated_risk": "low",
                    },
                    {
                        "order": 2,
                        "action": "fix",
                        "target": issue.file_path or "unknown",
                        "description": "Apply fix",
                        "estimated_risk": "medium",
                    },
                    {
                        "order": 3,
                        "action": "test",
                        "target": "tests/",
                        "description": "Verify",
                        "estimated_risk": "low",
                    },
                ]
            ),
            overall_risk=fix_plan.get("risk_level", "medium").lower(),
            requires_human_review=fix_plan.get("risk_level", "MEDIUM")
            in ["HIGH", "CRITICAL"],
            estimated_duration_minutes=(
                float(fix_plan.get("estimated_effort", "15").replace("min", "").strip())
                if fix_plan.get("estimated_effort")
                else 15.0
            ),
        )
        plans.append(plan)
        logger.log_info(
            "a2a_result",
            agent="iam-fix-plan",
            action="created",
            plan_id=plan.plan_id,
            issue_id=issue.id,
        )

    return plans


def iam_fix_impl_execute(plans: List[FixPlan]) -> List[CodeChange]:
    """
    Delegate fix implementation to iam-fix-impl specialist via A2A.

    Phase H: Real A2A call to iam-fix-impl agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation",
        agent="iam-fix-impl",
        action="implement",
        plans_count=len(plans),
    )

    changes = []

    for plan in plans:
        result = delegate_to_specialist(
            specialist="iam-fix-impl",
            skill_id="iam_fix_impl.implement_fix",
            payload={
                "fix_plan": {
                    "plan_id": plan.plan_id,
                    "issue_id": plan.issue_id,
                    "approach": plan.approach,
                    "steps": plan.steps,
                    "risk_level": plan.overall_risk,
                },
                "target_files": [
                    step.get("target") for step in plan.steps if step.get("target")
                ],
            },
        )

        if result.get("status") == "failure":
            logger.log_warning(
                "a2a_delegation_failed",
                agent="iam-fix-impl",
                plan_id=plan.plan_id,
                error=result.get("error"),
            )
            continue

        # Map A2A result to CodeChange
        a2a_result = result.get("result", {})
        impl_result = a2a_result.get("implementation_result", {})

        # Create a CodeChange for each file modified
        files_modified = impl_result.get("files_modified", [])
        target_file = (
            files_modified[0]
            if files_modified
            else (plan.steps[0].get("target") if plan.steps else "unknown.py")
        )

        change = CodeChange(
            plan_id=plan.plan_id,
            file_path=target_file,
            change_type="modify",
            original_content="# Original code (via A2A)",
            new_content=impl_result.get("changes_summary", "# Fixed code (via A2A)"),
            diff_text=f"# Diff generated by iam-fix-impl via A2A\n# Files modified: {', '.join(files_modified)}",
            syntax_valid=impl_result.get("status") == "SUCCESS",
            imports_resolved=impl_result.get("status") == "SUCCESS",
            confidence=0.9 if impl_result.get("status") == "SUCCESS" else 0.5,
        )
        changes.append(change)
        logger.log_info(
            "a2a_result",
            agent="iam-fix-impl",
            action="implemented",
            file_path=change.file_path,
            plan_id=plan.plan_id,
        )

    return changes


def iam_qa_verify(changes: List[CodeChange]) -> List[QAVerdict]:
    """
    Delegate QA verification to iam-qa specialist via A2A.

    Phase H: Real A2A call to iam-qa agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation", agent="iam-qa", action="verify", changes_count=len(changes)
    )

    verdicts = []

    for change in changes:
        # First run smoke tests
        smoke_result = delegate_to_specialist(
            specialist="iam-qa",
            skill_id="iam_qa.run_smoke_tests",
            payload={"target": change.file_path, "test_scope": "implementation"},
        )

        if smoke_result.get("status") == "failure":
            logger.log_warning(
                "a2a_smoke_test_failed",
                agent="iam-qa",
                plan_id=change.plan_id,
                error=smoke_result.get("error"),
            )
            # Create failed verdict
            verdicts.append(
                QAVerdict(
                    change_id=change.plan_id,
                    status=QAStatus.FAILED,
                    tests_run=[
                        {
                            "test_name": "smoke_test",
                            "passed": False,
                            "message": smoke_result.get("error", "A2A error"),
                        }
                    ],
                    tests_passed=0,
                    tests_failed=1,
                    safe_to_apply=False,
                    requires_manual_review=True,
                )
            )
            continue

        # Map smoke test results
        a2a_smoke = smoke_result.get("result", {})
        smoke_data = a2a_smoke.get("smoke_test_results", {})

        # Then get QA verdict
        verdict_result = delegate_to_specialist(
            specialist="iam-qa",
            skill_id="iam_qa.generate_qa_verdict",
            payload={
                "test_results": smoke_data,
                "coverage_analysis": {
                    "file_path": change.file_path,
                    "confidence": change.confidence,
                },
            },
        )

        if verdict_result.get("status") == "failure":
            logger.log_warning(
                "a2a_verdict_failed",
                agent="iam-qa",
                plan_id=change.plan_id,
                error=verdict_result.get("error"),
            )

        # Map A2A results to QAVerdict
        a2a_verdict = verdict_result.get("result", {}).get("verdict", {})

        # Convert A2A decision to QAStatus
        decision = a2a_verdict.get("decision", "CONDITIONAL")
        if decision == "APPROVE":
            status = QAStatus.PASSED
        elif decision == "REJECT":
            status = QAStatus.FAILED
        else:
            status = QAStatus.PARTIAL

        verdict = QAVerdict(
            change_id=change.plan_id,
            status=status,
            tests_run=[
                {
                    "test_name": "smoke_test",
                    "passed": smoke_data.get("status") == "PASS",
                    "message": f"Passed: {smoke_data.get('passed', 0)}",
                    "duration_ms": 50,
                }
            ],
            tests_passed=smoke_data.get("passed", 0),
            tests_failed=smoke_data.get("failed", 0),
            code_coverage_delta=2.5 if status == QAStatus.PASSED else 0.0,
            complexity_delta=-3 if status == QAStatus.PASSED else 0,
            safe_to_apply=decision == "APPROVE",
            requires_manual_review=decision != "APPROVE",
        )
        verdicts.append(verdict)
        logger.log_info(
            "a2a_result",
            agent="iam-qa",
            action="verdict",
            plan_id=change.plan_id,
            status=verdict.status.value,
        )

    return verdicts


def iam_doc_update(
    issues: List[IssueSpec], plans: List[FixPlan], verdicts: List[QAVerdict]
) -> List[DocumentationUpdate]:
    """
    Delegate documentation updates to iam-doc specialist via A2A.

    Phase H: Real A2A call to iam-doc agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation",
        agent="iam-doc",
        action="document",
        issues_count=len(issues),
        plans_count=len(plans),
    )

    docs = []

    # Generate AAR for the pipeline run
    if plans or issues:
        result = delegate_to_specialist(
            specialist="iam-doc",
            skill_id="iam_doc.generate_aar",
            payload={
                "phase_info": {
                    "phase_name": f"SWE Pipeline Run - {datetime.now().strftime('%Y-%m-%d')}",
                    "objectives": [
                        "Analyze ADK compliance",
                        f"Fix {len(plans)} pattern violations",
                        "Document changes",
                    ],
                    "outcomes": {
                        "issues_found": len(issues),
                        "fixes_planned": len(plans),
                        "qa_verdicts": len(verdicts),
                        "qa_passed": sum(
                            1 for v in verdicts if v.status == QAStatus.PASSED
                        ),
                    },
                    "decisions": [
                        {
                            "decision": f"Fixed {p.approach}",
                            "rationale": f"Issue {p.issue_id}",
                        }
                        for p in plans[:3]
                    ],
                    "lessons_learned": [
                        f"Pattern violations found in {len(issues)} locations",
                        f"Fix success rate: {sum(1 for v in verdicts if v.status == QAStatus.PASSED)}/{len(verdicts)}",
                    ],
                }
            },
        )

        if result.get("status") != "failure":
            a2a_result = result.get("result", {})
            aar_doc = a2a_result.get("aar_document", {})

            doc = DocumentationUpdate(
                doc_id=aar_doc.get(
                    "doc_id", f"DOC-{datetime.now().strftime('%Y%m%d')}-AAR"
                ),
                related_to=[p.plan_id for p in plans],
                doc_type="aar",
                file_path=aar_doc.get(
                    "file_path",
                    f"000-docs/{datetime.now().strftime('%Y%m%d')}-AA-REPT-pipeline-run.md",
                ),
                section="## After-Action Report",
                original_text="",
                updated_text=aar_doc.get(
                    "content",
                    f"# Pipeline Run AAR\n\nGenerated via A2A at {datetime.now().isoformat()}",
                ),
                auto_generated=True,
            )
            docs.append(doc)
            logger.log_info(
                "a2a_result", agent="iam-doc", action="created_aar", doc_id=doc.doc_id
            )
        else:
            logger.log_warning(
                "a2a_aar_generation_failed", agent="iam-doc", error=result.get("error")
            )

    return docs


def iam_cleanup_identify(repo_hint: str, issues: List[IssueSpec]) -> List[CleanupTask]:
    """
    Delegate cleanup identification to iam-cleanup specialist via A2A.

    Phase H: Real A2A call to iam-cleanup agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation", agent="iam-cleanup", action="identify", repo=repo_hint
    )

    tasks = []

    # First detect dead code
    dead_code_result = delegate_to_specialist(
        specialist="iam-cleanup",
        skill_id="iam_cleanup.detect_dead_code",
        payload={"scope": repo_hint, "include_dependencies": True},
    )

    if dead_code_result.get("status") == "failure":
        logger.log_warning(
            "a2a_dead_code_detection_failed",
            agent="iam-cleanup",
            error=dead_code_result.get("error"),
        )
    else:
        dead_code = dead_code_result.get("result", {}).get("dead_code_report", {})

        # Generate cleanup tasks from dead code findings
        cleanup_result = delegate_to_specialist(
            specialist="iam-cleanup",
            skill_id="iam_cleanup.generate_cleanup_tasks",
            payload={
                "analysis_results": {
                    "dead_code": dead_code,
                    "issues": [
                        {"id": i.id, "title": i.title, "file": i.file_path}
                        for i in issues[:5]
                    ],
                }
            },
        )

        if cleanup_result.get("status") != "failure":
            a2a_tasks = cleanup_result.get("result", {}).get("cleanup_tasks", [])

            for i, a2a_task in enumerate(a2a_tasks):
                task = CleanupTask(
                    task_id=a2a_task.get(
                        "task_id", f"CLEAN-{datetime.now().strftime('%Y%m%d')}-{i:03d}"
                    ),
                    category=(
                        "dead_code"
                        if "dead" in a2a_task.get("description", "").lower()
                        else "refactor"
                    ),
                    title=a2a_task.get("description", "Cleanup task"),
                    description=a2a_task.get("description", "Generated via A2A"),
                    file_paths=[],  # Would be populated from dead_code analysis
                    estimated_loc_reduction=dead_code.get("total_loc", 0),
                    estimated_complexity_reduction=10,
                    priority=a2a_task.get("priority", "medium").lower(),
                    safe_to_automate=a2a_task.get("safety_level") == "SAFE",
                )
                tasks.append(task)
                logger.log_info(
                    "a2a_result",
                    agent="iam-cleanup",
                    action="found",
                    task_id=task.task_id,
                    title=task.title,
                )
        else:
            logger.log_warning(
                "a2a_task_generation_failed",
                agent="iam-cleanup",
                error=cleanup_result.get("error"),
            )

    return tasks


def iam_index_update(result: PipelineResult) -> List[IndexEntry]:
    """
    Delegate knowledge indexing to iam-index specialist via A2A.

    Phase H: Real A2A call to iam-index agent using AgentCard contract.
    """
    logger.log_info(
        "a2a_delegation",
        agent="iam-index",
        action="index",
        issues_count=len(result.issues),
        plans_count=len(result.plans),
    )

    entries = []

    # Update knowledge base with pipeline results
    update_result = delegate_to_specialist(
        specialist="iam-index",
        skill_id="iam_index.update_knowledge_base",
        payload={
            "updates": [
                {
                    "operation": "add",
                    "document_id": f"pipeline-{result.pipeline_run_id}",
                    "content": {
                        "type": "pipeline_run",
                        "repo": result.request.repo_hint,
                        "task": result.request.task_description,
                        "issues_found": len(result.issues),
                        "issues_fixed": result.issues_fixed,
                        "timestamp": datetime.now().isoformat(),
                        "issues": [
                            {
                                "id": i.id,
                                "title": i.title,
                                "severity": (
                                    i.severity.value
                                    if hasattr(i.severity, "value")
                                    else str(i.severity)
                                ),
                            }
                            for i in result.issues[:10]
                        ],
                        "plans": [
                            {"id": p.plan_id, "approach": p.approach}
                            for p in result.plans[:10]
                        ],
                    },
                }
            ]
        },
    )

    if update_result.get("status") == "failure":
        logger.log_warning(
            "a2a_index_update_failed",
            agent="iam-index",
            error=update_result.get("error"),
        )
    else:
        # Create index entry for tracking
        entry = IndexEntry(
            entry_id=f"IDX-{datetime.now().strftime('%Y%m%d')}-{result.pipeline_run_id[:8]}",
            knowledge_type="pipeline_run",
            title=f"Pipeline run: {result.request.task_description}",
            summary=f"Found {len(result.issues)} issues, fixed {result.issues_fixed}",
            full_content=f"Indexed via A2A to iam-index. Pipeline ID: {result.pipeline_run_id}",
            tags=["pipeline", "issues", result.request.env, "a2a"],
            related_files=[i.file_path for i in result.issues if i.file_path],
            storage_path=f"knowledge/pipelines/{datetime.now().strftime('%Y%m')}/",
            ttl_days=90,
        )
        entries.append(entry)
        logger.log_info(
            "a2a_result", agent="iam-index", action="created", entry_id=entry.entry_id
        )

    # Also index patterns learned if we have plans
    if result.plans:
        pattern_result = delegate_to_specialist(
            specialist="iam-index",
            skill_id="iam_index.update_knowledge_base",
            payload={
                "updates": [
                    {
                        "operation": "add",
                        "document_id": f"patterns-{datetime.now().strftime('%Y%m%d')}",
                        "content": {
                            "type": "patterns_learned",
                            "fixes_applied": len(result.plans),
                            "patterns": [p.approach for p in result.plans],
                        },
                    }
                ]
            },
        )

        if pattern_result.get("status") != "failure":
            pattern_entry = IndexEntry(
                entry_id=f"IDX-{datetime.now().strftime('%Y%m%d')}-PATTERNS",
                knowledge_type="pattern",
                title="ADK patterns applied",
                summary=f"Applied {len(result.plans)} ADK pattern fixes via A2A",
                tags=["adk", "patterns", "fixes", "a2a"],
                storage_path="knowledge/patterns/",
            )
            entries.append(pattern_entry)
            logger.log_info(
                "a2a_result",
                agent="iam-index",
                action="patterns_indexed",
                entry_id=pattern_entry.entry_id,
            )

    return entries


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================


def run_swe_pipeline(request: PipelineRequest) -> PipelineResult:
    """
    Run the complete SWE pipeline orchestrated by iam-senior-adk-devops-lead.

    This coordinates all iam-* agents to analyze, fix, test, and document
    improvements to the target repository.

    Args:
        request: Pipeline request with repo and task details

    Returns:
        PipelineResult with all outputs from the pipeline
    """
    start_time = time.time()

    # Log pipeline start (Phase RC2)
    log_pipeline_start(
        pipeline_run_id=request.pipeline_run_id,
        repo_id=request.repo_id or request.repo_hint,
        task=request.task_description,
        env=request.env,
    )

    # Phase GH1: Resolve repo_id if provided
    if request.repo_id and not request.github_owner:
        repo_config = get_repo_by_id(request.repo_id)
        if repo_config:
            # Populate GitHub fields from registry
            request.github_owner = repo_config.github_owner
            request.github_repo = repo_config.github_repo
            request.github_ref = request.github_ref or repo_config.default_branch

            # Update metadata with repo info
            request.metadata["resolved_from_registry"] = True
            request.metadata["repo_full_name"] = repo_config.full_name
            request.metadata["repo_url"] = repo_config.github_url

            print(f"✓ Resolved repo_id '{request.repo_id}' to {repo_config.full_name}")
        else:
            print(f"⚠️ Warning: repo_id '{request.repo_id}' not found in registry")

    print("\n" + "=" * 60)
    print("SWE PIPELINE ORCHESTRATOR - iam-senior-adk-devops-lead")
    print("=" * 60)
    print(f"Repository: {request.repo_hint}")
    if request.github_owner and request.github_repo:
        print(
            f"GitHub: {request.github_owner}/{request.github_repo} @ {request.github_ref or 'default'}"
        )
    print(f"Task: {request.task_description}")
    print(f"Environment: {request.env}")
    print("=" * 60 + "\n")

    # Phase GH2: Fetch repository from GitHub if applicable
    repo_tree: Optional[RepoTree] = None
    if request.github_owner and request.github_repo:
        try:
            print("🐙 Fetching repository from GitHub...")
            gh_client = get_client()

            # Get registry settings for file filtering
            registry = get_registry()
            settings = registry.settings

            # Fetch repo tree with filtering
            repo_tree = gh_client.get_repo_tree(
                owner=request.github_owner,
                repo=request.github_repo,
                ref=request.github_ref or "main",
                file_patterns=settings.analysis_file_patterns,
                exclude_patterns=settings.analysis_exclude_patterns,
                max_file_size=settings.max_file_size_bytes,
                max_total_size=settings.max_total_size_bytes,
                fetch_content=False,  # Only fetch metadata for now
            )

            print(
                f"✓ Fetched {len(repo_tree.files)} files ({repo_tree.total_size / 1024:.1f}KB total)"
            )

            # Store in metadata for agents to use
            request.metadata["github_tree"] = {
                "file_count": len(repo_tree.files),
                "total_size": repo_tree.total_size,
                "files": [f.path for f in repo_tree.files[:20]],  # First 20 for preview
            }

        except GitHubClientError as e:
            print(f"⚠️ Could not fetch from GitHub: {e}")
            print("   Continuing with local analysis only")

    # Initialize result
    result = PipelineResult(
        request=request,
        pipeline_run_id=request.pipeline_run_id,  # Phase RC2: Correlation ID
        issues=[],
        plans=[],
        implementations=[],
        qa_report=[],
        docs=[],
        cleanup=[],
        index_updates=[],
    )

    try:
        # Step 1: Analysis (iam-adk)
        print("\n📊 STEP 1: ANALYSIS")
        print("-" * 40)
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-adk",
            step="analysis",
            status="started",
        )

        # Pass GitHub tree info to analysis if available
        repo_hint_with_github = request.repo_hint
        if repo_tree:
            repo_hint_with_github = f"{request.github_owner}/{request.github_repo} ({len(repo_tree.files)} files from GitHub)"

        analysis = iam_adk_analyze(repo_hint_with_github, request.task_description)
        print(f"✓ Compliance score: {analysis.compliance_score:.2f}")
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-adk",
            step="analysis",
            status="completed",
            compliance_score=analysis.compliance_score,
            violations_found=len(analysis.violations_found),
        )

        # Step 2: Issue Creation (iam-issue)
        print("\n🔍 STEP 2: ISSUE IDENTIFICATION")
        print("-" * 40)
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-issue",
            step="issue_creation",
            status="started",
        )
        result.issues = iam_issue_create(analysis)
        result.total_issues_found = len(result.issues)
        print(f"✓ Found {result.total_issues_found} issues")
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-issue",
            step="issue_creation",
            status="completed",
            issues_found=result.total_issues_found,
        )

        # Step 2b: GitHub Issue Creation (Phase GHC)
        if result.issues and request.github_owner and request.github_repo:
            print("\n🐙 GITHUB ISSUE HANDLING")
            print("-" * 40)

            mode = request.mode
            repo_id = request.repo_id or f"{request.github_owner}/{request.github_repo}"

            print(f"Mode: {mode}")
            print(f"Repository: {request.github_owner}/{request.github_repo}")

            if mode == "preview":
                # Preview mode (default): Just acknowledge issues found
                print("✓ Preview mode: Issues identified but not created on GitHub")
                print("  Run with --mode=dry-run to see GitHub issue payloads")
                print(
                    "  Run with --mode=create to create issues (requires feature flags)"
                )

            elif mode == "dry-run":
                # Dry-run mode: Show what would be created
                print("🔍 Dry-run mode: Showing GitHub issue payloads (no creation)")
                print()

                for i, issue in enumerate(result.issues, 1):
                    payload = issue_spec_to_github_payload(issue)
                    print(f"Issue {i}/{len(result.issues)}:")
                    print(preview_issue_payload(payload))
                    print()

                print("✓ Dry-run complete. No issues were created.")
                print(
                    "  To actually create issues, use --mode=create with proper feature flags"
                )

            elif mode == "create":
                # Create mode: Actually create issues (with safety checks)
                print("🚀 Create mode: Attempting to create GitHub issues...")

                # Safety check 1: Feature flags
                if not can_create_issues_for_repo(repo_id):
                    print("❌ GitHub issue creation BLOCKED by feature flags")
                    print()
                    status = get_feature_status_summary()
                    print(f"   {status['message']}")
                    if "recommendation" in status:
                        print(f"   💡 {status['recommendation']}")
                    if repo_id:
                        print(
                            f"   ℹ️  Add '{repo_id}' to GITHUB_ISSUE_CREATION_ALLOWED_REPOS"
                        )
                    print()
                    print("✓ Issues identified but not created (blocked by safety)")
                else:
                    # Safety check 2: GitHub token
                    try:
                        gh_client = get_client()
                        if not gh_client.token:
                            print("❌ GitHub token not found")
                            print(
                                "   Set GITHUB_TOKEN environment variable to create issues"
                            )
                            print("✓ Issues identified but not created (no token)")
                        else:
                            # All safety checks passed - create issues
                            print(
                                f"✅ Safety checks passed. Creating {len(result.issues)} issues..."
                            )
                            print()

                            created_count = 0
                            for i, issue in enumerate(result.issues, 1):
                                try:
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="started",
                                        issue_id=issue.id,
                                    )
                                    payload = issue_spec_to_github_payload(issue)
                                    created_issue = gh_client.create_issue(
                                        owner=request.github_owner,
                                        repo=request.github_repo,
                                        payload=payload,
                                    )

                                    print(
                                        f"  ✅ Created issue #{created_issue.number}: {created_issue.title}"
                                    )
                                    print(f"     {created_issue.html_url}")
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="success",
                                        issue_number=created_issue.number,
                                        issue_url=created_issue.html_url,
                                    )

                                    # Store GitHub URL in issue metadata for tracking
                                    issue.tags = issue.tags or []
                                    if created_issue.html_url not in issue.tags:
                                        issue.tags.append(
                                            f"github:{created_issue.html_url}"
                                        )

                                    created_count += 1

                                except GitHubClientError as e:
                                    print(f"  ❌ Failed to create issue {i}: {e}")
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="failed",
                                        error=str(e),
                                    )

                            print()
                            print(
                                f"✓ Created {created_count}/{len(result.issues)} GitHub issues"
                            )

                    except GitHubClientError as e:
                        print(f"❌ GitHub client error: {e}")
                        print("✓ Issues identified but not created (client error)")

        # Step 3: Fix Planning (iam-fix-plan)
        print("\n📝 STEP 3: FIX PLANNING")
        print("-" * 40)
        if result.issues:
            result.plans = iam_fix_plan_create(result.issues, request.max_issues_to_fix)
            print(f"✓ Created {len(result.plans)} fix plans")
        else:
            print("⚠ No issues to fix")

        # Step 4: Implementation (iam-fix-impl)
        print("\n🔧 STEP 4: FIX IMPLEMENTATION")
        print("-" * 40)
        if result.plans:
            result.implementations = iam_fix_impl_execute(result.plans)
            result.issues_fixed = len(result.implementations)
            print(f"✓ Implemented {result.issues_fixed} fixes")
        else:
            print("⚠ No plans to implement")

        # Step 5: QA Verification (iam-qa)
        print("\n✅ STEP 5: QA VERIFICATION")
        print("-" * 40)
        if result.implementations:
            result.qa_report = iam_qa_verify(result.implementations)
            passed = sum(1 for v in result.qa_report if v.status == QAStatus.PASSED)
            print(f"✓ QA passed: {passed}/{len(result.qa_report)}")
        else:
            print("⚠ No implementations to verify")

        # Step 6: Documentation (iam-doc)
        print("\n📚 STEP 6: DOCUMENTATION")
        print("-" * 40)
        result.docs = iam_doc_update(result.issues, result.plans, result.qa_report)
        result.issues_documented = len(result.docs)
        print(f"✓ Created {result.issues_documented} documentation updates")

        # Step 7: Cleanup (iam-cleanup) - Optional
        if request.include_cleanup:
            print("\n🧹 STEP 7: CLEANUP IDENTIFICATION")
            print("-" * 40)
            result.cleanup = iam_cleanup_identify(request.repo_hint, result.issues)
            print(f"✓ Found {len(result.cleanup)} cleanup opportunities")

        # Step 8: Knowledge Indexing (iam-index)
        if request.include_indexing:
            print("\n🗂️ STEP 8: KNOWLEDGE INDEXING")
            print("-" * 40)
            result.index_updates = iam_index_update(result)
            print(f"✓ Created {len(result.index_updates)} index entries")

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        logger.log_error(
            "pipeline_error",
            pipeline_run_id=request.pipeline_run_id,
            error=str(e),
            repo_id=request.repo_id or request.repo_hint,
        )
        import traceback

        traceback.print_exc()

    # Calculate duration
    result.pipeline_duration_seconds = time.time() - start_time

    # Log pipeline completion (Phase RC2)
    log_pipeline_complete(
        pipeline_run_id=request.pipeline_run_id,
        repo_id=request.repo_id or request.repo_hint,
        duration_seconds=result.pipeline_duration_seconds,
        issues_found=result.total_issues_found,
        issues_fixed=result.issues_fixed,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Pipeline Run ID: {request.pipeline_run_id}")
    print(f"Total Issues Found: {result.total_issues_found}")
    print(f"Issues Fixed: {result.issues_fixed}")
    print(f"Issues Documented: {result.issues_documented}")
    print(f"Duration: {result.pipeline_duration_seconds:.2f} seconds")
    print("=" * 60 + "\n")

    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def run_quick_audit(repo_path: str) -> PipelineResult:
    """
    Run a quick ADK audit on a repository.

    Convenience function for common use case.
    """
    request = PipelineRequest(
        repo_hint=repo_path,
        task_description="Audit ADK patterns and compliance",
        env="dev",
        max_issues_to_fix=2,
        include_cleanup=False,
        include_indexing=True,
    )
    return run_swe_pipeline(request)


def run_full_pipeline(repo_path: str, task: str) -> PipelineResult:
    """
    Run the full pipeline with all phases enabled.

    Includes cleanup and comprehensive indexing.
    """
    request = PipelineRequest(
        repo_hint=repo_path,
        task_description=task,
        env="staging",
        max_issues_to_fix=5,
        include_cleanup=True,
        include_indexing=True,
    )
    return run_swe_pipeline(request)


def run_swe_pipeline_for_repo(
    repo_id: str,
    mode: str = "preview",
    task: str = "Audit ADK patterns and compliance",
    env: str = "dev",
) -> PipelineResult:
    """
    Run SWE pipeline for a specific repo by ID from the registry.

    This is a convenience function for PORT1 (multi-repo) that:
    - Looks up repo_id in the registry
    - Checks if repo is locally available
    - Skips external repos with clear logging
    - Runs full pipeline for local repos

    Args:
        repo_id: Repository identifier from config/repos.yaml
        mode: Pipeline mode ("preview", "dry-run", "create")
        task: Task description for the pipeline
        env: Environment ("dev", "staging", "prod")

    Returns:
        PipelineResult with status and metrics
    """
    print(f"\n{'=' * 60}")
    print(f"RUN SWE PIPELINE FOR REPO: {repo_id}")
    print(f"{'=' * 60}")
    print(f"Mode: {mode}")
    print(f"Task: {task}")
    print(f"Environment: {env}")
    print(f"{'=' * 60}\n")

    # Look up repo in registry
    repo_config = get_repo_by_id(repo_id)

    if not repo_config:
        print(f"❌ ERROR: Repository '{repo_id}' not found in registry")
        print("   Check config/repos.yaml for available repo IDs")
        print()

        # Return empty result indicating error
        request = PipelineRequest(
            repo_hint=repo_id,
            repo_id=repo_id,
            task_description=task,
            env=env,
            mode=mode,
            metadata={"error": "repo_not_found"},
        )
        return PipelineResult(
            request=request,
            pipeline_run_id=request.pipeline_run_id,
            issues=[],
            plans=[],
            implementations=[],
            qa_report=[],
            docs=[],
            cleanup=[],
            index_updates=[],
            total_issues_found=0,
            issues_fixed=0,
            issues_documented=0,
            pipeline_duration_seconds=0.0,
        )

    # Check if repo is locally available
    if not repo_config.is_local:
        print(f"⏭️  SKIPPED: Repository '{repo_id}' has no local path")
        print(f"   Local path: {repo_config.local_path}")
        print(f"   GitHub: {repo_config.full_name}")
        print("   To analyze this repo:")
        print("     1. Clone it locally")
        print("     2. Update local_path in config/repos.yaml")
        print()

        # Return result indicating skipped
        request = PipelineRequest(
            repo_hint=repo_config.full_name,
            repo_id=repo_id,
            github_owner=repo_config.github_owner,
            github_repo=repo_config.github_repo,
            task_description=task,
            env=env,
            mode=mode,
            metadata={
                "status": "skipped",
                "reason": "no_local_path",
                "local_path": repo_config.local_path,
            },
        )
        return PipelineResult(
            request=request,
            pipeline_run_id=request.pipeline_run_id,
            issues=[],
            plans=[],
            implementations=[],
            qa_report=[],
            docs=[],
            cleanup=[],
            index_updates=[],
            total_issues_found=0,
            issues_fixed=0,
            issues_documented=0,
            pipeline_duration_seconds=0.0,
        )

    # Repo is local - run the pipeline!
    print(f"✅ Repository '{repo_id}' found and available locally")
    print(f"   Display name: {repo_config.display_name}")
    print(f"   Local path: {repo_config.local_path}")
    print(f"   GitHub: {repo_config.full_name}")
    if repo_config.arv_profile:
        print("   ARV requirements:")
        print(f"     - RAG: {repo_config.arv_profile.requires_rag}")
        print(f"     - IAM Dept: {repo_config.arv_profile.requires_iam_dept}")
        print(f"     - Tests: {repo_config.arv_profile.requires_tests}")
    print()

    # Build request from repo config
    request = PipelineRequest(
        repo_hint=repo_config.local_path,
        repo_id=repo_id,
        github_owner=repo_config.github_owner,
        github_repo=repo_config.github_repo,
        github_ref=repo_config.default_branch,
        task_description=task,
        env=env,
        mode=mode,
        metadata={
            "display_name": repo_config.display_name,
            "tags": repo_config.tags,
            "arv_profile": (
                {
                    "requires_rag": (
                        repo_config.arv_profile.requires_rag
                        if repo_config.arv_profile
                        else False
                    ),
                    "requires_iam_dept": (
                        repo_config.arv_profile.requires_iam_dept
                        if repo_config.arv_profile
                        else False
                    ),
                    "requires_tests": (
                        repo_config.arv_profile.requires_tests
                        if repo_config.arv_profile
                        else False
                    ),
                    "requires_dual_memory": (
                        repo_config.arv_profile.requires_dual_memory
                        if repo_config.arv_profile
                        else False
                    ),
                }
                if repo_config.arv_profile
                else {}
            ),
        },
    )

    # Run the full pipeline
    return run_swe_pipeline(request)


if __name__ == "__main__":
    # Demo: Run a quick audit when executed directly
    print("Running demo pipeline...")
    result = run_quick_audit("/home/user/test-repo")
    print(f"\nDemo complete! Found {result.total_issues_found} issues.")
