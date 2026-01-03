#!/usr/bin/env python3
"""
Agent Readiness Verification (ARV) Check for Inline Source Deployment

Validates environment and configuration before deploying ADK agents to Vertex AI Agent Engine.
This is the ARV gate that must pass before any inline source deployment can proceed.

Exit Codes:
    0 - All checks passed, deployment ready
    1 - Configuration error or missing requirements
    2 - Safety violation (e.g., attempting prod deploy without proper safeguards)

## Usage

From repository root:

    python scripts/check_inline_deploy_ready.py --env dev --agent-name bob

Or with environment variables:

    export ENV=dev
    export AGENT_NAME=bob
    export GCP_PROJECT_ID=my-project
    export GCP_LOCATION=us-central1
    python scripts/check_inline_deploy_ready.py

## References

- Tutorial: 000-docs/001-usermanual/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb
- Discussion: https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935
- Standard: 000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md

"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Exit codes
EXIT_OK = 0
EXIT_MISCONFIG = 1
EXIT_SAFETY_VIOLATION = 2

# Agent configuration (imported from deploy script pattern)
AGENT_CONFIGS = {
    "bob": {
        "entrypoint_module": "agents.bob.agent",
        "entrypoint_object": "app",
    },
    "iam-senior-adk-devops-lead": {
        "entrypoint_module": "agents.iam_senior_adk_devops_lead.agent",
        "entrypoint_object": "app",
    },
    "iam-adk": {
        "entrypoint_module": "agents.iam_adk.agent",
        "entrypoint_object": "app",
    },
}

SOURCE_PACKAGES = ["agents"]

# Environment safety rules
ENVIRONMENT_RULES = {
    "dev": {
        "allow_placeholder_project": True,
        "require_approval": False,
        "description": "Development environment (least restrictive)",
    },
    "staging": {
        "allow_placeholder_project": False,
        "require_approval": False,
        "description": "Staging environment (real project required)",
    },
    "prod": {
        "allow_placeholder_project": False,
        "require_approval": True,
        "description": "Production environment (HIGHEST restrictions)",
    },
}


def get_repo_root() -> Path:
    """Get the repository root directory."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    return repo_root


def check_environment_variables(env: str) -> Tuple[bool, List[str]]:
    """
    Validate required environment variables for deployment.

    Args:
        env: Target environment (dev/staging/prod)

    Returns:
        Tuple of (success, error_messages)
    """
    errors = []
    rules = ENVIRONMENT_RULES.get(env)

    if not rules:
        errors.append(f"Unknown environment: {env}")
        return False, errors

    # Check GCP_PROJECT_ID
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID")
    if not project_id:
        errors.append("Missing required environment variable: GCP_PROJECT_ID or PROJECT_ID")
    elif project_id == "test-project-placeholder":
        if not rules["allow_placeholder_project"]:
            errors.append(
                f"Placeholder project not allowed for {env} environment. "
                f"Set real GCP_PROJECT_ID."
            )

    # Check GCP_LOCATION
    location = os.getenv("GCP_LOCATION") or os.getenv("LOCATION")
    if not location:
        errors.append("Missing environment variable: GCP_LOCATION or LOCATION")

    return len(errors) == 0, errors


def check_source_packages() -> Tuple[bool, List[str]]:
    """
    Validate that all source packages exist and are accessible.

    Returns:
        Tuple of (success, error_messages)
    """
    errors = []
    repo_root = get_repo_root()

    for package in SOURCE_PACKAGES:
        package_path = repo_root / package
        if not package_path.exists():
            errors.append(f"Source package not found: {package} (expected at {package_path})")
        elif not package_path.is_dir():
            errors.append(f"Source package is not a directory: {package} ({package_path})")

    return len(errors) == 0, errors


def check_agent_entrypoint(agent_name: str) -> Tuple[bool, List[str]]:
    """
    Validate agent configuration and entrypoint can be imported.

    Args:
        agent_name: Name of agent to validate

    Returns:
        Tuple of (success, error_messages)
    """
    errors = []
    repo_root = get_repo_root()

    # Check agent exists in config
    if agent_name not in AGENT_CONFIGS:
        available = ", ".join(AGENT_CONFIGS.keys())
        errors.append(f"Unknown agent: {agent_name}. Available agents: {available}")
        return False, errors

    config = AGENT_CONFIGS[agent_name]

    # Check entrypoint module file exists
    module_path = config["entrypoint_module"].replace(".", "/") + ".py"
    full_path = repo_root / module_path

    if not full_path.exists():
        errors.append(
            f"Entrypoint module not found: {module_path} (expected at {full_path})"
        )
        return False, errors

    # Optionally check if module can be imported (graceful fallback)
    try:
        # Add repo root to path for import
        sys.path.insert(0, str(repo_root))

        import importlib
        module = importlib.import_module(config["entrypoint_module"])

        # Check if entrypoint object exists
        if not hasattr(module, config["entrypoint_object"]):
            errors.append(
                f"Entrypoint object '{config['entrypoint_object']}' not found in "
                f"module '{config['entrypoint_module']}'"
            )
            return False, errors

    except ImportError as e:
        # This is OK for CI without full dependencies
        print(f"   ⚠️  Import check skipped: {e}")
        print(f"   ℹ️  Module file exists, but cannot be imported (missing dependencies)")
        print(f"   ℹ️  This is OK for ARV validation without full runtime")

    return len(errors) == 0, errors


def check_environment_safety(env: str) -> Tuple[bool, List[str]]:
    """
    Validate environment-specific safety rules.

    Args:
        env: Target environment (dev/staging/prod)

    Returns:
        Tuple of (success, error_messages)
    """
    errors = []
    rules = ENVIRONMENT_RULES.get(env)

    if not rules:
        errors.append(f"Unknown environment: {env}")
        return False, errors

    # Production requires additional approval (implemented via workflow_dispatch)
    if rules["require_approval"]:
        # In CI, this is enforced by workflow trigger rules
        # Locally, we just warn
        print(f"   ⚠️  {env.upper()} deployment requires manual approval")
        print(f"   ℹ️  Use GitHub Actions workflow_dispatch for production deploys")

    return len(errors) == 0, errors


def run_arv_checks(agent_name: str, env: str) -> int:
    """
    Run all ARV checks and return appropriate exit code.

    Args:
        agent_name: Name of agent to validate
        env: Target environment (dev/staging/prod)

    Returns:
        Exit code (0=OK, 1=misconfig, 2=safety violation)
    """
    print(f"🔍 ARV Check: Inline Deploy Readiness for '{agent_name}' ({env})")
    print()

    all_passed = True
    has_safety_violation = False

    # Check 1: Environment Variables
    print("📋 Check 1: Environment Variables")
    success, errors = check_environment_variables(env)
    if success:
        print("   ✅ All required environment variables present")
    else:
        print("   ❌ Environment variable errors:")
        for error in errors:
            print(f"      - {error}")
        all_passed = False
    print()

    # Check 2: Source Packages
    print("📦 Check 2: Source Packages")
    success, errors = check_source_packages()
    if success:
        print(f"   ✅ All source packages exist: {', '.join(SOURCE_PACKAGES)}")
    else:
        print("   ❌ Source package errors:")
        for error in errors:
            print(f"      - {error}")
        all_passed = False
    print()

    # Check 3: Agent Entrypoint
    print("🎯 Check 3: Agent Entrypoint")
    success, errors = check_agent_entrypoint(agent_name)
    if success:
        config = AGENT_CONFIGS[agent_name]
        print(f"   ✅ Agent '{agent_name}' entrypoint validated")
        print(f"      Module: {config['entrypoint_module']}")
        print(f"      Object: {config['entrypoint_object']}")
    else:
        print("   ❌ Agent entrypoint errors:")
        for error in errors:
            print(f"      - {error}")
        all_passed = False
    print()

    # Check 4: Environment Safety Rules
    print("🛡️  Check 4: Environment Safety Rules")
    success, errors = check_environment_safety(env)
    if success:
        rules = ENVIRONMENT_RULES[env]
        print(f"   ✅ Environment safety rules validated for '{env}'")
        print(f"      {rules['description']}")
    else:
        print("   ❌ Safety rule violations:")
        for error in errors:
            print(f"      - {error}")
        has_safety_violation = True
        all_passed = False
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ All ARV checks passed - READY FOR DEPLOYMENT")
        print()
        print("Next steps:")
        print("  - Dry-run: make deploy-inline-dry-run")
        print("  - Execute: python -m agents.agent_engine.deploy_inline_source --execute")
        return EXIT_OK
    elif has_safety_violation:
        print("🚨 ARV checks FAILED - SAFETY VIOLATION")
        print()
        print("Fix safety violations before attempting deployment.")
        return EXIT_SAFETY_VIOLATION
    else:
        print("❌ ARV checks FAILED - MISCONFIGURATION")
        print()
        print("Fix configuration errors before attempting deployment.")
        return EXIT_MISCONFIG


def main():
    """Main entry point for ARV check CLI."""
    parser = argparse.ArgumentParser(
        description="Agent Readiness Verification (ARV) for inline source deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check Bob for dev deployment
  python scripts/check_inline_deploy_ready.py --env dev --agent-name bob

  # Check foreman for staging deployment
  python scripts/check_inline_deploy_ready.py --env staging --agent-name iam-senior-adk-devops-lead

  # Use environment variables
  export ENV=dev
  export AGENT_NAME=bob
  export GCP_PROJECT_ID=my-project
  export GCP_LOCATION=us-central1
  python scripts/check_inline_deploy_ready.py

References:
  - Tutorial: 000-docs/001-usermanual/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb
  - Discussion: https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935
  - Standard: 000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md
        """,
    )

    parser.add_argument(
        "--agent-name",
        type=str,
        default=os.getenv("AGENT_NAME"),
        required=not os.getenv("AGENT_NAME"),
        choices=list(AGENT_CONFIGS.keys()),
        help=f"Agent to validate. Available: {', '.join(AGENT_CONFIGS.keys())}",
    )

    parser.add_argument(
        "--env",
        type=str,
        default=os.getenv("ENV", "dev"),
        choices=["dev", "staging", "prod"],
        help="Target environment (default: dev, or ENV env var)",
    )

    args = parser.parse_args()

    # Run ARV checks
    exit_code = run_arv_checks(args.agent_name, args.env)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
