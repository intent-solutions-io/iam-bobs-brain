"""
Mission Spec Runner - CLI for Mission Operations.

This module provides a CLI for working with Mission Spec files:
- validate: Check mission file for errors
- compile: Generate execution plan
- dry-run: Preview execution without running
- run: Execute the mission (future)

Usage:
    python -m agents.mission_spec.runner validate missions/sample.mission.yaml
    python -m agents.mission_spec.runner compile missions/sample.mission.yaml
    python -m agents.mission_spec.runner dry-run missions/sample.mission.yaml
    python -m agents.mission_spec.runner run missions/sample.mission.yaml

See: 000-docs/257-DR-STND-mission-spec-v1.md
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.mission_spec.schema import load_mission, validate_mission, MissionSpec
from agents.mission_spec.compiler import compile_mission, CompilerResult, ExecutionPlan, PlannedTask
from agents.shared_contracts.evidence_bundle import (
    create_evidence_bundle,
    EvidenceBundle,
    ToolCallRecord,
)

logger = logging.getLogger(__name__)


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a mission file."""
    try:
        mission = load_mission(args.mission_file)
        errors = validate_mission(mission)

        if errors:
            print(f"Validation FAILED for {args.mission_file}:")
            for error in errors:
                print(f"  - {error}")
            return 1

        print(f"Validation PASSED for {args.mission_file}")
        print(f"  Mission ID: {mission.mission_id}")
        print(f"  Title: {mission.title}")
        print(f"  Agents: {', '.join(mission.get_all_agents())}")
        print(f"  Steps: {len(mission.workflow)}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error parsing mission file: {e}")
        return 1


def cmd_compile(args: argparse.Namespace) -> int:
    """Compile a mission file to execution plan."""
    try:
        mission = load_mission(args.mission_file)
        result = compile_mission(mission)

        if not result.success:
            print(f"Compilation FAILED for {args.mission_file}:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                f.write(result.plan.to_json())
            print(f"Execution plan written to: {output_path}")
        else:
            print(result.plan.to_json())

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error compiling mission: {e}")
        return 1


def cmd_dry_run(args: argparse.Namespace) -> int:
    """Preview mission execution without running."""
    try:
        mission = load_mission(args.mission_file)
        result = compile_mission(mission)

        if not result.success:
            print(f"Compilation FAILED for {args.mission_file}:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        plan = result.plan
        print("=" * 60)
        print("DRY RUN - Execution Preview")
        print("=" * 60)
        print(f"Mission: {plan.mission_title}")
        print(f"Mission ID: {plan.mission_id}")
        print(f"Plan ID: {plan.plan_id}")
        print(f"Content Hash: {plan.content_hash[:16]}...")
        print()
        print(f"Repos: {', '.join(plan.repos) or '(current)'}")
        print(f"Risk Tier: {plan.mandate.get('risk_tier', 'R0')}")
        print(f"Budget Limit: {plan.mandate.get('budget_limit', 0)} {plan.mandate.get('budget_unit', 'USD')}")
        print()
        print(f"Total Tasks: {len(plan.tasks)}")
        print(f"Has Loops: {plan.has_loops}")
        if plan.has_loops:
            print(f"Max Loop Iterations: {plan.max_loop_iterations}")
        print()
        print("Execution Order:")
        print("-" * 40)

        for i, task_id in enumerate(plan.execution_order, 1):
            task = next(t for t in plan.tasks if t.task_id == task_id)
            loop_info = ""
            if task.loop_name:
                loop_info = f" [loop: {task.loop_name}, iter: {task.loop_iteration}]"
            deps = f" (depends: {', '.join(task.depends_on)})" if task.depends_on else ""
            print(f"  {i}. [{task.task_id}] {task.step_name} -> {task.agent}{loop_info}{deps}")

        print()
        print("=" * 60)
        print("DRY RUN COMPLETE - No changes made")
        print("=" * 60)

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error in dry-run: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def execute_task(
    task: PlannedTask,
    context: Dict[str, Any],
    evidence: EvidenceBundle
) -> Dict[str, Any]:
    """
    Execute a single task via A2A delegation.

    Args:
        task: The planned task to execute
        context: Execution context with mission metadata
        evidence: Evidence bundle for recording

    Returns:
        Task result dict
    """
    # Import delegation at runtime (6767-LAZY pattern)
    from agents.iam_senior_adk_devops_lead.tools.delegation import delegate_to_specialist
    from agents.a2a.dispatcher import load_agentcard

    start_time = datetime.now(timezone.utc)

    # Map task to specialist skill call
    # Agent name in task is the canonical agent ID (e.g., "iam-compliance")
    agent = task.agent

    # Determine skill_id: explicit in task, or use agent's primary skill
    skill_id = task.skill_id
    if not skill_id:
        # Look up agent's primary skill from AgentCard
        try:
            agentcard = load_agentcard(agent)
            skills = agentcard.get("skills", [])
            if skills:
                skill_id = skills[0].get("id")  # Use first skill as primary
            else:
                skill_id = f"{agent.replace('-', '_')}.execute"  # Fallback
        except Exception:
            skill_id = f"{agent.replace('-', '_')}.execute"  # Fallback on error

    logger.info(f"Executing task {task.task_id}: {task.step_name} -> {agent}")

    try:
        result = delegate_to_specialist(
            specialist=agent,
            skill_id=skill_id,
            payload=task.inputs,
            context={
                "mission_id": context.get("mission_id"),
                "pipeline_run_id": context.get("pipeline_run_id"),
                "task_id": task.task_id,
            }
        )

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Record in evidence bundle
        evidence.record_task_executed(task.task_id)
        evidence.record_agent_invoked(agent)
        evidence.record_tool_call(ToolCallRecord(
            tool_name=skill_id,
            specialist=agent,
            timestamp=start_time.isoformat(),
            duration_ms=duration_ms,
            success=result.get("status") == "success",
            input_hash=EvidenceBundle.compute_sha256(
                json.dumps(task.inputs, sort_keys=True).encode()
            ),
            output_hash=EvidenceBundle.compute_sha256(
                json.dumps(result, sort_keys=True).encode()
            ),
            error_message=result.get("error")
        ))

        return {
            "task_id": task.task_id,
            "status": result.get("status", "unknown"),
            "result": result.get("result"),
            "duration_ms": duration_ms,
            "error": result.get("error"),
        }

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        logger.error(f"Task {task.task_id} failed: {e}")

        evidence.record_tool_call(ToolCallRecord(
            tool_name=skill_id,
            specialist=agent,
            timestamp=start_time.isoformat(),
            duration_ms=duration_ms,
            success=False,
            input_hash=EvidenceBundle.compute_sha256(
                json.dumps(task.inputs, sort_keys=True).encode()
            ),
            output_hash="",
            error_message=str(e)
        ))

        return {
            "task_id": task.task_id,
            "status": "error",
            "result": None,
            "duration_ms": duration_ms,
            "error": str(e),
        }


async def run_mission(
    plan: ExecutionPlan,
    evidence: EvidenceBundle
) -> Dict[str, Any]:
    """
    Execute a compiled mission plan.

    Args:
        plan: Compiled execution plan
        evidence: Evidence bundle for audit trail

    Returns:
        Execution results dict
    """
    context = {
        "mission_id": plan.mission_id,
        "pipeline_run_id": evidence.manifest.pipeline_run_id,
        "plan_id": plan.plan_id,
    }

    # Record all planned tasks
    for task_id in plan.execution_order:
        evidence.record_task_planned(task_id)

    # Set mandate snapshot
    if plan.mandate:
        evidence.set_mandate_snapshot(plan.mandate)

    results: List[Dict[str, Any]] = []
    task_map = {t.task_id: t for t in plan.tasks}

    for task_id in plan.execution_order:
        task = task_map.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found in plan, skipping")
            evidence.record_task_skipped(task_id)
            continue

        # Check if dependencies are satisfied
        deps_satisfied = all(
            any(r["task_id"] == dep and r["status"] == "success" for r in results)
            for dep in task.depends_on
        )

        if not deps_satisfied and task.depends_on:
            logger.warning(f"Task {task_id} dependencies not satisfied, skipping")
            evidence.record_task_skipped(task_id)
            results.append({
                "task_id": task_id,
                "status": "skipped",
                "result": None,
                "error": "Dependencies not satisfied",
            })
            continue

        # Execute the task
        result = await execute_task(task, context, evidence)
        results.append(result)

        # For loops, check exit conditions (simplified - always continue for now)
        if task.loop_name:
            # TODO: Implement loop exit condition checking
            pass

    return {
        "plan_id": plan.plan_id,
        "mission_id": plan.mission_id,
        "tasks_total": len(plan.execution_order),
        "tasks_executed": len([r for r in results if r["status"] == "success"]),
        "tasks_failed": len([r for r in results if r["status"] in ("error", "failure")]),
        "tasks_skipped": len([r for r in results if r["status"] == "skipped"]),
        "results": results,
    }


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a mission via A2A dispatcher."""
    try:
        # Step 1: Load and compile mission
        print(f"Loading mission: {args.mission_file}")
        mission = load_mission(args.mission_file)
        result = compile_mission(mission)

        if not result.success:
            print(f"Compilation FAILED for {args.mission_file}:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        plan = result.plan
        print(f"Compiled: {plan.mission_id} ({len(plan.tasks)} tasks)")

        # Step 2: Create evidence bundle
        evidence = create_evidence_bundle(
            mission_id=plan.mission_id,
            pipeline_run_id=f"mission-{plan.mission_id}",
            mandate_snapshot=plan.mandate,
        )
        print(f"Evidence bundle: {evidence.manifest.bundle_id}")

        # Step 3: Execute mission
        print()
        print("=" * 60)
        print("EXECUTING MISSION")
        print("=" * 60)

        execution_result = asyncio.run(run_mission(plan, evidence))

        # Step 4: Record results and save evidence
        if execution_result["tasks_failed"] > 0:
            evidence.mark_failed(
                f"{execution_result['tasks_failed']} tasks failed"
            )
        else:
            evidence.mark_completed()

        bundle_path = evidence.save()

        # Step 5: Print summary
        print()
        print("=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"Mission ID: {plan.mission_id}")
        print(f"Plan ID: {plan.plan_id}")
        print()
        print(f"Tasks Executed: {execution_result['tasks_executed']}")
        print(f"Tasks Failed: {execution_result['tasks_failed']}")
        print(f"Tasks Skipped: {execution_result['tasks_skipped']}")
        print()
        print(f"Evidence Bundle: {bundle_path}")
        print(f"Status: {evidence.manifest.status}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        # Print task results
        if args.verbose:
            print("\nTask Results:")
            for task_result in execution_result["results"]:
                status_icon = "✓" if task_result["status"] == "success" else "✗"
                print(f"  {status_icon} [{task_result['task_id']}] {task_result['status']}")
                if task_result.get("error"):
                    print(f"    Error: {task_result['error']}")

        return 0 if execution_result["tasks_failed"] == 0 else 1

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error executing mission: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main(argv: Optional[list] = None) -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="mission_spec",
        description="Mission Spec v1 - Declarative Workflow Runner"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a mission file"
    )
    validate_parser.add_argument(
        "mission_file",
        type=str,
        help="Path to mission YAML file"
    )

    # compile command
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile mission to execution plan"
    )
    compile_parser.add_argument(
        "mission_file",
        type=str,
        help="Path to mission YAML file"
    )
    compile_parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file for execution plan JSON"
    )

    # dry-run command
    dryrun_parser = subparsers.add_parser(
        "dry-run",
        help="Preview execution without running"
    )
    dryrun_parser.add_argument(
        "mission_file",
        type=str,
        help="Path to mission YAML file"
    )

    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="Execute the mission"
    )
    run_parser.add_argument(
        "mission_file",
        type=str,
        help="Path to mission YAML file"
    )
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed task results"
    )

    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "compile":
        return cmd_compile(args)
    elif args.command == "dry-run":
        return cmd_dry_run(args)
    elif args.command == "run":
        return cmd_run(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
