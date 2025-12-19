"""
Unit tests for Approval Workflow Pattern (Phase P4).

Tests the human-in-the-loop approval workflow implementation following
Google's Multi-Agent Patterns guide.

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Test contracts module (always available)
from agents.iam_contracts import (
    RiskLevel,
    ApprovalStatus,
    ApprovalRequest,
    ApprovalResponse,
)


class TestRiskLevelEnum:
    """Test RiskLevel enum functionality."""

    def test_risk_level_values(self):
        """Verify all risk level values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_requires_approval_low(self):
        """LOW risk should not require approval."""
        assert RiskLevel.requires_approval(RiskLevel.LOW) is False

    def test_requires_approval_medium(self):
        """MEDIUM risk should not require approval."""
        assert RiskLevel.requires_approval(RiskLevel.MEDIUM) is False

    def test_requires_approval_high(self):
        """HIGH risk should require approval."""
        assert RiskLevel.requires_approval(RiskLevel.HIGH) is True

    def test_requires_approval_critical(self):
        """CRITICAL risk should require approval."""
        assert RiskLevel.requires_approval(RiskLevel.CRITICAL) is True

    def test_from_string_valid(self):
        """from_string should parse valid values."""
        assert RiskLevel.from_string("low") == RiskLevel.LOW
        assert RiskLevel.from_string("MEDIUM") == RiskLevel.MEDIUM
        assert RiskLevel.from_string("High") == RiskLevel.HIGH
        assert RiskLevel.from_string("CRITICAL") == RiskLevel.CRITICAL

    def test_from_string_invalid_defaults_high(self):
        """from_string should default to HIGH for invalid values."""
        assert RiskLevel.from_string("invalid") == RiskLevel.HIGH
        assert RiskLevel.from_string("") == RiskLevel.HIGH


class TestApprovalStatus:
    """Test ApprovalStatus enum."""

    def test_approval_status_values(self):
        """Verify all approval status values."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.TIMEOUT.value == "timeout"
        assert ApprovalStatus.AUTO_APPROVED.value == "auto_approved"


class TestApprovalRequest:
    """Test ApprovalRequest dataclass."""

    def test_approval_request_creation(self):
        """Verify approval request can be created."""
        request = ApprovalRequest(
            action="deploy-to-production",
            description="Deploy version 1.2.3 to production",
            risk_level=RiskLevel.HIGH,
            requested_by="spiffe://intent.solutions/agent/iam-fix-impl",
        )

        assert request.action == "deploy-to-production"
        assert request.risk_level == RiskLevel.HIGH
        assert request.request_id is not None  # Auto-generated
        assert request.timeout_seconds == 300  # Default

    def test_approval_request_to_dict(self):
        """Verify to_dict serialization."""
        request = ApprovalRequest(
            action="test-action",
            description="Test description",
            risk_level=RiskLevel.CRITICAL,
            requested_by="test-agent",
            files_affected=["file1.py", "file2.py"],
        )

        result = request.to_dict()

        assert result["action"] == "test-action"
        assert result["risk_level"] == "critical"
        assert result["files_affected"] == ["file1.py", "file2.py"]
        assert "request_id" in result


class TestApprovalResponse:
    """Test ApprovalResponse dataclass."""

    def test_approval_response_approved(self):
        """Verify approved response."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.APPROVED,
            approved=True,
            reason="Looks good",
            approved_by="user@example.com",
            approved_at=datetime.utcnow(),
        )

        assert response.approved is True
        assert response.status == ApprovalStatus.APPROVED

    def test_approval_response_rejected(self):
        """Verify rejected response."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.REJECTED,
            approved=False,
            reason="Too risky",
        )

        assert response.approved is False
        assert response.status == ApprovalStatus.REJECTED

    def test_approval_response_to_dict(self):
        """Verify to_dict serialization."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.AUTO_APPROVED,
            approved=True,
            reason="Low risk",
            approved_by="system",
        )

        result = response.to_dict()

        assert result["request_id"] == "test-123"
        assert result["status"] == "auto_approved"
        assert result["approved"] is True


class TestApprovalTool:
    """Test approval tool functions."""

    def test_classify_risk_level_low(self):
        """Documentation changes should be LOW risk."""
        from agents.tools.approval_tool import classify_risk_level

        result = classify_risk_level(
            action="Update documentation",
            files_affected=["docs/README.md"],
            context={},
        )

        assert result == RiskLevel.LOW

    def test_classify_risk_level_medium(self):
        """Code refactoring should be MEDIUM risk."""
        from agents.tools.approval_tool import classify_risk_level

        result = classify_risk_level(
            action="Refactor utility functions",
            files_affected=["agents/utils.py"],
            context={},
        )

        assert result == RiskLevel.MEDIUM

    def test_classify_risk_level_high_deploy(self):
        """Deployments should be HIGH risk."""
        from agents.tools.approval_tool import classify_risk_level

        result = classify_risk_level(
            action="Deploy to staging",
            files_affected=["service/main.py"],
            context={},
        )

        assert result == RiskLevel.HIGH

    def test_classify_risk_level_high_infra(self):
        """Infrastructure changes should be HIGH risk."""
        from agents.tools.approval_tool import classify_risk_level

        result = classify_risk_level(
            action="Update configuration",
            files_affected=["infra/terraform/main.tf"],
            context={},
        )

        assert result == RiskLevel.HIGH

    def test_classify_risk_level_critical(self):
        """Destructive actions should be CRITICAL risk."""
        from agents.tools.approval_tool import classify_risk_level

        result = classify_risk_level(
            action="Delete old database tables",
            files_affected=["migrations/drop_tables.sql"],
            context={},
        )

        assert result == RiskLevel.CRITICAL

    def test_requires_approval(self):
        """Test requires_approval function."""
        from agents.tools.approval_tool import requires_approval

        assert requires_approval(RiskLevel.LOW) is False
        assert requires_approval(RiskLevel.MEDIUM) is False
        assert requires_approval(RiskLevel.HIGH) is True
        assert requires_approval(RiskLevel.CRITICAL) is True


class TestApprovalWorkflowCreation:
    """Test approval workflow creation (requires google.adk)."""

    @pytest.fixture(autouse=True)
    def skip_if_no_adk(self):
        """Skip tests if google.adk is not installed."""
        pytest.importorskip("google.adk", reason="google-adk not installed")

    def test_create_risk_assessor(self):
        """Verify risk assessor agent creation."""
        from agents.workflows.approval_workflow import create_risk_assessor
        from google.adk.agents import LlmAgent

        agent = create_risk_assessor()

        assert isinstance(agent, LlmAgent)
        assert agent.name == "risk_assessor"
        assert agent.output_key == "risk_assessment"

    def test_create_approval_workflow(self):
        """Verify approval workflow creation."""
        from agents.workflows.approval_workflow import create_approval_workflow
        from google.adk.agents import SequentialAgent

        workflow = create_approval_workflow()

        assert isinstance(workflow, SequentialAgent)
        assert workflow.name == "approval_workflow"
        assert len(workflow.sub_agents) == 2  # risk_assessor + fix_loop

    def test_create_approval_workflow_custom_iterations(self):
        """Verify custom max_iterations is passed through."""
        from agents.workflows.approval_workflow import create_approval_workflow

        workflow = create_approval_workflow(max_fix_iterations=5)

        # The fix_loop sub-agent should have max_iterations=5
        fix_loop = workflow.sub_agents[1]
        assert fix_loop.max_iterations == 5

    def test_create_deployment_gate(self):
        """Verify deployment gate agent creation."""
        from agents.workflows.approval_workflow import create_deployment_gate
        from google.adk.agents import LlmAgent

        agent = create_deployment_gate()

        assert isinstance(agent, LlmAgent)
        assert agent.name == "deployment_gate"
        assert agent.output_key == "deployment_decision"


class TestApprovalGateCallback:
    """Test approval gate callback logic."""

    @pytest.fixture(autouse=True)
    def skip_if_no_adk(self):
        """Skip tests if google.adk is not installed."""
        pytest.importorskip("google.adk", reason="google-adk not installed")

    def test_callback_auto_approves_low_risk(self):
        """Low risk should auto-approve."""
        from agents.workflows.approval_workflow import create_approval_gate_callback

        callback = create_approval_gate_callback()

        # Mock context
        ctx = MagicMock()
        ctx.state = {"risk_assessment": {"risk_level": "LOW"}}

        callback(ctx)

        assert ctx.state["approval_result"]["status"] == "auto_approved"

    def test_callback_auto_approves_medium_risk(self):
        """Medium risk should auto-approve."""
        from agents.workflows.approval_workflow import create_approval_gate_callback

        callback = create_approval_gate_callback()

        ctx = MagicMock()
        ctx.state = {"risk_assessment": {"risk_level": "MEDIUM"}}

        callback(ctx)

        assert ctx.state["approval_result"]["status"] == "auto_approved"

    def test_callback_requires_approval_high_risk(self):
        """High risk should require approval."""
        from agents.workflows.approval_workflow import create_approval_gate_callback

        callback = create_approval_gate_callback()

        ctx = MagicMock()
        ctx.state = {
            "risk_assessment": {
                "risk_level": "HIGH",
                "reason": "Infrastructure change",
                "files_affected": ["infra/main.tf"],
            },
            "fix_plan": {"summary": "Update terraform"},
        }

        callback(ctx)

        assert ctx.state["approval_result"]["status"] == "pending"
        assert "request_id" in ctx.state["approval_result"]

    def test_callback_requires_approval_critical_risk(self):
        """Critical risk should require approval."""
        from agents.workflows.approval_workflow import create_approval_gate_callback

        callback = create_approval_gate_callback()

        ctx = MagicMock()
        ctx.state = {
            "risk_assessment": {
                "risk_level": "CRITICAL",
                "reason": "Production deployment",
                "files_affected": [],
            },
            "fix_plan": {},
        }

        callback(ctx)

        assert ctx.state["approval_result"]["status"] == "pending"


class TestWorkflowModuleImports:
    """Test workflow module exports Phase P4 functions."""

    @pytest.fixture(autouse=True)
    def skip_if_no_adk(self):
        """Skip tests if google.adk is not installed."""
        pytest.importorskip("google.adk", reason="google-adk not installed")

    def test_workflow_module_imports_phase4(self):
        """Verify all Phase P4 workflow exports are importable."""
        from agents.workflows import (
            create_risk_assessor,
            create_approval_gate_callback,
            create_approval_workflow,
            create_deployment_gate,
        )

        assert callable(create_risk_assessor)
        assert callable(create_approval_gate_callback)
        assert callable(create_approval_workflow)
        assert callable(create_deployment_gate)


class TestWorkflowToolAvailability:
    """Test workflow tools are available to foreman."""

    @pytest.fixture(autouse=True)
    def skip_if_no_adk(self):
        """Skip tests if google.adk is not installed."""
        pytest.importorskip("google.adk", reason="google-adk not installed")

    def test_approval_workflow_tool_loaded(self):
        """Verify approval workflow tool is loaded."""
        from agents.shared_tools.custom_tools import get_workflow_tools

        tools = get_workflow_tools()

        assert len(tools) >= 4  # compliance + analysis + fix_loop + approval
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert "run_approval_workflow" in tool_names


class TestToolsModuleExports:
    """Test tools module exports approval functions."""

    def test_tools_module_exports_approval_functions(self):
        """Verify approval functions are exported from tools module."""
        from agents.tools import (
            classify_risk_level,
            create_approval_request,
            requires_approval,
            request_human_approval,
            check_approval_status,
        )

        assert callable(classify_risk_level)
        assert callable(create_approval_request)
        assert callable(requires_approval)
        assert callable(request_human_approval)
        assert callable(check_approval_status)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
