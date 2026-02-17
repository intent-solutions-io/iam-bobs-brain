"""
Test JSON AgentCards for Contract Alignment

Validates JSON-based AgentCards (.well-known/agent-card.json) for:
- Valid JSON syntax
- Required A2A protocol fields
- Skill schema structure
- Contract references ($comment fields)

Tests foreman (iam-senior-adk-devops-lead) and specialist (iam-adk) AgentCards.
"""

import json
from pathlib import Path

import pytest


def load_agentcard(agent_name: str) -> dict:
    """Load AgentCard JSON from agent directory."""
    agentcard_path = (
        Path(__file__).parent.parent.parent
        / "agents"
        / agent_name
        / ".well-known"
        / "agent-card.json"
    )

    if not agentcard_path.exists():
        pytest.skip(f"AgentCard not found for {agent_name}: {agentcard_path}")

    with open(agentcard_path) as f:
        return json.load(f)


class TestForemanAgentCard:
    """Tests for iam_senior_adk_devops_lead (foreman) AgentCard."""

    # Note: Directory uses underscores (iam_senior_adk_devops_lead),
    # canonical ID uses hyphens (iam-orchestrator)

    def test_agentcard_loads_valid_json(self):
        """AgentCard JSON is syntactically valid."""
        card = load_agentcard("iam_senior_adk_devops_lead")
        assert isinstance(card, dict)

    def test_required_fields_present(self):
        """AgentCard has all required A2A protocol fields."""
        card = load_agentcard("iam_senior_adk_devops_lead")

        required_fields = ["name", "description", "version", "spiffe_id", "skills"]
        for field in required_fields:
            assert field in card, f"Missing required field: {field}"

    def test_spiffe_id_format(self):
        """SPIFFE ID follows spiffe://intent.solutions/agent pattern."""
        card = load_agentcard("iam_senior_adk_devops_lead")
        spiffe_id = card["spiffe_id"]

        assert spiffe_id.startswith("spiffe://intent.solutions/agent/")
        # SPIFFE ID uses hyphenated canonical name
        assert (
            "iam-senior-adk-devops-lead" in spiffe_id or "iam-orchestrator" in spiffe_id
        )

    def test_skills_array_not_empty(self):
        """AgentCard has at least one skill defined."""
        card = load_agentcard("iam_senior_adk_devops_lead")

        assert "skills" in card
        assert isinstance(card["skills"], list)
        assert len(card["skills"]) > 0

    def test_skill_has_required_structure(self):
        """Each skill has required fields (id, name, description, input_schema, output_schema)."""
        card = load_agentcard("iam_senior_adk_devops_lead")

        for skill in card["skills"]:
            assert "id" in skill  # A2A v0.3.0 uses "id" not "skill_id"
            assert "name" in skill
            assert "description" in skill
            assert "input_schema" in skill
            assert "output_schema" in skill

    @pytest.mark.xfail(
        reason="Contract references ($comment) not yet implemented - future feature"
    )
    def test_contract_references_present(self):
        """AgentCard includes $comment references to contracts in shared_contracts.py."""
        card = load_agentcard("iam_senior_adk_devops_lead")

        # Check that at least one skill has $comment references
        found_input_comment = False
        found_output_comment = False

        for skill in card["skills"]:
            if "$comment" in skill["input_schema"]:
                found_input_comment = True
                assert "shared_contracts.py" in skill["input_schema"]["$comment"]

            if "$comment" in skill["output_schema"]:
                found_output_comment = True
                assert "shared_contracts.py" in skill["output_schema"]["$comment"]

        # At least the main skill should have contract references
        assert (
            found_input_comment or found_output_comment
        ), "No contract references ($comment) found in skill schemas"

    def test_orchestrate_workflow_skill_exists(self):
        """Primary orchestration skill is defined."""
        card = load_agentcard("iam_senior_adk_devops_lead")

        # Skill IDs use directory prefix: iam_senior_adk_devops_lead.{skill}
        skill_ids = [skill["id"] for skill in card["skills"]]
        # Look for any orchestration-related skill
        has_orchestration_skill = any(
            "orchestrate" in sid or "workflow" in sid or "delegate" in sid
            for sid in skill_ids
        )
        assert (
            has_orchestration_skill
        ), f"No orchestration skill found. Skills: {skill_ids}"


class TestSpecialistAgentCard:
    """Tests for iam-adk (specialist) AgentCard."""

    def test_agentcard_loads_valid_json(self):
        """AgentCard JSON is syntactically valid."""
        card = load_agentcard("iam_adk")
        assert isinstance(card, dict)

    def test_required_fields_present(self):
        """AgentCard has all required A2A protocol fields."""
        card = load_agentcard("iam_adk")

        required_fields = ["name", "description", "version", "spiffe_id", "skills"]
        for field in required_fields:
            assert field in card, f"Missing required field: {field}"

    def test_spiffe_id_format(self):
        """SPIFFE ID follows correct pattern."""
        card = load_agentcard("iam_adk")
        spiffe_id = card["spiffe_id"]

        assert spiffe_id.startswith("spiffe://intent.solutions/agent/")

    def test_skills_array_not_empty(self):
        """AgentCard has at least one skill defined."""
        card = load_agentcard("iam_adk")

        assert "skills" in card
        assert isinstance(card["skills"], list)
        assert len(card["skills"]) > 0

    def test_skill_has_required_structure(self):
        """Each skill has required fields."""
        card = load_agentcard("iam_adk")

        for skill in card["skills"]:
            assert (
                "id" in skill
            )  # Changed from skill_id to id for A2A v0.3.0 compliance
            assert "name" in skill
            assert "description" in skill
            assert "input_schema" in skill
            assert "output_schema" in skill

    @pytest.mark.xfail(
        reason="Contract references ($comment) not yet implemented - future feature"
    )
    def test_contract_references_present(self):
        """AgentCard includes $comment references to AnalysisReport/IssueSpec contracts."""
        card = load_agentcard("iam_adk")

        # Check output schema has AnalysisReport reference
        found_reference = False

        for skill in card["skills"]:
            if "$comment" in skill["output_schema"]:
                comment = skill["output_schema"]["$comment"]
                if "AnalysisReport" in comment or "IssueSpec" in comment:
                    found_reference = True
                    assert "shared_contracts.py" in comment

        assert (
            found_reference
        ), "No AnalysisReport/IssueSpec contract reference found in skill output schemas"

    def test_check_adk_compliance_skill_exists(self):
        """Primary ADK compliance checking skill is defined."""
        card = load_agentcard("iam_adk")

        # Skill IDs use directory prefix: iam_adk.{skill}
        skill_ids = [skill["id"] for skill in card["skills"]]
        assert (
            "iam_adk.check_adk_compliance" in skill_ids
        ), f"Skill not found. Skills: {skill_ids}"

    @pytest.mark.xfail(reason="Tags field not yet implemented - future feature")
    def test_specialist_tags(self):
        """AgentCard has appropriate specialist/worker tags."""
        card = load_agentcard("iam_adk")

        tags = card.get("tags", [])
        assert "specialist" in tags or "worker" in tags


class TestAgentCardConsistency:
    """Cross-agent consistency tests."""

    @pytest.mark.xfail(
        reason="Authentication field not yet implemented - future feature"
    )
    def test_both_agentcards_have_authentication(self):
        """Both agents define authentication requirements."""
        foreman_card = load_agentcard("iam_senior_adk_devops_lead")
        specialist_card = load_agentcard("iam_adk")

        assert "authentication" in foreman_card
        assert "authentication" in specialist_card

        assert foreman_card["authentication"]["required"] is True
        assert specialist_card["authentication"]["required"] is True

    @pytest.mark.xfail(reason="Dependencies field not yet implemented - future feature")
    def test_both_use_adk_framework(self):
        """Both agents specify google-adk as framework."""
        foreman_card = load_agentcard("iam_senior_adk_devops_lead")
        specialist_card = load_agentcard("iam_adk")

        assert "dependencies" in foreman_card
        assert "dependencies" in specialist_card

        assert foreman_card["dependencies"]["framework"] == "google-adk"
        assert specialist_card["dependencies"]["framework"] == "google-adk"

    @pytest.mark.xfail(
        reason="Authorization/allowed_callers not yet implemented - future feature"
    )
    def test_specialist_can_only_be_called_by_foreman(self):
        """Specialist authorization allows only foreman to call it."""
        specialist_card = load_agentcard("iam_adk")

        auth = specialist_card.get("authentication", {})
        authorization = auth.get("authorization", {})
        allowed_callers = authorization.get("allowed_callers", [])

        # Should have at least foreman in allowed callers
        foreman_pattern = "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead"
        has_foreman_access = any(
            foreman_pattern in caller for caller in allowed_callers
        )

        assert (
            has_foreman_access
        ), "Specialist must allow foreman (iam-senior-adk-devops-lead) in allowed_callers"
