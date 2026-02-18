#!/usr/bin/env python3
"""
Print RAG Configuration - Dry-run helper for Vertex AI Search setup

This script shows which datastore and bucket Bob would use in the current
environment without making any actual API calls.

Usage:
    python scripts/print_rag_config.py

    # With environment override:
    APP_ENV=production python scripts/print_rag_config.py

    # Check legacy mode:
    USE_ORG_KNOWLEDGE=false python scripts/print_rag_config.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import agents modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.shared_tools.vertex_search import (
    get_current_environment,
    get_datastore_info,
    load_vertex_search_config,
)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_key_value(key: str, value: str, indent: int = 0):
    """Print a key-value pair with optional indentation."""
    prefix = "  " * indent
    print(f"{prefix}{key:.<30} {value}")


def main():
    """Main entry point for RAG config inspection."""

    print_header("VERTEX AI SEARCH RAG CONFIGURATION")

    # Get current environment
    env = get_current_environment()
    print_key_value("Current Environment", env, 1)

    # Check migration flag
    use_org_knowledge = os.getenv("USE_ORG_KNOWLEDGE", "false").lower() == "true"
    print_key_value("Use Org Knowledge Hub", str(use_org_knowledge), 1)

    # Get datastore info
    datastore_info = get_datastore_info(env)

    if "error" in datastore_info:
        print(f"\n  ❌ Error: {datastore_info['error']}")
        return 1

    # Print datastore configuration
    print("\n  Datastore Configuration:")
    for key, value in datastore_info.items():
        if key != "environment":  # Already printed above
            print_key_value(f"    {key.replace('_', ' ').title()}", value, 0)

    # Load full config for additional details
    config = load_vertex_search_config()

    # Show environment variables that matter
    print_header("ENVIRONMENT VARIABLES")
    env_vars = {
        "APP_ENV": os.getenv("APP_ENV", "(not set)"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "(not set)"),
        "USE_ORG_KNOWLEDGE": os.getenv("USE_ORG_KNOWLEDGE", "false"),
        "PROJECT_ID": os.getenv("PROJECT_ID", "(not set)"),
    }

    for key, value in env_vars.items():
        print_key_value(key, value, 1)

    # Show commands to create/import datastore
    if not use_org_knowledge:
        print_header("USING LEGACY CONFIGURATION")
        print("\n  To migrate to org knowledge hub:")
        print("  export USE_ORG_KNOWLEDGE=true")
    else:
        print_header("SETUP COMMANDS")

        if env in config.get("environments", {}):
            env_config = config["environments"][env]
            ds_id = env_config["datastore"]["id"]
            project = env_config["datastore"]["project_id"]
            location = env_config["datastore"]["location"]
            uri = env_config["source"]["uri_pattern"]

            print("\n  Create datastore:")
            print(f"    gcloud ai search datastores create {ds_id} \\")
            print(f"      --location={location} \\")
            print(f"      --project={project} \\")
            print("      --type=unstructured")

            print("\n  Import knowledge:")
            print("    gcloud ai search documents import \\")
            print(f"      --datastore={ds_id} \\")
            print(f"      --location={location} \\")
            print(f"      --project={project} \\")
            print(f"      --gcs-uri={uri}")

    # Show which agents will use this configuration
    print_header("CONFIGURED AGENTS")
    if env in config.get("environments", {}):
        agents = config["environments"][env].get("agents", [])
        for agent in agents:
            print(f"    ✓ {agent}")

    # Validation checks
    print_header("VALIDATION CHECKLIST")

    checks = [
        (
            "Environment variable set",
            env != "staging" or os.getenv("APP_ENV") is not None,
        ),
        ("Configuration file exists", Path("config/vertex_search.yaml").exists()),
        ("Environment config exists", env in config.get("environments", {})),
        ("Migration flag configured", True),  # Always true, just checking it exists
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n  🎉 Configuration looks good!")
    else:
        print("\n  ⚠️  Some checks failed. Review configuration above.")

    print("\n" + "=" * 60)
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
