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
    Get workflow orchestration tools (Phase P1: Sequential Workflow).

    These tools allow the foreman to invoke SequentialAgent workflows
    for common multi-step pipelines like compliance analysis.

    Returns:
        List of workflow tools
    """
    try:
        from agents.workflows.compliance_workflow import create_compliance_workflow

        # Create a tool function that invokes the compliance workflow
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
            # Note: In production, this would invoke the SequentialAgent via Runner
            # For now, return a stub indicating the workflow is available
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

        return [run_compliance_workflow]
    except ImportError as e:
        logger.warning(f"Could not import workflow tools: {e}")
        return []


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