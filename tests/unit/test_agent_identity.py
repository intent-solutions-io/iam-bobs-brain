"""
Unit tests for agent identity module (252-DR-STND).

Tests canonical ID resolution, alias mapping, and backwards compatibility.
"""

import pytest
import warnings
from agents.shared_contracts.agent_identity import (
    # Types
    AgentTier,
    AgentDefinition,
    # Data
    CANONICAL_AGENTS,
    AGENT_ALIASES,
    CANONICAL_TO_DIRECTORY,
    DIRECTORY_TO_CANONICAL,
    # Functions
    canonicalize,
    is_canonical,
    is_valid,
    get_definition,
    get_directory,
    get_spiffe_id,
    list_canonical_ids,
    list_by_tier,
    list_specialists,
)


class TestCanonicalAgents:
    """Test the canonical agent registry."""

    def test_all_canonical_ids_defined(self):
        """All expected canonical IDs are in the registry."""
        expected = [
            "bob",
            "iam-orchestrator",
            "iam-compliance",
            "iam-triage",
            "iam-planner",
            "iam-engineer",
            "iam-qa",
            "iam-docs",
            "iam-hygiene",
            "iam-index",
        ]
        assert sorted(CANONICAL_AGENTS.keys()) == sorted(expected)

    def test_canonical_agents_have_required_fields(self):
        """All canonical agents have required definition fields."""
        for agent_id, defn in CANONICAL_AGENTS.items():
            assert isinstance(defn, AgentDefinition)
            assert defn.canonical_id == agent_id
            assert defn.tier in AgentTier
            assert len(defn.description) > 0
            assert "{env}" in defn.spiffe_template
            assert "{region}" in defn.spiffe_template
            assert "{version}" in defn.spiffe_template

    def test_bob_is_tier_1(self):
        """Bob is correctly classified as Tier 1."""
        assert CANONICAL_AGENTS["bob"].tier == AgentTier.TIER_1_UI

    def test_orchestrator_is_tier_2(self):
        """iam-orchestrator is correctly classified as Tier 2."""
        assert CANONICAL_AGENTS["iam-orchestrator"].tier == AgentTier.TIER_2_ORCHESTRATOR

    def test_specialists_are_tier_3(self):
        """All iam-* specialists are Tier 3."""
        specialists = [
            "iam-compliance",
            "iam-triage",
            "iam-planner",
            "iam-engineer",
            "iam-qa",
            "iam-docs",
            "iam-hygiene",
            "iam-index",
        ]
        for specialist in specialists:
            assert CANONICAL_AGENTS[specialist].tier == AgentTier.TIER_3_SPECIALIST


class TestAliasMap:
    """Test the alias map for backwards compatibility."""

    def test_canonical_ids_map_to_themselves(self):
        """Canonical IDs should map to themselves."""
        for canonical_id in CANONICAL_AGENTS.keys():
            assert AGENT_ALIASES[canonical_id] == canonical_id

    def test_legacy_ids_map_to_canonical(self):
        """Legacy IDs should map to their canonical equivalents."""
        legacy_mappings = {
            "iam_adk": "iam-compliance",
            "iam_issue": "iam-triage",
            "iam_fix_plan": "iam-planner",
            "iam_fix_impl": "iam-engineer",
            "iam_qa": "iam-qa",
            "iam_doc": "iam-docs",
            "iam_cleanup": "iam-hygiene",
            "iam_index": "iam-index",
            "iam_senior_adk_devops_lead": "iam-orchestrator",
            "iam-senior-adk-devops-lead": "iam-orchestrator",
        }
        for legacy, canonical in legacy_mappings.items():
            assert AGENT_ALIASES.get(legacy) == canonical, f"{legacy} -> {canonical}"


class TestCanonicalize:
    """Test the canonicalize function."""

    def test_canonical_id_returns_itself(self):
        """Canonical ID returns itself without warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = canonicalize("iam-compliance")
            assert result == "iam-compliance"
            # No deprecation warning for canonical IDs
            assert len([x for x in w if issubclass(x.category, DeprecationWarning)]) == 0

    def test_legacy_id_returns_canonical_with_warning(self):
        """Legacy ID returns canonical ID with deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = canonicalize("iam_adk")
            assert result == "iam-compliance"
            # Should have deprecation warning
            assert len([x for x in w if issubclass(x.category, DeprecationWarning)]) == 1

    def test_legacy_id_no_warning_when_disabled(self):
        """Legacy ID returns canonical ID without warning when warn=False."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = canonicalize("iam_adk", warn=False)
            assert result == "iam-compliance"
            # No warning when disabled
            assert len([x for x in w if issubclass(x.category, DeprecationWarning)]) == 0

    def test_unknown_id_raises_value_error(self):
        """Unknown ID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            canonicalize("unknown-agent")
        assert "Unknown agent ID" in str(exc_info.value)

    def test_foreman_aliases(self):
        """All foreman aliases resolve to iam-orchestrator."""
        foreman_aliases = [
            "iam_senior_adk_devops_lead",
            "iam-senior-adk-devops-lead",
            "iam_foreman",
            "iam-foreman",
            "foreman",
        ]
        for alias in foreman_aliases:
            result = canonicalize(alias, warn=False)
            assert result == "iam-orchestrator", f"{alias} should map to iam-orchestrator"


class TestIsCanonical:
    """Test the is_canonical function."""

    def test_canonical_ids_return_true(self):
        """Canonical IDs return True."""
        for canonical_id in CANONICAL_AGENTS.keys():
            assert is_canonical(canonical_id) is True

    def test_legacy_ids_return_false(self):
        """Legacy IDs return False."""
        legacy_ids = ["iam_adk", "iam_issue", "iam_senior_adk_devops_lead"]
        for legacy_id in legacy_ids:
            assert is_canonical(legacy_id) is False

    def test_unknown_ids_return_false(self):
        """Unknown IDs return False."""
        assert is_canonical("unknown-agent") is False


class TestIsValid:
    """Test the is_valid function."""

    def test_canonical_ids_are_valid(self):
        """Canonical IDs are valid."""
        for canonical_id in CANONICAL_AGENTS.keys():
            assert is_valid(canonical_id) is True

    def test_legacy_ids_are_valid(self):
        """Legacy IDs are valid (for backwards compatibility)."""
        legacy_ids = ["iam_adk", "iam_issue", "iam_senior_adk_devops_lead"]
        for legacy_id in legacy_ids:
            assert is_valid(legacy_id) is True

    def test_unknown_ids_are_invalid(self):
        """Unknown IDs are invalid."""
        assert is_valid("unknown-agent") is False


class TestGetDefinition:
    """Test the get_definition function."""

    def test_canonical_id_returns_definition(self):
        """Canonical ID returns the correct definition."""
        defn = get_definition("iam-compliance")
        assert defn.canonical_id == "iam-compliance"
        assert defn.tier == AgentTier.TIER_3_SPECIALIST

    def test_legacy_id_returns_definition(self):
        """Legacy ID returns the definition for the canonical equivalent."""
        defn = get_definition("iam_adk")
        assert defn.canonical_id == "iam-compliance"

    def test_unknown_id_raises_error(self):
        """Unknown ID raises ValueError."""
        with pytest.raises(ValueError):
            get_definition("unknown-agent")


class TestGetDirectory:
    """Test the get_directory function."""

    def test_canonical_id_returns_directory(self):
        """Canonical ID returns the correct directory."""
        assert get_directory("iam-compliance") == "iam_adk"
        assert get_directory("iam-orchestrator") == "iam_senior_adk_devops_lead"

    def test_legacy_id_returns_directory(self):
        """Legacy ID returns the correct directory."""
        assert get_directory("iam_adk") == "iam_adk"

    def test_all_directories_exist(self):
        """All mapped directories should be valid."""
        for canonical_id in CANONICAL_AGENTS.keys():
            directory = get_directory(canonical_id)
            assert directory in CANONICAL_TO_DIRECTORY.values()


class TestGetSpiffeId:
    """Test the get_spiffe_id function."""

    def test_default_spiffe_id(self):
        """Default SPIFFE ID uses default env/region/version."""
        spiffe = get_spiffe_id("iam-compliance")
        assert "spiffe://intent.solutions/agent/iam-compliance/dev/us-central1/0.1.0" == spiffe

    def test_custom_spiffe_id(self):
        """Custom SPIFFE ID uses provided parameters."""
        spiffe = get_spiffe_id("iam-compliance", env="prod", region="us-east1", version="1.0.0")
        assert "spiffe://intent.solutions/agent/iam-compliance/prod/us-east1/1.0.0" == spiffe

    def test_legacy_id_spiffe(self):
        """Legacy ID generates SPIFFE for canonical equivalent."""
        spiffe = get_spiffe_id("iam_adk")
        assert "iam-compliance" in spiffe


class TestListFunctions:
    """Test the list functions."""

    def test_list_canonical_ids(self):
        """list_canonical_ids returns all canonical IDs."""
        ids = list_canonical_ids()
        assert len(ids) == 10
        assert "bob" in ids
        assert "iam-orchestrator" in ids
        assert "iam-compliance" in ids

    def test_list_by_tier_ui(self):
        """list_by_tier for TIER_1_UI returns only bob."""
        ids = list_by_tier(AgentTier.TIER_1_UI)
        assert ids == ["bob"]

    def test_list_by_tier_orchestrator(self):
        """list_by_tier for TIER_2_ORCHESTRATOR returns iam-orchestrator."""
        ids = list_by_tier(AgentTier.TIER_2_ORCHESTRATOR)
        assert ids == ["iam-orchestrator"]

    def test_list_by_tier_specialist(self):
        """list_by_tier for TIER_3_SPECIALIST returns all specialists."""
        ids = list_by_tier(AgentTier.TIER_3_SPECIALIST)
        assert len(ids) == 8
        assert "iam-compliance" in ids
        assert "iam-qa" in ids

    def test_list_specialists(self):
        """list_specialists returns all Tier 3 specialists."""
        specialists = list_specialists()
        assert len(specialists) == 8
        assert "bob" not in specialists
        assert "iam-orchestrator" not in specialists


class TestDirectoryMapping:
    """Test directory name mappings."""

    def test_canonical_to_directory_complete(self):
        """All canonical IDs have directory mappings."""
        for canonical_id in CANONICAL_AGENTS.keys():
            assert canonical_id in CANONICAL_TO_DIRECTORY

    def test_directory_to_canonical_reverse(self):
        """Directory mappings are reversible."""
        for canonical_id, directory in CANONICAL_TO_DIRECTORY.items():
            assert DIRECTORY_TO_CANONICAL[directory] == canonical_id
