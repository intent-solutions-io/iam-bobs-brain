"""
Custom Tools Module

This module aggregates custom tools from various agent implementations.
It provides a central import point while maintaining backward compatibility.
"""

from typing import List, Any
import logging

logger = logging.getLogger(__name__)


def get_adk_docs_tools() -> List[Any]:
    """
    Get ADK documentation tools from Bob's implementation.

    Returns:
        List of ADK documentation tools
    """
    try:
        from agents.bob.tools.adk_tools import (
            search_adk_docs,
            get_adk_api_reference,
            list_adk_documentation,
        )
        return [search_adk_docs, get_adk_api_reference, list_adk_documentation]
    except ImportError as e:
        logger.warning(f"Could not import ADK docs tools: {e}")
        return []


def get_vertex_search_tools() -> List[Any]:
    """
    Get Vertex AI Search tools from Bob's implementation.

    Returns:
        List of Vertex Search tools
    """
    try:
        from agents.bob.tools.vertex_search_tool import (
            search_vertex_ai,
            get_vertex_search_status,
        )
        return [search_vertex_ai, get_vertex_search_status]
    except ImportError as e:
        logger.warning(f"Could not import Vertex Search tools: {e}")
        return []


def get_analysis_tools() -> List[Any]:
    """
    Get code analysis tools from iam-adk implementation.

    Returns:
        List of analysis tools
    """
    try:
        from agents.iam_adk.tools.analysis_tools import (
            analyze_agent_code,
            validate_adk_pattern,
            check_a2a_compliance,
        )
        return [analyze_agent_code, validate_adk_pattern, check_a2a_compliance]
    except ImportError as e:
        logger.warning(f"Could not import analysis tools: {e}")
        return []


def get_issue_management_tools() -> List[Any]:
    """
    Get issue management tools from iam-issue implementation.

    Returns:
        List of issue management tools
    """
    try:
        from agents.iam_issue.tools.formatting_tools import (
            create_issue_spec,
            analyze_problem,
            categorize_issue,
            estimate_severity,
            suggest_labels,
            format_github_issue,
        )
        return [
            create_issue_spec,
            analyze_problem,
            categorize_issue,
            estimate_severity,
            suggest_labels,
            format_github_issue,
        ]
    except ImportError as e:
        logger.warning(f"Could not import issue management tools: {e}")
        return []


def get_planning_tools() -> List[Any]:
    """
    Get planning tools from iam-fix-plan implementation.

    Returns:
        List of planning tools
    """
    try:
        from agents.iam_fix_plan.tools.planning_tools import (
            create_fix_plan,
            analyze_dependencies,
            estimate_effort,
            identify_risks,
            suggest_alternatives,
            validate_approach,
        )
        return [
            create_fix_plan,
            analyze_dependencies,
            estimate_effort,
            identify_risks,
            suggest_alternatives,
            validate_approach,
        ]
    except ImportError as e:
        logger.warning(f"Could not import planning tools: {e}")
        return []


def get_implementation_tools() -> List[Any]:
    """
    Get implementation tools from iam-fix-impl.

    Returns:
        List of implementation tools
    """
    try:
        from agents.iam_fix_impl.tools.implementation_tools import (
            implement_fix,
            generate_code,
            apply_patch,
            refactor_code,
            add_tests,
            update_documentation,
        )
        return [
            implement_fix,
            generate_code,
            apply_patch,
            refactor_code,
            add_tests,
            update_documentation,
        ]
    except ImportError as e:
        logger.warning(f"Could not import implementation tools: {e}")
        return []


def get_qa_tools() -> List[Any]:
    """
    Get QA tools from iam-qa implementation.

    Returns:
        List of QA tools
    """
    try:
        from agents.iam_qa.tools.qa_tools import (
            run_tests,
            validate_fix,
            check_regression,
            verify_requirements,
            generate_test_report,
            suggest_test_cases,
        )
        return [
            run_tests,
            validate_fix,
            check_regression,
            verify_requirements,
            generate_test_report,
            suggest_test_cases,
        ]
    except ImportError as e:
        logger.warning(f"Could not import QA tools: {e}")
        return []


def get_documentation_tools() -> List[Any]:
    """
    Get documentation tools from iam-doc implementation.

    Returns:
        List of documentation tools
    """
    try:
        from agents.iam_doc.tools.documentation_tools import (
            create_documentation,
            update_readme,
            generate_api_docs,
            create_runbook,
            update_changelog,
            format_markdown,
        )
        return [
            create_documentation,
            update_readme,
            generate_api_docs,
            create_runbook,
            update_changelog,
            format_markdown,
        ]
    except ImportError as e:
        logger.warning(f"Could not import documentation tools: {e}")
        return []


def get_cleanup_tools() -> List[Any]:
    """
    Get cleanup tools from iam-cleanup implementation.

    Returns:
        List of cleanup tools
    """
    try:
        from agents.iam_cleanup.tools.cleanup_tools import (
            identify_tech_debt,
            remove_dead_code,
            optimize_imports,
            standardize_formatting,
            update_dependencies,
            archive_old_files,
        )
        return [
            identify_tech_debt,
            remove_dead_code,
            optimize_imports,
            standardize_formatting,
            update_dependencies,
            archive_old_files,
        ]
    except ImportError as e:
        logger.warning(f"Could not import cleanup tools: {e}")
        return []


def get_indexing_tools() -> List[Any]:
    """
    Get indexing tools from iam-index implementation.

    Returns:
        List of indexing tools
    """
    try:
        from agents.iam_index.tools.indexing_tools import (
            index_adk_docs,
            index_project_docs,
            query_knowledge_base,
            sync_vertex_search,
            generate_index_entry,
            analyze_knowledge_gaps,
        )
        return [
            index_adk_docs,
            index_project_docs,
            query_knowledge_base,
            sync_vertex_search,
            generate_index_entry,
            analyze_knowledge_gaps,
        ]
    except ImportError as e:
        logger.warning(f"Could not import indexing tools: {e}")
        return []


def get_workflow_tools() -> List[Any]:
    """
    Get workflow orchestration tools (Phase P1 & P2).

    These tools allow the foreman to invoke workflow agents:
    - Phase P1: SequentialAgent for compliance pipeline
    - Phase P2: ParallelAgent for concurrent analysis

    Returns:
        List of workflow tools
    """
    tools = []

    # Phase P1: Sequential compliance workflow
    try:
        from agents.workflows.compliance_workflow import create_compliance_workflow

        def run_compliance_workflow(
            repo_path: str,
            focus_areas: list[str] | None = None,
            rules: list[str] | None = None,
        ) -> dict:
            """
            Run the full compliance analysis workflow.

            This executes a SequentialAgent pipeline:
            1. iam-adk: Analyze for ADK pattern violations -> adk_findings
            2. iam-issue: Create issue specifications -> issue_specs
            3. iam-fix-plan: Generate fix plans -> fix_plans

            Args:
                repo_path: Path to the repository to analyze
                focus_areas: Specific directories to focus on (e.g., ["agents/", "service/"])
                rules: Specific Hard Mode rules to check (e.g., ["R1", "R3", "R5"])

            Returns:
                dict: Workflow result with adk_findings, issue_specs, and fix_plans
            """
            return {
                "status": "workflow_available",
                "workflow": "compliance_workflow",
                "pipeline": ["iam-adk", "iam-issue", "iam-fix-plan"],
                "state_keys": ["adk_findings", "issue_specs", "fix_plans"],
                "message": "Use Runner to execute this SequentialAgent workflow",
                "input": {
                    "repo_path": repo_path,
                    "focus_areas": focus_areas or ["agents/"],
                    "rules": rules or ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
                },
            }

        tools.append(run_compliance_workflow)
    except ImportError as e:
        logger.warning(f"Could not import compliance workflow tools: {e}")

    # Phase P2: Parallel analysis workflow
    try:
        from agents.workflows.analysis_workflow import create_analysis_workflow

        def run_analysis_workflow(
            repo_path: str,
            include_adk: bool = True,
            include_cleanup: bool = True,
            include_index: bool = True,
        ) -> dict:
            """
            Run the parallel analysis workflow.

            This executes a ParallelAgent + aggregator pipeline:
            1. ParallelAgent runs concurrently:
               - iam-adk: ADK compliance -> adk_findings
               - iam-cleanup: Repo hygiene -> cleanup_findings
               - iam-index: Knowledge status -> index_status
            2. Result aggregator combines findings -> aggregated_analysis

            Args:
                repo_path: Path to the repository to analyze
                include_adk: Include ADK compliance analysis (default: True)
                include_cleanup: Include cleanup/hygiene analysis (default: True)
                include_index: Include knowledge index status (default: True)

            Returns:
                dict: Workflow result with aggregated_analysis
            """
            return {
                "status": "workflow_available",
                "workflow": "analysis_workflow",
                "pattern": "parallel_fan_out",
                "parallel_agents": ["iam-adk", "iam-cleanup", "iam-index"],
                "state_keys": ["adk_findings", "cleanup_findings", "index_status", "aggregated_analysis"],
                "message": "Use Runner to execute this ParallelAgent workflow",
                "input": {
                    "repo_path": repo_path,
                    "include_adk": include_adk,
                    "include_cleanup": include_cleanup,
                    "include_index": include_index,
                },
            }

        tools.append(run_analysis_workflow)
    except ImportError as e:
        logger.warning(f"Could not import analysis workflow tools: {e}")

    # Phase P3: Fix loop workflow (Generator-Critic + LoopAgent)
    try:
        from agents.workflows.fix_loop import create_fix_loop

        def run_fix_loop(
            fix_plan: dict,
            max_iterations: int = 3,
        ) -> dict:
            """
            Run the fix implementation loop with QA gates.

            This executes a LoopAgent workflow:
            1. iam-fix-impl: Implements fix from plan -> fix_output
            2. iam-qa: Reviews implementation -> qa_result (PASS/FAIL)
            3. If FAIL, loop back to step 1 (up to max_iterations)
            4. If PASS, exit loop early via escalate

            Args:
                fix_plan: The FixPlan specification from iam-fix-plan
                max_iterations: Maximum retry attempts (default: 3)

            Returns:
                dict: Workflow result with fix_output and qa_result
            """
            return {
                "status": "workflow_available",
                "workflow": "fix_loop",
                "pattern": "generator_critic_loop",
                "loop_agents": ["iam-fix-impl", "iam-qa"],
                "state_keys": ["fix_output", "qa_result"],
                "max_iterations": max_iterations,
                "exit_condition": "QA PASS (escalate=True) or max_iterations",
                "message": "Use Runner to execute this LoopAgent workflow",
                "input": {
                    "fix_plan": fix_plan,
                    "max_iterations": max_iterations,
                },
            }

        tools.append(run_fix_loop)
    except ImportError as e:
        logger.warning(f"Could not import fix loop tools: {e}")

    # Phase P4: Approval workflow (Human-in-the-Loop)
    try:
        from agents.workflows.approval_workflow import create_approval_workflow

        def run_approval_workflow(
            fix_plan: dict,
            max_iterations: int = 3,
        ) -> dict:
            """
            Run fix workflow with human-in-the-loop approval gates.

            This workflow adds approval gates for high-risk changes:
            1. Risk assessment: Classifies fix plan by risk level
            2. Approval gate: HIGH/CRITICAL triggers human approval
            3. Fix loop: Runs fix implementation with QA gates

            Args:
                fix_plan: The FixPlan specification from iam-fix-plan
                max_iterations: Maximum retry attempts for fix loop (default: 3)

            Returns:
                dict: Workflow result with risk_assessment, approval_result,
                      fix_output, and qa_result
            """
            return {
                "status": "workflow_available",
                "workflow": "approval_workflow",
                "pattern": "human_in_the_loop",
                "pipeline": ["risk_assessor", "approval_gate", "fix_loop"],
                "state_keys": [
                    "risk_assessment",
                    "approval_result",
                    "fix_output",
                    "qa_result",
                ],
                "risk_levels": {
                    "LOW": "Auto-approved, proceeds immediately",
                    "MEDIUM": "Auto-approved with logging",
                    "HIGH": "Requires human approval",
                    "CRITICAL": "Requires human approval + escalation",
                },
                "message": "Use Runner to execute this approval workflow",
                "input": {
                    "fix_plan": fix_plan,
                    "max_iterations": max_iterations,
                },
            }

        tools.append(run_approval_workflow)
    except ImportError as e:
        logger.warning(f"Could not import approval workflow tools: {e}")

    return tools


def get_delegation_tools() -> List[Any]:
    """
    Get delegation tools from iam-senior-adk-devops-lead implementation.

    Phase 17: Updated to use real A2A delegation functions.

    Returns:
        List of delegation tools
    """
    try:
        from agents.iam_senior_adk_devops_lead.tools.delegation import (
            delegate_to_specialist,
            delegate_to_multiple,
            check_specialist_availability,
            get_specialist_capabilities,
        )
        return [
            delegate_to_specialist,
            delegate_to_multiple,
            check_specialist_availability,
            get_specialist_capabilities,
        ]
    except ImportError:
        # Try with hyphenated directory name
        try:
            import sys
            import importlib.util

            # Manually load from hyphenated directory
            spec = importlib.util.spec_from_file_location(
                "delegation",
                "agents/iam-senior-adk-devops-lead/tools/delegation.py"
            )
            if spec and spec.loader:
                delegation = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(delegation)

                return [
                    delegation.delegate_to_specialist,
                    delegation.delegate_to_multiple,
                    delegation.check_specialist_availability,
                    delegation.get_specialist_capabilities,
                ]
        except Exception as e:
            logger.warning(f"Could not import delegation tools: {e}")

        return []