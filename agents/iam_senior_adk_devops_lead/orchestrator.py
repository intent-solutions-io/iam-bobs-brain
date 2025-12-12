"""
SWE Pipeline Orchestrator for iam-senior-adk-devops-lead (Foreman)

This module implements the end-to-end Software Engineering pipeline that
coordinates all iam-* specialist agents to analyze, fix, and improve code.

Currently uses local stub functions. Future: real A2A calls to agents.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import shared contracts
import sys
from pathlib import Path

# Add agents directory to path for consistent imports
_agents_dir = str(Path(__file__).parent.parent.parent)
if _agents_dir not in sys.path:
    sys.path.insert(0, _agents_dir)

# Import structured logging (Phase RC2)
from agents.utils.logging import (
    get_logger,
    log_pipeline_start,
    log_pipeline_complete,
    log_agent_step,
    log_github_operation
)

from agents.shared_contracts import (
    PipelineRequest, PipelineResult,
    AnalysisReport, IssueSpec, FixPlan, CodeChange,
    QAVerdict, DocumentationUpdate, CleanupTask, IndexEntry,
    Severity, IssueType, QAStatus,
    create_mock_issue, create_mock_fix_plan
)

# Import repo registry (Phase GH1)
from agents.config.repos import get_repo_by_id, RepoConfig, get_registry

# Import GitHub client (Phase GH2)
from agents.tools.github_client import get_client, GitHubClientError, RepoTree

# Import GitHub issue adapter (Phase GH3)
from agents.iam_issue.github_issue_adapter import issue_spec_to_github_payload, preview_issue_payload

# Import GitHub feature flags (Phase GHC)
from agents.config.github_features import can_create_issues_for_repo, get_feature_status_summary

# Create logger for orchestrator (Phase RC2)
logger = get_logger(__name__)


# ============================================================================
# IAM-* AGENT STUB FUNCTIONS (Future: A2A calls)
# ============================================================================

def iam_adk_analyze(repo_hint: str, task: str) -> AnalysisReport:
    """
    Stub for iam-adk agent analysis.

    Future: A2A call to iam-adk agent.
    """
    print(f"[iam-adk] Analyzing repo: {repo_hint}")
    print(f"[iam-adk] Task: {task}")

    return AnalysisReport(
        repo_path=repo_hint,
        patterns_checked=[
            "ADK LlmAgent usage",
            "Tool wiring patterns",
            "Memory configuration",
            "A2A protocol compliance",
            "Hard Mode rules (R1-R8)"
        ],
        violations_found=[
            {"pattern": "ADK imports", "file": "example.py", "line": 10},
            {"pattern": "Tool profiles", "file": "tools.py", "line": 25}
        ],
        compliance_score=0.75,
        recommendations=[
            "Migrate custom agents to ADK LlmAgent",
            "Consolidate tool profiles",
            "Add drift detection checks"
        ]
    )


def iam_issue_create(analysis: AnalysisReport) -> List[IssueSpec]:
    """
    Stub for iam-issue agent to create issue specs.

    Future: A2A call to iam-issue agent.
    """
    print(f"[iam-issue] Creating issues from {len(analysis.violations_found)} violations")

    issues = []

    # Create issues from violations
    for i, violation in enumerate(analysis.violations_found):
        issue = IssueSpec(
            id=f"ISS-{datetime.now().strftime('%Y%m%d')}-{i:03d}",
            type=IssueType.ADK_VIOLATION,
            severity=Severity.MEDIUM if i == 0 else Severity.LOW,
            title=f"Pattern violation: {violation['pattern']}",
            description=f"Found violation of {violation['pattern']} pattern in {violation['file']}",
            file_path=violation.get("file"),
            line_start=violation.get("line"),
            pattern_violated=violation['pattern'],
            expected_pattern=f"ADK-compliant {violation['pattern']}"
        )
        issues.append(issue)
        print(f"[iam-issue] Created: {issue.id} - {issue.title}")

    # Add a doc issue
    doc_issue = IssueSpec(
        id=f"ISS-{datetime.now().strftime('%Y%m%d')}-DOC",
        type=IssueType.MISSING_DOC,
        severity=Severity.LOW,
        title="Missing pipeline documentation",
        description="No 6767 doc found for current patterns"
    )
    issues.append(doc_issue)

    return issues


def iam_fix_plan_create(issues: List[IssueSpec], max_fixes: int) -> List[FixPlan]:
    """
    Stub for iam-fix-plan agent to create fix plans.

    Future: A2A call to iam-fix-plan agent.
    """
    print(f"[iam-fix-plan] Planning fixes for {len(issues)} issues (max: {max_fixes})")

    plans = []

    # Create fix plans for top priority issues
    for issue in issues[:max_fixes]:
        if issue.type == IssueType.ADK_VIOLATION:
            plan = FixPlan(
                issue_id=issue.id,
                plan_id=f"FP-{issue.id}",
                approach=f"Refactor to fix: {issue.title}",
                steps=[
                    {
                        "order": 1,
                        "action": "analyze",
                        "target": issue.file_path or "unknown",
                        "description": "Analyze current implementation",
                        "estimated_risk": "low"
                    },
                    {
                        "order": 2,
                        "action": "edit",
                        "target": issue.file_path or "unknown",
                        "description": f"Apply {issue.expected_pattern}",
                        "estimated_risk": "medium"
                    },
                    {
                        "order": 3,
                        "action": "test",
                        "target": "tests/",
                        "description": "Verify fix doesn't break tests",
                        "estimated_risk": "low"
                    }
                ],
                overall_risk="medium",
                requires_human_review=True,
                estimated_duration_minutes=15.0
            )
            plans.append(plan)
            print(f"[iam-fix-plan] Created plan: {plan.plan_id} for {issue.id}")

    return plans


def iam_fix_impl_execute(plans: List[FixPlan]) -> List[CodeChange]:
    """
    Stub for iam-fix-impl agent to implement fixes.

    Future: A2A call to iam-fix-impl agent.
    """
    print(f"[iam-fix-impl] Implementing {len(plans)} fix plans")

    changes = []

    for plan in plans:
        # Simulate implementing the fix
        change = CodeChange(
            plan_id=plan.plan_id,
            file_path=plan.steps[0]["target"] if plan.steps else "unknown.py",
            change_type="modify",
            original_content="# Original code with pattern violation\nclass CustomAgent:\n    pass",
            new_content="# Fixed code using ADK pattern\nfrom google.adk.agents import LlmAgent\n\nclass Agent(LlmAgent):\n    pass",
            diff_text="""--- a/agents/example.py
+++ b/agents/example.py
@@ -1,2 +1,4 @@
-# Original code with pattern violation
-class CustomAgent:
+# Fixed code using ADK pattern
+from google.adk.agents import LlmAgent
+
+class Agent(LlmAgent):""",
            syntax_valid=True,
            imports_resolved=True,
            confidence=0.85
        )
        changes.append(change)
        print(f"[iam-fix-impl] Implemented: {change.file_path} for plan {plan.plan_id}")

    return changes


def iam_qa_verify(changes: List[CodeChange]) -> List[QAVerdict]:
    """
    Stub for iam-qa agent to verify fixes.

    Future: A2A call to iam-qa agent.
    """
    print(f"[iam-qa] Verifying {len(changes)} code changes")

    verdicts = []

    for change in changes:
        # Simulate QA verification
        verdict = QAVerdict(
            change_id=change.plan_id,
            status=QAStatus.PASSED if change.confidence > 0.8 else QAStatus.PARTIAL,
            tests_run=[
                {"test_name": "syntax_check", "passed": True, "message": "Syntax valid", "duration_ms": 10},
                {"test_name": "import_check", "passed": True, "message": "Imports resolved", "duration_ms": 15},
                {"test_name": "pattern_check", "passed": True, "message": "ADK pattern applied", "duration_ms": 20}
            ],
            tests_passed=3,
            tests_failed=0,
            code_coverage_delta=2.5,  # Improved coverage
            complexity_delta=-3,  # Reduced complexity
            safe_to_apply=change.confidence > 0.8,
            requires_manual_review=change.confidence <= 0.8
        )
        verdicts.append(verdict)
        print(f"[iam-qa] Verdict for {change.plan_id}: {verdict.status.value}")

    return verdicts


def iam_doc_update(issues: List[IssueSpec], plans: List[FixPlan], verdicts: List[QAVerdict]) -> List[DocumentationUpdate]:
    """
    Stub for iam-doc agent to update documentation.

    Future: A2A call to iam-doc agent.
    """
    print(f"[iam-doc] Documenting {len(issues)} issues and {len(plans)} fixes")

    docs = []

    # Document the fixes
    if plans:
        doc = DocumentationUpdate(
            doc_id=f"DOC-{datetime.now().strftime('%Y%m%d')}-FIXES",
            related_to=[p.plan_id for p in plans],
            doc_type="changelog",
            file_path="CHANGELOG.md",
            section="## Recent Fixes",
            original_text="",
            updated_text=f"""## Recent Fixes - {datetime.now().strftime('%Y-%m-%d')}

### ADK Pattern Compliance
- Fixed {len(plans)} pattern violations
- Migrated custom agents to ADK LlmAgent
- Improved compliance score to 0.85

### Changes
{chr(10).join([f'- {p.plan_id}: {p.approach}' for p in plans])}
""",
            auto_generated=True
        )
        docs.append(doc)
        print(f"[iam-doc] Created: {doc.doc_id}")

    # Document new patterns learned
    if issues:
        pattern_doc = DocumentationUpdate(
            doc_id=f"DOC-{datetime.now().strftime('%Y%m%d')}-PATTERNS",
            related_to=[i.id for i in issues[:2]],
            doc_type="readme",
            file_path="000-docs/patterns-learned.md",
            updated_text=f"""# Patterns Learned

## Common Issues
{chr(10).join([f'- {i.title}: {i.description}' for i in issues[:3]])}

## Recommended Patterns
- Always use ADK LlmAgent for agents
- Centralize tool profiles
- Implement drift detection
""",
            auto_generated=True
        )
        docs.append(pattern_doc)

    return docs


def iam_cleanup_identify(repo_hint: str, issues: List[IssueSpec]) -> List[CleanupTask]:
    """
    Stub for iam-cleanup agent to identify cleanup tasks.

    Future: A2A call to iam-cleanup agent.
    """
    print(f"[iam-cleanup] Identifying cleanup opportunities in {repo_hint}")

    tasks = []

    # Simulate finding cleanup tasks
    task = CleanupTask(
        task_id=f"CLEAN-{datetime.now().strftime('%Y%m%d')}-001",
        category="deprecated",
        title="Remove deprecated agent patterns",
        description="Found old agent implementations that can be removed after ADK migration",
        file_paths=["agents/legacy/", "agents/old_tools.py"],
        estimated_loc_reduction=500,
        estimated_complexity_reduction=20,
        priority="medium",
        safe_to_automate=False
    )
    tasks.append(task)
    print(f"[iam-cleanup] Found: {task.task_id} - {task.title}")

    return tasks


def iam_index_update(result: PipelineResult) -> List[IndexEntry]:
    """
    Stub for iam-index agent to update knowledge index.

    Future: A2A call to iam-index agent.
    """
    print(f"[iam-index] Indexing {len(result.issues)} issues and {len(result.plans)} fixes")

    entries = []

    # Index the issues found
    if result.issues:
        entry = IndexEntry(
            entry_id=f"IDX-{datetime.now().strftime('%Y%m%d')}-ISSUES",
            knowledge_type="issue",
            title=f"Pipeline run: {result.request.task_description}",
            summary=f"Found {len(result.issues)} issues, fixed {result.issues_fixed}",
            full_content=f"""Pipeline Results
Repository: {result.request.repo_hint}
Task: {result.request.task_description}
Issues Found: {len(result.issues)}
Issues Fixed: {result.issues_fixed}

Top Issues:
{chr(10).join([f'- {i.id}: {i.title}' for i in result.issues[:5]])}
""",
            tags=["pipeline", "issues", result.request.env],
            related_files=[i.file_path for i in result.issues if i.file_path],
            storage_path=f"knowledge/pipelines/{datetime.now().strftime('%Y%m')}/",
            ttl_days=90
        )
        entries.append(entry)
        print(f"[iam-index] Created index: {entry.entry_id}")

    # Index patterns learned
    if result.plans:
        pattern_entry = IndexEntry(
            entry_id=f"IDX-{datetime.now().strftime('%Y%m%d')}-PATTERNS",
            knowledge_type="pattern",
            title="ADK patterns applied",
            summary=f"Applied {len(result.plans)} ADK pattern fixes",
            tags=["adk", "patterns", "fixes"],
            storage_path="knowledge/patterns/"
        )
        entries.append(pattern_entry)

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
        env=request.env
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
            request.metadata['resolved_from_registry'] = True
            request.metadata['repo_full_name'] = repo_config.full_name
            request.metadata['repo_url'] = repo_config.github_url

            print(f"✓ Resolved repo_id '{request.repo_id}' to {repo_config.full_name}")
        else:
            print(f"⚠️ Warning: repo_id '{request.repo_id}' not found in registry")

    print("\n" + "=" * 60)
    print("SWE PIPELINE ORCHESTRATOR - iam-senior-adk-devops-lead")
    print("=" * 60)
    print(f"Repository: {request.repo_hint}")
    if request.github_owner and request.github_repo:
        print(f"GitHub: {request.github_owner}/{request.github_repo} @ {request.github_ref or 'default'}")
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
                fetch_content=False  # Only fetch metadata for now
            )

            print(f"✓ Fetched {len(repo_tree.files)} files ({repo_tree.total_size / 1024:.1f}KB total)")

            # Store in metadata for agents to use
            request.metadata['github_tree'] = {
                'file_count': len(repo_tree.files),
                'total_size': repo_tree.total_size,
                'files': [f.path for f in repo_tree.files[:20]]  # First 20 for preview
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
        index_updates=[]
    )

    try:
        # Step 1: Analysis (iam-adk)
        print("\n📊 STEP 1: ANALYSIS")
        print("-" * 40)
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-adk",
            step="analysis",
            status="started"
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
            violations_found=len(analysis.violations_found)
        )

        # Step 2: Issue Creation (iam-issue)
        print("\n🔍 STEP 2: ISSUE IDENTIFICATION")
        print("-" * 40)
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-issue",
            step="issue_creation",
            status="started"
        )
        result.issues = iam_issue_create(analysis)
        result.total_issues_found = len(result.issues)
        print(f"✓ Found {result.total_issues_found} issues")
        log_agent_step(
            pipeline_run_id=request.pipeline_run_id,
            agent="iam-issue",
            step="issue_creation",
            status="completed",
            issues_found=result.total_issues_found
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
                print(f"  Run with --mode=dry-run to see GitHub issue payloads")
                print(f"  Run with --mode=create to create issues (requires feature flags)")

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
                print("  To actually create issues, use --mode=create with proper feature flags")

            elif mode == "create":
                # Create mode: Actually create issues (with safety checks)
                print("🚀 Create mode: Attempting to create GitHub issues...")

                # Safety check 1: Feature flags
                if not can_create_issues_for_repo(repo_id):
                    print("❌ GitHub issue creation BLOCKED by feature flags")
                    print()
                    status = get_feature_status_summary()
                    print(f"   {status['message']}")
                    if 'recommendation' in status:
                        print(f"   💡 {status['recommendation']}")
                    if repo_id:
                        print(f"   ℹ️  Add '{repo_id}' to GITHUB_ISSUE_CREATION_ALLOWED_REPOS")
                    print()
                    print("✓ Issues identified but not created (blocked by safety)")
                else:
                    # Safety check 2: GitHub token
                    try:
                        gh_client = get_client()
                        if not gh_client.token:
                            print("❌ GitHub token not found")
                            print("   Set GITHUB_TOKEN environment variable to create issues")
                            print("✓ Issues identified but not created (no token)")
                        else:
                            # All safety checks passed - create issues
                            print(f"✅ Safety checks passed. Creating {len(result.issues)} issues...")
                            print()

                            created_count = 0
                            for i, issue in enumerate(result.issues, 1):
                                try:
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="started",
                                        issue_id=issue.id
                                    )
                                    payload = issue_spec_to_github_payload(issue)
                                    created_issue = gh_client.create_issue(
                                        owner=request.github_owner,
                                        repo=request.github_repo,
                                        payload=payload
                                    )

                                    print(f"  ✅ Created issue #{created_issue.number}: {created_issue.title}")
                                    print(f"     {created_issue.html_url}")
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="success",
                                        issue_number=created_issue.number,
                                        issue_url=created_issue.html_url
                                    )

                                    # Store GitHub URL in issue metadata for tracking
                                    issue.tags = issue.tags or []
                                    if created_issue.html_url not in issue.tags:
                                        issue.tags.append(f"github:{created_issue.html_url}")

                                    created_count += 1

                                except GitHubClientError as e:
                                    print(f"  ❌ Failed to create issue {i}: {e}")
                                    log_github_operation(
                                        pipeline_run_id=request.pipeline_run_id,
                                        operation="create_issue",
                                        repo=f"{request.github_owner}/{request.github_repo}",
                                        status="failed",
                                        error=str(e)
                                    )

                            print()
                            print(f"✓ Created {created_count}/{len(result.issues)} GitHub issues")

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
            repo_id=request.repo_id or request.repo_hint
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
        issues_fixed=result.issues_fixed
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
        include_indexing=True
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
        include_indexing=True
    )
    return run_swe_pipeline(request)


def run_swe_pipeline_for_repo(
    repo_id: str,
    mode: str = "preview",
    task: str = "Audit ADK patterns and compliance",
    env: str = "dev"
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
        print(f"   Check config/repos.yaml for available repo IDs")
        print()

        # Return empty result indicating error
        request = PipelineRequest(
            repo_hint=repo_id,
            repo_id=repo_id,
            task_description=task,
            env=env,
            mode=mode,
            metadata={"error": "repo_not_found"}
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
            pipeline_duration_seconds=0.0
        )

    # Check if repo is locally available
    if not repo_config.is_local:
        print(f"⏭️  SKIPPED: Repository '{repo_id}' has no local path")
        print(f"   Local path: {repo_config.local_path}")
        print(f"   GitHub: {repo_config.full_name}")
        print(f"   To analyze this repo:")
        print(f"     1. Clone it locally")
        print(f"     2. Update local_path in config/repos.yaml")
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
                "local_path": repo_config.local_path
            }
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
            pipeline_duration_seconds=0.0
        )

    # Repo is local - run the pipeline!
    print(f"✅ Repository '{repo_id}' found and available locally")
    print(f"   Display name: {repo_config.display_name}")
    print(f"   Local path: {repo_config.local_path}")
    print(f"   GitHub: {repo_config.full_name}")
    if repo_config.arv_profile:
        print(f"   ARV requirements:")
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
            "arv_profile": {
                "requires_rag": repo_config.arv_profile.requires_rag if repo_config.arv_profile else False,
                "requires_iam_dept": repo_config.arv_profile.requires_iam_dept if repo_config.arv_profile else False,
                "requires_tests": repo_config.arv_profile.requires_tests if repo_config.arv_profile else False,
                "requires_dual_memory": repo_config.arv_profile.requires_dual_memory if repo_config.arv_profile else False
            } if repo_config.arv_profile else {}
        }
    )

    # Run the full pipeline
    return run_swe_pipeline(request)


if __name__ == "__main__":
    # Demo: Run a quick audit when executed directly
    print("Running demo pipeline...")
    result = run_quick_audit("/home/user/test-repo")
    print(f"\nDemo complete! Found {result.total_issues_found} issues.")