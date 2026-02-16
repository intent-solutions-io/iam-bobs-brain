"""
Unit tests for enterprise controls (Phase E - Vision Alignment).

Tests:
- Enhanced Mandate with risk_tier, tool_allowlist, approval fields
- Policy gates and risk tier enforcement
- Evidence bundle creation and validation
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import json

from agents.shared_contracts.pipeline_contracts import Mandate
from agents.shared_contracts.policy_gates import (
    RiskTier,
    GateResult,
    PolicyGate,
    RISK_TIER_DESCRIPTIONS,
    preflight_check,
)
from agents.shared_contracts.evidence_bundle import (
    ArtifactRecord,
    EvidenceBundleManifest,
    EvidenceBundle,
    create_evidence_bundle,
)


# ============================================================================
# MANDATE ENTERPRISE CONTROLS TESTS
# ============================================================================

class TestMandateEnterpriseFields:
    """Test enhanced Mandate with enterprise control fields."""

    def test_default_risk_tier_is_r0(self):
        """Default risk tier should be R0 (no restrictions)."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        assert mandate.risk_tier == "R0"

    def test_risk_tier_can_be_set(self):
        """Risk tier can be set to any valid value."""
        for tier in ["R0", "R1", "R2", "R3", "R4"]:
            mandate = Mandate(mandate_id="m-001", intent="test", risk_tier=tier)
            assert mandate.risk_tier == tier

    def test_default_tool_allowlist_is_empty(self):
        """Default tool allowlist should be empty (all tools allowed)."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        assert mandate.tool_allowlist == []

    def test_tool_allowlist_can_be_set(self):
        """Tool allowlist can be set with specific tools."""
        tools = ["search_code", "read_file", "write_file"]
        mandate = Mandate(mandate_id="m-001", intent="test", tool_allowlist=tools)
        assert mandate.tool_allowlist == tools

    def test_default_data_classification_is_internal(self):
        """Default data classification should be internal."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        assert mandate.data_classification == "internal"

    def test_default_approval_state_is_auto(self):
        """Default approval state should be auto."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        assert mandate.approval_state == "auto"

    def test_approver_id_and_timestamp_default_none(self):
        """Approver ID and timestamp should default to None."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        assert mandate.approver_id is None
        assert mandate.approval_timestamp is None


class TestMandateEnterpriseRequiresApproval:
    """Test Mandate requires_approval method."""

    def test_r0_does_not_require_approval(self):
        """R0 operations do not require approval."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R0")
        assert mandate.requires_approval() is False

    def test_r1_does_not_require_approval(self):
        """R1 operations do not require approval."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R1")
        assert mandate.requires_approval() is False

    def test_r2_does_not_require_approval(self):
        """R2 operations do not require approval."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R2")
        assert mandate.requires_approval() is False

    def test_r3_requires_approval(self):
        """R3 operations require approval."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R3")
        assert mandate.requires_approval() is True

    def test_r4_requires_approval(self):
        """R4 operations require approval."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R4")
        assert mandate.requires_approval() is True


class TestMandateEnterpriseApproval:
    """Test Mandate approval workflow."""

    def test_is_approved_for_non_r3r4(self):
        """R0-R2 are always considered approved."""
        for tier in ["R0", "R1", "R2"]:
            mandate = Mandate(mandate_id="m-001", intent="test", risk_tier=tier)
            assert mandate.is_approved() is True

    def test_is_approved_when_approved(self):
        """R3/R4 with approved state returns True."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="approved"
        )
        assert mandate.is_approved() is True

    def test_is_approved_when_pending(self):
        """R3/R4 with pending state returns False."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending"
        )
        assert mandate.is_approved() is False

    def test_is_pending_approval(self):
        """Test is_pending_approval method."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            approval_state="pending"
        )
        assert mandate.is_pending_approval() is True

    def test_is_denied(self):
        """Test is_denied method."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            approval_state="denied"
        )
        assert mandate.is_denied() is True

    def test_approve_sets_state_and_approver(self):
        """approve() sets state, approver_id, and timestamp."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending"
        )
        mandate.approve("user@example.com")
        assert mandate.approval_state == "approved"
        assert mandate.approver_id == "user@example.com"
        assert mandate.approval_timestamp is not None

    def test_deny_sets_state_and_approver(self):
        """deny() sets state, approver_id, and timestamp."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending"
        )
        mandate.deny("user@example.com")
        assert mandate.approval_state == "denied"
        assert mandate.approver_id == "user@example.com"
        assert mandate.approval_timestamp is not None


class TestMandateEnterpriseToolAllowlist:
    """Test Mandate tool allowlist."""

    def test_can_use_tool_with_empty_allowlist(self):
        """Empty allowlist allows all tools."""
        mandate = Mandate(mandate_id="m-001", intent="test", tool_allowlist=[])
        assert mandate.can_use_tool("any_tool") is True
        assert mandate.can_use_tool("another_tool") is True

    def test_can_use_tool_in_allowlist(self):
        """Tool in allowlist is allowed."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            tool_allowlist=["search_code", "read_file"]
        )
        assert mandate.can_use_tool("search_code") is True
        assert mandate.can_use_tool("read_file") is True

    def test_cannot_use_tool_not_in_allowlist(self):
        """Tool not in allowlist is blocked."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            tool_allowlist=["search_code", "read_file"]
        )
        assert mandate.can_use_tool("write_file") is False
        assert mandate.can_use_tool("delete_file") is False


class TestMandateEnterpriseCanInvokeSpecialist:
    """Test Mandate can_invoke_specialist with enterprise controls."""

    def test_r3_pending_blocks_invocation(self):
        """R3 with pending approval blocks specialist invocation."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending",
            authorized_specialists=["iam-compliance"]
        )
        assert mandate.can_invoke_specialist("iam-compliance") is False

    def test_r3_approved_allows_invocation(self):
        """R3 with approved state allows specialist invocation."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="approved",
            authorized_specialists=["iam-compliance"]
        )
        assert mandate.can_invoke_specialist("iam-compliance") is True

    def test_r0_always_allows_invocation(self):
        """R0 always allows invocation (no approval needed)."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R0",
            approval_state="auto",
            authorized_specialists=["iam-compliance"]
        )
        assert mandate.can_invoke_specialist("iam-compliance") is True


# ============================================================================
# POLICY GATES TESTS
# ============================================================================

class TestRiskTierEnum:
    """Test RiskTier enum."""

    def test_all_risk_tiers_defined(self):
        """All risk tiers R0-R4 are defined."""
        assert RiskTier.R0.value == "R0"
        assert RiskTier.R1.value == "R1"
        assert RiskTier.R2.value == "R2"
        assert RiskTier.R3.value == "R3"
        assert RiskTier.R4.value == "R4"

    def test_risk_tier_descriptions_complete(self):
        """All risk tiers have descriptions."""
        for tier in RiskTier:
            assert tier in RISK_TIER_DESCRIPTIONS


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_allowed_is_truthy(self):
        """GateResult with allowed=True is truthy."""
        result = GateResult(
            allowed=True,
            reason="Test",
            risk_tier="R0",
            gate_name="test"
        )
        assert bool(result) is True

    def test_gate_result_blocked_is_falsy(self):
        """GateResult with allowed=False is falsy."""
        result = GateResult(
            allowed=False,
            reason="Blocked",
            risk_tier="R0",
            gate_name="test"
        )
        assert bool(result) is False


class TestPolicyGateMandateRequired:
    """Test PolicyGate.check_mandate_required."""

    def test_r0_allows_without_mandate(self):
        """R0 allows operation without mandate."""
        result = PolicyGate.check_mandate_required("R0", None)
        assert result.allowed is True

    def test_r1_allows_without_mandate(self):
        """R1 allows operation without mandate."""
        result = PolicyGate.check_mandate_required("R1", None)
        assert result.allowed is True

    def test_r2_blocks_without_mandate(self):
        """R2 blocks operation without mandate."""
        result = PolicyGate.check_mandate_required("R2", None)
        assert result.allowed is False
        assert result.blocking_requirement == "mandate"

    def test_r2_allows_with_mandate(self):
        """R2 allows operation with mandate."""
        mandate = Mandate(mandate_id="m-001", intent="test")
        result = PolicyGate.check_mandate_required("R2", mandate)
        assert result.allowed is True


class TestPolicyGateApprovalRequired:
    """Test PolicyGate.check_approval_required."""

    def test_r0_r2_no_approval_needed(self):
        """R0-R2 do not require approval."""
        for tier in ["R0", "R1", "R2"]:
            result = PolicyGate.check_approval_required(tier, None)
            assert result.allowed is True

    def test_r3_blocks_without_mandate(self):
        """R3 blocks without mandate."""
        result = PolicyGate.check_approval_required("R3", None)
        assert result.allowed is False

    def test_r3_blocks_pending_approval(self):
        """R3 blocks with pending approval."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending"
        )
        result = PolicyGate.check_approval_required("R3", mandate)
        assert result.allowed is False
        assert result.blocking_requirement == "approval"

    def test_r3_blocks_denied(self):
        """R3 blocks if denied."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="denied"
        )
        result = PolicyGate.check_approval_required("R3", mandate)
        assert result.allowed is False
        assert result.blocking_requirement == "approval_denied"

    def test_r3_allows_approved(self):
        """R3 allows with approved state."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="approved"
        )
        result = PolicyGate.check_approval_required("R3", mandate)
        assert result.allowed is True


class TestPolicyGateToolAllowed:
    """Test PolicyGate.check_tool_allowed."""

    def test_no_mandate_allows_all_tools(self):
        """No mandate means no tool restrictions."""
        result = PolicyGate.check_tool_allowed("any_tool", None)
        assert result.allowed is True

    def test_empty_allowlist_allows_all_tools(self):
        """Empty tool allowlist allows all tools."""
        mandate = Mandate(mandate_id="m-001", intent="test", tool_allowlist=[])
        result = PolicyGate.check_tool_allowed("any_tool", mandate)
        assert result.allowed is True

    def test_tool_in_allowlist_allowed(self):
        """Tool in allowlist is allowed."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            tool_allowlist=["search_code"]
        )
        result = PolicyGate.check_tool_allowed("search_code", mandate)
        assert result.allowed is True

    def test_tool_not_in_allowlist_blocked(self):
        """Tool not in allowlist is blocked."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            tool_allowlist=["search_code"]
        )
        result = PolicyGate.check_tool_allowed("delete_file", mandate)
        assert result.allowed is False
        assert result.blocking_requirement == "tool_allowlist"


class TestPolicyGatePreflightCheck:
    """Test PolicyGate.preflight_check integration."""

    def test_preflight_r0_without_mandate(self):
        """R0 preflight passes without mandate."""
        results = preflight_check("iam-compliance", "R0", None)
        assert PolicyGate.is_all_gates_passed(results) is True

    def test_preflight_r3_without_approval_fails(self):
        """R3 preflight fails without approval."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R3",
            approval_state="pending"
        )
        results = preflight_check("iam-compliance", "R3", mandate)
        assert PolicyGate.is_all_gates_passed(results) is False
        blocking = PolicyGate.get_blocking_gates(results)
        assert len(blocking) > 0

    def test_preflight_with_tool_check(self):
        """Preflight includes tool checks when provided."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R1",
            tool_allowlist=["search_code"]
        )
        results = preflight_check(
            "iam-compliance",
            "R1",
            mandate,
            tools_to_use=["search_code", "delete_file"]
        )
        # delete_file should be blocked
        blocking = PolicyGate.get_blocking_gates(results)
        assert any("delete_file" in r.reason for r in blocking)


# ============================================================================
# EVIDENCE BUNDLE TESTS
# ============================================================================

class TestArtifactRecord:
    """Test ArtifactRecord dataclass."""

    def test_artifact_record_creation(self):
        """ArtifactRecord can be created with required fields."""
        record = ArtifactRecord(
            path="/path/to/file.txt",
            sha256="abc123",
            size_bytes=1024,
            artifact_type="file"
        )
        assert record.path == "/path/to/file.txt"
        assert record.sha256 == "abc123"
        assert record.size_bytes == 1024
        assert record.artifact_type == "file"

    def test_artifact_record_to_dict(self):
        """ArtifactRecord converts to dictionary."""
        record = ArtifactRecord(
            path="/path/to/file.txt",
            sha256="abc123",
            size_bytes=1024,
            artifact_type="file"
        )
        data = record.to_dict()
        assert isinstance(data, dict)
        assert data["path"] == "/path/to/file.txt"


class TestEvidenceBundleManifest:
    """Test EvidenceBundleManifest dataclass."""

    def test_manifest_has_auto_generated_ids(self):
        """Manifest auto-generates bundle_id and pipeline_run_id."""
        manifest = EvidenceBundleManifest()
        assert manifest.bundle_id.startswith("evb-")
        assert manifest.pipeline_run_id.startswith("run-")

    def test_manifest_to_json(self):
        """Manifest converts to valid JSON."""
        manifest = EvidenceBundleManifest()
        json_str = manifest.to_json()
        data = json.loads(json_str)
        assert data["bundle_id"] == manifest.bundle_id

    def test_manifest_from_json_roundtrip(self):
        """Manifest can roundtrip through JSON."""
        original = EvidenceBundleManifest(mission_id="test-mission")
        json_str = original.to_json()
        loaded = EvidenceBundleManifest.from_json(json_str)
        assert loaded.bundle_id == original.bundle_id
        assert loaded.mission_id == original.mission_id


class TestEvidenceBundle:
    """Test EvidenceBundle class."""

    def test_bundle_records_tasks(self):
        """Bundle records tasks planned and executed."""
        bundle = EvidenceBundle()
        bundle.record_task_planned("task-1")
        bundle.record_task_planned("task-2")
        bundle.record_task_executed("task-1")

        assert "task-1" in bundle.manifest.tasks_planned
        assert "task-2" in bundle.manifest.tasks_planned
        assert "task-1" in bundle.manifest.tasks_executed
        assert "task-2" not in bundle.manifest.tasks_executed

    def test_bundle_records_agents(self):
        """Bundle records agents invoked."""
        bundle = EvidenceBundle()
        bundle.record_agent_invoked("iam-compliance")
        bundle.record_agent_invoked("iam-qa")

        assert "iam-compliance" in bundle.manifest.agents_invoked
        assert "iam-qa" in bundle.manifest.agents_invoked

    def test_bundle_no_duplicate_tasks(self):
        """Bundle doesn't record duplicate tasks."""
        bundle = EvidenceBundle()
        bundle.record_task_planned("task-1")
        bundle.record_task_planned("task-1")

        assert bundle.manifest.tasks_planned.count("task-1") == 1

    def test_bundle_mark_completed(self):
        """Bundle can be marked completed."""
        bundle = EvidenceBundle()
        bundle.mark_completed()

        assert bundle.manifest.status == "completed"
        assert bundle.manifest.completed_at is not None

    def test_bundle_mark_failed(self):
        """Bundle can be marked failed with error."""
        bundle = EvidenceBundle()
        bundle.mark_failed("Test error")

        assert bundle.manifest.status == "failed"
        assert bundle.manifest.error_message == "Test error"

    def test_bundle_compute_sha256(self):
        """Bundle can compute SHA256 hash."""
        content = b"test content"
        hash_result = EvidenceBundle.compute_sha256(content)
        assert len(hash_result) == 64  # SHA256 hex length
        assert hash_result.isalnum()

    def test_bundle_save_and_load(self):
        """Bundle can save to disk and load back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save bundle
            bundle = create_evidence_bundle(
                mission_id="test-mission",
                base_path=Path(tmpdir)
            )
            bundle.record_task_planned("task-1")
            bundle.record_agent_invoked("iam-compliance")
            saved_path = bundle.save()

            # Load bundle
            loaded = EvidenceBundle.load(saved_path)
            assert loaded.manifest.mission_id == "test-mission"
            assert "task-1" in loaded.manifest.tasks_planned
            assert "iam-compliance" in loaded.manifest.agents_invoked

    def test_bundle_set_mandate_snapshot(self):
        """Bundle stores mandate snapshot."""
        bundle = EvidenceBundle()
        mandate_dict = {
            "mandate_id": "m-001",
            "intent": "test",
            "risk_tier": "R2"
        }
        bundle.set_mandate_snapshot(mandate_dict)

        assert bundle.manifest.mandate_snapshot == mandate_dict


class TestCreateEvidenceBundle:
    """Test create_evidence_bundle convenience function."""

    def test_creates_bundle_with_mission_id(self):
        """Creates bundle with mission_id."""
        bundle = create_evidence_bundle(mission_id="test-mission")
        assert bundle.manifest.mission_id == "test-mission"

    def test_creates_bundle_with_mandate_snapshot(self):
        """Creates bundle with mandate_snapshot."""
        mandate_dict = {"mandate_id": "m-001"}
        bundle = create_evidence_bundle(mandate_snapshot=mandate_dict)
        assert bundle.manifest.mandate_snapshot == mandate_dict


# ============================================================================
# BUG FIX TESTS - Risk Tier Enforcement Gaps
# ============================================================================

class TestBug1MalformedMandateFailsClosed:
    """Bug 1: Malformed mandate must raise A2AError, not silently bypass."""

    def test_malformed_expires_at_raises_error(self):
        """Bad datetime in expires_at must raise A2AError."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask, A2AError

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-bad",
                "intent": "test",
                "expires_at": "not-a-date",  # Malformed
            }
        )
        with pytest.raises(A2AError, match="Malformed mandate"):
            validate_mandate(task)

    def test_malformed_approval_timestamp_raises_error(self):
        """Bad datetime in approval_timestamp must raise A2AError."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask, A2AError

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-bad",
                "intent": "test",
                "approval_timestamp": 12345,  # Wrong type
            }
        )
        with pytest.raises(A2AError, match="Malformed mandate"):
            validate_mandate(task)

    def test_valid_mandate_does_not_raise(self):
        """Well-formed mandate should pass validation without error."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-good",
                "intent": "test",
                "risk_tier": "R0",
            }
        )
        # Should not raise
        validate_mandate(task)

    def test_error_message_omits_internal_details(self):
        """A2AError for malformed mandate must NOT expose raw parse error."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask, A2AError

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-bad",
                "intent": "test",
                "expires_at": "not-a-date",
            }
        )
        with pytest.raises(A2AError) as exc_info:
            validate_mandate(task)
        # Should NOT contain raw exception details like "Invalid isoformat"
        msg = str(exc_info.value)
        assert "fromisoformat" not in msg.lower()
        assert "fail-closed" in msg.lower()


class TestBug2MandateExpirationGate:
    """Bug 2: Expired mandate must be caught by preflight_check."""

    def test_expired_mandate_blocked_by_preflight(self):
        """Expired mandate should fail preflight with mandate_expired gate."""
        expired_mandate = Mandate(
            mandate_id="m-expired",
            intent="test",
            risk_tier="R2",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),  # In the past
        )
        results = preflight_check("iam-compliance", "R2", expired_mandate)
        blocking = PolicyGate.get_blocking_gates(results)
        assert len(blocking) > 0
        gate_names = [g.gate_name for g in blocking]
        assert "mandate_expired" in gate_names

    def test_valid_mandate_passes_expiration_gate(self):
        """Non-expired mandate should pass expiration gate."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        valid_mandate = Mandate(
            mandate_id="m-valid",
            intent="test",
            risk_tier="R1",
            expires_at=future,
        )
        result = PolicyGate.check_mandate_expired(valid_mandate)
        assert result.allowed is True

    def test_no_mandate_passes_expiration_gate(self):
        """No mandate at all should pass expiration gate."""
        result = PolicyGate.check_mandate_expired(None)
        assert result.allowed is True

    def test_no_expiry_passes_expiration_gate(self):
        """Mandate with no expires_at should pass expiration gate."""
        mandate = Mandate(
            mandate_id="m-noexpiry",
            intent="test",
        )
        result = PolicyGate.check_mandate_expired(mandate)
        assert result.allowed is True

    def test_expired_mandate_blocks_via_dispatcher(self):
        """Expired mandate causes A2AError in validate_mandate."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask, A2AError

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-expired",
                "intent": "test",
                "risk_tier": "R2",
                "expires_at": "2020-01-01T00:00:00+00:00",
            }
        )
        with pytest.raises(A2AError, match="Policy gate check failed"):
            validate_mandate(task)


class TestBug3RecordInvocation:
    """Bug 3: record_invocation must increment counters."""

    def test_record_invocation_increments_iterations(self):
        """record_invocation() should increment iterations_used."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            max_iterations=10,
            iterations_used=0,
        )
        mandate.record_invocation()
        assert mandate.iterations_used == 1

    def test_record_invocation_increments_budget(self):
        """record_invocation() should increment budget_spent."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            budget_limit=1.0,
            budget_spent=0.0,
        )
        mandate.record_invocation(cost=0.05)
        assert mandate.budget_spent == 0.05

    def test_record_invocation_repeated_calls(self):
        """Multiple record_invocation() calls accumulate correctly."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            max_iterations=10,
            budget_limit=1.0,
        )
        for _ in range(5):
            mandate.record_invocation(cost=0.10)
        assert mandate.iterations_used == 5
        assert abs(mandate.budget_spent - 0.50) < 1e-9

    def test_exhausted_after_max_iterations(self):
        """After max_iterations invocations, is_iterations_exhausted returns True."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            max_iterations=3,
        )
        for _ in range(3):
            mandate.record_invocation()
        assert mandate.is_iterations_exhausted() is True

    def test_budget_exhausted_after_limit(self):
        """After budget_limit spent, is_budget_exhausted returns True."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            budget_limit=0.50,
        )
        for _ in range(5):
            mandate.record_invocation(cost=0.10)
        assert mandate.is_budget_exhausted() is True


class TestValidateMandateReturnValue:
    """validate_mandate() returns parsed Mandate for reuse (no duplicate parsing)."""

    def test_returns_mandate_when_present(self):
        """validate_mandate() returns Mandate object when task has mandate."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
            mandate={
                "mandate_id": "m-ret",
                "intent": "return test",
                "risk_tier": "R1",
                "budget_limit": 5.0,
                "iterations_used": 3,
            }
        )
        result = validate_mandate(task)
        assert result is not None
        assert result.mandate_id == "m-ret"
        assert result.risk_tier == "R1"
        assert result.budget_limit == 5.0
        assert result.iterations_used == 3

    def test_returns_none_without_mandate(self):
        """validate_mandate() returns None when task has no mandate."""
        from agents.a2a.dispatcher import validate_mandate
        from agents.a2a.types import A2ATask

        task = A2ATask(
            specialist="iam-compliance",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob"},
        )
        result = validate_mandate(task)
        assert result is None


class TestMandateFromDictHelper:
    """_mandate_from_dict() shared helper parses all fields correctly."""

    def test_parses_all_enterprise_fields(self):
        """All enterprise control fields are parsed by shared helper."""
        from agents.a2a.dispatcher import _mandate_from_dict

        mandate = _mandate_from_dict({
            "mandate_id": "m-full",
            "intent": "full test",
            "risk_tier": "R3",
            "tool_allowlist": ["search_code"],
            "data_classification": "confidential",
            "approval_state": "approved",
            "approver_id": "admin@example.com",
            "budget_limit": 10.0,
            "budget_spent": 2.5,
            "max_iterations": 50,
            "iterations_used": 7,
        })
        assert mandate.mandate_id == "m-full"
        assert mandate.risk_tier == "R3"
        assert mandate.tool_allowlist == ["search_code"]
        assert mandate.data_classification == "confidential"
        assert mandate.approval_state == "approved"
        assert mandate.approver_id == "admin@example.com"
        assert mandate.budget_limit == 10.0
        assert mandate.budget_spent == 2.5
        assert mandate.iterations_used == 7

    def test_raises_on_bad_datetime(self):
        """Malformed datetime fields raise ValueError."""
        from agents.a2a.dispatcher import _mandate_from_dict

        with pytest.raises((ValueError, TypeError, AttributeError)):
            _mandate_from_dict({
                "mandate_id": "m-bad",
                "intent": "test",
                "expires_at": "garbage",
            })


class TestBug4ToolAllowlistPreflightCount:
    """Bug 4: Preflight should include mandate_expired gate in results."""

    def test_preflight_returns_4_gates_without_tools(self):
        """Preflight without tools_to_use should return 4 gates (including mandate_expired)."""
        mandate = Mandate(mandate_id="m-001", intent="test", risk_tier="R1")
        results = preflight_check("iam-compliance", "R1", mandate)
        gate_names = [r.gate_name for r in results]
        assert "mandate_required" in gate_names
        assert "mandate_expired" in gate_names
        assert "approval_required" in gate_names
        assert "specialist_authorized" in gate_names
        assert len(results) == 4

    def test_preflight_returns_extra_gates_with_tools(self):
        """Preflight with tools_to_use should add tool_allowed gates."""
        mandate = Mandate(
            mandate_id="m-001",
            intent="test",
            risk_tier="R1",
            tool_allowlist=["search_code"],
        )
        results = preflight_check(
            "iam-compliance", "R1", mandate,
            tools_to_use=["search_code", "write_file"]
        )
        # 4 base gates + 2 tool gates
        assert len(results) == 6
        tool_gates = [r for r in results if r.gate_name == "tool_allowed"]
        assert len(tool_gates) == 2
