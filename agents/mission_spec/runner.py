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
import json
import sys
from pathlib import Path
from typing import Optional

from agents.mission_spec.schema import load_mission, validate_mission, MissionSpec
from agents.mission_spec.compiler import compile_mission, CompilerResult


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


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a mission (future implementation)."""
    print("Mission execution is not yet implemented.")
    print("Use 'dry-run' to preview the execution plan.")
    print()
    print("When implemented, 'run' will:")
    print("  1. Compile the mission to an execution plan")
    print("  2. Create a Beads epic for tracking")
    print("  3. Create an evidence bundle")
    print("  4. Execute each task via the A2A dispatcher")
    print("  5. Record results in the evidence bundle")
    print("  6. Close the Beads epic")
    return 0


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
