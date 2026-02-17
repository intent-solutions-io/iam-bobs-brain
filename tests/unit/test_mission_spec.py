"""
Unit tests for Mission Spec v1 (Phase F - Vision Alignment).

Tests:
- Schema validation and parsing
- Compiler execution plan generation
- Deterministic compilation
- Runner CLI commands
"""

import json
import tempfile
from pathlib import Path

import pytest

from agents.mission_spec.compiler import (
    ExecutionPlan,
    PlannedTask,
    compile_mission,
)
from agents.mission_spec.runner import main as runner_main
from agents.mission_spec.schema import (
    MissionMandate,
    MissionScope,
    MissionSpec,
    RepoScope,
    WorkflowStep,
    load_mission,
    validate_mission,
)

# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestMissionSpecSchema:
    """Test MissionSpec schema parsing."""

    def test_minimal_mission_spec(self):
        """Create minimal valid MissionSpec."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent"
        )
        assert mission.mission_id == "test-mission"
        assert mission.version == "1"  # Default

    def test_mission_with_workflow(self):
        """Create MissionSpec with workflow steps."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(
                    step="analyze",
                    agent="iam-compliance",
                    inputs={"target": "agents/"}
                )
            ]
        )
        assert len(mission.workflow) == 1
        assert mission.workflow[0].agent == "iam-compliance"

    def test_mission_with_scope(self):
        """Create MissionSpec with repo scope."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            scope=MissionScope(repos=[
                RepoScope(path=".", ref="main")
            ])
        )
        assert len(mission.scope.repos) == 1
        # Access the RepoScope object's path attribute
        repo = mission.scope.repos[0]
        assert repo.path == "."
        assert repo.ref == "main"

    def test_mission_with_mandate(self):
        """Create MissionSpec with mandate config."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            mandate=MissionMandate(
                budget_limit=5.0,
                risk_tier="R2",
                authorized_specialists=["iam-compliance"]
            )
        )
        assert mission.mandate.budget_limit == 5.0
        assert mission.mandate.risk_tier == "R2"

    def test_get_all_agents(self):
        """Test get_all_agents method."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="a", agent="iam-compliance"),
                WorkflowStep(step="b", agent="iam-qa"),
                WorkflowStep(step="c", agent="iam-compliance"),  # Duplicate
            ]
        )
        agents = mission.get_all_agents()
        assert agents == ["iam-compliance", "iam-qa"]  # Sorted, no duplicates


class TestMissionValidation:
    """Test mission validation."""

    def test_valid_mission(self):
        """Valid mission has no errors."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ]
        )
        errors = validate_mission(mission)
        assert errors == []

    def test_empty_workflow_error(self):
        """Empty workflow produces error."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[]
        )
        errors = validate_mission(mission)
        assert any("workflow must have" in e for e in errors)

    def test_missing_dependency_error(self):
        """Missing dependency produces error."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(
                    step="analyze",
                    agent="iam-compliance",
                    depends_on=["nonexistent"]
                )
            ]
        )
        errors = validate_mission(mission)
        assert any("unknown step" in e for e in errors)

    def test_unauthorized_agent_error(self):
        """Agent not in authorized_specialists produces error."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ],
            mandate=MissionMandate(
                authorized_specialists=["iam-qa"]  # Missing iam-compliance
            )
        )
        errors = validate_mission(mission)
        assert any("not in authorized_specialists" in e for e in errors)


class TestLoadMission:
    """Test loading missions from YAML files."""

    def test_load_valid_yaml(self):
        """Load valid mission YAML."""
        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow:
  - step: analyze
    agent: iam-compliance
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            mission = load_mission(f.name)
            assert mission.mission_id == "test-mission"
            assert len(mission.workflow) == 1

    def test_load_nonexistent_file(self):
        """Loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_mission("/nonexistent/path.yaml")

    def test_load_sample_mission(self):
        """Load the sample mission file."""
        sample_path = Path("missions/sample-single-repo.mission.yaml")
        if sample_path.exists():
            mission = load_mission(sample_path)
            assert mission.mission_id == "audit-adk-compliance"
            assert len(mission.workflow) >= 1


# ============================================================================
# COMPILER TESTS
# ============================================================================

class TestMissionCompiler:
    """Test MissionCompiler."""

    def test_compile_simple_mission(self):
        """Compile a simple mission."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ]
        )
        result = compile_mission(mission)
        assert result.success is True
        assert result.plan is not None
        assert len(result.plan.tasks) == 1

    def test_compile_mission_with_dependencies(self):
        """Compile mission with step dependencies."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance"),
                WorkflowStep(
                    step="triage",
                    agent="iam-triage",
                    depends_on=["analyze"]
                ),
            ]
        )
        result = compile_mission(mission)
        assert result.success is True
        assert len(result.plan.tasks) == 2
        # Check execution order respects dependencies
        order = result.plan.execution_order
        analyze_idx = next(
            i for i, tid in enumerate(order)
            if any(t.step_name == "analyze" and t.task_id == tid
                   for t in result.plan.tasks)
        )
        triage_idx = next(
            i for i, tid in enumerate(order)
            if any(t.step_name == "triage" and t.task_id == tid
                   for t in result.plan.tasks)
        )
        assert analyze_idx < triage_idx

    def test_compile_creates_mandate(self):
        """Compile creates mandate from mission config."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ],
            mandate=MissionMandate(
                budget_limit=5.0,
                risk_tier="R2"
            )
        )
        result = compile_mission(mission)
        assert result.success is True
        assert result.plan.mandate["budget_limit"] == 5.0
        assert result.plan.mandate["risk_tier"] == "R2"

    def test_compile_creates_pipeline_request(self):
        """Compile creates PipelineRequest."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ]
        )
        result = compile_mission(mission)
        assert result.success is True
        assert result.pipeline_request is not None
        assert result.pipeline_request.pipeline_run_id == "mission-test-mission"
        assert result.pipeline_request.task_description == "Test intent"


class TestCompilerDeterminism:
    """Test that compiler output is deterministic."""

    def test_same_mission_same_plan(self):
        """Same mission produces same plan."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="a", agent="iam-compliance"),
                WorkflowStep(step="b", agent="iam-qa", depends_on=["a"]),
            ]
        )

        result1 = compile_mission(mission, seed="fixed-seed")
        result2 = compile_mission(mission, seed="fixed-seed")

        assert result1.plan.content_hash == result2.plan.content_hash
        assert result1.plan.execution_order == result2.plan.execution_order
        assert [t.task_id for t in result1.plan.tasks] == \
               [t.task_id for t in result2.plan.tasks]

    def test_different_seed_different_task_ids(self):
        """Different seeds produce different task IDs."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam-compliance")
            ]
        )

        result1 = compile_mission(mission, seed="seed1")
        result2 = compile_mission(mission, seed="seed2")

        assert result1.plan.tasks[0].task_id != result2.plan.tasks[0].task_id


class TestCompilerErrors:
    """Test compiler error handling."""

    def test_compile_invalid_mission(self):
        """Compiling invalid mission returns errors."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[]  # Invalid: empty workflow
        )
        result = compile_mission(mission)
        assert result.success is False
        assert len(result.errors) > 0

    def test_compile_warns_on_legacy_ids(self):
        """Compiling with legacy agent IDs produces warnings."""
        mission = MissionSpec(
            mission_id="test-mission",
            title="Test Mission",
            intent="Test intent",
            workflow=[
                WorkflowStep(step="analyze", agent="iam_adk")  # Legacy ID
            ]
        )
        result = compile_mission(mission)
        assert result.success is True
        assert any("legacy" in w.lower() for w in result.warnings)


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""

    def test_plan_to_json(self):
        """ExecutionPlan converts to JSON."""
        plan = ExecutionPlan(
            plan_id="plan-123",
            mission_id="test-mission",
            mission_title="Test",
            created_at="2026-01-02T00:00:00Z",
            content_hash="abc123",
            tasks=[
                PlannedTask(
                    task_id="task-1",
                    step_name="analyze",
                    agent="iam-compliance",
                    inputs={}
                )
            ],
            execution_order=["task-1"]
        )
        json_str = plan.to_json()
        data = json.loads(json_str)
        assert data["plan_id"] == "plan-123"
        assert len(data["tasks"]) == 1


# ============================================================================
# RUNNER TESTS
# ============================================================================

class TestRunnerCLI:
    """Test runner CLI commands."""

    def test_validate_command_valid_file(self):
        """Validate command with valid file returns 0."""
        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow:
  - step: analyze
    agent: iam-compliance
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            result = runner_main(["validate", f.name])
            assert result == 0

    def test_validate_command_invalid_file(self):
        """Validate command with invalid file returns 1."""
        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            result = runner_main(["validate", f.name])
            assert result == 1

    def test_validate_command_nonexistent_file(self):
        """Validate command with nonexistent file returns 1."""
        result = runner_main(["validate", "/nonexistent/path.yaml"])
        assert result == 1

    def test_compile_command(self):
        """Compile command produces execution plan."""
        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow:
  - step: analyze
    agent: iam-compliance
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out:
                result = runner_main(["compile", f.name, "-o", out.name])
                assert result == 0

                # Check output file
                with open(out.name) as f:
                    data = json.load(f)
                    assert data["mission_id"] == "test-mission"

    def test_dryrun_command(self):
        """Dry-run command returns 0 for valid mission."""
        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow:
  - step: analyze
    agent: iam-compliance
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            result = runner_main(["dry-run", f.name])
            assert result == 0

    def test_run_command_executes_mission(self):
        """Run command executes mission with A2A delegation (mocked)."""
        from unittest.mock import patch

        yaml_content = """
mission_id: test-mission
title: Test Mission
intent: Test intent
workflow:
  - step: analyze
    agent: iam-compliance
"""
        # Mock the A2A delegation to return success
        mock_result = {
            "specialist": "iam-compliance",
            "status": "success",
            "result": {"compliance_status": "COMPLIANT"},
            "error": None,
            "metadata": {"duration_ms": 100}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            with patch(
                "agents.iam_senior_adk_devops_lead.tools.delegation.delegate_to_specialist",
                return_value=mock_result
            ):
                result = runner_main(["run", f.name])
                assert result == 0

    def test_no_command_shows_help(self):
        """No command returns 1 and shows help."""
        result = runner_main([])
        assert result == 1
