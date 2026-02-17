"""
Mission Spec Compiler - Mission to Execution Plan.

This module compiles a MissionSpec into:
1. An ExecutionPlan with ordered tasks
2. A PipelineRequest ready for dispatcher execution
3. Beads task creation commands (optional)

The compiler ensures deterministic output: same input always produces
the same execution plan, enabling dry-run previews and replay.

See: 000-docs/257-DR-STND-mission-spec-v1.md
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.mission_spec.schema import (
    LoopStep,
    MissionSpec,
    WorkflowStep,
    validate_mission,
)
from agents.shared_contracts.pipeline_contracts import Mandate, PipelineRequest


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@dataclass
class PlannedTask:
    """A task planned for execution."""
    task_id: str
    step_name: str
    agent: str
    inputs: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    loop_name: Optional[str] = None
    loop_iteration: Optional[int] = None
    skill_id: Optional[str] = None  # Explicit skill to invoke (from step definition)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ExecutionPlan:
    """
    Compiled execution plan from a MissionSpec.

    This is the output of the compiler - a deterministic plan that
    can be previewed (dry-run) or executed.
    """
    plan_id: str
    mission_id: str
    mission_title: str
    created_at: str
    content_hash: str  # SHA-256 of mission spec for determinism check

    tasks: List[PlannedTask] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)  # Task IDs in order

    mandate: Optional[Dict[str, Any]] = None
    repos: List[str] = field(default_factory=list)

    # Metadata
    total_steps: int = 0
    has_loops: bool = False
    max_loop_iterations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["tasks"] = [t.to_dict() for t in self.tasks]
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=_json_serializer)


@dataclass
class CompilerResult:
    """Result of compiling a MissionSpec."""
    success: bool
    plan: Optional[ExecutionPlan] = None
    pipeline_request: Optional[PipelineRequest] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "plan": self.plan.to_dict() if self.plan else None,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class MissionCompiler:
    """
    Compiler for MissionSpec -> ExecutionPlan + PipelineRequest.

    The compiler is deterministic: given the same MissionSpec, it will
    always produce the same ExecutionPlan (with the same task IDs).
    """

    def __init__(self, seed: Optional[str] = None):
        """
        Initialize compiler.

        Args:
            seed: Optional seed for deterministic ID generation.
                  If not provided, uses mission_id as seed.
        """
        self.seed = seed

    def _generate_task_id(self, mission_id: str, step_name: str, index: int) -> str:
        """Generate a deterministic task ID."""
        seed = self.seed or mission_id
        content = f"{seed}:{step_name}:{index}"
        hash_bytes = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"task-{hash_bytes}"

    def _compute_content_hash(self, mission: MissionSpec) -> str:
        """Compute SHA-256 hash of mission content for determinism check."""
        # Serialize mission to JSON for hashing
        content = json.dumps(mission.model_dump(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def _create_mandate(self, mission: MissionSpec) -> Mandate:
        """Create Mandate from mission mandate config."""
        return Mandate(
            mandate_id=f"mandate-{mission.mission_id}",
            intent=mission.intent,
            budget_limit=mission.mandate.budget_limit,
            budget_unit=mission.mandate.budget_unit,
            max_iterations=mission.mandate.max_iterations,
            authorized_specialists=mission.mandate.authorized_specialists,
            risk_tier=mission.mandate.risk_tier,
            data_classification=mission.mandate.data_classification,
        )

    def _expand_workflow(
        self,
        mission: MissionSpec
    ) -> tuple[List[PlannedTask], List[str]]:
        """
        Expand workflow into flat list of tasks with execution order.

        Returns:
            Tuple of (tasks, execution_order)
        """
        tasks: List[PlannedTask] = []
        execution_order: List[str] = []
        task_index = 0

        for item in mission.workflow:
            if isinstance(item, WorkflowStep):
                task_id = self._generate_task_id(
                    mission.mission_id, item.step, task_index
                )
                task = PlannedTask(
                    task_id=task_id,
                    step_name=item.step,
                    agent=item.agent,
                    inputs=item.inputs,
                    depends_on=item.depends_on,
                    skill_id=item.skill_id,  # Preserve explicit skill_id
                )
                tasks.append(task)
                execution_order.append(task_id)
                task_index += 1

            elif isinstance(item, LoopStep):
                # Expand loop into individual iterations
                # For dry-run, we show max_iterations as upper bound
                for iteration in range(item.max_iterations):
                    for step in item.steps:
                        task_id = self._generate_task_id(
                            mission.mission_id,
                            f"{item.name}:{step.step}:{iteration}",
                            task_index
                        )
                        task = PlannedTask(
                            task_id=task_id,
                            step_name=step.step,
                            agent=step.agent,
                            inputs=step.inputs,
                            depends_on=step.depends_on,
                            loop_name=item.name,
                            loop_iteration=iteration,
                        )
                        tasks.append(task)
                        execution_order.append(task_id)
                        task_index += 1

        return tasks, execution_order

    def _topological_sort(
        self,
        tasks: List[PlannedTask]
    ) -> List[str]:
        """
        Sort tasks topologically based on dependencies.

        Returns list of task IDs in execution order.
        """
        # Build dependency graph
        task_map = {t.task_id: t for t in tasks}
        step_to_task = {t.step_name: t.task_id for t in tasks if not t.loop_name}

        # Resolve step name dependencies to task IDs
        for task in tasks:
            resolved_deps = []
            for dep in task.depends_on:
                if dep in step_to_task:
                    resolved_deps.append(step_to_task[dep])
                elif dep in task_map:
                    resolved_deps.append(dep)
            task.depends_on = resolved_deps

        # Kahn's algorithm for topological sort
        in_degree = {t.task_id: 0 for t in tasks}
        graph = {t.task_id: [] for t in tasks}

        for task in tasks:
            for dep in task.depends_on:
                if dep in graph:
                    graph[dep].append(task.task_id)
                    in_degree[task.task_id] += 1

        # Start with tasks that have no dependencies
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort for determinism
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(tasks):
            # Cycle detected - return original order
            return [t.task_id for t in tasks]

        return result

    def compile(self, mission: MissionSpec) -> CompilerResult:
        """
        Compile a MissionSpec into an ExecutionPlan.

        Args:
            mission: MissionSpec to compile

        Returns:
            CompilerResult with plan and/or errors
        """
        # Validate mission first
        errors = validate_mission(mission)
        if errors:
            return CompilerResult(success=False, errors=errors)

        warnings: List[str] = []

        # Check for legacy agent IDs
        for agent in mission.get_all_agents():
            if "_" in agent:
                warnings.append(
                    f"Agent '{agent}' uses legacy underscore ID. "
                    f"Consider using canonical kebab-case ID."
                )

        # Expand workflow into tasks
        tasks, initial_order = self._expand_workflow(mission)

        # Sort topologically
        execution_order = self._topological_sort(tasks)

        # Detect loops
        has_loops = any(
            isinstance(item, LoopStep) for item in mission.workflow
        )
        max_loop_iterations = max(
            (item.max_iterations for item in mission.workflow
             if isinstance(item, LoopStep)),
            default=0
        )

        # Create plan
        plan = ExecutionPlan(
            plan_id=f"plan-{hashlib.sha256(mission.mission_id.encode()).hexdigest()[:8]}",
            mission_id=mission.mission_id,
            mission_title=mission.title,
            created_at=datetime.now(timezone.utc).isoformat(),
            content_hash=self._compute_content_hash(mission),
            tasks=tasks,
            execution_order=execution_order,
            mandate=self._create_mandate(mission).__dict__,
            repos=[r.path for r in mission.scope.repos],
            total_steps=len([t for t in tasks if not t.loop_name]),
            has_loops=has_loops,
            max_loop_iterations=max_loop_iterations,
        )

        # Create PipelineRequest
        mandate = self._create_mandate(mission)
        repos = [r.path for r in mission.scope.repos]
        pipeline_request = PipelineRequest(
            repo_hint=repos[0] if repos else ".",
            task_description=mission.intent,
            pipeline_run_id=f"mission-{mission.mission_id}",
            mandate=mandate,
        )

        return CompilerResult(
            success=True,
            plan=plan,
            pipeline_request=pipeline_request,
            warnings=warnings,
        )


def compile_mission(mission: MissionSpec, seed: Optional[str] = None) -> CompilerResult:
    """
    Convenience function to compile a MissionSpec.

    Args:
        mission: MissionSpec to compile
        seed: Optional seed for deterministic ID generation

    Returns:
        CompilerResult with plan and/or errors
    """
    compiler = MissionCompiler(seed=seed)
    return compiler.compile(mission)
