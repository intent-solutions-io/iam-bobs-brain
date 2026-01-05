"""
Integration tests for A2A (Agent-to-Agent) delegation from foreman to specialists.

Phase 17: Tests real A2A wiring using AgentCard contracts and local invocation.
Phase H+: Updated for async A2A dispatch.

Tests:
- Happy path delegation to specialists
- Skill existence validation
- AgentCard alignment
- Input structure validation
- Error handling
"""

import pytest
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add repo root to path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import A2A components (using sync wrapper for test compatibility)
from agents.a2a import A2ATask, A2AResult, A2AError, call_specialist_sync, discover_specialists
from agents.a2a.dispatcher import (
    load_agentcard,
    validate_skill_exists,
    validate_input_structure,
)

# Repository root already defined above

# Check if google.adk is available (Phase 18)
try:
    import google.adk
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

# Check if Vertex AI environment is configured (for real agent execution)
VERTEX_AI_CONFIGURED = all([
    os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CLOUD_REGION"),
])

# Pytest marker for tests requiring ADK
requires_adk = pytest.mark.skipif(
    not ADK_AVAILABLE,
    reason="google.adk not installed (expected in local environment, runs in Agent Engine)"
)

# Pytest marker for tests that need Vertex AI credentials to run real agents
requires_vertex_ai = pytest.mark.skipif(
    not VERTEX_AI_CONFIGURED,
    reason="Vertex AI not configured (set PROJECT_ID and credentials for real agent execution)"
)


class TestAgentCardDiscovery:
    """Test AgentCard loading and discovery."""

    def test_load_agentcard_for_all_specialists(self):
        """Verify all specialists have valid AgentCards."""
        specialists = [
            "iam_adk",
            "iam_issue",
            "iam_fix_plan",
            "iam_fix_impl",
            "iam_qa",
            "iam_doc",
            "iam_cleanup",
            "iam_index",
        ]

        for specialist in specialists:
            agentcard = load_agentcard(specialist)

            # Verify required fields
            assert "name" in agentcard, f"{specialist} missing 'name'"
            assert "description" in agentcard, f"{specialist} missing 'description'"
            assert "skills" in agentcard, f"{specialist} missing 'skills'"
            assert "spiffe_id" in agentcard, f"{specialist} missing 'spiffe_id'"

    def test_discover_all_specialists(self):
        """Test discover_specialists returns all available specialists."""
        specialists = discover_specialists()

        # Should find at least 8 specialists
        assert len(specialists) >= 8

        # Each specialist should have required metadata
        for spec in specialists:
            assert "name" in spec
            assert "capabilities" in spec
            assert "skills" in spec
            assert "description" in spec

    def test_agentcard_not_found_raises_error(self):
        """Verify loading non-existent AgentCard raises A2AError."""
        with pytest.raises(A2AError, match="AgentCard not found"):
            load_agentcard("non_existent_specialist")


class TestSkillValidation:
    """Test skill existence and input validation."""

    def test_validate_skill_exists_happy_path(self):
        """Verify skill validation for valid skill_id."""
        agentcard = load_agentcard("iam_adk")

        # iam_adk should have check_adk_compliance skill
        skill = validate_skill_exists(
            agentcard,
            "iam_adk.check_adk_compliance",
            "iam_adk"
        )

        # AgentCard uses "id" field, not "skill_id"
        assert skill["id"] == "iam_adk.check_adk_compliance"
        assert "input_schema" in skill
        assert "output_schema" in skill

    def test_validate_skill_not_found_raises_error(self):
        """Verify non-existent skill raises A2AError."""
        agentcard = load_agentcard("iam_adk")

        with pytest.raises(A2AError, match="Skill .* not found"):
            validate_skill_exists(
                agentcard,
                "iam_adk.non_existent_skill",
                "iam_adk"
            )

    def test_validate_input_structure_happy_path(self):
        """Verify input validation passes with correct payload."""
        agentcard = load_agentcard("iam_adk")
        skill = validate_skill_exists(
            agentcard,
            "iam_adk.check_adk_compliance",
            "iam_adk"
        )

        input_schema = skill["input_schema"]
        payload = {
            "target": "agents/bob/agent.py",
            "focus_rules": ["R1", "R5"]
        }

        # Should not raise
        validate_input_structure(payload, input_schema, "iam_adk.check_adk_compliance")

    def test_validate_input_structure_missing_required_field(self):
        """Verify input validation fails when required field is missing."""
        agentcard = load_agentcard("iam_adk")
        skill = validate_skill_exists(
            agentcard,
            "iam_adk.check_adk_compliance",
            "iam_adk"
        )

        input_schema = skill["input_schema"]
        payload = {
            # Missing 'target' field
            "focus_rules": ["R1", "R5"]
        }

        with pytest.raises(A2AError, match="missing required fields"):
            validate_input_structure(payload, input_schema, "iam_adk.check_adk_compliance")


class TestA2ADelegation:
    """Test end-to-end A2A delegation from foreman to specialists."""

    @requires_vertex_ai
    def test_call_specialist_happy_path(self):
        """Test successful delegation to iam_adk specialist.

        Phase 18: This test works in both environments:
        - Without ADK: Returns mock result with 'mock' flag
        - With ADK: Returns real execution result via Runner
        """
        task = A2ATask(
            specialist="iam_adk",
            skill_id="iam_adk.check_adk_compliance",
            payload={
                "target": "agents/bob/agent.py",
                "focus_rules": ["R1", "R5"]
            },
            context={"request_id": "test_123"},
            spiffe_id="spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0"
        )

        result = call_specialist_sync(task)

        # Verify result structure (works in both mock and real mode)
        assert isinstance(result, A2AResult)
        assert result.status == "SUCCESS"
        assert result.specialist == "iam_adk"
        assert result.skill_id == "iam_adk.check_adk_compliance"
        assert result.result is not None
        assert result.duration_ms is not None
        assert result.timestamp is not None

        # Check if this is mock or real execution
        if ADK_AVAILABLE:
            # Real execution - result should NOT have 'mock' flag
            assert result.result.get("mock") is None or result.result.get("mock") is False
        else:
            # Mock execution - result should have 'mock' flag
            assert result.result.get("mock") is True

    def test_call_specialist_with_non_existent_specialist(self):
        """Test delegation to non-existent specialist raises A2AError."""
        task = A2ATask(
            specialist="non_existent",
            skill_id="non_existent.some_skill",
            payload={},
            spiffe_id="spiffe://intent.solutions/agent/test/dev/us-central1/0.1.0"
        )

        with pytest.raises(A2AError, match="AgentCard not found"):
            call_specialist_sync(task)

    def test_call_specialist_with_invalid_skill(self):
        """Test delegation with invalid skill_id raises A2AError."""
        task = A2ATask(
            specialist="iam_adk",
            skill_id="iam_adk.non_existent_skill",
            payload={"target": "agents/bob/agent.py"},
            spiffe_id="spiffe://intent.solutions/agent/test/dev/us-central1/0.1.0"
        )

        with pytest.raises(A2AError, match="Skill .* not found"):
            call_specialist_sync(task)

    def test_call_specialist_with_missing_required_input(self):
        """Test delegation with missing required input raises A2AError."""
        task = A2ATask(
            specialist="iam_adk",
            skill_id="iam_adk.check_adk_compliance",
            payload={
                # Missing 'target' field
                "focus_rules": ["R1"]
            },
            spiffe_id="spiffe://intent.solutions/agent/test/dev/us-central1/0.1.0"
        )

        with pytest.raises(A2AError, match="missing required fields"):
            call_specialist_sync(task)


class TestForemanDelegationTools:
    """Test foreman's delegation tool functions."""

    @staticmethod
    def _load_delegation_module():
        """Helper to load delegation module using importlib."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "delegation",
            str(REPO_ROOT / "agents" / "iam_senior_adk_devops_lead" / "tools" / "delegation.py")
        )
        if spec and spec.loader:
            delegation = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(delegation)
            return delegation
        raise ImportError("Could not load delegation module")

    def test_check_specialist_availability(self):
        """Test check_specialist_availability for valid specialists."""
        delegation = self._load_delegation_module()

        # Valid specialists should be available
        assert delegation.check_specialist_availability("iam_adk") is True
        assert delegation.check_specialist_availability("iam_issue") is True
        assert delegation.check_specialist_availability("iam_qa") is True

        # Invalid specialist should not be available
        assert delegation.check_specialist_availability("non_existent") is False

    def test_get_specialist_capabilities(self):
        """Test get_specialist_capabilities returns AgentCard data."""
        delegation = self._load_delegation_module()

        capabilities = delegation.get_specialist_capabilities("iam_adk")

        # Verify structure
        assert "description" in capabilities
        assert "capabilities" in capabilities
        assert "skills" in capabilities
        assert "spiffe_id" in capabilities

        # Verify skills list
        assert len(capabilities["skills"]) > 0
        assert any("iam_adk." in skill for skill in capabilities["skills"])

    @requires_vertex_ai
    def test_delegate_to_specialist(self):
        """Test delegate_to_specialist with valid inputs.

        Phase 18: Works in both environments (mock and real execution).
        """
        delegation = self._load_delegation_module()

        result = delegation.delegate_to_specialist(
            specialist="iam_adk",
            skill_id="iam_adk.check_adk_compliance",
            payload={
                "target": "agents/bob/agent.py",
                "focus_rules": ["R1", "R5"]
            },
            context={"request_id": "test_456"}
        )

        # Verify result structure (works in both mock and real mode)
        assert "specialist" in result
        assert "status" in result
        assert "result" in result
        assert "metadata" in result

        # Verify metadata
        assert result["metadata"]["a2a_protocol"] is True
        assert result["metadata"]["phase"] == "Phase 17 - Real A2A Wiring"

        # Check if this is mock or real execution
        if ADK_AVAILABLE:
            # Real execution - result should NOT have 'mock' flag
            assert result["result"].get("mock") is None or result["result"].get("mock") is False
        else:
            # Mock execution - result should have 'mock' flag
            assert result["result"].get("mock") is True

    @requires_vertex_ai
    def test_delegate_to_multiple(self):
        """Test delegate_to_multiple with sequential execution."""
        delegation = self._load_delegation_module()

        delegations = [
            {
                "specialist": "iam_adk",
                "skill_id": "iam_adk.check_adk_compliance",
                "payload": {"target": "agents/bob/agent.py"}
            },
            {
                "specialist": "iam_issue",
                "skill_id": "iam_issue.create_issue_spec",
                "payload": {
                    "title": "Test issue",
                    "description": "Test description"
                }
            }
        ]

        results = delegation.delegate_to_multiple(delegations, execution_mode="sequential")

        # Verify results
        assert len(results) == 2
        assert all("specialist" in r for r in results)
        assert all("status" in r for r in results)


class TestR7SPIFFEPropagation:
    """Test R7 SPIFFE ID propagation through A2A calls."""

    def test_spiffe_id_in_task(self):
        """Verify SPIFFE ID is propagated in A2ATask."""
        foreman_spiffe = "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.10.0"

        task = A2ATask(
            specialist="iam_adk",
            skill_id="iam_adk.check_adk_compliance",
            payload={"target": "agents/bob/agent.py"},
            spiffe_id=foreman_spiffe
        )

        assert task.spiffe_id == foreman_spiffe

    def test_spiffe_id_in_agentcard(self):
        """Verify all AgentCards have SPIFFE ID field."""
        specialists = [
            "iam_adk",
            "iam_issue",
            "iam_fix_plan",
            "iam_fix_impl",
            "iam_qa",
            "iam_doc",
            "iam_cleanup",
            "iam_index",
        ]

        for specialist in specialists:
            agentcard = load_agentcard(specialist)
            assert "spiffe_id" in agentcard, f"{specialist} missing SPIFFE ID"
            assert agentcard["spiffe_id"].startswith("spiffe://"), \
                f"{specialist} SPIFFE ID doesn't start with spiffe://"


class TestAgentCardSkillsAlignment:
    """Test that all specialists' AgentCards follow skill naming conventions."""

    def test_all_skills_follow_naming_convention(self):
        """Verify all skills follow {directory}.{skill} naming convention.

        Note: Skill IDs use directory names (iam_adk) not canonical IDs (iam-compliance).
        """
        specialists = discover_specialists()

        for spec in specialists:
            directory = spec["directory"]
            skills = spec["skills"]

            for skill_id in skills:
                # Skill ID should start with directory name (iam_adk, iam_issue, etc.)
                assert skill_id is not None, \
                    f"Skill ID is None for {directory}"
                assert skill_id.startswith(f"{directory}."), \
                    f"Skill '{skill_id}' doesn't follow naming convention for {directory}"

    def test_all_skills_have_schemas(self):
        """Verify all skills have input_schema and output_schema."""
        specialists = discover_specialists()

        for spec in specialists:
            specialist_name = spec["name"]
            agentcard = load_agentcard(specialist_name)

            for skill in agentcard.get("skills", []):
                skill_id = skill.get("id")  # AgentCard uses "id" not "skill_id"

                assert "input_schema" in skill, \
                    f"Skill '{skill_id}' missing input_schema"
                assert "output_schema" in skill, \
                    f"Skill '{skill_id}' missing output_schema"

                # Verify schemas have required fields
                assert "type" in skill["input_schema"], \
                    f"Skill '{skill_id}' input_schema missing 'type'"
                assert "type" in skill["output_schema"], \
                    f"Skill '{skill_id}' output_schema missing 'type'"
