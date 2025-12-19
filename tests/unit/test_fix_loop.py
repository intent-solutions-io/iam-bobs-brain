"""
Unit tests for Fix Loop Pattern (Phase P3).

Tests the fix_loop LoopAgent implementation following
Google's Multi-Agent Patterns guide (Generator-Critic + Iterative Refinement).

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

import pytest
from unittest.mock import patch, MagicMock

# Skip all tests if google.adk is not installed
pytest.importorskip("google.adk", reason="google-adk not installed")


class TestFixReviewCreation:
    """Test fix-review generator-critic pair creation."""

    def test_create_fix_review_returns_sequential_agent(self):
        """Verify fix_review is a SequentialAgent instance."""
        from agents.workflows.fix_loop import create_fix_review
        from google.adk.agents import SequentialAgent

        review = create_fix_review()

        assert isinstance(review, SequentialAgent)
        assert review.name == "fix_review"

    def test_fix_review_has_two_sub_agents(self):
        """Verify fix_review has generator and critic."""
        from agents.workflows.fix_loop import create_fix_review

        review = create_fix_review()

        assert len(review.sub_agents) == 2

    def test_fix_review_sub_agent_order(self):
        """Verify generator comes before critic."""
        from agents.workflows.fix_loop import create_fix_review

        review = create_fix_review()
        names = [agent.name for agent in review.sub_agents]

        assert names[0] == "iam_fix_impl"  # Generator first
        assert names[1] == "iam_qa"        # Critic second


class TestFixLoopCreation:
    """Test fix-loop LoopAgent creation."""

    def test_create_fix_loop_returns_loop_agent(self):
        """Verify fix_loop is a LoopAgent instance."""
        from agents.workflows.fix_loop import create_fix_loop
        from google.adk.agents import LoopAgent

        loop = create_fix_loop()

        assert isinstance(loop, LoopAgent)
        assert loop.name == "fix_loop"

    def test_fix_loop_default_max_iterations(self):
        """Verify default max_iterations is 3."""
        from agents.workflows.fix_loop import create_fix_loop

        loop = create_fix_loop()

        assert loop.max_iterations == 3

    def test_fix_loop_custom_max_iterations(self):
        """Verify custom max_iterations is respected."""
        from agents.workflows.fix_loop import create_fix_loop

        loop = create_fix_loop(max_iterations=5)

        assert loop.max_iterations == 5

    def test_fix_loop_has_one_sub_agent(self):
        """Verify loop wraps the fix_review SequentialAgent."""
        from agents.workflows.fix_loop import create_fix_loop
        from google.adk.agents import SequentialAgent

        loop = create_fix_loop()

        assert len(loop.sub_agents) == 1
        assert isinstance(loop.sub_agents[0], SequentialAgent)
        assert loop.sub_agents[0].name == "fix_review"


class TestSpecialistAgentOutputKeys:
    """Test that specialist agents have output_key configured for loop workflow."""

    def test_iam_fix_impl_has_output_key(self):
        """Verify iam-fix-impl specialist has output_key."""
        from agents.iam_fix_impl.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "fix_output"

    def test_iam_qa_has_output_key(self):
        """Verify iam-qa specialist has output_key."""
        from agents.iam_qa.agent import get_agent

        agent = get_agent()

        assert hasattr(agent, "output_key")
        assert agent.output_key == "qa_result"


class TestOutputKeysUnique:
    """Test that all loop agents have unique output keys."""

    def test_fix_review_output_keys_unique(self):
        """Verify generator and critic have unique output_keys."""
        from agents.workflows.fix_loop import create_fix_review

        review = create_fix_review()

        output_keys = [agent.output_key for agent in review.sub_agents]

        assert len(output_keys) == len(set(output_keys)), "output_keys must be unique"
        assert "fix_output" in output_keys
        assert "qa_result" in output_keys


class TestQAInstructionReferences:
    """Test that iam-qa instruction references fix_output."""

    def test_qa_references_fix_output(self):
        """Verify iam-qa instruction references {fix_output}."""
        from agents.iam_qa.agent import get_agent

        agent = get_agent()

        assert "{fix_output}" in agent.instruction


class TestQAEscalationCallback:
    """Test QA escalation callback logic."""

    def test_callback_exists(self):
        """Verify escalation callback factory exists."""
        from agents.workflows.fix_loop import create_qa_escalation_callback

        callback = create_qa_escalation_callback()
        assert callable(callback)

    def test_callback_escalates_on_pass_string(self):
        """Verify callback sets escalate=True on PASS string."""
        from agents.workflows.fix_loop import create_qa_escalation_callback

        callback = create_qa_escalation_callback()

        # Mock context
        ctx = MagicMock()
        ctx.state = {"qa_result": "PASS - All tests passed"}
        ctx.actions = MagicMock()
        ctx.actions.escalate = False

        callback(ctx)

        assert ctx.actions.escalate is True

    def test_callback_escalates_on_pass_dict(self):
        """Verify callback sets escalate=True on PASS dict."""
        from agents.workflows.fix_loop import create_qa_escalation_callback

        callback = create_qa_escalation_callback()

        # Mock context
        ctx = MagicMock()
        ctx.state = {"qa_result": {"status": "PASS", "reason": "All tests passed"}}
        ctx.actions = MagicMock()
        ctx.actions.escalate = False

        callback(ctx)

        assert ctx.actions.escalate is True

    def test_callback_no_escalate_on_fail(self):
        """Verify callback does NOT escalate on FAIL."""
        from agents.workflows.fix_loop import create_qa_escalation_callback

        callback = create_qa_escalation_callback()

        # Mock context
        ctx = MagicMock()
        ctx.state = {"qa_result": {"status": "FAIL", "reason": "Tests failed"}}
        ctx.actions = MagicMock()
        ctx.actions.escalate = False

        callback(ctx)

        # Should not have been set to True
        assert ctx.actions.escalate is False


class TestWorkflowModuleImports:
    """Test workflow module can be imported correctly."""

    def test_workflow_module_imports_phase3(self):
        """Verify all Phase P3 workflow exports are importable."""
        from agents.workflows import (
            create_fix_review,
            create_fix_loop,
            create_qa_escalation_callback,
        )

        assert callable(create_fix_review)
        assert callable(create_fix_loop)
        assert callable(create_qa_escalation_callback)

    def test_loop_agent_import(self):
        """Verify LoopAgent is importable from ADK."""
        from google.adk.agents import LoopAgent

        assert LoopAgent is not None


class TestWorkflowToolAvailability:
    """Test workflow tools are available to foreman."""

    def test_fix_loop_tool_loaded(self):
        """Verify fix loop tool is loaded."""
        from agents.shared_tools.custom_tools import get_workflow_tools

        tools = get_workflow_tools()

        assert len(tools) >= 3  # compliance + analysis + fix_loop
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert "run_fix_loop" in tool_names

    def test_foreman_has_fix_loop_tool(self):
        """Verify foreman profile includes fix loop tool."""
        from agents.shared_tools import get_foreman_tools

        tools = get_foreman_tools()
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]

        assert "run_fix_loop" in tool_names


class TestCreateAgentAliases:
    """Test that create_agent aliases work correctly."""

    def test_iam_fix_impl_create_agent_alias(self):
        """Verify iam-fix-impl has create_agent alias."""
        from agents.iam_fix_impl.agent import create_agent, get_agent

        assert create_agent is get_agent

    def test_iam_qa_create_agent_alias(self):
        """Verify iam-qa has create_agent alias."""
        from agents.iam_qa.agent import create_agent, get_agent

        assert create_agent is get_agent


# ============================================================================
# Integration-style tests (mock-based, no actual LLM calls)
# ============================================================================


class TestFixLoopIntegration:
    """Integration tests for fix loop workflow (mocked)."""

    @patch("agents.workflows.fix_loop.create_iam_fix_impl")
    @patch("agents.workflows.fix_loop.create_iam_qa")
    def test_loop_can_be_created_with_mocked_agents(
        self, mock_qa, mock_impl
    ):
        """Loop should be creatable with mocked agents."""
        from google.adk.agents import LlmAgent

        # Create mock agents with required attributes
        mock_impl.return_value = MagicMock(
            spec=LlmAgent, name="iam_fix_impl", output_key="fix_output"
        )
        mock_qa.return_value = MagicMock(
            spec=LlmAgent, name="iam_qa", output_key="qa_result"
        )

        from agents.workflows.fix_loop import create_fix_loop

        loop = create_fix_loop()

        assert loop is not None
        assert loop.max_iterations == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
