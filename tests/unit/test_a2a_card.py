"""
Test A2A AgentCard - Hard Mode (R7)

Tests AgentCard creation and SPIFFE ID inclusion for all agents.
"""

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        # Required by agent.py
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": "spiffe://test.intent.solutions/agent/bobs-brain/test/us-central1/0.6.0",
        # Required by a2a_card.py
        "APP_NAME": "bobs-brain-test",
        "APP_VERSION": "0.6.0-test",
        "PUBLIC_URL": "https://test.example.com"
    }):
        yield


def test_get_agent_card(mock_env):
    """Test AgentCard creation"""
    from agents.bob.a2a_card import get_agent_card

    card = get_agent_card()

    assert card is not None
    assert card.name == "bobs-brain-test"
    assert card.version == "0.6.0-test"
    assert card.url == "https://test.example.com"
    assert "Bob's Brain" in card.description


def test_agent_card_spiffe_id(mock_env):
    """Test SPIFFE ID is included in AgentCard description (R7)"""
    from agents.bob.a2a_card import get_agent_card

    card = get_agent_card()

    # R7: SPIFFE ID must be in description
    assert "spiffe://test.intent.solutions/agent/bobs-brain/test/us-central1/0.6.0" in card.description


def test_get_agent_card_dict(mock_env):
    """Test AgentCard dict serialization"""
    from agents.bob.a2a_card import get_agent_card_dict

    card_dict = get_agent_card_dict()

    assert isinstance(card_dict, dict)
    assert "name" in card_dict
    assert "description" in card_dict
    assert "url" in card_dict
    assert "version" in card_dict
    assert "skills" in card_dict
    assert "spiffe_id" in card_dict  # R7: Explicit SPIFFE field


def test_agent_card_dict_spiffe_field(mock_env):
    """Test SPIFFE ID is in dict (R7)"""
    from agents.bob.a2a_card import get_agent_card_dict

    card_dict = get_agent_card_dict()

    assert card_dict["spiffe_id"] == "spiffe://test.intent.solutions/agent/bobs-brain/test/us-central1/0.6.0"


def test_agent_card_skills_array(mock_env):
    """Test AgentCard has skills array"""
    from agents.bob.a2a_card import get_agent_card

    card = get_agent_card()

    assert hasattr(card, "skills")
    assert isinstance(card.skills, list)


def test_agent_card_required_fields():
    """Test AgentCard has all required A2A protocol fields"""
    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": "spiffe://test.intent.solutions/agent/bobs-brain/test/us-central1/0.6.0",
        "APP_NAME": "test-agent",
        "APP_VERSION": "1.0.0",
        "PUBLIC_URL": "https://test.com"
    }):
        from agents.bob.a2a_card import get_agent_card

        card = get_agent_card()

        # All required A2A fields must be present
        assert hasattr(card, "name")
        assert hasattr(card, "description")
        assert hasattr(card, "url")
        assert hasattr(card, "version")
        assert hasattr(card, "capabilities")
        assert hasattr(card, "default_input_modes")
        assert hasattr(card, "default_output_modes")
        assert hasattr(card, "skills")

        # Verify types
        assert isinstance(card.default_input_modes, list)
        assert isinstance(card.default_output_modes, list)
        assert "text" in card.default_input_modes
        assert "text" in card.default_output_modes


# --- Parametrized tests for all agents (Bob + 9 IAM agents) ---

ALL_AGENTS = [
    ("bob", "bob", "bobs-brain"),
    ("iam-senior-adk-devops-lead", "iam-senior-adk-devops-lead", "iam-senior-adk-devops-lead"),
    ("iam_adk", "iam_adk", "iam-adk"),
    ("iam_issue", "iam_issue", "iam-issue"),
    ("iam_fix_plan", "iam_fix_plan", "iam-fix-plan"),
    ("iam_fix_impl", "iam_fix_impl", "iam-fix-impl"),
    ("iam_qa", "iam_qa", "iam-qa"),
    ("iam_doc", "iam_doc", "iam-doc"),
    ("iam_cleanup", "iam_cleanup", "iam-cleanup"),
    ("iam_index", "iam_index", "iam-index"),
]


def load_agent_card_module(agent_dir: str):
    """Dynamically load an agent's a2a_card module."""
    repo_root = Path(__file__).parent.parent.parent
    module_file = repo_root / "agents" / agent_dir / "a2a_card.py"

    if not module_file.exists():
        pytest.skip(f"a2a_card.py not found for {agent_dir}")

    spec = importlib.util.spec_from_file_location(f"{agent_dir}.a2a_card", module_file)
    if spec is None or spec.loader is None:
        pytest.skip(f"Could not load spec for {agent_dir}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("agent_dir,module_name,expected_name_prefix", ALL_AGENTS)
def test_all_agents_have_agentcard(agent_dir, module_name, expected_name_prefix):
    """Test all agents have get_agent_card() function"""
    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": f"spiffe://test.intent.solutions/agent/{agent_dir}/test/us-central1/0.10.0",
        "APP_NAME": f"{agent_dir}-test",
        "APP_VERSION": "0.10.0-test",
        "PUBLIC_URL": f"https://{agent_dir}.test.com"
    }):
        module = load_agent_card_module(agent_dir)
        assert hasattr(module, "get_agent_card"), f"{agent_dir} missing get_agent_card()"

        card = module.get_agent_card()
        assert card is not None
        assert hasattr(card, "name")
        assert hasattr(card, "description")


@pytest.mark.parametrize("agent_dir,module_name,expected_name_prefix", ALL_AGENTS)
def test_all_agents_spiffe_in_description(agent_dir, module_name, expected_name_prefix):
    """Test all agents include SPIFFE ID in description (R7)"""
    test_spiffe = f"spiffe://test.intent.solutions/agent/{agent_dir}/test/us-central1/0.10.0"

    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": test_spiffe,
        "APP_NAME": f"{agent_dir}-test",
        "APP_VERSION": "0.10.0-test",
        "PUBLIC_URL": f"https://{agent_dir}.test.com"
    }):
        module = load_agent_card_module(agent_dir)
        card = module.get_agent_card()

        # R7: SPIFFE ID must be in description
        assert test_spiffe in card.description, f"{agent_dir} missing SPIFFE ID in description"


@pytest.mark.parametrize("agent_dir,module_name,expected_name_prefix", ALL_AGENTS)
def test_all_agents_have_card_dict(agent_dir, module_name, expected_name_prefix):
    """Test all agents have get_agent_card_dict() function with spiffe_id field (R7)"""
    test_spiffe = f"spiffe://test.intent.solutions/agent/{agent_dir}/test/us-central1/0.10.0"

    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": test_spiffe,
        "APP_NAME": f"{agent_dir}-test",
        "APP_VERSION": "0.10.0-test",
        "PUBLIC_URL": f"https://{agent_dir}.test.com"
    }):
        module = load_agent_card_module(agent_dir)
        assert hasattr(module, "get_agent_card_dict"), f"{agent_dir} missing get_agent_card_dict()"

        card_dict = module.get_agent_card_dict()

        # R7: Explicit spiffe_id field must be present
        assert "spiffe_id" in card_dict, f"{agent_dir} missing spiffe_id field in dict"
        assert card_dict["spiffe_id"] == test_spiffe


@pytest.mark.parametrize("agent_dir,module_name,expected_name_prefix", ALL_AGENTS)
def test_all_agents_required_fields(agent_dir, module_name, expected_name_prefix):
    """Test all agents have required A2A protocol fields"""
    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": f"spiffe://test.intent.solutions/agent/{agent_dir}/test/us-central1/0.10.0",
        "APP_NAME": f"{agent_dir}-test",
        "APP_VERSION": "0.10.0-test",
        "PUBLIC_URL": f"https://{agent_dir}.test.com"
    }):
        module = load_agent_card_module(agent_dir)
        card = module.get_agent_card()

        # All required A2A fields must be present
        required_fields = ["name", "description", "url", "version", "capabilities",
                          "default_input_modes", "default_output_modes", "skills"]

        for field in required_fields:
            assert hasattr(card, field), f"{agent_dir} missing required field: {field}"

        # Verify types
        assert isinstance(card.default_input_modes, list)
        assert isinstance(card.default_output_modes, list)
        assert "text" in card.default_input_modes
        assert "text" in card.default_output_modes
        assert isinstance(card.skills, list)


@pytest.mark.parametrize("agent_dir,module_name,expected_name_prefix", ALL_AGENTS)
def test_all_agents_have_skills(agent_dir, module_name, expected_name_prefix):
    """Test all agents have at least 3 skills defined"""
    with patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "test-engine-id",
        "AGENT_SPIFFE_ID": f"spiffe://test.intent.solutions/agent/{agent_dir}/test/us-central1/0.10.0",
        "APP_NAME": f"{agent_dir}-test",
        "APP_VERSION": "0.10.0-test",
        "PUBLIC_URL": f"https://{agent_dir}.test.com"
    }):
        module = load_agent_card_module(agent_dir)
        card = module.get_agent_card()

        assert len(card.skills) >= 3, f"{agent_dir} has fewer than 3 skills (found {len(card.skills)})"

        # Verify each skill has required fields
        for i, skill in enumerate(card.skills):
            assert "skill_id" in skill, f"{agent_dir} skill {i} missing skill_id"
            assert "name" in skill, f"{agent_dir} skill {i} missing name"
            assert "description" in skill, f"{agent_dir} skill {i} missing description"
            assert "input_schema" in skill, f"{agent_dir} skill {i} missing input_schema"
            assert "output_schema" in skill, f"{agent_dir} skill {i} missing output_schema"
