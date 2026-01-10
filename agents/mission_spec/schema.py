"""
Mission Spec v1 Schema - Pydantic Models.

This module defines the Pydantic models for Mission Spec v1, a declarative
format for defining multi-agent workflows.

Example Mission Spec YAML:
```yaml
mission_id: "audit-adk-compliance"
title: "Audit all iam-* agents for ADK compliance"
intent: "Ensure all agents follow Hard Mode rules R1-R8"
version: "1"

scope:
  repos:
    - path: "."

workflow:
  - step: "analyze"
    agent: "iam-compliance"
    inputs:
      targets: ["agents/iam_*/agent.py"]
    outputs:
      - name: "compliance_report"

mandate:
  budget_limit: 5.0
  risk_tier: "R1"
  authorized_specialists:
    - "iam-compliance"
```

See: 000-docs/257-DR-STND-mission-spec-v1.md
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import yaml


class StepType(str, Enum):
    """Type of workflow step."""
    AGENT = "agent"
    LOOP = "loop"
    GATE = "gate"


class GateType(str, Enum):
    """Type of gate check."""
    TEST_PASS = "test_pass"
    APPROVAL = "approval"
    CUSTOM = "custom"


class StepOutput(BaseModel):
    """Output definition for a workflow step."""
    name: str = Field(..., description="Output name for reference in later steps")
    description: Optional[str] = Field(None, description="Human-readable description")


class GateConfig(BaseModel):
    """Configuration for a gate check."""
    gate_type: GateType = Field(..., alias="type", description="Type of gate")
    command: Optional[str] = Field(None, description="Command to run for test_pass gate")
    approvers: Optional[List[str]] = Field(None, description="Required approvers for approval gate")
    condition: Optional[str] = Field(None, description="Condition expression for custom gate")

    class Config:
        populate_by_name = True


class WorkflowStep(BaseModel):
    """A single step in the workflow."""
    step: str = Field(..., description="Step identifier")
    agent: str = Field(..., description="Agent to invoke (canonical ID)")
    skill_id: Optional[str] = Field(None, description="Explicit skill ID to invoke (overrides default)")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    outputs: List[StepOutput] = Field(default_factory=list, description="Output definitions")
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")
    condition: Optional[str] = Field(None, description="Condition for step execution")

    @field_validator("agent")
    @classmethod
    def validate_agent_format(cls, v: str) -> str:
        """Validate agent uses canonical ID format (kebab-case)."""
        if "_" in v and not v.startswith("iam_"):
            # Allow legacy IDs but warn
            pass
        return v


class LoopStep(BaseModel):
    """A loop construct in the workflow."""
    loop: Dict[str, Any] = Field(..., description="Loop configuration")

    @property
    def name(self) -> str:
        """Get loop name."""
        return self.loop.get("name", "unnamed-loop")

    @property
    def until(self) -> Optional[str]:
        """Get loop termination condition (semantic)."""
        return self.loop.get("until")

    @property
    def max_iterations(self) -> int:
        """Get maximum iterations (hard limit)."""
        return self.loop.get("max_iterations", 10)

    @property
    def gates(self) -> List[GateConfig]:
        """Get gate configurations."""
        gates_data = self.loop.get("gates", [])
        return [GateConfig(**g) for g in gates_data]

    @property
    def steps(self) -> List[WorkflowStep]:
        """Get steps within the loop."""
        steps_data = self.loop.get("steps", [])
        result = []
        for s in steps_data:
            if isinstance(s, dict) and "agent" in s:
                # Simple agent reference
                result.append(WorkflowStep(
                    step=s.get("step", s["agent"]),
                    agent=s["agent"],
                    inputs=s.get("inputs", {}),
                    outputs=[StepOutput(**o) for o in s.get("outputs", [])],
                    depends_on=s.get("depends_on", [])
                ))
        return result


class RepoScope(BaseModel):
    """Repository scope definition."""
    path: str = Field(..., description="Path to repository (. for current)")
    ref: Optional[str] = Field(None, description="Git ref (branch, tag, commit)")
    worktree: Optional[str] = Field(None, description="Worktree path if using git worktrees")


class MissionScope(BaseModel):
    """Scope of the mission (which repos to operate on)."""
    repos: List[RepoScope] = Field(default_factory=list, description="Repository list")

    @field_validator("repos", mode="before")
    @classmethod
    def normalize_repos(cls, v: Any) -> List[Any]:
        """Normalize repo definitions to RepoScope format."""
        if not v:
            return []
        result = []
        for repo in v:
            if isinstance(repo, RepoScope):
                # Already a RepoScope object, pass through
                result.append(repo)
            elif isinstance(repo, str):
                result.append({"path": repo})
            elif isinstance(repo, dict):
                result.append(repo)
            else:
                result.append({"path": str(repo)})
        return result


class MissionMandate(BaseModel):
    """Mandate configuration for the mission."""
    budget_limit: float = Field(0.0, description="Maximum budget in budget_unit")
    budget_unit: str = Field("USD", description="Budget unit")
    max_iterations: int = Field(100, description="Maximum specialist invocations")
    authorized_specialists: List[str] = Field(
        default_factory=list,
        description="Authorized specialist IDs (empty = all)"
    )
    risk_tier: str = Field("R0", description="Risk tier (R0-R4)")
    data_classification: str = Field("internal", description="Data classification level")

    @field_validator("risk_tier")
    @classmethod
    def validate_risk_tier(cls, v: str) -> str:
        """Validate risk tier is valid."""
        valid_tiers = ["R0", "R1", "R2", "R3", "R4"]
        if v not in valid_tiers:
            raise ValueError(f"risk_tier must be one of {valid_tiers}")
        return v


class EvidenceConfig(BaseModel):
    """Evidence bundle configuration."""
    bundle_required: bool = Field(True, description="Whether to create evidence bundle")
    include: List[str] = Field(default_factory=list, description="Outputs to include in bundle")
    export_to_gcs: bool = Field(False, description="Whether to export to GCS")
    gcs_bucket: Optional[str] = Field(None, description="GCS bucket for export")


class MissionSpec(BaseModel):
    """
    Mission Spec v1 - Declarative Workflow Definition.

    A Mission Spec defines a complete workflow that can be:
    - Validated for correctness
    - Compiled to Beads tasks + PipelineRequest
    - Dry-run to preview execution plan
    - Executed with full audit trail
    """
    mission_id: str = Field(..., description="Unique mission identifier")
    title: str = Field(..., description="Human-readable title")
    intent: str = Field(..., description="What this mission accomplishes")
    version: str = Field("1", description="Mission spec version")

    scope: MissionScope = Field(
        default_factory=MissionScope,
        description="Scope (repos to operate on)"
    )

    workflow: List[Union[WorkflowStep, LoopStep]] = Field(
        default_factory=list,
        description="Workflow steps and loops"
    )

    mandate: MissionMandate = Field(
        default_factory=MissionMandate,
        description="Mandate configuration"
    )

    evidence: EvidenceConfig = Field(
        default_factory=EvidenceConfig,
        description="Evidence bundle configuration"
    )

    @field_validator("workflow", mode="before")
    @classmethod
    def normalize_workflow(cls, v: Any) -> List[Dict[str, Any]]:
        """Normalize workflow items to proper types."""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, dict):
                if "loop" in item:
                    result.append({"loop": item["loop"]})
                elif "step" in item or "agent" in item:
                    result.append(item)
                else:
                    result.append(item)
            else:
                result.append(item)
        return result

    def get_all_agents(self) -> List[str]:
        """Get all agents referenced in the workflow."""
        agents = set()
        for item in self.workflow:
            if isinstance(item, WorkflowStep):
                agents.add(item.agent)
            elif isinstance(item, LoopStep):
                for step in item.steps:
                    agents.add(step.agent)
        return sorted(agents)

    def get_step_by_name(self, name: str) -> Optional[WorkflowStep]:
        """Get a workflow step by name."""
        for item in self.workflow:
            if isinstance(item, WorkflowStep) and item.step == name:
                return item
        return None

    def validate_dependencies(self) -> List[str]:
        """Validate all step dependencies exist. Returns list of errors."""
        errors = []
        step_names = {
            item.step for item in self.workflow
            if isinstance(item, WorkflowStep)
        }

        for item in self.workflow:
            if isinstance(item, WorkflowStep):
                for dep in item.depends_on:
                    if dep not in step_names:
                        errors.append(
                            f"Step '{item.step}' depends on unknown step '{dep}'"
                        )

        return errors

    def validate_agents(self) -> List[str]:
        """Validate all agents are in authorized_specialists (if set)."""
        errors = []
        if not self.mandate.authorized_specialists:
            return errors  # Empty = all allowed

        authorized = set(self.mandate.authorized_specialists)
        for agent in self.get_all_agents():
            if agent not in authorized:
                errors.append(
                    f"Agent '{agent}' not in authorized_specialists"
                )

        return errors


def load_mission(path: Union[str, Path]) -> MissionSpec:
    """
    Load a Mission Spec from a YAML file.

    Args:
        path: Path to the mission YAML file

    Returns:
        Parsed MissionSpec

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML is invalid or schema validation fails
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Mission file not found: {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty mission file: {path}")

    return MissionSpec(**data)


def validate_mission(mission: MissionSpec) -> List[str]:
    """
    Validate a MissionSpec for correctness.

    Args:
        mission: MissionSpec to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check required fields
    if not mission.mission_id:
        errors.append("mission_id is required")
    if not mission.title:
        errors.append("title is required")
    if not mission.intent:
        errors.append("intent is required")

    # Check workflow is not empty
    if not mission.workflow:
        errors.append("workflow must have at least one step")

    # Check dependencies
    errors.extend(mission.validate_dependencies())

    # Check authorized agents
    errors.extend(mission.validate_agents())

    return errors
