#!/usr/bin/env python3
"""
Print Agent Engine Configuration

Displays all Agent Engine reasoning engine IDs, regions, and SPIFFE IDs
for all agents across all environments.

Usage:
    python scripts/print_agent_engine_config.py
    python scripts/print_agent_engine_config.py --verbose
    make print-agent-engine-config

Part of Phase AE1 - Agent Engine deployment model.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config.agent_engine import (
    ALL_ENVIRONMENTS,
    AgentEngineConfig,
    validate_config,
)


def print_environment_config(
    env_name: str, agents: Dict[str, AgentEngineConfig], verbose: bool = False
) -> None:
    """
    Print configuration for a single environment.

    Args:
        env_name: Environment name (dev, staging, prod)
        agents: Dictionary of agent role -> config
        verbose: Whether to include full details
    """
    print(f"\n{'=' * 80}")
    print(f"{env_name.upper()} ENVIRONMENT")
    print(f"{'=' * 80}")

    if not agents:
        print("  No agents deployed to Agent Engine in this environment")
        return

    for agent_role, config in sorted(agents.items()):
        print(f"\n{agent_role}:")

        if verbose:
            # Verbose: Show all fields
            print("  Reasoning Engine ID:")
            print(f"    {config.reasoning_engine_id}")
            print("  Region:")
            print(f"    {config.region}")
            print("  SPIFFE ID:")
            print(f"    {config.spiffe_id}")

            if config.notes:
                print("  Notes:")
                # Indent multi-line notes
                for line in config.notes.split("\n"):
                    print(f"    {line}")
        else:
            # Concise: One line per agent
            # Extract just the engine ID from the full resource name
            engine_id = config.reasoning_engine_id.split("/")[-1]
            print(f"  Engine ID: {engine_id}")
            print(f"  Region: {config.region}")

            # Show special marker for current canonical Bob
            if "CANONICAL" in (config.notes or "").upper():
                print("  ⭐ CURRENT CANONICAL PRODUCTION BOB")


def print_summary_table(verbose: bool = False) -> None:
    """
    Print summary table of all agents across all environments.

    Args:
        verbose: Whether to include full details
    """
    print("\n" + "=" * 80)
    print("AGENT ENGINE CONFIGURATION SUMMARY")
    print("=" * 80)
    print("\nAgent deployment matrix:")
    print("-" * 80)

    # Get all unique agent roles across all environments
    all_agent_roles = set()
    for agents in ALL_ENVIRONMENTS.values():
        all_agent_roles.update(agents.keys())

    # Print header
    print(f"{'Agent Role':<30} {'Dev':<10} {'Staging':<10} {'Prod':<10}")
    print("-" * 80)

    # Print each agent
    for agent_role in sorted(all_agent_roles):
        row = f"{agent_role:<30}"

        for env in ["dev", "staging", "prod"]:
            if agent_role in ALL_ENVIRONMENTS[env]:
                config = ALL_ENVIRONMENTS[env][agent_role]
                engine_id = config.reasoning_engine_id.split("/")[-1]

                # Special marker for canonical Bob
                if "CANONICAL" in (config.notes or "").upper():
                    row += f"{'⭐ ' + engine_id[:8]:<10}"
                else:
                    row += f"{engine_id[:8]:<10}"
            else:
                row += f"{'(stub)':<10}"

        print(row)

    print("-" * 80)

    # Print legend
    print("\nLegend:")
    print("  (stub)   = Agent uses local stub (not deployed to Agent Engine)")
    print("  ⭐       = Current canonical production Bob")
    print("  [8 chars] = First 8 characters of reasoning engine numeric ID")

    # Print placeholder note
    print("\nNote:")
    print("  Entries like 'BOB_DEV_P' are placeholders.")
    print("  Real reasoning engine IDs will be assigned during deployment.")
    print("  Current canonical Bob (...6448) is the only real ID.")


def print_all_configs(verbose: bool = False) -> None:
    """
    Print all Agent Engine configurations.

    Args:
        verbose: Whether to include full details
    """
    # Print summary table first
    print_summary_table(verbose)

    # Then print detailed config for each environment
    for env_name in ["dev", "staging", "prod"]:
        agents = ALL_ENVIRONMENTS[env_name]
        print_environment_config(env_name, agents, verbose)

    # Print related docs
    print("\n" + "=" * 80)
    print("RELATED DOCUMENTATION")
    print("=" * 80)
    print("\n📄 Agent Engine Topology:")
    print("  000-docs/6767-101-AT-ARCH-agent-engine-topology-and-envs.md")
    print("\n📄 Agent Engine Config Module:")
    print("  agents/config/agent_engine.py")
    print("\n📄 A2A Adapter:")
    print("  agents/utils/a2a_adapter.py")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Print Agent Engine configuration for all environments"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show full details (reasoning engine IDs, SPIFFE IDs, notes)",
    )

    args = parser.parse_args()

    try:
        # Validate configuration first
        validate_config()

        # Print all configs
        print_all_configs(verbose=args.verbose)

        print("\n✅ Agent Engine configuration displayed successfully\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
