"""
Unit tests for Sequential Workflow Pattern (Phase P1).

Tests the compliance_workflow SequentialAgent implementation following
Google's Multi-Agent Patterns guide.

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

import pytest
from unittest.mock import patch, MagicMock

# Skip all tests if google.adk is not installed
pytest.importorskip("google.adk", reason="google-adk not installed")


class TestComplianceWorkflowCreation:
    """Test workflow creation and structure."""

    def test_create_compliance_workflow_returns_sequential_agent(self):
        """Verify workflow is a SequentialAgent instance."""
        from agents.workflows.compliance_workflow import create_compliance_workflow
        from google.adk.agents import SequentialAgent

        workflow = create_compliance_workflow()

        assert isinstance(workflow, SequentialAgent)
        assert workflow.name == "compliance_workflow"

    def test_workflow_has_three_sub_agents(self):
        """Verify workflow has exactly 3 sub-agents in correct order."""
        from agents.workflows.compliance_workflow import create_compliance_workflow

        workflow = create_compliance_workflow()

        assert len(workflow.sub_agents) == 3
        assert workflow.sub_agents[0].name == "workflow_analysis"
        assert workflow.sub_agents[1].name == "workflow_issue"
        assert workflow.sub_agents[2].name == "workflow_planning"

    def test_analysis_agent_has_output_key(self):
        """Verify analysis agent writes to adk_findings."""
        from agents.workflows.compliance_workflow import create_analysis_agent

        agent = create_analysis_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "adk_findings"

    def test_issue_agent_has_output_key(self):
        """Verify issue agent writes to issue_specs."""
        from agents.workflows.compliance_workflow import create_issue_agent

        agent = create_issue_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "issue_specs"

    def test_planning_agent_has_output_key(self):
        """Verify planning agent writes to fix_plans."""
        from agents.workflows.compliance_workflow import create_planning_agent

        agent = create_planning_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "fix_plans"


class TestSpecialistAgentOutputKeys:
    """Test that specialist agents have output_key configured."""

    def test_iam_adk_has_output_key(self):
        """Verify iam-adk specialist has output_key."""
        from agents.iam_adk.agent import create_agent

        agent = create_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "adk_findings"

    def test_iam_issue_has_output_key(self):
        """Verify iam-issue specialist has output_key."""
        from agents.iam_issue.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "issue_specs"

    def test_iam_fix_plan_has_output_key(self):
        """Verify iam-fix-plan specialist has output_key."""
        from agents.iam_fix_plan.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "fix_plans"


class TestWorkflowStateFlow:
    """Test state flow between agents in the pipeline."""

    def test_output_keys_are_unique(self):
        """Verify each agent has a unique output_key."""
        from agents.workflows.compliance_workflow import create_compliance_workflow

        workflow = create_compliance_workflow()

        output_keys = [agent.output_key for agent in workflow.sub_agents]

        assert len(output_keys) == len(set(output_keys)), "output_keys must be unique"
        assert output_keys == ["adk_findings", "issue_specs", "fix_plans"]

    def test_state_keys_follow_pipeline_order(self):
        """Verify state keys follow the logical pipeline order."""
        from agents.workflows.compliance_workflow import create_compliance_workflow

        workflow = create_compliance_workflow()

        # First agent: analysis -> adk_findings
        assert workflow.sub_agents[0].output_key == "adk_findings"

        # Second agent: issue -> issue_specs (reads adk_findings)
        assert workflow.sub_agents[1].output_key == "issue_specs"
        assert "{adk_findings}" in workflow.sub_agents[1].instruction

        # Third agent: planning -> fix_plans (reads issue_specs)
        assert workflow.sub_agents[2].output_key == "fix_plans"
        assert "{issue_specs}" in workflow.sub_agents[2].instruction


class TestWorkflowToolAvailability:
    """Test workflow tools are available to foreman."""

    def test_workflow_tools_loaded(self):
        """Verify workflow tools are loaded."""
        from agents.shared_tools.custom_tools import get_workflow_tools

        tools = get_workflow_tools()

        assert len(tools) >= 1
        assert any("compliance_workflow" in str(t) for t in tools)

    def test_foreman_has_workflow_tools(self):
        """Verify foreman profile includes workflow tools."""
        from agents.shared_tools import get_foreman_tools

        tools = get_foreman_tools()
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]

        assert "run_compliance_workflow" in tool_names


class TestWorkflowInstructionReferences:
    """Test that agent instructions properly reference state variables."""

    def test_issue_agent_references_adk_findings(self):
        """Issue agent should read from {adk_findings}."""
        from agents.workflows.compliance_workflow import create_issue_agent

        agent = create_issue_agent()

        assert "{adk_findings}" in agent.instruction

    def test_planning_agent_references_issue_specs(self):
        """Planning agent should read from {issue_specs}."""
        from agents.workflows.compliance_workflow import create_planning_agent

        agent = create_planning_agent()

        assert "{issue_specs}" in agent.instruction


class TestWorkflowModuleImports:
    """Test workflow module can be imported correctly."""

    def test_workflow_module_imports(self):
        """Verify all workflow exports are importable."""
        from agents.workflows import (
            create_compliance_workflow,
            create_analysis_agent,
            create_issue_agent,
            create_planning_agent,
        )

        assert callable(create_compliance_workflow)
        assert callable(create_analysis_agent)
        assert callable(create_issue_agent)
        assert callable(create_planning_agent)

    def test_sequential_agent_import(self):
        """Verify SequentialAgent is importable from ADK."""
        from google.adk.agents import SequentialAgent

        assert SequentialAgent is not None


# ============================================================================
# Integration-style tests (mock-based, no actual LLM calls)
# ============================================================================


class TestWorkflowIntegration:
    """Integration tests for workflow execution (mocked)."""

    @patch("agents.workflows.compliance_workflow.IAM_ADK_TOOLS", [])
    @patch("agents.workflows.compliance_workflow.IAM_ISSUE_TOOLS", [])
    @patch("agents.workflows.compliance_workflow.IAM_FIX_PLAN_TOOLS", [])
    def test_workflow_can_be_created_without_tools(self):
        """Workflow should be creatable even if tools fail to load."""
        # This tests graceful degradation
        from agents.workflows.compliance_workflow import create_compliance_workflow

        workflow = create_compliance_workflow()

        assert workflow is not None
        assert len(workflow.sub_agents) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
