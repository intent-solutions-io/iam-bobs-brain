"""
Unit tests for all IAM specialist agents.

Provides test coverage for:
- iam_issue: GitHub issue creation
- iam_cleanup: Repository hygiene
- iam_index: Knowledge indexing
- iam_fix_plan: Fix planning
- iam_doc: Documentation
- iam_fix_impl: Fix implementation
- iam_qa: Testing and validation

These tests validate:
1. Agent module structure (create_agent, create_app, app symbols)
2. Valid Python syntax
3. Lazy-loading pattern compliance (6767-LAZY)
4. AgentCard JSON validity (if present)

Note: Full ADK tests require google-adk package.
"""

import ast
import json
from pathlib import Path

import pytest

# All IAM specialist agents (excluding foreman/orchestrator)
IAM_SPECIALISTS = [
    "iam_issue",
    "iam_cleanup",
    "iam_index",
    "iam_fix_plan",
    "iam_doc",
    "iam_fix_impl",
    "iam_qa",
]


class TestIAMSpecialistStructure:
    """Test that all IAM specialists have correct module structure."""

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_py_exists(self, agent_name):
        """Test that agent.py exists for each specialist."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        assert agent_path.exists(), f"{agent_name}/agent.py not found"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_py_valid_syntax(self, agent_name):
        """Test that agent.py has valid Python syntax."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"{agent_name}/agent.py has syntax error: {e}")

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_has_required_symbols(self, agent_name):
        """Test that agent.py defines required symbols (via AST inspection).

        Accepts either:
        - New 6767-LAZY pattern: create_agent, create_app, app
        - Old pattern: get_agent, create_runner, root_agent
        """
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Collect all function and variable names at module level
        symbols = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.add(target.id)

        # Accept either new (6767-LAZY) or old pattern
        new_pattern = {"create_agent", "create_app", "app"}
        old_pattern = {"get_agent", "create_runner", "root_agent"}

        has_new = new_pattern.issubset(symbols)
        has_old = old_pattern.issubset(symbols)

        assert has_new or has_old, \
            f"{agent_name} must define either 6767-LAZY pattern (create_agent, create_app, app) " \
            f"or old pattern (get_agent, create_runner, root_agent). Found: {symbols}"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_uses_adk_imports(self, agent_name):
        """Test that agent.py uses ADK imports (R1 compliance)."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Must import from google.adk
        has_adk_import = False
        forbidden_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("google.adk"):
                        has_adk_import = True
                    # Check for forbidden frameworks
                    for forbidden in ["langchain", "crewai", "autogen"]:
                        if alias.name.startswith(forbidden):
                            forbidden_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("google.adk"):
                    has_adk_import = True
                # Check for forbidden frameworks
                if node.module:
                    for forbidden in ["langchain", "crewai", "autogen"]:
                        if node.module.startswith(forbidden):
                            forbidden_imports.append(node.module)

        assert has_adk_import, f"{agent_name} must import from google.adk (R1)"
        assert not forbidden_imports, \
            f"{agent_name} has forbidden imports (R1 violation): {forbidden_imports}"


class TestIAMSpecialistAgentCards:
    """Test AgentCard JSON validity for IAM specialists."""

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agentcard_exists(self, agent_name):
        """Test that AgentCard JSON exists for each specialist."""
        card_path = Path(f"agents/{agent_name}/.well-known/agent-card.json")
        assert card_path.exists(), f"{agent_name} missing .well-known/agent-card.json"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agentcard_valid_json(self, agent_name):
        """Test that AgentCard is valid JSON."""
        card_path = Path(f"agents/{agent_name}/.well-known/agent-card.json")
        if not card_path.exists():
            pytest.skip(f"No AgentCard for {agent_name}")

        with open(card_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"{agent_name} AgentCard has invalid JSON: {e}")

        assert isinstance(data, dict), "AgentCard must be a JSON object"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agentcard_has_required_fields(self, agent_name):
        """Test that AgentCard has required A2A fields."""
        card_path = Path(f"agents/{agent_name}/.well-known/agent-card.json")
        if not card_path.exists():
            pytest.skip(f"No AgentCard for {agent_name}")

        with open(card_path) as f:
            data = json.load(f)

        required_fields = ["name", "description", "version", "skills"]
        for field in required_fields:
            assert field in data, f"{agent_name} AgentCard missing '{field}'"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agentcard_skills_not_empty(self, agent_name):
        """Test that AgentCard has at least one skill."""
        card_path = Path(f"agents/{agent_name}/.well-known/agent-card.json")
        if not card_path.exists():
            pytest.skip(f"No AgentCard for {agent_name}")

        with open(card_path) as f:
            data = json.load(f)

        skills = data.get("skills", [])
        assert len(skills) > 0, f"{agent_name} must have at least one skill"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agentcard_skill_has_id(self, agent_name):
        """Test that each skill has an ID."""
        card_path = Path(f"agents/{agent_name}/.well-known/agent-card.json")
        if not card_path.exists():
            pytest.skip(f"No AgentCard for {agent_name}")

        with open(card_path) as f:
            data = json.load(f)

        for skill in data.get("skills", []):
            assert "id" in skill, f"{agent_name} skill missing 'id' field"


class TestIAMSpecialistLazyLoading:
    """Test lazy-loading pattern compliance.

    Accepts both:
    - New 6767-LAZY pattern: create_agent(), create_app(), app
    - Old pattern: get_agent(), create_runner(), root_agent
    """

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_no_eager_agent_instantiation(self, agent_name):
        """Test that agent is not instantiated at module level with LlmAgent()."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Look for module-level LlmAgent(...) instantiation (bad pattern)
        # Pattern: agent = LlmAgent(...) at module level
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "agent":
                        if isinstance(node.value, ast.Call):
                            call = node.value
                            if isinstance(call.func, ast.Name):
                                func_name = call.func.id
                                # Only fail if directly calling LlmAgent
                                if func_name == "LlmAgent":
                                    pytest.fail(
                                        f"{agent_name} has eager agent instantiation: "
                                        f"agent = LlmAgent(...) at module level"
                                    )

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_no_import_time_validation(self, agent_name):
        """Test that no assert statements exist at module level."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Look for module-level assert statements (bad pattern)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assert):
                pytest.fail(
                    f"{agent_name} has module-level assert (blocks imports)"
                )

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_factory_function_exists(self, agent_name):
        """Test that an agent factory function exists (create_agent or get_agent)."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Accept either create_agent (new) or get_agent (old)
        factory_functions = {"create_agent", "get_agent"}
        found_functions = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in factory_functions:
                found_functions.add(node.name)

        assert found_functions, \
            f"{agent_name} must define create_agent() or get_agent() function"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_app_or_runner_factory_exists(self, agent_name):
        """Test that an app/runner factory function exists (create_app or create_runner)."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Accept either create_app (new) or create_runner (old)
        factory_functions = {"create_app", "create_runner"}
        found_functions = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in factory_functions:
                found_functions.add(node.name)

        assert found_functions, \
            f"{agent_name} must define create_app() or create_runner() function"


class TestIAMSpecialistDocumentation:
    """Test that IAM specialists have documentation."""

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_has_some_documentation(self, agent_name):
        """Test that agent has at least one form of documentation."""
        agent_dir = Path(f"agents/{agent_name}")

        doc_options = [
            agent_dir / "README.md",
            agent_dir / "prompts" / "system.md",
            agent_dir / "prompts" / "system_prompt.md",
            agent_dir / ".well-known" / "agent-card.json",  # AgentCard counts as docs
        ]

        has_docs = any(p.exists() for p in doc_options)
        assert has_docs, f"{agent_name} has no documentation (README, prompts/, or AgentCard)"

    @pytest.mark.parametrize("agent_name", IAM_SPECIALISTS)
    def test_agent_py_has_docstring(self, agent_name):
        """Test that agent.py has a module docstring."""
        agent_path = Path(f"agents/{agent_name}/agent.py")
        with open(agent_path) as f:
            content = f.read()

        tree = ast.parse(content)

        # Check for module docstring
        docstring = ast.get_docstring(tree)
        assert docstring is not None, f"{agent_name}/agent.py should have a module docstring"
