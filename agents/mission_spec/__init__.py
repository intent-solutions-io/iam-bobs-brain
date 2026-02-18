"""
Mission Spec v1 - Declarative Workflow-as-Code.

This package implements Mission Spec v1, a declarative format for defining
multi-agent workflows that compile to Beads tasks and PipelineRequests.

Modules:
- schema.py: Pydantic models for Mission Spec YAML
- compiler.py: Mission -> Beads + PipelineRequest compilation
- runner.py: CLI for validate/compile/dry-run/run

See: 000-docs/257-DR-STND-mission-spec-v1.md
"""

from agents.mission_spec.schema import (
    EvidenceConfig,
    GateConfig,
    GateType,
    LoopStep,
    MissionMandate,
    MissionScope,
    # Core models
    MissionSpec,
    RepoScope,
    StepOutput,
    # Enums
    StepType,
    WorkflowStep,
    # Functions
    load_mission,
    validate_mission,
)

__all__ = [
    "EvidenceConfig",
    "GateConfig",
    "GateType",
    "LoopStep",
    "MissionMandate",
    "MissionScope",
    "MissionSpec",
    "RepoScope",
    "StepOutput",
    "StepType",
    "WorkflowStep",
    "load_mission",
    "validate_mission",
]
