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
    # Core models
    MissionSpec,
    MissionScope,
    RepoScope,
    WorkflowStep,
    LoopStep,
    MissionMandate,
    EvidenceConfig,
    StepOutput,
    GateConfig,
    # Enums
    StepType,
    GateType,
    # Functions
    load_mission,
    validate_mission,
)

__all__ = [
    # Core models
    "MissionSpec",
    "MissionScope",
    "RepoScope",
    "WorkflowStep",
    "LoopStep",
    "MissionMandate",
    "EvidenceConfig",
    "StepOutput",
    "GateConfig",
    # Enums
    "StepType",
    "GateType",
    # Functions
    "load_mission",
    "validate_mission",
]
