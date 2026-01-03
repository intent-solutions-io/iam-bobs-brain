"""
Unit tests for Parallel Workflow Pattern (Phase P2).

Tests the analysis_workflow ParallelAgent implementation following
Google's Multi-Agent Patterns guide.

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

import pytest
from unittest.mock import patch, MagicMock

# Skip all tests if google.adk is not installed
pytest.importorskip("google.adk", reason="google-adk not installed")


class TestParallelAnalysisCreation:
    """Test parallel analysis workflow creation and structure."""

    def test_create_parallel_analysis_returns_parallel_agent(self):
        """Verify parallel analysis is a ParallelAgent instance."""
        from agents.workflows.analysis_workflow import create_parallel_analysis
        from google.adk.agents import ParallelAgent

        parallel = create_parallel_analysis()

        assert isinstance(parallel, ParallelAgent)
        assert parallel.name == "parallel_analysis"

    def test_parallel_analysis_has_three_sub_agents(self):
        """Verify parallel analysis has exactly 3 sub-agents."""
        from agents.workflows.analysis_workflow import create_parallel_analysis

        parallel = create_parallel_analysis()

        assert len(parallel.sub_agents) == 3

    def test_parallel_analysis_sub_agent_names(self):
        """Verify parallel analysis sub-agents are correct specialists."""
        from agents.workflows.analysis_workflow import create_parallel_analysis

        parallel = create_parallel_analysis()
        names = [agent.name for agent in parallel.sub_agents]

        assert "iam_adk" in names
        assert "iam_cleanup" in names
        assert "iam_index" in names


class TestResultAggregatorCreation:
    """Test result aggregator creation."""

    def test_create_result_aggregator_returns_llm_agent(self):
        """Verify result aggregator is an LlmAgent instance."""
        from agents.workflows.analysis_workflow import create_result_aggregator
        from google.adk.agents import LlmAgent

        aggregator = create_result_aggregator()

        assert isinstance(aggregator, LlmAgent)
        assert aggregator.name == "result_aggregator"

    def test_aggregator_has_output_key(self):
        """Verify aggregator writes to aggregated_analysis."""
        from agents.workflows.analysis_workflow import create_result_aggregator

        aggregator = create_result_aggregator()

        assert hasattr(aggregator, "output_key")
        assert aggregator.output_key == "aggregated_analysis"

    def test_aggregator_references_parallel_outputs(self):
        """Verify aggregator instruction references all parallel agent outputs."""
        from agents.workflows.analysis_workflow import create_result_aggregator

        aggregator = create_result_aggregator()

        assert "{adk_findings}" in aggregator.instruction
        assert "{cleanup_findings}" in aggregator.instruction
        assert "{index_status}" in aggregator.instruction


class TestAnalysisWorkflowCreation:
    """Test complete analysis workflow creation."""

    def test_create_analysis_workflow_returns_sequential_agent(self):
        """Verify analysis workflow is a SequentialAgent (fan-out then gather)."""
        from agents.workflows.analysis_workflow import create_analysis_workflow
        from google.adk.agents import SequentialAgent

        workflow = create_analysis_workflow()

        assert isinstance(workflow, SequentialAgent)
        assert workflow.name == "analysis_workflow"

    def test_analysis_workflow_has_two_stages(self):
        """Verify workflow has parallel stage + aggregator stage."""
        from agents.workflows.analysis_workflow import create_analysis_workflow
        from google.adk.agents import ParallelAgent

        workflow = create_analysis_workflow()

        assert len(workflow.sub_agents) == 2
        assert isinstance(workflow.sub_agents[0], ParallelAgent)
        assert workflow.sub_agents[0].name == "parallel_analysis"
        assert workflow.sub_agents[1].name == "result_aggregator"


class TestSpecialistAgentOutputKeys:
    """Test that specialist agents have output_key configured for parallel workflow."""

    def test_iam_cleanup_has_output_key(self):
        """Verify iam-cleanup specialist has output_key."""
        from agents.iam_cleanup.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "cleanup_findings"

    def test_iam_index_has_output_key(self):
        """Verify iam-index specialist has output_key."""
        from agents.iam_index.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "index_status"


class TestParallelOutputKeysUnique:
    """Test that all parallel agents have unique output keys."""

    def test_output_keys_are_unique(self):
        """Verify each parallel agent has a unique output_key."""
        from agents.workflows.analysis_workflow import create_parallel_analysis

        parallel = create_parallel_analysis()

        output_keys = [agent.output_key for agent in parallel.sub_agents]

        assert len(output_keys) == len(set(output_keys)), "output_keys must be unique"
        assert "adk_findings" in output_keys
        assert "cleanup_findings" in output_keys
        assert "index_status" in output_keys


class TestWorkflowModuleImports:
    """Test workflow module can be imported correctly."""

    def test_workflow_module_imports_phase2(self):
        """Verify all Phase P2 workflow exports are importable."""
        from agents.workflows import (
            create_parallel_analysis,
            create_result_aggregator,
            create_analysis_workflow,
        )

        assert callable(create_parallel_analysis)
        assert callable(create_result_aggregator)
        assert callable(create_analysis_workflow)

    def test_parallel_agent_import(self):
        """Verify ParallelAgent is importable from ADK."""
        from google.adk.agents import ParallelAgent

        assert ParallelAgent is not None


class TestWorkflowToolAvailability:
    """Test workflow tools are available to foreman."""

    def test_analysis_workflow_tool_loaded(self):
        """Verify analysis workflow tool is loaded."""
        from agents.shared_tools.custom_tools import get_workflow_tools

        tools = get_workflow_tools()

        assert len(tools) >= 2  # compliance + analysis workflows
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert "run_analysis_workflow" in tool_names

    def test_foreman_has_analysis_workflow_tool(self):
        """Verify foreman profile includes analysis workflow tool."""
        from agents.shared_tools import get_foreman_tools

        tools = get_foreman_tools()
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]

        assert "run_analysis_workflow" in tool_names


class TestCreateAgentAliases:
    """Test that create_agent aliases work correctly."""

    def test_iam_cleanup_create_agent_alias(self):
        """Verify iam-cleanup has create_agent alias."""
        from agents.iam_cleanup.agent import create_agent, get_agent

        assert create_agent is get_agent

    def test_iam_index_create_agent_alias(self):
        """Verify iam-index has create_agent alias."""
        from agents.iam_index.agent import create_agent, get_agent

        assert create_agent is get_agent


# ============================================================================
# Integration-style tests (mock-based, no actual LLM calls)
# ============================================================================


class TestParallelWorkflowIntegration:
    """Integration tests for parallel workflow execution (mocked)."""

    @patch("agents.workflows.analysis_workflow.create_iam_adk")
    @patch("agents.workflows.analysis_workflow.create_iam_cleanup")
    @patch("agents.workflows.analysis_workflow.create_iam_index")
    def test_workflow_can_be_created_with_mocked_agents(
        self, mock_index, mock_cleanup, mock_adk
    ):
        """Workflow should be creatable with mocked agents."""
        from google.adk.agents import LlmAgent

        # Create mock agents with required attributes
        mock_adk.return_value = MagicMock(
            spec=LlmAgent, name="iam_adk", output_key="adk_findings"
        )
        mock_cleanup.return_value = MagicMock(
            spec=LlmAgent, name="iam_cleanup", output_key="cleanup_findings"
        )
        mock_index.return_value = MagicMock(
            spec=LlmAgent, name="iam_index", output_key="index_status"
        )

        from agents.workflows.analysis_workflow import create_parallel_analysis

        parallel = create_parallel_analysis()

        assert parallel is not None
        assert len(parallel.sub_agents) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
