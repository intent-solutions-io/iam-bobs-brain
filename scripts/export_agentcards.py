#!/usr/bin/env python3
"""
Export all agent AgentCards to .well-known/agent-card.json files.

This script imports all a2a_card modules and exports their AgentCards
to JSON files following the A2A protocol specification.

Usage:
    python3 scripts/export_agentcards.py
"""

import importlib.util
import json
import sys
from pathlib import Path

# Add agents directory to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "agents"))

# Agent configuration
AGENTS = [
    {"name": "bob", "module": "bob.a2a_card", "dir": "bob"},
    {"name": "iam-senior-adk-devops-lead", "module": "a2a_card", "dir": "iam-senior-adk-devops-lead"},
    {"name": "iam_adk", "module": "iam_adk.a2a_card", "dir": "iam_adk"},
    {"name": "iam_issue", "module": "iam_issue.a2a_card", "dir": "iam_issue"},
    {"name": "iam_fix_plan", "module": "iam_fix_plan.a2a_card", "dir": "iam_fix_plan"},
    {"name": "iam_fix_impl", "module": "iam_fix_impl.a2a_card", "dir": "iam_fix_impl"},
    {"name": "iam_qa", "module": "iam_qa.a2a_card", "dir": "iam_qa"},
    {"name": "iam_doc", "module": "iam_doc.a2a_card", "dir": "iam_doc"},
    {"name": "iam_cleanup", "module": "iam_cleanup.a2a_card", "dir": "iam_cleanup"},
    {"name": "iam_index", "module": "iam_index.a2a_card", "dir": "iam_index"},
]


def export_agent_card(agent_name: str, agent_dir: str) -> None:
    """Export an agent's AgentCard to JSON file.

    Args:
        agent_name: Display name for the agent
        agent_dir: Agent directory name
    """
    try:
        # Build path to a2a_card.py module
        agent_path = repo_root / "agents" / agent_dir
        module_file = agent_path / "a2a_card.py"

        if not module_file.exists():
            raise FileNotFoundError(f"a2a_card.py not found in {agent_path}")

        # Load module using importlib
        spec = importlib.util.spec_from_file_location(f"{agent_dir}.a2a_card", module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {module_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the AgentCard dictionary
        card_dict = module.get_agent_card_dict()

        # Create .well-known directory
        well_known_dir = agent_path / ".well-known"
        well_known_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        json_path = well_known_dir / "agent-card.json"
        with open(json_path, "w") as f:
            json.dump(card_dict, f, indent=2)

        print(f"✓ Exported {agent_name} → {json_path.relative_to(repo_root)}")

    except Exception as e:
        print(f"✗ Failed to export {agent_name}: {e}")
        raise


def main():
    """Export all agent AgentCards to JSON files."""
    print("Exporting AgentCards to JSON files...")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for agent in AGENTS:
        try:
            export_agent_card(agent["name"], agent["dir"])
            success_count += 1
        except Exception:
            fail_count += 1

    print("=" * 60)
    print(f"Results: {success_count} succeeded, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
